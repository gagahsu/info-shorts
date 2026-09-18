import json
from pathlib import Path

import pytest

from infoshorts.adapters import get_adapter, names
from infoshorts.content import validate

FIXTURES = Path(__file__).parent / "fixtures" / "generic"


def test_registry() -> None:
    assert "generic" in names()
    with pytest.raises(ValueError):
        get_adapter("nope")


def test_fixture_to_content() -> None:
    raw = json.loads((FIXTURES / "input.json").read_text(encoding="utf-8"))
    expected = json.loads((FIXTURES / "expected_content.json").read_text(encoding="utf-8"))
    content = get_adapter("generic").to_content(raw, run_id="2026-09-20-test")
    validate(content)
    assert content == expected


def test_defaults_and_direction() -> None:
    raw = {"title": "只有標題", "sections": [{"type": "stat", "label": "x", "value": 1, "delta": "-3"}]}
    content = get_adapter("generic").to_content(raw, run_id="rid")
    assert content["id"] == "rid"
    assert content["kind"] == "generic"
    assert content["aspect"] == "9:16"
    assert content["target_duration"] == 45
    assert content["disclaimer"] is False
    assert content["date"]  # 今天
    s = content["sections"][0]
    assert s["delta_direction"] == "down"
    assert s["unit"] == ""
    assert s["narration"] is None


def test_rejects_plain_text() -> None:
    with pytest.raises(ValueError):
        get_adapter("generic").to_content("這不是 JSON", run_id="rid")


def test_schema_violation() -> None:
    with pytest.raises(ValueError):
        get_adapter("generic").to_content({"title": "x", "sections": [{"type": "chart"}]}, run_id="rid")
