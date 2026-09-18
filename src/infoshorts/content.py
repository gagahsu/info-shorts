"""content.json 讀取、驗證與預設值補齊。schemas/content.schema.json 是 core 唯一輸入格式。"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "content.schema.json"


@lru_cache(maxsize=1)
def schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def apply_defaults(content: dict[str, Any], *, run_id: str | None = None) -> dict[str, Any]:
    """補齊 schema 的 default；缺 date 用今天。不改動 sections 的資料值（不編造）。"""
    c = dict(content)
    props = schema()["properties"]
    for key, spec in props.items():
        if key not in c and "default" in spec:
            c[key] = spec["default"]
    c.setdefault("id", run_id or f"{date.today():%Y-%m-%d}-untitled")
    c.setdefault("subtitle", None)
    c.setdefault("brand", None)
    if not c.get("date"):
        c["date"] = date.today().isoformat()
    c.setdefault("bgm", None)
    sections = []
    for s in c.get("sections", []):
        s = dict(s)
        s.setdefault("narration", None)
        if s.get("type") == "stat":
            s.setdefault("delta", None)
            s.setdefault("delta_pct", None)
            s.setdefault("delta_kind", "change")
            s.setdefault("unit", "")
            s.setdefault("delta_direction", _direction(s.get("delta")) or _direction(s.get("delta_pct")))
        if s.get("type") == "quote":
            s.setdefault("source", None)
        sections.append(s)
    c["sections"] = sections
    return c


def _direction(delta: Any) -> str | None:
    if delta is None or delta == "":
        return None
    try:
        v = float(str(delta).replace(",", "").replace("%", "").replace("+", ""))
    except ValueError:
        return None
    return "up" if v > 0 else "down" if v < 0 else "flat"


def validate(content: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(schema()).iter_errors(content), key=lambda e: list(e.path))
    if errors:
        msgs = [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]
        raise ValueError("content.json 不符合 schema：\n  " + "\n  ".join(msgs))


def load(path: str | Path) -> dict[str, Any]:
    c = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(c)
    return c


def dump(content: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
