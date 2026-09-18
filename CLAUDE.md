# info-shorts — 資訊 → 圖片＋字幕＋人聲短影音

> 給 Claude Code 的入口文件。開始任何工作前先讀完本檔，再依需要讀 `docs/`。
> 進度以 `docs/TASKS.md` 為準；架構決策以 `docs/DECISIONS.md` 為準。

## 1. 這個專案在做什麼

把「AI 蒐集／整理好的結構化資訊」轉成直式短影音（9:16，30–60 秒）：
畫面（Remotion 渲染的資訊卡）＋ 逐字字幕 ＋ 中文人聲旁白 ＋ 可選 BGM。

架構是**通用底層 + adapter**：

```
adapter（來源專屬）  →  content.json（統一格式）  →  core pipeline（通用）  →  out/*.mp4
```

| adapter | 來源 | 狀態 |
|---|---|---|
| `generic` | 任何文字／JSON | Phase 1 先做 |
| `briefing` | 台股盤前速報（既有 gagahsu/ig-auto-post 的 `IG_BRIEFING_PAYLOAD` JSON） | Phase 3 ✓ |
| `company` | 公司介紹圖卡 skill 的 `slides[]` JSON（月營收、產品、競爭對手、展望） | Phase 3 ✓ |
| `closing` | 台股盤後速報（ig-auto-post 的 `CLOSING_PAYLOAD` JSON） | 2026-09-19 追加 ✓ |

Core 不知道來源是什麼，只認 `content.json`。新來源＝新 adapter，不改 core。

## 2. 不可違反的原則（Hard rules）

1. **AI Agent 以外一律免費開源。** TTS 用 edge-tts（主）/ Kokoro（備援），不用 ElevenLabs、Google TTS 等付費服務。
2. **Core 與 adapter 嚴格分離。** adapter 只能產 `content.json`，不可直接呼叫 render；core 不可引用任何 adapter 的欄位名稱。
3. **視覺風格只從 `remotion/src/theme.ts` 讀。** 預設是米白手繪風（`paper`，ADR-017），另有 `neutral`；換風格只改 theme，不動 scene 元件。
4. **每支影片先過 Kinocut 品檢再算完成。** 時長、解析度 1080×1920、音量、無黑幀。
5. **不自動發布。** 本專案輸出到 `out/`；上傳 IG 是既有 ig-auto-post pipeline 的事，本專案不碰 Meta API、不存 token。
6. **不編造數據。** adapter 只轉換輸入的資料；資料缺欄位就在 `content.json` 標 `null`，畫面顯示「—」，不猜值。
7. **股票內容一律加免責聲明 scene**（`disclaimer: true` 時 core 自動在片尾插入）。

## 3. 技術棧（已定案）

- 執行環境：**Windows 原生**（ADR-008；WSL 缺 sudo/node/ffmpeg）。Python 用 `uv`（`uv sync` / `uv run infoshorts …`）。GPU 等級不高：Remotion render 走 CPU；本專案不跑 Whisper（字幕時間碼直接來自 edge-tts）。
- FFmpeg 必須 6+（Kinocut 要求）；PATH 上的 miniconda 4.x 不能用，`src/infoshorts/ffmpeg.py` 會自動選 winget 的 8.x。
- 語言：Python 3.11+（adapter、編排、TTS）、Node.js 22+ / TypeScript（Remotion）。
- TTS＋字幕：`edge-tts`，一次輸出 `voice.mp3` + `voice.srt`（字幕時間碼由此而來，不需要 Whisper）。
- 渲染：Remotion，`Short` composition 吃 `props.json`；字幕層用 `@remotion/captions` 讀 srt。
- 後製／品檢／轉檔：Kinocut MCP。
- 觸發：Phase 1–3 手動（Claude Code 或 CLI）；Phase 4 評估 GitHub Actions（與 ig-auto-post 同平台）。

## 4. 目錄結構

