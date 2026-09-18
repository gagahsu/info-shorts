# TASKS

> Claude：開工前讀「當前階段」。完成一項就勾掉並在 Log 加一行。不跳階段。

## 當前階段：Phase 3 完成 → Phase 4 評估

---

## Phase 0 — 環境與骨架
- [x] 依 `docs/SETUP.md` 完成環境，通過驗證（改為 Windows 原生，見 ADR-008）
- [x] 確認 Kinocut MCP 啟動指令，更新 `.mcp.json`（`uvx --from kinocut kino --mcp` + FFmpeg 8 環境變數）
- [x] `pyproject.toml`（套件 `infoshorts`，CLI `infoshorts`），ruff/pyright/pytest
- [x] `remotion/` 骨架（TypeScript strict），`theme.ts` 放入 neutral token
- [x] `schemas/content.schema.json` 定稿，`examples/generic.json` 一份
- **驗收**：`uv run infoshorts --help` ✓；`npx remotion studio` 開得起來 ✓（`src/sample.ts` 假資料）；kinocut MCP stdio 連線 ✓（196 tools）

## Phase 1 — Core 最小可用（generic adapter）
- [x] `adapters/generic.py` + fixture 測試
- [x] `scenes.py`：title 自動插入、section→scene、bullets 拆分
- [x] `format.py`：數字／百分比／日期中文讀法 + 單元測試
- [x] `tts.py`：每段各自合成 → concat → 回填時間 → 合併 srt（時間碼位移）→ 字幕切分規則（對照原文標點，ADR-011）
- [x] `props.py`
- [x] Remotion `Short.tsx` + scenes：title / stat / bullets / quote（table、disclaimer 也一併做了，見 Phase 2）
- [x] `@remotion/captions` 字幕層，讀 srt
- [x] `qa.py` 接 Kinocut：時長、解析度、音量（LUFS）、黑幀
- [x] `infoshorts build` 串起全部；`--dry-run`
- **驗收**：`examples/generic.json` → 一支 9:16 mp4（22.6s；example 內容短，45s 是目標不是下限），字幕與語音對齊、QA 通過

## Phase 2 — 補齊 scene 與細節
- [x] `table` scene、`disclaimer` scene（`disclaimer: true` 自動插入）— `examples/multi-stat.json` 已 render 驗證
- [x] BGM 支援 + voice ducking（`Bgm.tsx`：0.25 / 旁白中 0.08、8 frame 斜坡、片尾淡出；ADR-014）
- [x] 數字 counting-up 動畫（`Stat.tsx`，0.8s，保留千分位／小數／前後綴）
- [x] 漲跌顏色 `deltaColor(kind, dir)`（theme.ts）
- [x] Kokoro 備援引擎 `--engine kokoro`（`uv sync --group kokoro`；字幕時間等比估算，ADR-013）
- [x] 三支不同內容的 generic 測試（`examples/text-only.json`、`long-bullets.json`、`multi-stat.json`；`tests/test_examples.py`）
- [x] Kinocut 視覺檢查在 Windows 路徑上失敗 → `qa.py` monkeypatch（ADR-012），亮度／對比現在有數據（深色底只是 advisory）
- **驗收**：所有 scene 型態都有 example 可 render ✓；換 `theme` 不改元件 ✓（元件內無色碼，`captionBg` 也進 theme）

## Phase 3 — 兩個 adapter
- [x] `IG_BRIEFING_PAYLOAD` 實際 schema（使用者提供 2026-09-18 樣本）寫進 ADAPTERS.md
- [x] `adapters/briefing.py` + 真實 payload fixture（`tests/fixtures/briefing/`，公開行情資料無需去識別化）
- [x] ~~讓 ig-company-intro-card skill 多輸出 `company_data.json`~~ 不需要：skill 的 `slides[]` JSON 已含結構化 `revenue_chart`（ADR-016）
- [x] `adapters/company.py` + fixture（`tests/fixtures/company/`，京元電子 2449）
- [x] 追加 `adapters/closing.py`（`CLOSING_PAYLOAD` 盤後速報）+ fixture
- [x] briefing 真實資料出片（`runs/2026-09-18-briefing`）；旁白讀法已檢視（四萬七千一百六十點／漲幅一點五一個百分點／百分之十三點一八）
- [x] company／closing 真實資料出片（`runs/2026-09-19-company`、`runs/2026-09-19-closing`），旁白讀法已檢視
- **驗收**：`--adapter briefing` / `company` / `closing` 各能一鍵出片並過 QA ✓

## Phase 4 — 自動化（評估後才做）
- [ ] 評估：GitHub Actions（與 ig-auto-post 同平台）能否跑 Remotion render（時間、Chrome deps、免費額度）
- [ ] 若可行：briefing 出片接在 ig-auto-post 的 payload 之後，產物交回該 pipeline 上傳
- [ ] 若不可行：本機排程（WSL cron / Task Scheduler）+ 成品同步
- **驗收**：連續 5 個交易日無人工介入出片

## Backlog
- [ ] 16:9 版本（YouTube）
- [ ] 多聲音／多語言（zh-CN、en）
- [ ] 圖表 scene（折線／長條，Remotion 內畫 SVG）
- [ ] 從 `ali-abassi/remotion-templates` 挑 kinetic text 模板增加變化
- [x] 第二個 theme：米白手繪風 `paper`，2026-09-19 起為預設（ADR-017）

## Log
- 2026-09-18：專案文件初版（尚未開始 Phase 0）
- 2026-09-18：Phase 0 完成。執行環境改 Windows 原生（ADR-008）；uv + Python 3.11、Node 22、Remotion 4.0.526、FFmpeg 8.1（winget）、kinocut 1.15。
- 2026-09-18：Phase 1 完成。`examples/generic.json` 全流程出片（TTS edge-tts → Remotion render 676 frames 約 1 分鐘 → Kinocut QA）。
  修過的坑：(1) 字幕硬切 14 字會把詞切半 → 對照原文標點切（ADR-011）；(2) blackdetect 預設 pix_th=0.10 把深灰底空曠畫面當黑幀 → 改 0.04；
  (3) 旁白 -19.5 LUFS 貼近下限 → 最終混音 loudnorm 到 -16；(4) Kinocut signalstats 在 Windows 路徑失敗 → 只列 advisory。
- 2026-09-19：Phase 2 完成。三支 generic 範例（30s / 34s / 51s）全部過 QA；multi-stat 帶 BGM 驗證 ducking；Kokoro 中文備援可用（CPU 約 0.6× 即時，首次下載模型 330 MB）。
  修過的坑：(1) Kinocut `movie=` 路徑在 Windows 需加引號 → monkeypatch；(2) 表格欄名「漲跌%」被讀成「漲跌百分比」→ 旁白去掉單位標記；
  (3) edge-tts 段尾約 0.7s 靜音會讓 ducking 區間過長 → 用最後一個字的結束時間（`scenes[].speech_end`）。
- 2026-09-19：使用者看完成品的三點回饋全部處理：(1) 新 theme `paper`（米白手繪風，預設；ADR-017）；(2) 「／」唸「、」；
  (3) 字幕顯示數字、語音唸中文（顯示／唸法雙軌，ADR-018）。
