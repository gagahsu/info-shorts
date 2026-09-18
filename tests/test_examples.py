"""每個 examples/*.json 都要能過 adapter、schema 與 scenes（不跑 TTS / render）。"""

import json
from pathlib import Path

import pytest

from infoshorts.adapters import get_adapter
from infoshorts.props import build_props
from infoshorts.scenes import build_scenes

EXAMPLES = sorted((Path(__file__).parents[1] / "examples").glob("*.json"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.stem for p in EXAMPLES])
def test_example_builds_scenes_and_props(path: Path, tmp_path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    content = get_adapter("generic").to_content(raw, run_id=path.stem)
    scenes = build_scenes(content)
    assert scenes[0]["type"] == "title"
    assert all(s["narration"] for s in scenes if s["type"] == "title")
    if content["disclaimer"]:
        assert scenes[-1]["type"] == "disclaimer"
    # 假裝 TTS 跑過：每段 3 秒
    t = 0.0
    for s in scenes:
        s["start"], s["end"] = t, t + 3.0
        t += 3.0
    props = build_props(content, scenes, tmp_path, total_seconds=t)
    assert props["durationInFrames"] == round(t * 30)
    assert [s["startFrame"] for s in props["scenes"]] == [round(i * 90) for i in range(len(scenes))]
    assert props["scenes"][-1]["endFrame"] == props["durationInFrames"]
    assert len(props["audio"]["voiceRanges"]) == sum(1 for s in scenes if s["narration"])


def test_long_bullets_split() -> None:
    raw = json.loads((Path(__file__).parents[1] / "examples" / "long-bullets.json").read_text(encoding="utf-8"))
    scenes = build_scenes(get_adapter("generic").to_content(raw, run_id="x"))
    bullets = [s for s in scenes if s["type"] == "bullets"]
    assert [len(s["props"]["items"]) for s in bullets] == [4, 4]


def test_multi_stat_null_value_reads_as_missing() -> None:
    raw = json.loads((Path(__file__).parents[1] / "examples" / "multi-stat.json").read_text(encoding="utf-8"))
    scenes = build_scenes(get_adapter("generic").to_content(raw, run_id="x"))
    stats = [s for s in scenes if s["type"] == "stat"]
    assert stats[0]["narration"] == "台指期夜盤，兩萬三千四百五十六點，上漲一百二十點。"
    assert stats[1]["narration"] == "費城半導體，五千四百三十二點一，下跌零點八個百分點。"
    assert stats[2]["props"]["value"] is None  # 缺資料 → null，畫面顯示「—」
    assert stats[2]["props"]["deltaDirection"] is None
