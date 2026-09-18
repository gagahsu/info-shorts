# DECISIONS (ADR)

## ADR-001 2026-09-18 通用 core + adapter
- 決策：core 只認 content.json；每個來源一個 adapter。
- 理由：三種來源（generic / briefing / company）輸入差異大，但畫面型態高度重疊。
- 後果：新來源不改 core；adapter 必須有 fixture 測試。

## ADR-002 2026-09-18 TTS 用 edge-tts，字幕時間碼由它產生，不用 Whisper
- 理由：免費、零 API key、同時輸出 srt、中文品質可接受；Whisper 對已知文字是多餘且更不準。
- 風險：非官方服務可能失效 → Kokoro 備援，介面抽象在 `tts.py`。

## ADR-003 2026-09-18 每段旁白各自合成再 concat
- 理由：段落邊界時間精準，scene 切換不會壓到語音；合併 srt 只要位移時間碼。
- 後果：多次呼叫 edge-tts，速度略慢，可接受。

## ADR-004 2026-09-18 Remotion + JSON props，theme 為唯一風格來源
- 理由：與 trip-cut 同一套技術，Claude 只產 JSON；之後換風格只換 theme。
- 風險：Remotion 授權（個人免費）；CPU render 時間。

## ADR-005 2026-09-18 中性置位風格，不沿用 ig-company-intro-card 的米白手繪風
- 理由：使用者決定全新設計；避免綁死在某個來源的品牌感。
- 後果：米白風放 Backlog 當第二 theme。

## ADR-006 2026-09-18 本專案不發布、不抓資料
- 理由：上傳與資料蒐集已由 ig-auto-post / skill 負責；避免重複持有 token 與抓取邏輯。
- 後果：Phase 4 自動化只負責「產 mp4 並交回」。

## ADR-007 2026-09-18 QA 由 Kinocut 執行，QA 未過不算完成
- 理由：無人工介入的排程出片必須有機械化把關。

## ADR-008 2026-09-18 執行環境改為 Windows 原生（不走 WSL2）
- 決策：pipeline（uv/Python 3.11、Node 22、FFmpeg 8、Kinocut）全部在 Windows 原生跑；`docs/SETUP.md` 改寫。
- 理由：repo 與 Claude Code 都在 Windows；WSL 缺 node/ffmpeg 且 sudo 需要密碼（無法無人值守安裝）；Remotion 在 /mnt/c 上 render 很慢。
- 後果：程式碼維持跨平台（路徑用 pathlib、ffmpeg 自動定位、Remotion 用 `--public-dir` 而非絕對路徑）；WSL/Linux 仍可依 SETUP §7 執行。

## ADR-009 2026-09-18 Python 依賴用 uv 管理；Kinocut 以 Python API 做 QA
- 決策：`pyproject.toml` + `uv sync`；`kinocut` 列為執行依賴，`qa.py` 直接 import 它的 `probe` / `quality_check` / `run_metric_qc`。
- 理由：uv 已在機器上、能自動抓 3.11；MCP 是給 Claude 互動用，pipeline 內同進程呼叫更簡單、可測。
- 風險：Kinocut 這些模組不是公開 API，升版可能變動 → `pyproject` 釘 `>=1.15`，升版時跑 `infoshorts qa` 驗證。
- 補充：Kinocut 需要 FFmpeg 6+，本機 PATH 上是 miniconda 的 4.3 → `ffmpeg.py` 自動選 winget 的 8.1 並設 `KINOCUT_FFMPEG_EXECUTABLE`。

## ADR-010 2026-09-18 音訊／字幕以「相對 run 目錄」交給 Remotion
- 決策：props.json 內 `audio.voice = "voice.mp3"`、`captions = "voice.srt"`，render 時 `--public-dir=runs/<run>`，元件用 `staticFile()`。
- 理由：Remotion 不能直接讀任意絕對路徑；用 public-dir 免複製檔案、免處理 Windows/WSL 路徑差異。

## ADR-011 2026-09-18 字幕切分對照旁白原文的標點
- 決策：edge-tts 的 WordBoundary 不含標點，`tts.py` 把事件對回旁白原文找出詞前標點：句號／分號必切，逗號累積 ≥ 4 字才切，超長時回溯到最近逗號。
- 理由：純按 14 字硬切會把「內建」這類詞切成兩半；對照原文成本低且不需要額外模型。

## ADR-012 2026-09-19 qa.py 對 Kinocut 的 Windows 路徑問題做 monkeypatch
- 問題：kinocut 1.15 `quality_guardrails._escape_lavfi_path` 對 `movie=` filter 只逃脫不加引號，Windows 磁碟機的冒號讓 ffmpeg 讀成 'C'，亮度／對比／飽和全部「analysis failed」。
- 決策：`qa.py` 在 Windows 上把該函式換成「單引號包住 + `\:`」版本（實測 ffmpeg 8 可讀）。升版 kinocut 修好後移除。
- 理由：只影響 advisory 檢查，但有分析結果才能在 Phase 2 之後調亮度；改法一行，風險低。

## ADR-013 2026-09-19 Kokoro 中文備援的字幕時間用等比估算
- 事實：`KPipeline(lang_code='z')` 回傳的 tokens 是 None（只有英文 G2P 有 start_ts/end_ts），而且整段旁白通常是單一 chunk（實測 8.9s 一段）。
- 決策：在該段音訊長度內依字寬（中文 1、英數 0.5）＋標點停頓權重（句號 1.6、逗號 0.8…）等比分配每個字的起迄。
- 後果：Kokoro 模式字幕可能早晚 0.3–0.8s；只在 edge-tts 失效時使用，不追求同等精度。實測 CPU 合成速度約 0.6× 即時（8.9s 語音 15s）。

## ADR-014 2026-09-19 BGM ducking 在 Remotion 內以 frame 函數實作
- 決策：`props.audio.voiceRanges`（有旁白的 frame 區間，由 props.py 從 scenes 推得）→ `Bgm.tsx` 的 `volume={(f) => …}`：無旁白 0.25、旁白中 0.08、8 frame 斜坡、片尾 1s 淡出。
- 理由：不用先在 ffmpeg 混音（保持「Remotion 是唯一合成點」），且 Remotion 會把音量函數烘進輸出。

## ADR-015 2026-09-19 briefing adapter 的對應取捨；stat 增加通用欄位 delta_pct
- 來源：ig-auto-post 的 `IG_BRIEFING_PAYLOAD`（真實 schema 記在 docs/ADAPTERS.md）。
- schema：stat 多一個 `delta_pct`（漲跌幅 %），因為台指期同時有「漲跌點數」與「漲跌幅」，兩者都該顯示與唸出；這是通用概念（company 的月營收 YoY 也用得到），不是 adapter 專屬欄位。
- 對應取捨：`news[].detail` 不用（太長，短影音只唸標題）；`groups_note` 只取族群名稱（冒號前）；`caption` 不用；`premium` 拆成 stat（溢價率／折價率 + 數值），解析失敗給 null。
- 旁白規則（core，非 adapter）：只有漲跌% 的表格不重複唸欄名；unit 為 % 的數值讀「百分之 X」；漲跌幅讀「漲幅／跌幅 X 個百分點」。
- 風險：payload 是 Gemini 產的，欄位可能漂移；adapter 對每個欄位都容錯（缺 → null 或不產 scene），fixture 測試釘住目前版本。
