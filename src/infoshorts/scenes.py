"""content.json → scenes.json：自動插入開場 title、每個 section 一個 scene、bullets 拆分、旁白稿生成。

旁白稿規則：口語、短句；數字讀法一律透過 format.py。
`narration` 已提供就照用（只做 readable_text 的數字轉換），為 null 才依畫面內容生成。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infoshorts import format as fmt

MAX_BULLETS_PER_SCENE = 5
DISCLAIMER_TEXT = "以上內容僅供參考，不構成任何投資建議。投資有風險，請自行審慎評估。"
DISCLAIMER_NARRATION = "以上內容僅供參考，不構成投資建議。"
ORDINALS = ["第一", "第二", "第三", "第四", "第五"]


def _scene(idx: int, type_: str, props: dict[str, Any], narration: str | None) -> dict[str, Any]:
    return {"idx": idx, "type": type_, "props": props, "narration": narration, "start": None, "end": None}


def _title_narration(c: dict[str, Any]) -> str:
    parts = [p for p in (fmt.date_to_zh(c.get("date")), c["title"], c.get("subtitle")) if p]
    return "，".join(parts) + "。"


def _stat_narration(s: dict[str, Any]) -> str:
    unit = s.get("unit") or ""
    label = s.get("label", "")
    text = f"{label}，{fmt.value_to_zh(s.get('value'), unit)}"
    delta = fmt.delta_to_zh(s.get("delta"), unit)
    if delta:
        text += f"，{delta}"
    return text + "。"


def _bullets_narration(heading: str, items: list[str]) -> str:
    body = "；".join(f"{ORDINALS[i]}，{fmt.readable_text(item)}" for i, item in enumerate(items))
    return f"{heading}。{body}。" if heading else body + "。"


def _table_narration(s: dict[str, Any]) -> str:
    cols = s.get("columns") or []
    rows = s.get("rows") or []
    lines = []
    for row in rows:
        cells = [fmt.value_to_zh(v) for v in row]
        if len(cols) == len(cells) and len(cells) > 1:
            rest = "，".join(f"{cols[i]}{cells[i]}" for i in range(1, len(cells)))
            lines.append(f"{cells[0]}，{rest}")
        else:
            lines.append("，".join(cells))
    head = s.get("heading") or ""
    return (head + "。" if head else "") + "；".join(lines) + "。"


def _quote_narration(s: dict[str, Any]) -> str:
    text = fmt.readable_text(s.get("text", ""))
    src = s.get("source")
    return f"{src}說，{text}" if src else text


def _chunks(items: list[str], size: int) -> list[list[str]]:
    if len(items) <= size:
        return [items]
    n = -(-len(items) // size)  # 拆成盡量平均的幾份
    per = -(-len(items) // n)
    return [items[i : i + per] for i in range(0, len(items), per)]


def build_scenes(content: dict[str, Any]) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    title_props = {"title": content["title"], "subtitle": content.get("subtitle"), "date": content.get("date")}
    scenes.append(_scene(0, "title", title_props, _title_narration(content)))
    for s in content["sections"]:
        given = s.get("narration")
        narration = fmt.readable_text(given) if given else None
        t = s["type"]
        if t == "stat":
            props = {
                "label": s.get("label", ""),
                "value": s.get("value"),
                "delta": s.get("delta"),
                "deltaDirection": s.get("delta_direction"),
                "unit": s.get("unit", ""),
            }
            scenes.append(_scene(len(scenes), t, props, narration or _stat_narration(s)))
        elif t == "bullets":
            heading = s.get("heading", "")
            groups = _chunks(list(s.get("items", [])), MAX_BULLETS_PER_SCENE)
            for gi, items in enumerate(groups):
                h = heading if gi == 0 else f"{heading}（續）"
                if narration:
                    nar = narration if gi == 0 else None  # 使用者給的旁白只放第一段，續段靜音
                else:
                    nar = _bullets_narration(heading if gi == 0 else "", items)
                scenes.append(_scene(len(scenes), t, {"heading": h, "items": items}, nar))
        elif t == "table":
            props = {"heading": s.get("heading", ""), "columns": s.get("columns", []), "rows": s.get("rows", [])}
            scenes.append(_scene(len(scenes), t, props, narration or _table_narration(s)))
        elif t == "quote":
            props = {"text": s.get("text", ""), "source": s.get("source")}
            scenes.append(_scene(len(scenes), t, props, narration or _quote_narration(s)))
        else:
            raise ValueError(f"未知 section type：{t}")
    if content.get("disclaimer"):
        scenes.append(_scene(len(scenes), "disclaimer", {"text": DISCLAIMER_TEXT}, DISCLAIMER_NARRATION))
    return scenes


def narration_summary(scenes: list[dict[str, Any]]) -> str:
    lines = []
    for s in scenes:
        nar = s["narration"] or "（無旁白，固定 2.5 秒）"
        lines.append(f"[{s['idx']}] {s['type']:<10} {nar}")
    return "\n".join(lines)


def dump(scenes: list[dict[str, Any]], path: str | Path) -> None:
    Path(path).write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")


def load(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
