import json
from pathlib import Path

from infoshorts.adapters import get_adapter
from infoshorts.adapters.briefing import _focus_groups, _iso_date, _premium
from infoshorts.content import validate
from infoshorts.scenes import build_scenes

FIXTURES = Path(__file__).parent / "fixtures" / "briefing"


def _raw() -> dict:
    return json.loads((FIXTURES / "input.json").read_text(encoding="utf-8"))


def test_fixture_to_content() -> None:
    expected = json.loads((FIXTURES / "expected_content.json").read_text(encoding="utf-8"))
    content = get_adapter("briefing").to_content(_raw(), run_id="2026-09-18-briefing")
    validate(content)
    assert content == expected
    assert content["kind"] == "briefing"
    assert content["disclaimer"] is True
    assert content["date"] == "2026-09-18"
    assert content["subtitle"] == "偏多開高"  # emoji 去掉


def test_section_mapping() -> None:
    content = get_adapter("briefing").to_content(_raw(), run_id="x")
    types = [s["type"] for s in content["sections"]]
    assert types == ["stat", "table", "table", "stat", "bullets", "bullets", "quote"]
    futures = content["sections"][0]
    assert (futures["value"], futures["delta"], futures["delta_pct"], futures["unit"]) == (
        "47,160",
        "+701",
        "+1.51%",
        "點",
    )
    assert futures["delta_direction"] == "up"
    us = content["sections"][1]
    assert us["columns"] == ["指數", "漲跌%"]
    assert us["rows"][0] == ["道瓊", "+0.61%"] and len(us["rows"]) == 4
    premium = content["sections"][3]
    assert (premium["label"], premium["value"], premium["unit"]) == ("台積電 ADR 溢價率", "13.18", "%")
    news = content["sections"][4]
    assert len(news["items"]) == 2 and news["items"][0].startswith("美債殖利率回落")
    groups = content["sections"][5]
    assert groups["items"] == ["晶圓代工與先進封裝", "AI伺服器與散熱零組件", "營建與資產活化概念"]
    assert content["sections"][6]["text"] == "開盤訊號：偏多開高"


def test_narration_readings() -> None:
    scenes = build_scenes(get_adapter("briefing").to_content(_raw(), run_id="x"))
    nar = {s["idx"]: s["narration"] for s in scenes}
    assert nar[0] == "九月十八日，台股盤前速報，偏多開高。"
    assert nar[1] == "台指期夜盤，四萬七千一百六十點，上漲七百零一點，漲幅一點五一個百分點。"
    assert (
        nar[2] == "美股主要指數全數上漲，道瓊零點六一、S&P 500一點一四、那斯達克一點六九、費城半導體三點一四個百分點。"
    )
    assert nar[4] == "台積電 ADR 溢價率，百分之十三點一八。"
    assert scenes[-1]["type"] == "disclaimer"


def test_missing_fields_do_not_invent_data() -> None:
    content = get_adapter("briefing").to_content({"date": "2026-09-19", "futures_close": None}, run_id="x")
    types = [s["type"] for s in content["sections"]]
    assert types == ["stat", "stat"]  # 台指期（缺值）+ 溢價（缺值）；其他 scene 不產生
    assert content["sections"][0]["value"] is None
    assert content["sections"][1]["value"] is None
    assert content["subtitle"] is None


def test_helpers() -> None:
    assert _iso_date("2026.9.8") == "2026-09-08"
    assert _iso_date("2026-09-18") == "2026-09-18"
    assert _iso_date("昨天") == "昨天"
    assert _premium("折價 -2.1%") == ("台積電 ADR 折價率", "2.1")
    assert _premium("溢價 +13.18%") == ("台積電 ADR 溢價率", "13.18")
    assert _premium("n/a") == ("台積電 ADR 溢價率", None)
    note = (
        "<strong>【焦點族群】</strong><br>1. 甲族群：內文 3.14%：多個冒號<br>2. 乙族群：內文<br><br>"
        "<strong>【開盤觀測】</strong><br>3. 不是族群：x"
    )
    assert _focus_groups(note) == ["甲族群", "乙族群"]
    assert _focus_groups(None) == []
