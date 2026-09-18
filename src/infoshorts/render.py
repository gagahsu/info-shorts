"""呼叫 Remotion CLI render。GPU 不高 → CPU、--concurrency 保守。"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = ROOT / "remotion"
COMPOSITION = "Short"


def npx() -> str:
    exe = shutil.which("npx.cmd") or shutil.which("npx")
    if not exe:
        raise RuntimeError("找不到 npx，請安裝 Node.js 22+")
    return exe


def render(props_path: Path, run_dir: Path, out_path: Path, *, concurrency: int = 2, log: str = "warn") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        npx(),
        "remotion",
        "render",
        "src/index.ts",
        COMPOSITION,
        str(out_path.resolve()),
        f"--props={props_path.resolve()}",
        f"--public-dir={run_dir.resolve()}",
        f"--concurrency={concurrency}",
        f"--log={log}",
        "--codec=h264",
    ]
    env = {**os.environ, "CI": "true"}
    subprocess.run(cmd, cwd=REMOTION_DIR, check=True, env=env)
    if not out_path.is_file():
        raise RuntimeError(f"Remotion 沒有產出 {out_path}")
    return out_path
