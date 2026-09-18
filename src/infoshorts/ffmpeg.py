"""ffmpeg / ffprobe 定位與小工具。

Kinocut 需要 FFmpeg 6+；Windows 上 PATH 常被舊版（例如 miniconda 的 4.x）搶先，
所以這裡集中處理「找到夠新的 ffmpeg」並把路徑同步給 Kinocut 的環境變數。
"""

from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

MIN_MAJOR = 6


def _candidates() -> list[Path]:
    out: list[Path] = []
    env_dir = os.environ.get("INFOSHORTS_FFMPEG_DIR")
    if env_dir:
        out.append(Path(env_dir))
    env_exe = os.environ.get("KINOCUT_FFMPEG_EXECUTABLE")
    if env_exe:
        out.append(Path(env_exe).parent)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        pattern = os.path.join(local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "ffmpeg-*", "bin")
        out.extend(Path(p) for p in sorted(glob.glob(pattern), reverse=True))
    which = shutil.which("ffmpeg")
    if which:
        out.append(Path(which).parent)
    return out


def _version_of(exe: Path) -> int | None:
    try:
        text = subprocess.run([str(exe), "-version"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"ffmpeg version (?:n)?(\d+)", text)
    return int(m.group(1)) if m else None


@lru_cache(maxsize=1)
def ffmpeg_dir() -> Path:
    """回傳含 ffmpeg/ffprobe 的目錄；優先選版本 >= 6 的。"""
    exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    fallback: Path | None = None
    for d in _candidates():
        exe = d / exe_name
        if not exe.is_file():
            continue
        fallback = fallback or d
        v = _version_of(exe)
        if v is not None and v >= MIN_MAJOR:
            return d
    if fallback is None:
        raise RuntimeError("找不到 ffmpeg，請先安裝（建議 winget install Gyan.FFmpeg）或設定 INFOSHORTS_FFMPEG_DIR")
    return fallback


def ffmpeg() -> str:
    return str(ffmpeg_dir() / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"))


def ffprobe() -> str:
    return str(ffmpeg_dir() / ("ffprobe.exe" if os.name == "nt" else "ffprobe"))


def export_env() -> None:
    """把選到的 ffmpeg 同步給 Kinocut（它讀 KINOCUT_FFMPEG_EXECUTABLE / KINOCUT_FFPROBE_EXECUTABLE）。"""
    os.environ.setdefault("KINOCUT_FFMPEG_EXECUTABLE", ffmpeg())
    os.environ.setdefault("KINOCUT_FFPROBE_EXECUTABLE", ffprobe())
    d = str(ffmpeg_dir())
    if d not in os.environ.get("PATH", ""):
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def run(args: list[str], *, timeout: float = 600) -> subprocess.CompletedProcess[str]:
    cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)


def duration(path: str | Path) -> float:
    cp = subprocess.run(
        [ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(cp.stdout.strip())
