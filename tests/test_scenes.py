from infoshorts.adapters import get_adapter
from infoshorts.scenes import DISCLAIMER_NARRATION, build_scenes


def _content(**over):
    raw = {
        "title": "測試",
        "subtitle": "副標",
        "date": "2026-09-20",
        "sections": [
            {"type": "stat", "label": "台指期", "value": "23,456", "delta": "+120", "unit": "點"},
            {"type": "bullets", "heading": "重點", "items": [f"第{i}條" for i in range(1, 8)]},
            {"type": "quote", "text": "結論。", "source": "某人"},
            {
                "type": "table",
                "heading": "指數",
                "columns": ["指數", "收盤", "漲跌%"],
                "rows": [["道瓊", "42,100", "+0.5%"], ["標普", None, None]],
            },
        ],
    }
    raw.update(over)
    return get_adapter("generic").to_content(raw, run_id="rid")


def test_title_inserted_and_narrations() -> None:
    scenes = build_scenes(_content())
    assert scenes[0]["type"] == "title"
    assert scenes[0]["narration"] == "九月二十日，測試，副標。"
    stat = scenes[1]
    assert stat["type"] == "stat"
    assert stat["narration"] == "台指期，兩萬三千四百五十六點，上漲一百二十點。"
    assert stat["props"]["deltaDirection"] == "up"
    assert all(s["start"] is None and s["end"] is None for s in scenes)
    assert [s["idx"] for s in scenes] == list(range(len(scenes)))


def test_bullets_split_over_five() -> None:
    scenes = build_scenes(_content())
    bullets = [s for s in scenes if s["type"] == "bullets"]
    assert len(bullets) == 2
    assert len(bullets[0]["props"]["items"]) == 4
    assert len(bullets[1]["props"]["items"]) == 3
    assert bullets[0]["narration"].startswith("重點。第一，第1條；第二，")
    assert bullets[1]["props"]["heading"] == "重點（續）"
    assert bullets[1]["narration"].startswith("第一，第5條")


def test_quote_and_table_narration() -> None:
    scenes = build_scenes(_content())
    quote = next(s for s in scenes if s["type"] == "quote")
    assert quote["narration"] == "某人說，結論。"
    table = next(s for s in scenes if s["type"] == "table")
    assert table["narration"] == "指數。道瓊，收盤四萬兩千一百，上漲零點五個百分點；標普，收盤無資料，漲跌無資料。"


def test_disclaimer_appended() -> None:
    scenes = build_scenes(_content(disclaimer=True))
    assert scenes[-1]["type"] == "disclaimer"
    assert scenes[-1]["narration"] == DISCLAIMER_NARRATION
    assert build_scenes(_content(disclaimer=False))[-1]["type"] != "disclaimer"


def test_given_narration_gets_number_reading() -> None:
    c = _content(sections=[{"type": "stat", "label": "x", "value": 1, "narration": "今天漲了 +1.25%。"}])
    assert build_scenes(c)[1]["narration"] == "今天漲了 上漲一點二五個百分點。"


def test_pct_table_compact_narration() -> None:
    same = _content(
        sections=[
            {
                "type": "table",
                "heading": "美股主要指數",
                "columns": ["指數", "漲跌%"],
                "rows": [["道瓊", "+0.61%"], ["那斯達克", "+1.69%"], ["費半", None]],
            }
        ]
    )
    assert build_scenes(same)[1][
        "narration"
    ] == "美股主要指數全數上漲，道瓊零點六一、那斯達克一點六九、費半無資料個百分點。".replace(
        "費半無資料個百分點", "費半無資料個百分點"
    )
    mixed = _content(
        sections=[
            {
                "type": "table",
                "heading": "",
                "columns": ["指數", "漲跌%"],
                "rows": [["道瓊", "+0.61%"], ["標普", "-0.2%"]],
            }
        ]
    )
    assert build_scenes(mixed)[1]["narration"] == "道瓊上漲零點六一、標普下跌零點二個百分點。"
    plain = _content(
        sections=[{"type": "table", "heading": "x", "columns": ["名稱", "收盤"], "rows": [["道瓊", "42,100"]]}]
    )
    assert build_scenes(plain)[1]["narration"] == "x。道瓊，收盤四萬兩千一百。"
