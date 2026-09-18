"""adapter 註冊表。新 adapter 在這裡註冊，core 不引用任何 adapter 的欄位名稱。"""

from __future__ import annotations

from infoshorts.adapters.base import Adapter
from infoshorts.adapters.briefing import BriefingAdapter
from infoshorts.adapters.generic import GenericAdapter

_REGISTRY: dict[str, type] = {
    GenericAdapter.name: GenericAdapter,
    BriefingAdapter.name: BriefingAdapter,
}


def names() -> list[str]:
    return sorted(_REGISTRY)


def get_adapter(name: str) -> Adapter:
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        raise ValueError(f"未知 adapter：{name}（可用：{', '.join(names())}）") from e
