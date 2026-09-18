"""TTS：每段旁白各自合成 → 補 0.4s 緩衝 → concat → 回填每個 scene 的起迄秒 → 合併字幕（時間碼位移）。

引擎介面：`Engine.synthesize(text, mp3_path) -> list[Word]`；預設 edge-tts，備援 Kokoro（Phase 2）。
字幕時間碼直接來自 edge-tts 的 WordBoundary 事件，不用 Whisper（ADR-002）。
字幕切分：每段 ≤ 14 個中文字（英文單字以字母數 / 2 計）、≤ 2 行；詞間停頓 > 0.35s 也切。
"""

from __future__ import annotations

import asyncio
import re
import shutil
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Protocol

from infoshorts import ffmpeg
from infoshorts import format as fmt

DEFAULT_VOICE = "zh-TW-HsiaoChenNeural"
DEFAULT_RATE = "+5%"
SCENE_BUFFER = 0.4  # 每段旁白後的緩衝秒數
SILENT_SCENE = 2.5  # 沒有旁白的 scene 固定長度
MAX_CUE_CHARS = 14
CUE_GAP_BREAK = 0.35
CUE_TAIL = 0.15  # 最後一個字結束後字幕再停留的秒數
SAMPLE_RATE = 24000
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"  # 最終旁白音量正規化到 -16 LUFS（Kinocut 門檻 -20 ~ -12）


@dataclass
class Word:
    text: str
    start: float  # 秒，相對於該段音檔
    end: float


@dataclass
class Cue:
    start: float
    end: float
    text: str


class Engine(Protocol):
    name: str

    def synthesize(self, text: str, mp3_path: Path) -> list[Word]: ...


class EdgeEngine:
    name = "edge"

    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> None:
        self.voice = voice
        self.rate = rate

    def synthesize(self, text: str, mp3_path: Path) -> list[Word]:
        return asyncio.run(self._run(text, mp3_path))

    async def _run(self, text: str, mp3_path: Path) -> list[Word]:
        import edge_tts

        comm = edge_tts.Communicate(text, self.voice, rate=self.rate, boundary="WordBoundary")
        audio = bytearray()
        words: list[Word] = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk.get("data", b""))
            elif chunk["type"] == "WordBoundary":
                offset = float(chunk.get("offset", 0))
                dur = float(chunk.get("duration", 0))
                start = offset / 10_000_000
                words.append(Word(str(chunk.get("text", "")), start, start + dur / 10_000_000))
        if not audio:
            raise RuntimeError("edge-tts 沒有回傳音訊（服務可能失效，考慮 --engine kokoro）")
        mp3_path.write_bytes(bytes(audio))
        return words


KOKORO_REPO = "hexgrad/Kokoro-82M"
KOKORO_DEFAULT_VOICE = "zf_xiaobei"  # 中文女聲；男聲 zm_yunjian / zm_yunxi


def _rate_to_speed(rate: str) -> float:
    """edge-tts 風格的 '+5%' → Kokoro speed 1.05。"""
    m = re.fullmatch(r"([+-]?)(\d+(?:\.\d+)?)%", rate.strip())
    if not m:
        return 1.0
    pct = float(m.group(2)) * (-1 if m.group(1) == "-" else 1)
    return max(0.5, min(2.0, 1.0 + pct / 100))


PAUSE_WEIGHT = {"。": 1.6, "！": 1.6, "？": 1.6, "；": 1.2, "，": 0.8, "、": 0.5, "：": 0.8, ".": 1.6, ",": 0.8}
_SPREAD_RE = re.compile(r"[㐀-鿿]|[A-Za-z0-9][A-Za-z0-9.'-]*|[。！？；，、：.,]")


def spread_words(text: str, start: float, duration: float) -> list[Word]:
    """沒有逐字時間碼時的退路：把文字拆成字／英文詞，依字寬在 [start, start+duration] 內等比分配。

    標點不輸出成詞，但佔停頓權重（PAUSE_WEIGHT），讓句尾的字幕不會提早結束。
    """
    tokens = _SPREAD_RE.findall(text)
    if not tokens:
        return []
    weights = [PAUSE_WEIGHT.get(t, _width(t)) for t in tokens]
    total = sum(weights)
    out: list[Word] = []
    t = start
    for tok, w in zip(tokens, weights, strict=True):
        d = duration * w / total
        if tok not in PAUSE_WEIGHT:
            out.append(Word(tok, t, t + d))
        t += d
    return out


