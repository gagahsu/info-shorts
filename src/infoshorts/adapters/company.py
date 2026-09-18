"""company adapter：ig-company-intro-card skill 的圖卡 payload（slides[]）→ content.json。

payload（2026-09-19 樣本，見 docs/ADAPTERS.md）：
  ticker "2449 京元電子"、slides[]：
    cover{title, subtitle, industry}、intro{paragraphs[]}、bullets{tag, items[]}、
    financial{revenue_chart{months[], revenue[], yoy[]}, stats[{label,value}], items[]}、
    competitors{competitors[{region,name,note}]}、sections{sections[{title, items[]}]}、cta。
  brand_*、src_note、caption 不用。

取捨（短影音 45–60 秒）：產品／競爭對手／展望只取「名稱」，不唸內文；財務用 revenue_chart 的結構化數字，
不用 stats 的自由文字；intro 段落不用（太長）。缺欄位 → null／不產 scene，不猜值。
"""

from __future__ import annotations

import json
import re
from typing import Any

from infoshorts.content import apply_defaults, validate

REVENUE_ROWS = 3  # 表格取最近幾個月
MAX_ITEMS = 5
_TICKER_RE = re.compile(r"^\s*(\d{4,6})\s+(.+?)\s*$")
_PAREN_RE = re.compile(r"\s*[（(][^）)]*[）)]\s*")


def _slide(slides: list[dict[str, Any]], type_: str) -> dict[str, Any] | None:
    return next((s for s in slides if isinstance(s, dict) and s.get("type") == type_), None)


def _name_only(text: str) -> str:
    """'晶圓測試（Wafer Probe / CP Test）：內文…' → '晶圓測試'；沒有冒號就整句去括號。"""
    head = re.split(r"[：:]", text, maxsplit=1)[0]
    return _PAREN_RE.sub("", head).strip()


def _month_zh_label(m: str) -> str:
    """'26/08' → '2026年8月'；其他格式原樣。"""
    mm = re.fullmatch(r"(\d{2})/(\d{1,2})", m.strip())
    return f"20{mm.group(1)}年{int(mm.group(2))}月" if mm else m


def _signed_pct(v: Any) -> str | None:
    if v is None:
        return None
    try:
        f = float(str(v).replace(",", "").replace("%", ""))
    except ValueError:
        return None
    return f"{'+' if f > 0 else ''}{f:g}%"


class CompanyAdapter:
    name = "company"

    def to_content(self, raw: dict[str, Any] | str, *, run_id: str) -> dict[str, Any]:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, dict):
            raise ValueError("company adapter 的輸入必須是公司介紹圖卡 JSON 物件")
        slides = [s for s in raw.get("slides") or [] if isinstance(s, dict)]
        cover = _slide(slides, "cover") or {}
        m = _TICKER_RE.match(str(raw.get("ticker") or ""))
        code, name = (m.group(1), m.group(2)) if m else (None, cover.get("title"))
        name = name or cover.get("title") or "公司介紹"
        title = f"{name}（{code}）" if code else name

        sections: list[dict[str, Any]] = []
        industry = cover.get("industry")
        if industry:
            sections.append({"type": "quote", "text": f"產業：{str(industry).replace(' / ', '、')}", "source": None})

        products = _slide(slides, "bullets")
        if products and products.get("items"):
            names = [_name_only(str(i)) for i in products["items"]][:MAX_ITEMS]
            sections.append({"type": "bullets", "heading": "主要產品／服務", "items": [n for n in names if n]})

        fin = _slide(slides, "financial") or {}
        chart = fin.get("revenue_chart") or {}
        months = list(chart.get("months") or [])
        revenue = list(chart.get("revenue") or [])
        yoy = list(chart.get("yoy") or [])
        if months and revenue and len(months) == len(revenue):
            sections.append(
                {
                    "type": "stat",
                    "label": f"{_month_zh_label(str(months[-1]))}營收",
                    "value": revenue[-1],
                    "delta": None,
                    "delta_pct": _signed_pct(yoy[-1]) if len(yoy) == len(months) else None,
                    "delta_kind": "yoy",
                    "unit": "億元",
                }
            )
            rows = []
            prev_year = None
            for i in range(max(0, len(months) - REVENUE_ROWS), len(months)):
                label = _month_zh_label(str(months[i]))
                year = label.split("年")[0] if "年" in label else None
                if year and year == prev_year:
                    label = label.split("年", 1)[1]  # 同一年只唸月份：2026年6月、7月、8月
                prev_year = year
                rows.append([label, revenue[i], _signed_pct(yoy[i]) if len(yoy) == len(months) else None])
            sections.append(
                {"type": "table", "heading": "近期月營收", "columns": ["月份", "營收(億)", "年增率"], "rows": rows}
            )

        comp = _slide(slides, "competitors")
        if comp and comp.get("competitors"):
            names = [str(c.get("name", "")).strip() for c in comp["competitors"] if isinstance(c, dict)]
            sections.append(
                {"type": "bullets", "heading": "主要競爭對手", "items": [n for n in names if n][:MAX_ITEMS]}
            )

        outlook = _slide(slides, "sections")
        if outlook and outlook.get("sections"):
            titles = [str(s.get("title", "")).strip() for s in outlook["sections"] if isinstance(s, dict)]
            sections.append({"type": "bullets", "heading": "未來展望", "items": [t for t in titles if t][:MAX_ITEMS]})

        if not sections:
            raise ValueError("company payload 沒有任何可用的 slide")

        content = apply_defaults(
            {
                "id": run_id,
                "kind": "company",
                "title": title,
                "subtitle": cover.get("subtitle"),
                "date": None,
                "disclaimer": True,
                "target_duration": 60,
                "sections": sections,
            },
            run_id=run_id,
        )
        validate(content)
        return content
