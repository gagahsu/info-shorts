"""Adapter 介面：來源專屬資料 → content.json。adapter 只做欄位對應，不呼叫 render。"""

from __future__ import annotations

from typing import Any, Protocol


class Adapter(Protocol):
    name: str

    def to_content(self, raw: dict[str, Any] | str, *, run_id: str) -> dict[str, Any]:
        """回傳符合 schemas/content.schema.json 的 dict。"""
        ...