class KokoroEngine:
    """離線備援：Kokoro-82M（CPU）。安裝：`uv sync --group kokoro`。

    中文 pipeline（lang_code='z'）沒有逐詞時間碼，而且整段文字通常是單一 chunk，
    字幕時間用 spread_words 依字寬＋標點停頓權重估算（ADR-013）。
    """

    name = "kokoro"

    def __init__(self, voice: str = KOKORO_DEFAULT_VOICE, rate: str = "+0%") -> None:
        self.voice = voice
        self.speed = _rate_to_speed(rate)
        self._pipeline: Any = None

    def _load(self) -> Any:
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
            except ImportError as e:
                raise RuntimeError("Kokoro 未安裝：uv sync --group kokoro") from e
            self._pipeline = KPipeline(lang_code="z", repo_id=KOKORO_REPO)
        return self._pipeline

    def synthesize(self, text: str, mp3_path: Path) -> list[Word]:
        import numpy as np
        import soundfile as sf

        pipeline = self._load()
        chunks: list[Any] = []
        words: list[Word] = []
        offset = 0.0
        for r in pipeline(text, voice=self.voice, speed=self.speed):
            if r.audio is None:
                continue
            audio = r.audio.numpy() if hasattr(r.audio, "numpy") else np.asarray(r.audio)
            dur = len(audio) / SAMPLE_RATE
            tokens = getattr(r, "tokens", None)
            timed = [t for t in (tokens or []) if getattr(t, "start_ts", None) is not None]
            if timed:
                words.extend(Word(t.text, offset + float(t.start_ts), offset + float(t.end_ts)) for t in timed)
            else:
                words.extend(spread_words(r.graphemes, offset, dur))
            chunks.append(audio)
            offset += dur
        if not chunks:
            raise RuntimeError("Kokoro 沒有產生音訊")
        wav = mp3_path.with_suffix(".kokoro.wav")
        sf.write(str(wav), np.concatenate(chunks), SAMPLE_RATE)
        ffmpeg.run(["-i", str(wav), "-c:a", "libmp3lame", "-q:a", "2", str(mp3_path)])
        wav.unlink(missing_ok=True)
        return words


def make_engine(name: str, voice: str | None, rate: str) -> Engine:
    if name == "edge":
        return EdgeEngine(voice or DEFAULT_VOICE, rate)
    if name == "kokoro":
        return KokoroEngine(voice or KOKORO_DEFAULT_VOICE, rate)
    raise ValueError(f"未知 TTS 引擎：{name}")


# ---------------------------------------------------------------- 顯示文字對齊


def align_display(words: list[Word], marked: str) -> list[Word]:
    """把 TTS 依「唸法」回傳的詞，換成字幕要「顯示」的文字（format.mark 的雙軌）。

    唸法裡被替換的區段（例如「四萬七千一百六十」）視為一個整體：所有落在該區段的詞合併成一個 Word，
    文字改成顯示形式（「47,160」）、時間取合併範圍。其他詞原樣保留。
    """
    segs = fmt.segments(marked)
    if not any(sub for _, _, sub in segs):
        return words
    # 每個區段在「唸法全文」裡的位置
    spans: list[tuple[int, int, str, bool]] = []  # (start, end, display, is_sub)
    pos = 0
    for disp, spk, sub in segs:
        spans.append((pos, pos + len(spk), disp, sub))
        pos += len(spk)
    spoken_text = "".join(spk for _, spk, _ in segs)

    def display_for(i: int, j: int) -> str:
        out = []
        for a, b, disp, sub in spans:
            if b <= i or a >= j:
                continue
            out.append(disp if sub else spoken_text[max(a, i) : min(b, j)])
        return "".join(out)

    def sub_hit(i: int, j: int) -> int | None:
        for k, (a, b, _, sub) in enumerate(spans):
            if sub and a < j and b > i:
                return k
        return None

    out: list[Word] = []
    cursor = 0
    group: list[Word] | None = None
    group_range = [0, 0]
    group_key: int | None = None

    def flush() -> None:
        nonlocal group
        if group:
            out.append(Word(display_for(*group_range), min(w.start for w in group), max(w.end for w in group)))
            group = None

    for w in words:
        token = w.text.strip()
        i = spoken_text.find(token, cursor) if token else -1
        if i < 0:
            flush()
            out.append(w)
            continue
        j = i + len(token)
        cursor = j
        key = sub_hit(i, j)
        if key is None:
            flush()
            out.append(Word(display_for(i, j), w.start, w.end))
        elif group is not None and key == group_key:
            group.append(w)
            group_range[1] = j
        else:
            flush()
            group, group_key, group_range = [w], key, [i, j]
    flush()
    return out


