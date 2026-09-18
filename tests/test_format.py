import pytest

from infoshorts import format as fmt
from infoshorts.format import display, spoken


@pytest.mark.parametrize(
    ("n", "zh"),
    [
        (0, "零"),
        (2, "二"),
        (10, "十"),
        (12, "十二"),
        (20, "二十"),
        (105, "一百零五"),
        (200, "兩百"),
        (1050, "一千零五十"),
        (2000, "兩千"),
        (10500, "一萬零五百"),
        (20000, "兩萬"),
        (23456, "兩萬三千四百五十六"),
        (120000, "十二萬"),
        (100000000, "一億"),
        (250300000, "兩億五千零三十萬"),
    ],
)
def test_int_to_zh(n: int, zh: str) -> None:
    assert fmt.int_to_zh(n) == zh


def test_decimal_to_zh() -> None:
    assert fmt.decimal_to_zh("1.25") == "一點二五"
    assert fmt.decimal_to_zh("0.8") == "零點八"
    assert fmt.decimal_to_zh("23,456.789") == "兩萬三千四百五十六點七九"
    assert fmt.decimal_to_zh("-3.50") == "負三點五"
    assert fmt.decimal_to_zh(190) == "一百九十"


def test_mark_spoken_display() -> None:
    m = fmt.mark("47,160", "四萬七千一百六十")
    assert spoken(m) == "四萬七千一百六十"
    assert display(m) == "47,160"
    assert fmt.mark("同", "同") == "同"
    assert fmt.segments("收在" + m + "點") == [
        ("收在", "收在", False),
        ("47,160", "四萬七千一百六十", True),
        ("點", "點", False),
    ]


def test_percent_to_zh() -> None:
    assert spoken(fmt.percent_to_zh("+1.25%")) == "上漲一點二五個百分點"
    assert display(fmt.percent_to_zh("+1.25%")) == "上漲1.25%"
    assert spoken(fmt.percent_to_zh("-0.8%")) == "下跌零點八個百分點"
    assert spoken(fmt.percent_to_zh("3%")) == "三個百分點"
    assert fmt.percent_to_zh("0%") == "持平"
    assert fmt.percent_to_zh("abc") == "abc"


def test_delta_to_zh() -> None:
    assert spoken(fmt.delta_to_zh("+120", "點")) == "上漲一百二十點"
    assert display(fmt.delta_to_zh("+120", "點")) == "上漲120點"
    assert spoken(fmt.delta_to_zh(-15.5, "點")) == "下跌十五點五點"
    assert spoken(fmt.delta_to_zh("-0.8%")) == "下跌零點八個百分點"
    assert fmt.delta_to_zh(None) is None
    assert fmt.delta_to_zh(0) == "持平"
    assert spoken(fmt.delta_to_zh("+869.94億", kind="net")) == "買超八百六十九點九四億"
    assert display(fmt.delta_to_zh("+869.94億", kind="net")) == "買超869.94億"
    assert spoken(fmt.delta_to_zh("+31.58%", kind="yoy")) == "年增三十一點五八個百分點"


def test_pct_change_to_zh() -> None:
    assert spoken(fmt.pct_change_to_zh("+1.51%")) == "漲幅一點五一個百分點"
    assert display(fmt.pct_change_to_zh("+1.51%")) == "漲幅1.51%"
    assert spoken(fmt.pct_change_to_zh("-0.8%", "yoy")) == "年減零點八個百分點"
    assert fmt.pct_change_to_zh(None) is None


def test_value_to_zh() -> None:
    assert spoken(fmt.value_to_zh("190+")) == "超過一百九十"
    assert display(fmt.value_to_zh("190+")) == "超過190"
    assert spoken(fmt.value_to_zh("23,456", "點")) == "兩萬三千四百五十六點"
    assert display(fmt.value_to_zh("23,456", "點")) == "23,456點"
    assert fmt.value_to_zh(None) == "無資料"
    assert fmt.value_to_zh("N/A") == "N/A"
    assert spoken(fmt.value_to_zh("12.5%")) == "十二點五個百分點"
    assert spoken(fmt.value_to_zh("13.18", "%")) == "百分之十三點一八"
    assert display(fmt.value_to_zh("13.18", "%")) == "13.18%"


def test_date_to_zh() -> None:
    assert spoken(fmt.date_to_zh("2026-09-20")) == "九月二十日"
    assert display(fmt.date_to_zh("2026-09-20")) == "9月20日"
    assert spoken(fmt.date_to_zh("2026-11-03")) == "十一月三日"
    assert fmt.date_to_zh(None) is None
    assert fmt.date_to_zh("昨天") == "昨天"


def test_ticker_to_zh() -> None:
    m = fmt.ticker_to_zh("京元電子（2449）與欣銓 (3264)")
    assert spoken(m) == "京元電子（二四四九）與欣銓 (三二六四)"
    assert display(m) == "京元電子（2449）與欣銓 (3264)"


def test_readable_text() -> None:
    m = fmt.readable_text("台積電 ADR +1.25%，費半 -0.8%")
    assert spoken(m) == "台積電 ADR 上漲一點二五個百分點，費半 下跌零點八個百分點"
    assert display(m) == "台積電 ADR 上漲1.25%，費半 下跌0.8%"
    assert spoken(fmt.readable_text("台指期 +120 點")) == "台指期 上漲一百二十 點"
    assert fmt.readable_text("v2.0 更新") == "v2.0 更新"
    slash = fmt.readable_text("主要產品／服務 與 A / B")
    assert spoken(slash) == "主要產品、服務 與 A、B"
    assert display(slash) == "主要產品／服務 與 A / B"
    assert fmt.readable_text("2026/06") == "2026/06"  # 日期斜線不動
    once = fmt.readable_text("+5%")
    assert fmt.readable_text(once) == once  # 已標記的文字不再處理


def test_kind_for_column() -> None:
    assert fmt.kind_for_column("年增率") == "yoy"
    assert fmt.kind_for_column("YoY") == "yoy"
    assert fmt.kind_for_column("月增") == "mom"
    assert fmt.kind_for_column("買賣超") == "net"
    assert fmt.kind_for_column("漲跌%") == "change"
