# PIPELINE

工作目錄 `runs/<YYYY-MM-DD>-<slug>/`。時間單位秒（float）。

## Step 1 — adapter → content.json

`content.json` 是 core 唯一輸入。範例（generic）：

```json
{
  "id": "2026-09-20-test",
  "kind": "generic",
  "title": "本週三件事",
  "subtitle": "AI 工具速覽",
  "date": "2026-09-20",
  "lang": "zh-TW",
  "aspect": "9:16",
  "target_duration": 45,
  "disclaimer": false,
  "sections": [
    {"type": "stat", "label": "Kinocut MCP tools", "value": "190+", "delta": null, "unit": "", "narration": "第一件事，Kinocut 這個影片剪輯 MCP，工具數已經超過一百九十個。"},
    {"type": "bullets", "heading": "為什麼重要", "items": ["typed tools 不用猜 ffmpeg flag", "內建品檢", "本機免費"], "narration": "它的重點有三個：不用再猜 ffmpeg 參數、內建品質檢查、而且完全在本機跑、免費。"},
    {"type": "quote", "text": "先用 Kinocut，再談 Remotion。", "source": null, "narration": "一句話總結：先把 Kinocut 用起來，再談 Remotion。"}
  ],
  "bgm": null
}
```

規則：
- `narration` 可為 null → scenes.py 依畫面內容生成口語旁白稿（Claude 潤稿）。
- 數字欄位保持原始值（字串或數字都可），讀法在 scenes.py 轉。
- `disclaimer: true` → core 在片尾自動加 disclaimer scene。

## Step 2 — scenes.py → scenes.json

- 自動插入開場 `title` scene（用 title/subtitle/date）。
- 每個 section → 一個 scene；`bullets` 超過 5 條就拆兩個 scene。
- 旁白稿轉換（集中在 `format.py`）：
  - `+1.25%` → 「上漲一點二五個百分點」；`-0.8%` → 「下跌零點八個百分點」
  - `23,456` → 「兩萬三千四百五十六」（≥ 1 萬用中文單位；小數保留兩位）
  - 日期 `2026-09-20` → 「九月二十日」
  - 英文縮寫（ADR、ETF、AI）保留原文，edge-tts 會讀字母
- 產出 `scenes.json`：`[{"idx":0,"type":"title","props":{...},"narration":"唸法","narration_display":"字幕顯示（數字）","narration_marked":"標記原文","start":null,"end":null}]`（tts 之後多一個 `speech_end`＝最後一個字的結束秒，給 BGM ducking 用）。三種旁白文字的關係見 ADR-018。
- 表格欄名的單位標記不讀（「漲跌%」→「漲跌」）；缺值讀「無資料」。
- Claude 在此步驟後**回報旁白稿摘要**。

## Step 3 — tts.py

```bash
edge-tts --voice zh-TW-HsiaoChenNeural --rate=+5% \
  --text "$(cat runs/<run>/narration.txt)" \
  --write-media runs/<run>/voice.mp3 --write-subtitles runs/<run>/voice.srt
```
- `narration.txt`＝各 scene 旁白依序串接，段落間用 `。` 與換行分隔；每段前後在文字裡插入標記句（例如全形空格＋停頓）不可行時，改成**每段各自合成一個 mp3**，再用 ffmpeg concat 並記錄各段時長 → 這是預設做法，時間更準。
- 回填每個 scene 的 `start/end`＝該段音檔在整體中的位置；scene 顯示長度＝旁白長度 + 0.4s；無旁白的 scene 固定 2.5s（靜音 wav）。
- 實作：`tts.py` 用 edge-tts Python API（`boundary="WordBoundary"`）拿逐詞時間碼，每段 mp3 → 補 0.4s 靜音的 wav → concat demuxer → `loudnorm` 到 -16 LUFS → voice.mp3。
- srt 合併時要位移時間碼；字幕切分（ADR-011）：≤14 字寬（英數算半字）、句號／分號必切、逗號累積 ≥4 字才切、詞間停頓 >0.35s 切、超長回溯到最近逗號。標點來自對照旁白原文（edge-tts 事件不含標點）。
- 聲音選項：`zh-TW-HsiaoChenNeural`（女，預設）、`zh-TW-YunJheNeural`（男）；用 `edge-tts --list-voices | grep zh-TW` 查最新清單。
- edge-tts 失敗 → 切 Kokoro（SETUP §5），介面相同（輸入文字，輸出 mp3；srt 由 Kokoro 的 timestamps 產）。

## Step 4 — props.py → props.json

```json
{
  "fps": 30,
  "width": 1080, "height": 1920,
  "theme": "paper",
  "meta": {"title": "台股盤後速報", "date": "2026-09-18", "brand": "個人盤後筆記", "disclaimer": true},
  "audio": {"voice": "voice.mp3", "bgm": null, "bgmVolume": 0.25, "duckVolume": 0.08, "voiceRanges": [[0, 150], [162, 270]]},
  "captions": "voice.srt",
  "scenes": [
    {"type": "title", "startFrame": 0, "endFrame": 96, "props": {"title": "...", "subtitle": "...", "date": "..."}},
    {"type": "stat", "startFrame": 96, "endFrame": 240, "props": {...}}
  ]
}
```

`voiceRanges`＝有旁白的 frame 區間（扣掉 0.4s 緩衝），Remotion 的 `Bgm.tsx` 用它做 ducking（ADR-014）。
`--bgm path` 會把檔案複製到 run 目錄成 `bgm.<ext>`。

## Step 5 — Remotion render

```bash
cd remotion && npx remotion render src/index.ts Short ../runs/<run>/out/<run>.mp4 --props=../runs/<run>/props.json --public-dir=../runs/<run> --concurrency=2
```
`--public-dir` 指到 run 目錄，props 內的 `audio.voice` / `captions` 是相對檔名，元件用 `staticFile()` 讀（ADR-010）。
GPU 等級不高 → `--concurrency` 保守；45 秒影片 CPU render 預期 1–3 分鐘。

## Step 6 — QA（Kinocut）

檢查項目（`qa.py`，直接 import kinocut 的 Python API）：時長與 props 一致（±0.5s）、1080×1920、音訊與影片等長（±0.5s）、
整體音量 -20 ~ -12 LUFS 且 true peak ≤ -1 dBTP（Kinocut `quality_check` 的 audio_levels）、無連續黑幀 > 0.5s（blackdetect，pix_th 0.04 以免深灰底誤判）。
Kinocut 的亮度／對比／飽和／色偏只列 advisory（深色 theme 天生偏暗；且它在 Windows 路徑上目前會分析失敗）。
任一硬性檢查失敗 → `infoshorts build` 退出碼 2，`qa.json` 留在 run 目錄，Claude 報告原因。

## 一鍵指令

`infoshorts build --adapter <name> --input <file> [--voice ...] [--bgm path] [--dry-run]`
`--dry-run` 只跑到 scenes.json，用來檢查旁白稿。
