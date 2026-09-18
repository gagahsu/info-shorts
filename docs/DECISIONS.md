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
