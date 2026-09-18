"""briefing adapter：ig-auto-post 的 `IG_BRIEFING_PAYLOAD` JSON → content.json。

payload 欄位（以 gagahsu/ig-auto-post 2026-09 版為準，見 docs/ADAPTERS.md）：
  date "2026.09.18"、futures_close "47,160"、futures_change "+701"、futures_change_pct "+1.51%"、outlook "偏多開高 🚀"、
  us_indices [{name, value:"+0.61%"}]、adr [{name, value}]、premium "溢價 +13.18%"、
  news [{headline, detail}]、groups_note（HTML）、caption（IG 文案，不用）。

只做欄位對應，不寫文案；旁白由 scenes.py 依畫面生成。缺欄位 → null，不猜值。
"""

from __future__ import annotations

import html
import json
import re
from typing import Any

from infoshorts.content import apply_defaults, validate

_EMOJI_RE = re.compile("[\U0001f300-\U0001faff\U0001f000-\U0001f2ff☀-➿⬀-⯿️‍]+")
_PREMIUM_RE = re.compile(r"(折價|溢價)?\s*([+-]?\d[\d,]*(?:\.\d+)?)\s*%")
# 只認行首的「1. 名稱：」，避免吃到內文的 3.14%
_GROUP_ITEM_RE = re.compile(r"(?m)^\s*\d+\.\s*([^：:\n]+?)\s*[：:]")
MAX_NEWS = 2  # 每則標題約 7 秒旁白；3 則會把整支片推到 80 秒以上
MAX_GROUPS = 5


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    return _EMOJI_RE.sub("", text).strip() or None


def _iso_date(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.fullmatch(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", raw.strip())
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else raw


def _premium(raw: str | None) -> tuple[str, str | None]:
    """'溢價 +13.18%' → ('台積電 ADR 溢價率', '13.18')；'折價 -2.1%' → ('…折價率', '2.1')；解析不到 → (label, None)。"""
    if not raw:
        return ("台積電 ADR 溢價率", None)
    m = _PREMIUM_RE.search(raw)
    if not m:
        return ("台積電 ADR 溢價率", None)
    kind = m.group(1) or ("折價" if m.group(2).startswith("-") else "溢價")
    return (f"台積電 ADR {kind}率", m.group(2).lstrip("+-"))


def _focus_groups(note: str | None) -> list[str]:
    """groups_note HTML 的【焦點族群】段落 → 只取族群名稱（冒號前）。"""
    if not note:
        return []
    text = html.unescape(re.sub(r"<[^>]+>", "\n", note))
    start = text.find("焦點族群")
    end = text.find("【", start + 1) if start >= 0 else -1
    section = text[start:end] if start >= 0 else text
    if end < 0 and start >= 0:
        section = text[start:]
    return [m.group(1).strip() for m in _GROUP_ITEM_RE.finditer(section)][:MAX_GROUPS]


def _rows(items: Any) -> list[list[Any]]:
    out: list[list[Any]] = []
    for it in items or []:
        if isinstance(it, dict):
            out.append([it.get("name"), it.get("value")])
    return out[:5]


class BriefingAdapter:
    name = "briefing"

    def to_content(self, raw: dict[str, Any] | str, *, run_id: str) -> dict[str, Any]:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, dict):
            raise ValueError("briefing adapter 的輸入必須是 IG_BRIEFING_PAYLOAD JSON 物件")

        sections: list[dict[str, Any]] = [
            {
                "type": "stat",
                "label": "台指期夜盤",
                "value": raw.get("futures_close"),
                "delta": raw.get("futures_change"),
                "delta_pct": raw.get("futures_change_pct"),
                "unit": "點",
            }
        ]
        us = _rows(raw.get("us_indices"))
        if us:
            sections.append({"type": "table", "heading": "美股主要指數", "columns": ["指數", "漲跌%"], "rows": us})
        adr = _rows(raw.get("adr"))
        if adr:
            sections.append({"type": "table", "heading": "台股 ADR", "columns": ["ADR", "漲跌%"], "rows": adr})
        label, premium = _premium(raw.get("premium"))
        sections.append({"type": "stat", "label": label, "value": premium, "delta": None, "unit": "%"})
        headlines = [_clean(n.get("headline")) for n in raw.get("news") or [] if isinstance(n, dict)]
        headlines = [h for h in headlines if h][:MAX_NEWS]
        if headlines:
            sections.append({"type": "bullets", "heading": "今日新聞重點", "items": headlines})
        groups = _focus_groups(raw.get("groups_note"))
        if groups:
            sections.append({"type": "bullets", "heading": "今日焦點族群", "items": groups})
        outlook = _clean(raw.get("outlook"))
        if outlook:
            sections.append({"type": "quote", "text": f"開盤訊號：{outlook}", "source": None})

        content = apply_defaults(
            {
                "id": run_id,
                "kind": "briefing",
                "title": "台股盤前速報",
                "subtitle": outlook,
                "date": _iso_date(raw.get("date")),
                "disclaimer": True,
                "target_duration": 60,
                "sections": sections,
            },
            run_id=run_id,
        )
        validate(content)
        return content