# ---------------------------------------------------------------- 字幕切分


def _width(text: str) -> float:
    """中文字算 1，其他（英數）算 0.5。"""
    return sum(1.0 if ord(ch) > 0x2E7F else 0.5 for ch in text)


def _join(a: str, b: str) -> str:
    """中文相接不加空白；英文詞旁邊加空白（Kinocut 這個 MCP）；數字貼著中文不加（2026年6月、701點）。"""
    if not a:
        return b
    if re.search(r"[A-Za-z]$", a) or re.match(r"^[A-Za-z]", b):
        return a + " " + b
    if re.search(r"[0-9]$", a) and re.match(r"^[0-9]", b):
        return a + " " + b
    return a + b


STRONG_PUNCT = "。！？；!?;"
WEAK_PUNCT = "，、：,:"
MIN_WEAK_BREAK = 4  # 逗號前至少累積這麼多字寬才在逗號切（「九月二十日，本週三件事」會在逗號切）


def punctuation_before(words: list[Word], text: str) -> list[str]:
    """對照旁白原文，找出每個 WordBoundary 詞「前面」的標點（edge-tts 的事件不含標點）。

    回傳與 words 等長的字串列表；找不到對應就給空字串。
    """
    out: list[str] = []
    pos = 0
    for w in words:
        token = w.text.strip()
        idx = text.find(token, pos) if token else -1
        if idx < 0:
            out.append("")
            continue
        between = text[pos:idx]
        punct = "".join(ch for ch in between if ch in STRONG_PUNCT + WEAK_PUNCT)
        out.append(punct[-1] if punct else "")
        pos = idx + len(token)
    return out


def build_cues(
    words: list[Word],
    text: str | None = None,
    *,
    max_chars: int = MAX_CUE_CHARS,
    gap_break: float = CUE_GAP_BREAK,
) -> list[Cue]:
    """把 WordBoundary 事件切成字幕。

    規則：≤ max_chars 字寬；句號／分號一定切；逗號在累積 ≥ MIN_WEAK_BREAK 字寬時切；
    詞間停頓 > gap_break 也切；超長時優先回溯到最近的逗號切，避免把詞切成兩半。
    """
    puncts = punctuation_before(words, text) if text else [""] * len(words)
    cues: list[Cue] = []
    cur: list[Word] = []
    cur_text = ""
    weak_at: int | None = None  # 最近一個逗號之前的詞數（回溯切點）
    weak_text = ""

    def flush(upto: int | None = None) -> None:
        nonlocal cur, cur_text, weak_at, weak_text
        if not cur:
            return
        if upto is None or upto >= len(cur):
            cues.append(Cue(cur[0].start, cur[-1].end, cur_text))
            cur, cur_text = [], ""
        else:
            head, tail = cur[:upto], cur[upto:]
            cues.append(Cue(head[0].start, head[-1].end, weak_text))
            cur = tail
            cur_text = ""
            for w in tail:
                cur_text = _join(cur_text, w.text.strip())
        weak_at, weak_text = None, ""

    for i, w in enumerate(words):
        token = w.text.strip()
        if not token:
            continue
        punct = puncts[i]
        if cur:
            gap = (w.start - cur[-1].end) > gap_break
            if punct in STRONG_PUNCT and punct or gap:
                flush()
            elif punct and punct in WEAK_PUNCT:
                if _width(cur_text) >= MIN_WEAK_BREAK:
                    flush()
                else:
                    weak_at, weak_text = len(cur), cur_text
        candidate = _join(cur_text, token)
        if cur and _width(candidate) > max_chars:
            if weak_at:
                flush(weak_at)
                candidate = _join(cur_text, token)
                if _width(candidate) > max_chars:
                    flush()
                    candidate = token
            else:
                flush()
                candidate = token
        cur.append(w)
        cur_text = candidate
    flush()
    # 字幕之間不留空洞：每段延伸到下一段開始（最多 +CUE_TAIL）
    for i, c in enumerate(cues):
        limit = cues[i + 1].start if i + 1 < len(cues) else c.end + CUE_TAIL
        c.end = min(c.end + CUE_TAIL, limit) if limit > c.end else c.end
    return cues


