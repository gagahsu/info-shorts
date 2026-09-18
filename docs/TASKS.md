# TASKS

> Claude：開工前讀「當前階段」。完成一項就勾掉並在 Log 加一行。不跳階段。

## 當前階段：Phase 0

---

## Phase 0 — 環境與骨架
- [ ] 依 `docs/SETUP.md` 完成環境，通過驗證
- [ ] 確認 Kinocut MCP 啟動指令，更新 `.mcp.json`
- [ ] `pyproject.toml`（套件 `infoshorts`，CLI `infoshorts`），ruff/pyright/pytest
- [ ] `remotion/` 骨架（TypeScript blank），`theme.ts` 放入 neutral token
- [ ] `schemas/content.schema.json` 定稿，`examples/generic.json` 一份
- **驗收**：`infoshorts --help`；`npx remotion studio` 開得起來；kinocut 連線

## Phase 1 — Core 最小可用（generic adapter）
- [ ] `adapters/generic.py` + fixture 測試
- [ ] `scenes.py`：title 自動插入、section→scene、bullets 拆分
- [ ] `format.py`：數字／百分比／日期中文讀法 + 單元測試
- [ ] `tts.py`：每段各自合成 → concat → 回填時間 → 合併 srt（時間碼位移）→ 字幕切分規則
- [ ] `props.py`
- [ ] Remotion `Short.tsx` + scenes：title / stat / bullets / quote（table、disclaimer 留 Phase 2）
- [ ] `@remotion/captions` 字幕層，讀 srt
- [ ] `qa.py` 接 Kinocut：時長、解析度、音量、黑幀
- [ ] `infoshorts build` 串起全部；`--dry-run`
- **驗收**：`examples/generic.json` → 一支 45s 9:16 mp4，字幕與語音對齊、QA 通過

## Phase 2 — 補齊 scene 與細節
- [ ] `table` scene、`disclaimer` scene（`disclaimer: true` 自動插入）
- [ ] BGM 支援 + voice ducking
- [ ] 數字 counting-up 動畫
- [ ] 漲跌顏色 `deltaColor(kind, dir)`
- [ ] Kokoro 備援引擎 `--engine kokoro`
- [ ] 三支不同內容的 generic 測試（純文字、長 bullets、多 stat）
- **驗收**：所有 scene 型態都有 example 可 render；換 `theme` 不改元件

## Phase 3 — 兩個 adapter
- [ ] 去 ig-auto-post 讀 `IG_BRIEFING_PAYLOAD` 實際 schema，寫進 ADAPTERS.md
- [ ] `adapters/briefing.py` + 真實 payload fixture（去識別化）
- [ ] 讓 ig-company-intro-card skill 多輸出 `company_data.json`（不動它的圖卡）
- [ ] `adapters/company.py` + fixture
- [ ] 各出一支真實資料的影片，人工檢視旁白讀法（數字、專有名詞）
- **驗收**：`--adapter briefing` 與 `--adapter company` 各能一鍵出片並過 QA

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
- [ ] 第二個 theme（例如沿用 ig-company-intro-card 米白手繪風）

## Log
- 2026-09-18：專案文件初版（尚未開始 Phase 0）
