"""generic adapter：輸入已接近 content.json 的 JSON，只做 schema 補齊與驗證。

純文字（.md/.txt）不在這裡處理：依 docs/PIPELINE.md Step 1，由 Claude Code 先整理成 JSON。
"""

from __future__ import annotations

import json
from typing import Any

from infoshorts.content import apply_defaults, validate


class GenericAdapter:
    name = "generic"

    def to_content(self, raw: dict[str, Any] | str, *, run_id: str) -> dict[str, Any]:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(
                    "generic adapter 只吃 JSON；純文字請先依 docs/PIPELINE.md Step 1 整理成 content JSON"
                ) from e
        if not isinstance(raw, dict):
            raise ValueError("generic adapter 的輸入必須是 JSON 物件")
        content = apply_defaults(raw, run_id=run_id)
        content["kind"] = "generic"
        validate(content)
        return content
