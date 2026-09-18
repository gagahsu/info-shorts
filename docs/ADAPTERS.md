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

- 輸入：ig-auto-post pipeline 的 `IG_BRIEFING_PAYLOAD YYYY-MM-DD` JSON（Gemini Spark 產）。實際 schema（2026-09-18 取得，`tests/fixtures/briefing/input.json` 是一份真實樣本）：

  | 欄位 | 型別／範例 | 用途 |
  |---|---|---|
  | `date` | `"2026.09.18"` | → `date`（轉 ISO） |
  | `futures_close` / `futures_change` / `futures_change_pct` | `"47,160"` / `"+701"` / `"+1.51%"` | stat：台指期夜盤（value / delta / delta_pct，unit 點） |
  | `outlook` | `"偏多開高 🚀"` | 去 emoji → `subtitle`，並做片尾 quote「開盤訊號：…」 |
  | `us_indices[]` | `[{name:"道瓊", value:"+0.61%"}, …]`（4 筆） | table：美股主要指數（指數／漲跌%） |
  | `adr[]` | `[{name:"台積電", value:"+3.00%"}, …]`（3 筆） | table：台股 ADR |
  | `premium` | `"溢價 +13.18%"` | stat：台積電 ADR 溢價率／折價率（value 13.18，unit %） |
  | `news[]` | `[{headline, detail}]`（3 筆） | bullets：今日新聞重點，只取 `headline`（前 2 則，`MAX_NEWS`；3 則會讓整支片超過 80 秒） |
  | `groups_note` | HTML：`【焦點族群】1. 名稱：內文<br>2. …【開盤觀測與關鍵點位】…` | bullets：今日焦點族群，只取每條的「名稱」（冒號前，前 5 條） |
  | `caption` | IG 貼文文案 | 不用（那是 ig-auto-post 的事） |

- `disclaimer: true` 固定；`target_duration: 60`。
- 旁白稿由 scenes.py 依畫面生成，不用 payload 內的文案；stat 會讀「上漲七百零一點，漲幅一點五一個百分點」，
  兩欄且第二欄全是漲跌% 的 table 用壓縮讀法（「美股主要指數全數上漲，道瓊零點六一、那斯達克一點六九個百分點」）。
- 實測長度：真實 payload 一支約 70 秒（title 5s + 台指期 8s + 美股表 10s + ADR 表 8s + 溢價 5s + 新聞 2 則 15s + 族群 12s + quote 3s + 免責 4.5s）。
- 缺欄位：`premium` 解析不到 → value null（畫面「—」，旁白「無資料」）；`us_indices`/`adr`/`news`/`groups_note` 空 → 不產該 scene。

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
