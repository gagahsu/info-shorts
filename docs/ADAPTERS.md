# ADAPTERS

介面（`src/infoshorts/adapters/base.py`）：

```python
class Adapter(Protocol):
    name: str
    def to_content(self, raw: dict | str, *, run_id: str) -> dict: ...   # 回傳符合 content.schema.json 的 dict
```
每個 adapter 附 `tests/fixtures/<name>/input.*` 與 `expected_content.json`。

## generic（Phase 1）

- 輸入：已接近 content.json 的 JSON；或純文字（`.md/.txt`）→ Claude Code 先依 `docs/PIPELINE.md` Step 1 的格式整理成 JSON 再餵。
- 規則：只做 schema 補齊（缺 `date` 用今天、缺 `aspect` 用 9:16、缺 `target_duration` 用 45）。

## briefing（Phase 3）— 台股盤前速報

- 輸入：ig-auto-post pipeline 的 `IG_BRIEFING_PAYLOAD YYYY-MM-DD` JSON（Gemini Spark 產）。**欄位以 gagahsu/ig-auto-post 目前的 payload schema 為準；實作前先去該 repo 讀，不要猜。**
- 對應（預期，待確認）：
  | payload 區塊 | scene type | 備註 |
  |---|---|---|
  | 台指期夜盤 | stat | value=點數, delta=漲跌 |
  | 美股三大指數 | table | 3 列 × (指數/收盤/漲跌%) |
  | 台積電 ADR 等 | table 或 stat | ADR 折溢價 |
  | 新聞重點 | bullets | 取前 3–5 條 |
  | 結論一句話 | quote | 若 payload 有 |
- `disclaimer: true` 固定。
- 旁白稿：由 scenes.py 依畫面生成，不依賴 payload 內的文案。

## company（Phase 3）— 公司介紹圖卡

- 輸入：ig-company-intro-card skill 在產圖前的中間資料（公司基本資料、月營收、歷年獲利能力）。若 skill 目前沒有輸出中間 JSON，Phase 3 第一項工作是讓 skill 多輸出一份 `company_data.json`（不改它的圖卡輸出）。
- 對應：
  | 資料 | scene type |
  |---|---|
  | 公司名稱、代碼、產業 | title |
  | 最新月營收 + YoY | stat |
  | 近 4 季 EPS / 毛利率 | table |
  | 三句話介紹 | bullets |
- `disclaimer: true` 固定。
- 風格與該 skill 的米白手繪風無關，用本專案 `neutral` theme。

## 新增 adapter 的步驟

1. 在 ADR 記一條（來源、為什麼要）。
2. `adapters/<name>.py` 實作 `to_content`。
3. `tests/fixtures/<name>/` 放一組真實輸入（去識別化）＋期望輸出。
4. 在 `cli.py` 註冊。
5. 更新本檔的對應表。
