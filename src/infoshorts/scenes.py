"""content.json → scenes.json：自動插入開場 title、每個 section 一個 scene、bullets 拆分、旁白稿生成。

旁白稿規則：口語、短句；數字讀法一律透過 format.py。
`narration` 已提供就照用（只做 readable_text 的數字轉換），為 null 才依畫面內容生成。
"""

from __future__ import annotations

import json
import re
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
    return fmt.ticker_to_zh("，".join(parts)) + "。"


def _stat_narration(s: dict[str, Any]) -> str:
    unit = s.get("unit") or ""
    label = s.get("label", "")
    kind = s.get("delta_kind") or "change"
    text = f"{fmt.ticker_to_zh(label)}，{fmt.value_to_zh(s.get('value'), unit)}"
    delta = fmt.delta_to_zh(s.get("delta"), unit, kind)
    if delta:
        text += f"，{delta}"
    pct = fmt.pct_change_to_zh(s.get("delta_pct"), kind)
    if pct:
        text += f"，{pct}"
    return text + "。"


def _bullets_narration(heading: str, items: list[str]) -> str:
    body = "；".join(f"{ORDINALS[i]}，{fmt.readable_text(item)}" for i, item in enumerate(items))
    return f"{heading}。{body}。" if heading else body + "。"


def _signed_table_narration(heading: str, rows: list[list[Any]], kind: str) -> str | None:
    """兩欄且第二欄全是同單位帶號數值（或缺值）的表格，用壓縮讀法；否則回 None。

    同方向：「美股主要指數全數上漲，道瓊零點六一、那斯達克一點六九個百分點。」
    混合：  「美股主要指數。道瓊上漲零點六一、標普下跌零點二個百分點。」
    法人：  「三大法人全數買超，外資八百六十九點九四、投信五十二點八九億。」（kind=net）
    """
    parsed: list[tuple[str, str | None, str | None]] = []  # (name, sign, num)
    suffixes: set[str] = set()
    for row in rows:
        if len(row) != 2:
            return None
        name, val = row
        if val is None or str(val).strip() == "":
            parsed.append((str(name or "—"), None, None))
            continue
        p = fmt.parse_signed(val)
        if p is None or p[0] == "":
            return None
        parsed.append((str(name or "—"), p[0], p[1]))
        suffixes.add(p[2])
    signs = {p[1] for p in parsed if p[1]}
    if not signs or len(suffixes) != 1:
        return None
    suffix = suffixes.pop()
    tail = "個百分點" if suffix == "%" else suffix
    up, down, _, _ = fmt.KIND_WORDS.get(kind, fmt.KIND_WORDS["change"])
    word = {"+": up, "-": down}
    if len(signs) == 1:
        sign = signs.pop()
        items = [f"{n}{fmt.decimal_to_zh(num)}" if num else f"{n}無資料" for n, _, num in parsed]
        head = f"{heading}全數{word[sign]}，" if heading else f"全數{word[sign]}，"
        return head + "、".join(items) + tail + "。"
    items = [f"{n}{word[sg]}{fmt.decimal_to_zh(num)}" if (num and sg) else f"{n}無資料" for n, sg, num in parsed]
    return (f"{heading}。" if heading else "") + "、".join(items) + tail + "。"


def _cell_to_zh(value: Any, col: str) -> str:
    """儲存格讀法：帶號數值依欄名語意（年增／買超／上漲）；純數值帶上欄名括號裡的單位（營收(億) → 三十六點二二億）。"""
    p = fmt.parse_signed(value)
    if p and p[0]:
        return fmt.signed_to_zh(value, fmt.kind_for_column(col)) or fmt.value_to_zh(value)
    if p and not p[2]:
        return fmt.value_to_zh(value, _column_unit(col))
    return fmt.value_to_zh(value)


_COL_UNIT_RE = re.compile(r"[（(]\s*([^）)]*?)\s*[）)]\s*$")


def _column_unit(col: str) -> str:
    """欄名括號內的單位：'營收(億)' → '億'；'漲跌%' → ''（% 走帶號路徑）；沒有 → ''。"""
    m = _COL_UNIT_RE.search(col)
    unit = m.group(1) if m else ""
    return "" if unit in ("%", "％") else unit


def _table_narration(s: dict[str, Any]) -> str:
    cols = s.get("columns") or []
    rows = s.get("rows") or []
    if len(cols) == 2:
        compact = _signed_table_narration(s.get("heading") or "", rows, fmt.kind_for_column(cols[1]))
        if compact:
            return compact
    lines = []
    for row in rows:
        if len(cols) == len(row) and len(row) > 1:
            first = fmt.ticker_to_zh(fmt.value_to_zh(row[0]))
            names = [_column_name(c) for c in cols]
            cells = [_cell_to_zh(row[i], cols[i]) for i in range(1, len(row))]
            # 讀法已含方向（上漲／年增／買超…）就不再唸欄名，避免「漲跌上漲零點六個百分點」
            parts = [c if c.startswith(fmt.DIRECTION_WORDS) else f"{names[i + 1]}{c}" for i, c in enumerate(cells)]
            lines.append(f"{first}，{'，'.join(parts)}")
        else:
            lines.append("，".join(fmt.value_to_zh(v) for v in row))
    head = s.get("heading") or ""
    return (head + "。" if head else "") + "；".join(lines) + "。"


def _column_name(col: str) -> str:
    """欄名的單位標記不讀：「漲跌%」→「漲跌」、「收盤(點)」→「收盤」。"""
    return re.sub(r"[\s（(]*[%％][）)]*$|[（(][^）)]*[）)]$", "", col).strip()


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
                "deltaPct": s.get("delta_pct"),
                "deltaKind": s.get("delta_kind") or "change",
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
