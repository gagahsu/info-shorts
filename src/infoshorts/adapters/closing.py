"""closing adapter：ig-auto-post 的 `CLOSING_PAYLOAD`（台股盤後速報）→ content.json。

payload（2026-09-18 樣本，見 docs/ADAPTERS.md）：
  date、taiex_close/change/change_pct/volume、otc_close/change/change_pct/volume、
  institutional[{name, value:"+869.94億"}]、margin_change/margin_balance、
  breadth{up, down, limit_up, limit_down}、leading_groups/weak_groups（HTML，【族群名】內文）、notes（HTML）、caption。

取捨：成交量、融資、notes、caption 不用（時間預算）；族群只取【】內名稱。缺欄位 → null／不產 scene。
"""

from __future__ import annotations

import html
import json
import re
from typing import Any

from infoshorts.adapters.briefing import _iso_date
from infoshorts.content import apply_defaults, validate

_GROUP_NAME_RE = re.compile(r"【([^】]+)】")
MAX_GROUPS = 4


def _group_names(note: str | None) -> list[str]:
    if not note:
        return []
    text = html.unescape(re.sub(r"<[^>]+>", "", note))
    return [n.strip() for n in _GROUP_NAME_RE.findall(text) if n.strip()][:MAX_GROUPS]


def _rows(items: Any) -> list[list[Any]]:
    return [[it.get("name"), it.get("value")] for it in (items or []) if isinstance(it, dict)][:5]


class ClosingAdapter:
    name = "closing"

    def to_content(self, raw: dict[str, Any] | str, *, run_id: str) -> dict[str, Any]:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, dict):
            raise ValueError("closing adapter 的輸入必須是 CLOSING_PAYLOAD JSON 物件")

        sections: list[dict[str, Any]] = [
            {
                "type": "stat",
                "label": "加權指數",
                "value": raw.get("taiex_close"),
                "delta": raw.get("taiex_change"),
                "delta_pct": raw.get("taiex_change_pct"),
                "unit": "點",
            },
            {
                "type": "stat",
                "label": "櫃買指數",
                "value": raw.get("otc_close"),
                "delta": raw.get("otc_change"),
                "delta_pct": raw.get("otc_change_pct"),
                "unit": "點",
            },
        ]
        inst = _rows(raw.get("institutional"))
        if inst:
            sections.append({"type": "table", "heading": "三大法人買賣超", "columns": ["法人", "買賣超"], "rows": inst})
        breadth = raw.get("breadth") or {}
        if isinstance(breadth, dict) and any(breadth.get(k) for k in ("up", "down", "limit_up", "limit_down")):
            rows = [
                ["上漲家數", breadth.get("up")],
                ["下跌家數", breadth.get("down")],
                ["漲停", breadth.get("limit_up")],
                ["跌停", breadth.get("limit_down")],
            ]
            sections.append({"type": "table", "heading": "漲跌家數", "columns": [], "rows": rows})
        leading = _group_names(raw.get("leading_groups"))
        if leading:
            sections.append({"type": "bullets", "heading": "領漲族群", "items": leading})
        weak = _group_names(raw.get("weak_groups"))
        if weak:
            sections.append({"type": "bullets", "heading": "弱勢族群", "items": weak})

        content = apply_defaults(
            {
                "id": run_id,
                "kind": "closing",
                "title": "台股盤後速報",
                "subtitle": None,
                "date": _iso_date(raw.get("date")),
                "disclaimer": True,
                "target_duration": 60,
                "sections": sections,
            },
            run_id=run_id,
        )
        validate(content)
        return content
