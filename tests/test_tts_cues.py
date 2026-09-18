from pathlib import Path

from infoshorts.tts import Word, build_cues, punctuation_before, write_srt


def _words(spec: list[tuple[str, float, float]]) -> list[Word]:
    return [Word(t, s, e) for t, s, e in spec]


def _seq(tokens: list[str], step: float = 0.3) -> list[Word]:
    return _words([(t, i * step, i * step + step * 0.8) for i, t in enumerate(tokens)])


def test_cues_respect_14_chars() -> None:
    words = _words([("字字", i * 0.3, i * 0.3 + 0.25) for i in range(20)])  # 每個 2 字
    cues = build_cues(words)
    assert all(len(c.text) <= 14 for c in cues)
    assert cues[0].text == "字字" * 7
    assert cues[0].start == 0.0
    assert cues[-1].end >= words[-1].end


def test_cues_break_on_pause() -> None:
    words = _words([("第一件事", 0.0, 0.5), ("很重要", 0.55, 0.9), ("第二件事", 2.0, 2.5)])
    cues = build_cues(words)
    assert [c.text for c in cues] == ["第一件事很重要", "第二件事"]
    assert cues[0].end <= cues[1].start


def test_latin_words_get_spaces_and_half_width() -> None:
    words = _words([("Kinocut", 0.0, 0.4), ("這個", 0.45, 0.7), ("MCP", 0.75, 1.0), ("工具", 1.05, 1.3)])
    cues = build_cues(words)
    assert cues[0].text == "Kinocut 這個 MCP 工具"


def test_punctuation_before() -> None:
    text = "為什麼重要。第一，不用猜 ffmpeg 參數；第二，內建品質檢查。"
    words = _seq(["為什麼", "重要", "第一", "不用", "猜", "ffmpeg", "參數", "第二", "內建", "品質", "檢查"])
    assert punctuation_before(words, text) == ["", "", "。", "，", "", "", "", "；", "，", "", ""]


def test_strong_punct_forces_break_and_weak_backtracks() -> None:
    text = "為什麼重要。第一，不用猜 ffmpeg 參數；第二，內建品質檢查；第三，本機免費。"
    tokens = [
        "為什麼",
        "重要",
        "第一",
        "不用",
        "猜",
        "ffmpeg",
        "參數",
        "第二",
        "內",
        "建",
        "品質",
        "檢查",
        "第三",
        "本機",
        "免費",
    ]
    cues = build_cues(_seq(tokens, step=0.2), text)
    texts = [c.text for c in cues]
    assert texts[0] == "為什麼重要"  # 句號一定切
    assert "第一不用猜 ffmpeg 參數" in texts  # 分號切
    assert "第二內建品質檢查" in texts  # 超長時回溯到逗號，不把「內建」切半
    assert all(len(t.replace(" ", "")) <= 14 for t in texts)


def test_weak_punct_breaks_when_long_enough() -> None:
    text = "台指期夜盤兩萬三千點，上漲一百二十點。"
    tokens = ["台指期", "夜盤", "兩萬", "三千", "點", "上漲", "一百", "二十", "點"]
    cues = build_cues(_seq(tokens), text)
    assert [c.text for c in cues] == ["台指期夜盤兩萬三千點", "上漲一百二十點"]


def test_write_srt(tmp_path: Path) -> None:
    cues = build_cues(_words([("你好", 0.0, 0.5), ("世界", 0.6, 1.0)]))
    out = tmp_path / "x.srt"
    write_srt(cues, out)
    text = out.read_text(encoding="utf-8")
    assert text.startswith("1\n00:00:00,000 --> ")
    assert "你好世界" in text
