# ARCHITECTURE

## 資料流

```
input（文字/JSON/briefing payload/company data）
   │ adapter（來源專屬，只做欄位對應，不做文案）
   ▼
content.json（統一格式，schemas/content.schema.json）
   │ scenes.py：切段、決定每段畫面型態、寫旁白稿（Claude 可介入潤稿）
   ▼
scenes.json
   │ tts.py：edge-tts → voice.mp3 + voice.srt；依 srt 回填每段 start/end
   ▼
voice.mp3 + voice.srt + scenes.json（含時間）
   │ props.py
   ▼
props.json ──► Remotion render ──► out/<run>.mp4 ──► Kinocut QA ──► ✅/❌
```

## 為什麼字幕時間碼來自 edge-tts 而不是 Whisper

edge-tts 合成語音時就知道每個字的邊界，直接輸出 srt，時間碼精準且零成本；Whisper 反而是「把已知文字再猜一次」，中文逐字精度還更差。所以本專案不裝 Whisper。

## Scene 型態（Phase 1 先做前 4 種）

| type | 用途 | props 欄位 |
|---|---|---|
| `title` | 開場標題、日期 | title, subtitle, date |
| `stat` | 單一大數字（指數、漲跌幅） | label, value, delta, unit |
| `bullets` | 3–5 條重點 | heading, items[] |
| `table` | 小表格（≤5 列 ×3 欄） | heading, columns[], rows[][] |
| `quote` | 一句話結論 | text, source |
| `disclaimer` | 免責（股票內容自動加） | 固定文案 |

每個 scene 的長度＝該段旁白長度＋0.4s 緩衝；沒有旁白的 scene 固定 2.5s。

## 三個 adapter 的關係

- `generic`：輸入就是接近 content.json 的 JSON（或純文字 → Claude 先整理成 JSON），是 core 的直接測試入口。
- `briefing`：讀 ig-auto-post 的 `IG_BRIEFING_PAYLOAD` JSON（台指期、美股指數、ADR、新聞），對應到 stat/table/bullets。
- `company`：讀公司介紹圖卡 skill 的中間資料（月營收、獲利能力），對應到 title/stat/table。

adapter 之間不共用程式碼；共用的欄位轉換（數字格式、日期）放 `src/infoshorts/format.py`。

## 與其他專案的邊界

- 上傳 IG：ig-auto-post 負責。本專案只產 mp4 到 `out/`。
- 資料蒐集：briefing 由 Gemini Spark 產 payload；company 由 skill 抓 Goodinfo。本專案不抓資料。
- 風格：與 ig-company-intro-card 的米白手繪風**無關**，本專案是獨立的 `neutral` theme。