```
info-shorts/
├── CLAUDE.md
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PIPELINE.md          content.json → scenes → TTS → render → QA
│   ├── ADAPTERS.md          每個 adapter 的輸入格式與對應規則
│   ├── STYLE.md             視覺規範（中性置位版）
│   ├── SETUP.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   └── REFERENCES.md
├── schemas/
│   └── content.schema.json  統一內容格式（core 的唯一輸入）
├── src/infoshorts/
│   ├── adapters/
│   │   ├── base.py          Adapter 介面：`to_content(raw) -> Content`
│   │   ├── generic.py
│   │   ├── briefing.py
│   │   ├── company.py
│   │   └── closing.py
│   ├── content.py           schema 驗證與預設值
│   ├── format.py            數字／百分比／日期中文讀法（唯一出處）
│   ├── scenes.py            content.json → scenes（切段、每段的旁白稿與畫面型態）
│   ├── tts.py               edge-tts：旁白 mp3 + srt，並回填每個 scene 的起迄秒
│   ├── props.py             scenes + 音訊時間 → Remotion props.json
│   ├── render.py            呼叫 npx remotion render（--public-dir 指到 run 目錄）
│   ├── ffmpeg.py            定位 ffmpeg 6+，同步給 Kinocut
│   ├── qa.py                呼叫 Kinocut 品檢
│   └── cli.py               `infoshorts build --adapter generic --input x.json`
├── remotion/
│   └── src/
│       ├── Short.tsx        主 composition：依 props.scenes 逐段渲染
│       ├── theme.ts         色彩／字體／間距 token（唯一風格來源）
│       └── scenes/          Title / Stat / Bullets / Table / Quote / Disclaimer
├── tests/                   pytest；adapter fixture 在 tests/fixtures/<adapter>/
├── runs/<YYYY-MM-DD>-<slug>/
│   ├── input.*              原始輸入
│   ├── content.json
│   ├── scenes.json
│   ├── seg/                 每段旁白的 mp3/wav（不進 git）
│   ├── voice.mp3 / voice.srt
│   ├── props.json
│   ├── qa.json              Kinocut 品檢結果
│   └── out/                 成品（不進 git）
├── .mcp.json
└── .gitignore
```

## 5. 標準工作流程

```
uv run infoshorts build --adapter generic --input runs/<run>/input.json
# 等同於依序：
#   adapter  → content.json
#   scenes   → scenes.json（旁白稿在這裡定稿）
#   tts      → voice.mp3 + voice.srt，回填 scene 時間
#   props    → props.json
#   render   → npx remotion render ... out/<run>.mp4
#   qa       → Kinocut 品檢，失敗就報告不算完成
```

Claude 在 `scenes.json` 產生後**回報旁白稿摘要**（不必等確認，但要讓使用者看得到）；QA 失敗要說明原因與建議修正。

## 6. 開發規範

- Python：`ruff` + `pyright`（basic），adapter 必須有單元測試（給一個 fixture 輸入，斷言 content.json）。
- TypeScript：`strict: true`；動畫只用 Remotion API（`useCurrentFrame`/`interpolate`/`spring`/`<Sequence>`），禁用 CSS transition。
- 時間單位：scenes/props 用秒（float）；Remotion 內部轉 frame（30 fps）。
- 字幕：每段字幕 ≤ 14 個中文字、≤ 2 行；由 `tts.py` 依 srt 切，超長就重切。
- 旁白稿：口語、短句、數字用中文讀法（`+1.25%` → 「上漲一點二五個百分點」），轉換規則寫在 `format.py`，不散落各 adapter。字幕顯示數字、語音唸中文（`format.mark` 雙軌，ADR-018）。
- Commit：`feat|fix|docs|chore(scope): 說明`。
- 新依賴先寫 ADR。

## 7. 現在的階段

看 `docs/TASKS.md`「當前階段」。Phase 0/1 只做 `generic` adapter；不要提前做 briefing/company。

## 8. 遇到不確定時

- 資料格式不確定 → 讀 `docs/ADAPTERS.md`；briefing 的 payload 格式以 ig-auto-post repo 為準，不要猜欄位。
- 風格不確定 → 讀 `docs/STYLE.md`，只用 `theme.ts` 已定義的 token。
- edge-tts 失效 → 切 Kokoro（見 SETUP），並在 TASKS Log 記錄。
- Kinocut / Remotion API 不確定 → 查官方文件，不要憑記憶。
