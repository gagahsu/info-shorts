# info-shorts

結構化資訊 → 直式短影音（資訊卡畫面 + 逐字字幕 + 中文人聲）。通用 core + 來源 adapter（generic / 台股盤前速報 / 公司介紹卡）。全免費工具鏈：edge-tts、Remotion、Kinocut。

## 快速開始

1. 依 `docs/SETUP.md` 建 WSL2 環境。
2. `mkdir -p runs/2026-09-20-test && cp examples/generic.json runs/2026-09-20-test/input.json`
3. `infoshorts build --adapter generic --input runs/2026-09-20-test/input.json`
4. 成品在 `runs/2026-09-20-test/out/`。

## 文件
- `CLAUDE.md` — agent 入口與規則
- `docs/ARCHITECTURE.md`、`docs/PIPELINE.md`、`docs/ADAPTERS.md`、`docs/STYLE.md`、`docs/SETUP.md`、`docs/TASKS.md`、`docs/DECISIONS.md`、`docs/REFERENCES.md`
