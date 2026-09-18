"""數字／百分比／日期的中文讀法。所有 adapter 與 scenes.py 共用，規則只寫在這裡。

- 整數：≥ 1 萬用中文單位（兩萬三千四百五十六）；「兩」用在百／千／萬／億前，「二」用在個／十位。
- 小數：逐位讀（一點二五），最多保留兩位。
- 百分比：+1.25% → 上漲一點二五個百分點；-0.8% → 下跌零點八個百分點；無正負號只讀數值。
- 日期：2026-09-20 → 九月二十日。
- 英文縮寫（ADR、ETF、AI）保留原文，edge-tts 會讀字母。
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

DIGITS = "零一二三四五六七八九"
SMALL_UNITS = ["", "十", "百", "千"]
BIG_UNITS = ["", "萬", "億", "兆"]

_PERCENT_RE = re.compile(r"([+-]?)(\d[\d,]*(?:\.\d+)?)\s*%")
_SIGNED_RE = re.compile(r"(?<![\w.])([+-])(\d[\d,]*(?:\.\d+)?)(?!\s*%)")
_PLAIN_NUM_RE = re.compile(r"[+-]?\d[\d,]*(?:\.\d+)?")


def _section_to_zh(n: int) -> str:
    """0 < n < 10000 的讀法，含內部零：1005 → 一千零五；1050 → 一千零五十。"""
    if n == 0:
        return ""
    out: list[str] = []
    digits = [int(d) for d in str(n)]
    length = len(digits)
    pending_zero = False
    for i, d in enumerate(digits):
        pos = length - i - 1
        if d == 0:
            pending_zero = True
            continue
        if pending_zero and out:
            out.append("零")
        pending_zero = False
        char = "兩" if (d == 2 and pos >= 2) else DIGITS[d]
        out.append(char + SMALL_UNITS[pos])
    text = "".join(out)
    if text.startswith("一十"):
        text = text[1:]
    return text


def int_to_zh(n: int) -> str:
    if n < 0:
        return "負" + int_to_zh(-n)
    if n == 0:
        return "零"
    parts: list[str] = []
    sections: list[int] = []
    while n > 0:
        sections.append(n % 10000)
        n //= 10000
    for idx in range(len(sections) - 1, -1, -1):
        sec = sections[idx]
        if sec == 0:
            continue
        if sec == 2 and idx > 0:
            text = "兩"  # 兩萬 / 兩億
        else:
            text = _section_to_zh(sec)
        if idx < len(sections) - 1 and sec < 1000:
            text = "零" + text
        parts.append(text + BIG_UNITS[idx])
    return "".join(parts).replace("零零", "零")


def decimal_to_zh(value: str | float | int | Decimal, places: int = 2) -> str:
    """任意數字（字串可含逗號與正負號）→ 中文讀法。小數最多 `places` 位（四捨五入，去尾零）。"""
    s = str(value).replace(",", "").strip()
    neg = s.startswith("-")
    s = s.lstrip("+-")
    d = Decimal(s)
    if d == d.to_integral_value():
        text = int_to_zh(int(d))
    else:
        q = d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        int_part, _, frac = str(q).partition(".")
        frac = frac.rstrip("0")
        text = int_to_zh(int(int_part))
        if frac:
            text += "點" + "".join(DIGITS[int(ch)] for ch in frac)
    return ("負" if neg else "") + text


def percent_to_zh(text: str) -> str:
    """'+1.25%' → 上漲一點二五個百分點；'-0.8%' → 下跌零點八個百分點；'3%' → 三個百分點；0 → 持平。"""
    m = _PERCENT_RE.fullmatch(text.strip())
    if not m:
        return text
    sign, num = m.group(1), m.group(2)
    if Decimal(num.replace(",", "")) == 0:
        return "持平"
    body = decimal_to_zh(num) + "個百分點"
    return {"+": "上漲", "-": "下跌"}.get(sign, "") + body


def delta_to_zh(delta: Any, unit: str = "") -> str | None:
    """漲跌值讀法：'+120' 點 → 上漲一百二十點；'-0.8%' → 下跌零點八個百分點；None → None。"""
    if delta is None or str(delta).strip() == "":
        return None
    s = str(delta).strip()
    if s.endswith("%"):
        return percent_to_zh(s)
    m = re.fullmatch(r"([+-]?)(\d[\d,]*(?:\.\d+)?)", s)
    if not m:
        return s
    sign, num = m.group(1), m.group(2)
    if Decimal(num.replace(",", "")) == 0:
        return "持平"
    return {"+": "上漲", "-": "下跌"}.get(sign, "") + decimal_to_zh(num) + unit


def value_to_zh(value: Any, unit: str = "") -> str:
    """主要數值讀法：'190+' → 超過一百九十；'23,456' → 兩萬三千四百五十六；非數字原樣。None → 「無資料」。"""
    if value is None:
        return "無資料"
    s = str(value).strip()
    if s.endswith("%"):
        return percent_to_zh(s)
    more = s.endswith("+")
    core = s.rstrip("+")
    if _PLAIN_NUM_RE.fullmatch(core):
        text = decimal_to_zh(core) + unit
        return "超過" + text if more else text
    return s + unit


def date_to_zh(iso: str | None) -> str | None:
    """'2026-09-20' → 九月二十日（不讀年）。格式不對就原樣回傳。"""
    if not iso:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", iso.strip())
    if not m:
        return iso
    month, day = int(m.group(2)), int(m.group(3))
    return f"{int_to_zh(month)}月{int_to_zh(day)}日"


def readable_text(text: str) -> str:
    """自由文字中的百分比與帶正負號數字轉中文讀法；純數字交給 TTS 自行處理。"""
    text = _PERCENT_RE.sub(lambda m: percent_to_zh(m.group(0)), text)
    text = _SIGNED_RE.sub(lambda m: delta_to_zh(m.group(0)) or m.group(0), text)
    return text