def _srt_time(sec: float) -> str:
    td = timedelta(seconds=max(sec, 0))
    total_ms = int(round(td.total_seconds() * 1000))
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: list[Cue], path: Path) -> None:
    blocks = [f"{i}\n{_srt_time(c.start)} --> {_srt_time(c.end)}\n{c.text}\n" for i, c in enumerate(cues, 1)]
    path.write_text("\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")


# ---------------------------------------------------------------- 主流程


def _silence_wav(path: Path, seconds: float) -> None:
    ffmpeg.run(
        [
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={SAMPLE_RATE}:cl=mono",
            "-t",
            f"{seconds:.3f}",
            "-c:a",
            "pcm_s16le",
            str(path),
        ]
    )


def _to_padded_wav(mp3: Path, wav: Path, pad: float) -> float:
    """mp3 → 單聲道 wav 並在尾端補 pad 秒靜音；回傳補靜音「前」的語音長度。"""
    speech = ffmpeg.duration(mp3)
    ffmpeg.run(
        [
            "-i",
            str(mp3),
            "-af",
            f"apad=pad_dur={pad:.3f}",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ]
    )
    return speech


def synthesize_scenes(
    scenes: list[dict[str, Any]],
    run_dir: Path,
    *,
    engine: Engine,
) -> float:
    """就地回填 scenes[i]['start'/'end']，輸出 run_dir/voice.mp3 + voice.srt。回傳總長（秒）。"""
    seg_dir = run_dir / "seg"
    if seg_dir.exists():
        shutil.rmtree(seg_dir)
    seg_dir.mkdir(parents=True)

    t = 0.0
    wavs: list[Path] = []
    cues: list[Cue] = []
    for s in scenes:
        idx = s["idx"]
        marked = (s.get("narration_marked") or s.get("narration") or "").strip()
        narration = fmt.spoken(marked)
        wav = seg_dir / f"{idx:02d}.wav"
        if narration:
            mp3 = seg_dir / f"{idx:02d}.mp3"
            words = engine.synthesize(narration, mp3)
            speech = _to_padded_wav(mp3, wav, SCENE_BUFFER)
            seg_len = ffmpeg.duration(wav)
            shown = align_display(words, marked)  # 唸「四萬七千一百六十」→ 字幕顯示「47,160」
            for c in build_cues(shown, fmt.display(marked)):
                cues.append(Cue(t + c.start, min(t + c.end, t + speech + SCENE_BUFFER), c.text))
            # 實際語音結束點（最後一個字的結尾；TTS 通常在段尾留約 0.7s 靜音），給 BGM ducking 用
            speech_end = max((w.end for w in words), default=speech)
            s["speech_end"] = round(t + min(speech_end, speech), 3)
        else:
            _silence_wav(wav, SILENT_SCENE)
            seg_len = SILENT_SCENE
            s["speech_end"] = None
        s["start"] = round(t, 3)
        s["end"] = round(t + seg_len, 3)
        t += seg_len
        wavs.append(wav)

    concat_list = seg_dir / "concat.txt"
    concat_list.write_text("".join(f"file '{w.name}'\n" for w in wavs), encoding="utf-8")
    voice_wav = run_dir / "voice.wav"
    ffmpeg.run(["-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "pcm_s16le", str(voice_wav)])
    ffmpeg.run(
        [
            "-i",
            str(voice_wav),
            "-af",
            LOUDNORM,
            "-ar",
            str(SAMPLE_RATE),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(run_dir / "voice.mp3"),
        ]
    )
    write_srt(cues, run_dir / "voice.srt")
    total = ffmpeg.duration(voice_wav)
    if scenes:
        scenes[-1]["end"] = round(total, 3)
    return total
