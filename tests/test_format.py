import pytest

from infoshorts import format as fmt


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


def test_percent_to_zh() -> None:
    assert fmt.percent_to_zh("+1.25%") == "上漲一點二五個百分點"
    assert fmt.percent_to_zh("-0.8%") == "下跌零點八個百分點"
    assert fmt.percent_to_zh("3%") == "三個百分點"
    assert fmt.percent_to_zh("0%") == "持平"
    assert fmt.percent_to_zh("abc") == "abc"


def test_delta_to_zh() -> None:
    assert fmt.delta_to_zh("+120", "點") == "上漲一百二十點"
    assert fmt.delta_to_zh(-15.5, "點") == "下跌十五點五點"
    assert fmt.delta_to_zh("-0.8%") == "下跌零點八個百分點"
    assert fmt.delta_to_zh(None) is None
    assert fmt.delta_to_zh(0) == "持平"


def test_value_to_zh() -> None:
    assert fmt.value_to_zh("190+") == "超過一百九十"
    assert fmt.value_to_zh("23,456", "點") == "兩萬三千四百五十六點"
    assert fmt.value_to_zh(None) == "無資料"
    assert fmt.value_to_zh("N/A") == "N/A"
    assert fmt.value_to_zh("12.5%") == "十二點五個百分點"


def test_date_to_zh() -> None:
    assert fmt.date_to_zh("2026-09-20") == "九月二十日"
    assert fmt.date_to_zh("2026-11-03") == "十一月三日"
    assert fmt.date_to_zh(None) is None
    assert fmt.date_to_zh("昨天") == "昨天"


def test_readable_text() -> None:
    assert (
        fmt.readable_text("台積電 ADR +1.25%，費半 -0.8%") == "台積電 ADR 上漲一點二五個百分點，費半 下跌零點八個百分點"
    )
    assert fmt.readable_text("台指期 +120 點") == "台指期 上漲一百二十 點"
    assert fmt.readable_text("v2.0 更新") == "v2.0 更新"
