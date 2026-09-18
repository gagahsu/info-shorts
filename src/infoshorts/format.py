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
_SLASH_RE = re.compile(r"(?<!\d)\s*[／/]\s*(?!\d)")

# ---------------------------------------------------------------- 顯示／唸法雙軌
# 旁白稿裡的數字要「唸」中文（四萬七千一百六十）但字幕要「顯示」數字（47,160）。
# 讀法函式回傳的是「標記文字」：顯示唸法；TTS 前用 spoken() 取唸法，字幕用 display() 取顯示。
M_START, M_SEP, M_END = "", "", ""
_MARK_RE = re.compile(f"{M_START}(.*?){M_SEP}(.*?){M_END}", re.DOTALL)


def mark(display_text: str, spoken_text: str) -> str:
    """把「顯示文字」與「唸法」綁在一起；兩者相同就不加標記。"""
    if display_text == spoken_text:
        return spoken_text
    return f"{M_START}{display_text}{M_SEP}{spoken_text}{M_END}"


def spoken(text: str | None) -> str:
    """標記文字 → 給 TTS 唸的純文字（None → ''）。"""
    return _MARK_RE.sub(lambda m: m.group(2), text or "")


def display(text: str | None) -> str:
    """標記文字 → 給字幕顯示的純文字（None → ''）。"""
    return _MARK_RE.sub(lambda m: m.group(1), text or "")


def segments(text: str) -> list[tuple[str, str, bool]]:
    """標記文字 → [(顯示, 唸法, 是否為替換段)]，依序串接即原文。"""
    out: list[tuple[str, str, bool]] = []
    pos = 0
    for m in _MARK_RE.finditer(text):
        if m.start() > pos:
            plain = text[pos : m.start()]
            out.append((plain, plain, False))
        out.append((m.group(1), m.group(2), True))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], text[pos:], False))
    return out


def num(raw: str, places: int = 2) -> str:
    """數字的標記讀法：'47,160' → 顯示 47,160、唸 四萬七千一百六十。"""
    return mark(raw, decimal_to_zh(raw, places))


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
    sign, n = m.group(1), m.group(2)
    if Decimal(n.replace(",", "")) == 0:
        return "持平"
    body = mark(f"{n}%", decimal_to_zh(n) + "個百分點")
    return {"+": "上漲", "-": "下跌"}.get(sign, "") + body


# 漲跌的語意（content.json stat.delta_kind / 表格欄名推得）：(正, 負, 正幅度, 負幅度)
KIND_WORDS = {
    "change": ("上漲", "下跌", "漲幅", "跌幅"),
    "yoy": ("年增", "年減", "年增", "年減"),
    "mom": ("月增", "月減", "月增", "月減"),
    "net": ("買超", "賣超", "買超", "賣超"),
}
DIRECTION_WORDS = tuple({w for ws in KIND_WORDS.values() for w in ws} | {"持平"})
_SIGNED_ANY_RE = re.compile(r"([+-]?)\s*(\d[\d,]*(?:\.\d+)?)\s*(%|％|[^\d\s+\-.,]*)")
_TICKER_RE = re.compile(r"([（(])\s*(\d{4,6})\s*([)）])")


def kind_for_column(name: str) -> str:
    """從表格欄名推語意：年增／YoY → yoy；月增／MoM → mom；買賣超／法人 → net；其餘 change。"""
    n = name.lower()
    if "年增" in n or "年減" in n or "yoy" in n:
        return "yoy"
    if "月增" in n or "月減" in n or "mom" in n:
        return "mom"
    if "買超" in n or "賣超" in n or "買賣超" in n or "法人" in n:
        return "net"
    return "change"


def parse_signed(text: Any) -> tuple[str, str, str] | None:
    """'+869.94億' → ('+','869.94','億')；'-0.8%' → ('-','0.8','%')；'47,160' → ('','47,160','')；非數值 → None。"""
    if text is None:
        return None
    m = _SIGNED_ANY_RE.fullmatch(str(text).strip())
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3).replace("％", "%")


def signed_to_zh(text: Any, kind: str = "change", unit: str = "") -> str | None:
    """帶號數值讀法（含 % 或單位後綴）：'+120'（unit 點）→ 上漲一百二十點；'+869.94億'（net）→ 買超八百六十九點九四億；
    '-0.8%' → 下跌零點八個百分點；'+31.58%'（yoy）→ 年增三十一點五八個百分點；0 → 持平；None／非數值 → None。"""
    parsed = parse_signed(text)
    if parsed is None:
        return None
    sign, n, suffix = parsed
    if Decimal(n.replace(",", "")) == 0:
        return "持平"
    up, down, _, _ = KIND_WORDS.get(kind, KIND_WORDS["change"])
    if suffix == "%":
        body = mark(f"{n}%", decimal_to_zh(n) + "個百分點")
    else:
        body = num(n) + (suffix or unit)
    return {"+": up, "-": down}.get(sign, "") + body


def delta_to_zh(delta: Any, unit: str = "", kind: str = "change") -> str | None:
    """漲跌值讀法：'+120' 點 → 上漲一百二十點；'-0.8%' → 下跌零點八個百分點；None → None；非數值原樣。"""
    if delta is None or str(delta).strip() == "":
        return None
    return signed_to_zh(delta, kind, unit) or str(delta).strip()


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
        if unit in ("%", "％"):
            text = mark(f"{core}%", "百分之" + decimal_to_zh(core))
        else:
            text = num(core) + unit
        return "超過" + text if more else text
    return s + unit


def pct_change_to_zh(pct: Any, kind: str = "change") -> str | None:
    """漲跌幅讀法：'+1.51%' → 漲幅一點五一個百分點；'-0.8%' → 跌幅零點八個百分點；yoy：年增／年減；0 → 持平。"""
    if pct is None or str(pct).strip() == "":
        return None
    parsed = parse_signed(pct)
    if parsed is None:
        return str(pct).strip()
    sign, n, _ = parsed
    if Decimal(n.replace(",", "")) == 0:
        return "持平"
    _, _, up, down = KIND_WORDS.get(kind, KIND_WORDS["change"])
    return {"+": up, "-": down}.get(sign, "幅度") + mark(f"{n}%", decimal_to_zh(n) + "個百分點")


def ticker_to_zh(text: str) -> str:
    """括號內的股票代號逐位讀：京元電子（2449）→ 唸「二四四九」、顯示 2449。"""
    return _TICKER_RE.sub(
        lambda m: m.group(1) + mark(m.group(2), "".join(DIGITS[int(ch)] for ch in m.group(2))) + m.group(3), text
    )


def date_to_zh(iso: str | None) -> str | None:
    """'2026-09-20' → 唸「九月二十日」、顯示 9月20日（不讀年）。格式不對就原樣回傳。"""
    if not iso:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", iso.strip())
    if not m:
        return iso
    month, day = int(m.group(2)), int(m.group(3))
    return mark(f"{month}月{day}日", f"{int_to_zh(month)}月{int_to_zh(day)}日")


def readable_text(text: str) -> str:
    """自由文字：股票代號逐位讀、百分比與帶號數字轉中文讀法、「／」唸成「、」；純數字交給 TTS。"""
    if M_START in text:  # 已經是標記文字（例如使用者提供的旁白經過一次處理）就不再處理
        return text
    text = ticker_to_zh(text)
    text = _PERCENT_RE.sub(lambda m: percent_to_zh(m.group(0)), text)
    text = _SIGNED_RE.sub(lambda m: delta_to_zh(m.group(0)) or m.group(0), text)
    text = _SLASH_RE.sub(lambda m: mark(m.group(0), "、"), text)
    return text
