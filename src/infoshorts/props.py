"""scenes（含時間）+ 音訊 → Remotion props.json。秒 → frame（30 fps）只在這裡轉。

音訊與字幕檔以「相對於 run 目錄」的檔名給 Remotion，render 時用 --public-dir 指到 run 目錄，
元件用 staticFile() 讀，避免絕對路徑與 Windows/WSL 路徑差異。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

FPS = 30
SIZES = {"9:16": (1080, 1920), "16:9": (1920, 1080)}
BGM_VOLUME = 0.25  # 無旁白時
DUCK_VOLUME = 0.08  # 旁白進行中（ducking）
SCENE_BUFFER = 0.4  # 與 tts.SCENE_BUFFER 一致：每段旁白後的緩衝，這段不算「有聲」


def to_frame(sec: float) -> int:
    return int(round(sec * FPS))


def build_props(
    content: dict[str, Any],
    scenes: list[dict[str, Any]],
    run_dir: Path,
    *,
    total_seconds: float,
    theme: str = "neutral",
    bgm: Path | None = None,
) -> dict[str, Any]:
    width, height = SIZES[content.get("aspect", "9:16")]
    total_frames = to_frame(total_seconds)
    out_scenes = []
    for i, s in enumerate(scenes):
        start = to_frame(s["start"])
        end = total_frames if i == len(scenes) - 1 else to_frame(scenes[i + 1]["start"])
        out_scenes.append({"type": s["type"], "startFrame": start, "endFrame": end, "props": s["props"]})

    bgm_name = None
    if bgm:
        bgm_name = "bgm" + bgm.suffix.lower()
        target = run_dir / bgm_name
        if bgm.resolve() != target.resolve():
            shutil.copyfile(bgm, target)

    # 有旁白的區間（frame），給 Remotion 做 BGM ducking；靜音 scene 不算
    voice_ranges = [
        [to_frame(s["start"]), to_frame(s.get("speech_end") or (s["end"] - SCENE_BUFFER))]
        for s in scenes
        if (s.get("narration") or "").strip()
    ]

    return {
        "fps": FPS,
        "width": width,
        "height": height,
        "durationInFrames": total_frames,
        "theme": theme,
        "kind": content.get("kind", "generic"),
        "meta": {
            "title": content["title"],
            "date": content.get("date"),
            "brand": content.get("brand"),
            "disclaimer": bool(content.get("disclaimer")),
        },
        "audio": {
            "voice": "voice.mp3",
            "bgm": bgm_name,
            "bgmVolume": BGM_VOLUME,
            "duckVolume": DUCK_VOLUME,
            "voiceRanges": voice_ranges,
        },
        "captions": "voice.srt",
        "scenes": out_scenes,
    }


def dump(props: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
