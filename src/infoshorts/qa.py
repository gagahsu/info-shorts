"""品檢：呼叫 Kinocut（probe / quality_check / metric_qc）。任一硬性檢查失敗就回傳 ok=False。

硬性檢查（docs/PIPELINE.md Step 6）：
- 時長與 props 一致（±0.5s）
- 解析度與 props 一致（預設 1080×1920）
- 音訊與影片等長（±0.5s）
- 音量：整體 LUFS 在 Kinocut 的門檻內（-20 ~ -12 LUFS，true peak ≤ -1 dBTP）
- 無連續黑幀 > 0.5s（Kinocut 只給整體黑幀比例；連續段落用 ffmpeg blackdetect 補）

Kinocut 其他視覺檢查（亮度、對比、飽和、色偏）只列為 advisory，不擋出片：深色 theme 天生偏暗。
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from infoshorts import ffmpeg

DURATION_TOL = 0.5
MAX_BLACK_RUN = 0.5
# blackdetect 的像素門檻：ffmpeg 預設 0.10 會把深灰底（neutral bg 亮度約 17/255 = 0.067）的空曠畫面當黑幀，
# 這裡只抓「真的黑」（亮度 < 10/255），render 失敗產生的全黑幀仍抓得到。
BLACK_PIX_TH = 0.04


@dataclass
class Check:
    name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    video: str
    ok: bool
    checks: list[Check]
    advisory: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "video": self.video,
            "ok": self.ok,
            "checks": [asdict(c) for c in self.checks],
            "advisory": self.advisory,
        }

    def summary(self) -> str:
        lines = [f"QA {'PASS' if self.ok else 'FAIL'}: {self.video}"]
        for c in self.checks:
            lines.append(f"  [{'ok' if c.passed else 'FAIL'}] {c.name}: {c.message}")
        for a in self.advisory:
            lines.append(f"  [advisory] {a}")
        return "\n".join(lines)


def _black_runs(video: Path) -> list[tuple[float, float]]:
    """ffmpeg blackdetect：回傳長度 > MAX_BLACK_RUN 的黑幀段落。"""
    cp = subprocess.run(
        [
            ffmpeg.ffmpeg(),
            "-hide_banner",
            "-i",
            str(video),
            "-vf",
            f"blackdetect=d={MAX_BLACK_RUN}:pix_th={BLACK_PIX_TH}",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    runs = []
    for m in re.finditer(r"black_start:(\S+) black_end:(\S+)", cp.stderr):
        runs.append((float(m.group(1)), float(m.group(2))))
    return runs


def run_qa(video: Path, props: dict[str, Any]) -> Report:
    ffmpeg.export_env()  # Kinocut 讀 KINOCUT_FFMPEG_EXECUTABLE，必須在 import 前設好
    logging.getLogger("kinocut").setLevel(logging.CRITICAL)  # 它的 warning 很吵，結果都在 report 裡
    from kinocut.engine_probe import probe
    from kinocut.quality_guardrails import quality_check
    from kinocut.watching.metrics import run_metric_qc

    checks: list[Check] = []
    advisory: list[str] = []
    path = str(video.resolve())

    info = probe(path)
    expected = props["durationInFrames"] / props["fps"]
    dur = float(info.duration)
    checks.append(
        Check(
            "duration",
            abs(dur - expected) <= DURATION_TOL,
            f"{dur:.2f}s（預期 {expected:.2f}s ± {DURATION_TOL}）",
            {"actual": dur, "expected": expected},
        )
    )
    w, h = int(info.width), int(info.height)
    checks.append(
        Check(
            "resolution",
            (w, h) == (props["width"], props["height"]),
            f"{w}×{h}（預期 {props['width']}×{props['height']}）",
        )
    )

    audio_dur = _audio_duration(path)
    if audio_dur is None:
        checks.append(Check("audio_present", False, "沒有音軌"))
    else:
        checks.append(
            Check(
                "audio_length",
                abs(audio_dur - dur) <= DURATION_TOL,
                f"音軌 {audio_dur:.2f}s vs 影片 {dur:.2f}s",
                {"audio": audio_dur, "video": dur},
            )
        )

    report = quality_check(path)
    for c in report.get("checks", []):
        if c["name"] == "audio_levels":
            checks.append(Check("loudness", bool(c["passed"]), c["message"], c.get("details", {})))
        elif not c["passed"]:
            advisory.append(f"kinocut {c['name']}: {c['message']}")
    if not any(c.name == "loudness" for c in checks):
        checks.append(Check("loudness", False, "Kinocut 沒有回傳 audio_levels 檢查"))

    findings = run_metric_qc(path)
    for f in findings:
        if f.check_id.startswith("black") and f.severity == "fail":
            checks.append(Check("black_ratio", False, f.message, f.evidence or {}))
    runs = _black_runs(video)
    checks.append(
        Check(
            "black_frames",
            not runs,
            "無連續黑幀 > 0.5s" if not runs else "黑幀段落：" + ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in runs),
            {"runs": runs},
        )
    )

    ok = all(c.passed for c in checks)
    return Report(path, ok, checks, advisory)


def _audio_duration(path: str) -> float | None:
    cp = subprocess.run(
        [
            ffmpeg.ffprobe(),
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=duration",
            "-of",
            "json",
            path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        streams = json.loads(cp.stdout).get("streams", [])
    except json.JSONDecodeError:
        return None
    if not streams:
        return None
    d = streams[0].get("duration")
    return float(d) if d else None


def dump(report: Report, path: Path) -> None:
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
