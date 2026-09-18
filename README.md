# info-shorts

結構化資訊 → 直式短影音（資訊卡畫面 + 逐字字幕 + 中文人聲）。通用 core + 來源 adapter（generic / 台股盤前速報 / 公司介紹卡）。全免費工具鏈：edge-tts、Remotion、Kinocut。

## 快速開始（Windows 原生，見 `docs/SETUP.md`）

```powershell
uv sync                                  # Python 3.11 + edge-tts + kinocut + dev tools
cd remotion; npm install; npx remotion browser ensure; cd ..
uv run infoshorts doctor                 # ffmpeg 6+ / kinocut / npx / remotion 是否就緒

uv run infoshorts build --adapter generic --input examples/generic.json
# 產物：runs/<今天>-generic/{content,scenes,props}.json、voice.mp3、voice.srt、out/<run>.mp4、qa.json
```

常用選項：`--dry-run`（只到 scenes.json，看旁白稿）、`--run <名稱>`、`--voice zh-TW-YunJheNeural`、`--rate +5%`、`--bgm x.mp3`（自動 ducking）、`--engine kokoro`（離線備援，先 `uv sync --group kokoro`）。
更多範例：`examples/text-only.json`、`examples/long-bullets.json`、`examples/multi-stat.json`（含 table 與免責聲明）。
只跑品檢：`uv run infoshorts qa runs/<run>/out/<run>.mp4`。預覽畫面：`cd remotion && npx remotion studio`。

## 流程

```
input.json ─adapter─▶ content.json ─scenes.py─▶ scenes.json ─tts.py─▶ voice.mp3 + voice.srt
          ─props.py─▶ props.json ─Remotion─▶ out/<run>.mp4 ─Kinocut QA─▶ ✅ / ❌（非零退出）
```

## 開發

```powershell
uv run ruff check src tests; uv run ruff format src tests
uv run pyright
uv run pytest
cd remotion; npx tsc --noEmit
```

## 文件
- `CLAUDE.md` — agent 入口與規則
- `docs/ARCHITECTURE.md`、`docs/PIPELINE.md`、`docs/ADAPTERS.md`、`docs/STYLE.md`、`docs/SETUP.md`、`docs/TASKS.md`、`docs/DECISIONS.md`、`docs/REFERENCES.md`
