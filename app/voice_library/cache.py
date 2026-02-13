from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar

T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    expires_at: float
    value: T


class TTLCache:
    def __init__(self) -> None:
        self._data: Dict[str, _Entry[Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        ent = self._data.get(key)
        if not ent:
            return None
        if ent.expires_at <= time.time():
            self._data.pop(key, None)
            return None
        return ent.value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        self._data[key] = _Entry(expires_at=time.time() + ttl_seconds, value=value)

    def clear(self) -> None:
        self._data.clear()
