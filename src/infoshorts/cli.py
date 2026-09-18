"""CLI：`infoshorts build --adapter generic --input runs/<run>/input.json`。

依序：adapter → content.json → scenes.json（回報旁白稿）→ voice.mp3/srt → props.json → render → QA。
`--dry-run` 只跑到 scenes.json。QA 失敗回傳非零。
"""

from __future__ import annotations

import io
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from infoshorts import adapters, ffmpeg, tts
from infoshorts import content as content_mod
from infoshorts import props as props_mod
from infoshorts import qa as qa_mod
from infoshorts import render as render_mod
from infoshorts import scenes as scenes_mod

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"

app = typer.Typer(help="結構化資訊 → 直式短影音", no_args_is_help=True, add_completion=False)

# Windows 主控台常是 cp950；遇到印不出的字元用 ? 取代而不是整個炸掉
for stream in (sys.stdout, sys.stderr):
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(errors="replace")


def _slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9一-鿿]+", "-", text).strip("-").lower()
    return s or "untitled"


def _run_dir(input_path: Path, name: str | None) -> Path:
    if name:
        return RUNS / name
    if input_path.parent.parent == RUNS:  # 輸入已放在 runs/<run>/ 內
        return input_path.parent
    return RUNS / f"{date.today():%Y-%m-%d}-{_slug(input_path.stem)}"


@app.command()
def build(
    input: Annotated[Path, typer.Option("--input", "-i", exists=True, dir_okay=False, help="來源檔（generic：JSON）")],
    adapter: Annotated[str, typer.Option("--adapter", "-a", help="來源 adapter")] = "generic",
    run: Annotated[str | None, typer.Option("--run", help="runs/ 下的目錄名；預設 <今天>-<檔名>")] = None,
    voice: Annotated[str | None, typer.Option("--voice", help="TTS 聲音，預設 zh-TW-HsiaoChenNeural")] = None,
    rate: Annotated[str, typer.Option("--rate", help="語速，例如 +5%")] = tts.DEFAULT_RATE,
    engine: Annotated[str, typer.Option("--engine", help="edge | kokoro")] = "edge",
    bgm: Annotated[Path | None, typer.Option("--bgm", exists=True, dir_okay=False, help="背景音樂（可選）")] = None,
    theme: Annotated[str, typer.Option("--theme", help="remotion/src/theme.ts 裡的 theme 名")] = "neutral",
    concurrency: Annotated[int, typer.Option("--concurrency", help="Remotion render 並行數")] = 2,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="只跑到 scenes.json，檢查旁白稿")] = False,
) -> None:
    run_dir = _run_dir(input, run)
    run_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_dir.name
    typer.echo(f"▶ run: {run_dir}")

    # 原始輸入留底
    target_input = run_dir / f"input{input.suffix}"
    if input.resolve() != target_input.resolve():
        shutil.copyfile(input, target_input)

    # 1. adapter → content.json
    ad = adapters.get_adapter(adapter)
    raw_text = input.read_text(encoding="utf-8")
    raw = json.loads(raw_text) if input.suffix.lower() == ".json" else raw_text
    content = ad.to_content(raw, run_id=run_id)
    content_mod.dump(content, run_dir / "content.json")
    typer.echo(f"✓ content.json（{len(content['sections'])} sections，disclaimer={content.get('disclaimer')}）")

    # 2. scenes.json
    scenes = scenes_mod.build_scenes(content)
    scenes_mod.dump(scenes, run_dir / "scenes.json")
    typer.echo(f"✓ scenes.json（{len(scenes)} scenes）\n--- 旁白稿 ---\n{scenes_mod.narration_summary(scenes)}\n---")
    if dry_run:
        typer.echo("dry-run：到此為止")
        return

    # 3. TTS
    eng = tts.make_engine(engine, voice, rate)
    total = tts.synthesize_scenes(scenes, run_dir, engine=eng)
    scenes_mod.dump(scenes, run_dir / "scenes.json")
    typer.echo(f"✓ voice.mp3 + voice.srt（{total:.1f}s，引擎 {eng.name}）")
    target = content.get("target_duration") or 45
    if total > target * 1.4:
        typer.echo(f"⚠ 總長 {total:.1f}s 超過目標 {target}s 的 140%，考慮精簡旁白")

    # 4. props.json
    p = props_mod.build_props(content, scenes, run_dir, total_seconds=total, theme=theme, bgm=bgm)
    props_mod.dump(p, run_dir / "props.json")
    typer.echo(f"✓ props.json（{p['durationInFrames']} frames @ {p['fps']} fps）")

    # 5. render
    out = run_dir / "out" / f"{run_id}.mp4"
    typer.echo("▶ Remotion render（CPU，請稍候）…")
    render_mod.render(run_dir / "props.json", run_dir, out, concurrency=concurrency)
    typer.echo(f"✓ {out}")

    # 6. QA
    report = qa_mod.run_qa(out, p)
    qa_mod.dump(report, run_dir / "qa.json")
    typer.echo(report.summary())
    if not report.ok:
        raise typer.Exit(code=2)


@app.command()
def qa(
    video: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    props: Annotated[Path | None, typer.Option("--props", help="props.json；預設用影片同一個 run 目錄")] = None,
) -> None:
    """只跑 Kinocut 品檢。"""
    props_path = props or video.parent.parent / "props.json"
    p = json.loads(props_path.read_text(encoding="utf-8"))
    report = qa_mod.run_qa(video, p)
    typer.echo(report.summary())
    if not report.ok:
        raise typer.Exit(code=2)


@app.command()
def voices(lang: Annotated[str, typer.Option("--lang")] = "zh-TW") -> None:
    """列出 edge-tts 可用聲音。"""
    import asyncio

    import edge_tts

    for v in asyncio.run(edge_tts.list_voices()):
        if v["Locale"].startswith(lang):
            typer.echo(f"{v['ShortName']:<32} {v['Gender']}")


@app.command()
def doctor() -> None:
    """檢查 ffmpeg / Kinocut / Node / Remotion 是否就緒。"""
    typer.echo(f"ffmpeg: {ffmpeg.ffmpeg()}")
    ffmpeg.export_env()
    try:
        import kinocut  # noqa: F401

        typer.echo("kinocut: ok")
    except ImportError as e:
        typer.echo(f"kinocut: 缺少（{e}）")
    typer.echo(f"npx: {render_mod.npx()}")
    has_remotion = (render_mod.REMOTION_DIR / "node_modules" / "remotion").exists()
    typer.echo(f"remotion: {'ok' if has_remotion else '請先 cd remotion && npm install'}")
    typer.echo(f"adapters: {', '.join(adapters.names())}")


if __name__ == "__main__":
    app()
