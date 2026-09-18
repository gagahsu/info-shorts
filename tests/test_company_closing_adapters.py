import json
from pathlib import Path

import pytest

from infoshorts.adapters import get_adapter, names
from infoshorts.adapters.closing import _group_names
from infoshorts.adapters.company import _month_zh_label, _name_only, _signed_pct
from infoshorts.content import validate
from infoshorts.scenes import build_scenes

FIX = Path(__file__).parent / "fixtures"


def _raw(name: str) -> dict:
    return json.loads((FIX / name / "input.json").read_text(encoding="utf-8"))


def test_registry_has_all_adapters() -> None:
    assert names() == ["briefing", "closing", "company", "generic"]


@pytest.mark.parametrize(("name", "rid"), [("company", "2026-09-19-company"), ("closing", "2026-09-18-closing")])
def test_fixture_to_content(name: str, rid: str) -> None:
    expected = json.loads((FIX / name / "expected_content.json").read_text(encoding="utf-8"))
    content = get_adapter(name).to_content(_raw(name), run_id=rid)
    validate(content)
    assert content == expected
    assert content["kind"] == name
    assert content["disclaimer"] is True


# ---------------------------------------------------------------- company


def test_company_mapping() -> None:
    c = get_adapter("company").to_content(_raw("company"), run_id="x")
    assert c["title"] == "京元電子（2449）"
    assert c["subtitle"] == "全球專業測試龍頭・AI晶片測試品質守門員"
    types = [s["type"] for s in c["sections"]]
    assert types == ["quote", "bullets", "stat", "table", "bullets", "bullets"]
    products = c["sections"][1]
    assert products["items"] == ["晶圓測試", "成品測試", "高功率預燒測試"]
    stat = c["sections"][2]
    assert (stat["label"], stat["value"], stat["delta_pct"], stat["delta_kind"], stat["unit"]) == (
        "2026年8月營收",
        40.8,
        "+31.58%",
        "yoy",
        "億元",
    )
    assert stat["delta_direction"] == "up"
    table = c["sections"][3]
    assert table["columns"] == ["月份", "營收(億)", "年增率"]
    assert table["rows"] == [
        ["2026年6月", 36.22, "+28.64%"],
        ["7月", 39.91, "+36.75%"],
        ["8月", 40.8, "+31.58%"],
    ]
    assert c["sections"][4]["items"] == ["欣銓 (3264)", "矽格 (6257)", "日月光投控 (3711)", "Amkor (艾克爾)"]
    assert c["sections"][5]["items"] == ["AI 測試佔比持續衝高", "擴大資本支出與擴產佈局"]


def test_company_narration() -> None:
    scenes = build_scenes(get_adapter("company").to_content(_raw("company"), run_id="x"))
    nar = {s["idx"]: s["narration"] for s in scenes}
    assert nar[0].endswith("京元電子（二四四九），全球專業測試龍頭・AI晶片測試品質守門員。")
    assert nar[3] == "2026年8月營收，四十點八億元，年增三十一點五八個百分點。"
    assert nar[4].startswith("近期月營收。2026年6月，營收三十六點二二億，年增二十八點六四個百分點；")
    assert "欣銓 (三二六四)" in nar[5]
    assert scenes[-1]["type"] == "disclaimer"


def test_company_missing_slides() -> None:
    minimal = {"ticker": "1234 測試", "slides": [{"type": "bullets", "items": ["甲：內文", "乙"]}]}
    c = get_adapter("company").to_content(minimal, run_id="x")
    assert c["title"] == "測試（1234）"
    assert c["subtitle"] is None
    assert [s["type"] for s in c["sections"]] == ["bullets"]
    assert c["sections"][0]["items"] == ["甲", "乙"]
    with pytest.raises(ValueError):  # 只有 cover、沒有任何可用內容 → 不出片
        get_adapter("company").to_content({"slides": [{"type": "cover", "title": "測試"}]}, run_id="x")


def test_company_helpers() -> None:
    assert _name_only("晶圓測試（Wafer Probe / CP Test）：內文") == "晶圓測試"
    assert _name_only("沒有冒號 (x)") == "沒有冒號"
    assert _month_zh_label("26/08") == "2026年8月"
    assert _month_zh_label("2026-08") == "2026-08"
    assert _signed_pct(31.58) == "+31.58%"
    assert _signed_pct(-5) == "-5%"
    assert _signed_pct("n/a") is None


# ---------------------------------------------------------------- closing


def test_closing_mapping() -> None:
    c = get_adapter("closing").to_content(_raw("closing"), run_id="x")
    assert c["date"] == "2026-09-18"
    types = [s["type"] for s in c["sections"]]
    assert types == ["stat", "stat", "table", "table", "bullets", "bullets"]
    taiex, otc = c["sections"][0], c["sections"][1]
    assert (taiex["value"], taiex["delta"], taiex["delta_pct"]) == ("47180.75", "+892.75", "+1.93%")
    assert (otc["value"], otc["delta"], otc["delta_pct"]) == ("412.68", "+14.51", "+3.64%")
    inst = c["sections"][2]
    assert inst["columns"] == ["法人", "買賣超"]
    assert inst["rows"][0] == ["外資", "+869.94億"] and len(inst["rows"]) == 4
    breadth = c["sections"][3]
    assert breadth["rows"] == [["上漲家數", "1321"], ["下跌家數", "474"], ["漲停", "68"], ["跌停", "1"]]
    assert c["sections"][4]["items"] == ["半導體與高價ASIC", "記憶體族群", "營建資產族群"]
    assert c["sections"][5]["items"] == ["金融保險", "傳統傳產族群", "面板與遭調節股"]


def test_closing_narration() -> None:
    scenes = build_scenes(get_adapter("closing").to_content(_raw("closing"), run_id="x"))
    nar = {s["idx"]: s["narration"] for s in scenes}
    assert nar[1] == "加權指數，四萬七千一百八十點七五點，上漲八百九十二點七五點，漲幅一點九三個百分點。"
    assert nar[3].startswith("三大法人買賣超全數買超，外資八百六十九點九四、投信五十二點八九、")
    assert nar[3].endswith("自營商兩百四十三點零三、合計一千一百六十五點八七億。")
    assert nar[4] == "漲跌家數。上漲家數，一千三百二十一；下跌家數，四百七十四；漲停，六十八；跌停，一。"


def test_closing_missing() -> None:
    c = get_adapter("closing").to_content({"date": "2026.09.19"}, run_id="x")
    assert [s["type"] for s in c["sections"]] == ["stat", "stat"]
    assert c["sections"][0]["value"] is None
    assert _group_names("<strong>【甲】</strong>x<br><strong>【乙】</strong>y") == ["甲", "乙"]
    assert _group_names(None) == []
