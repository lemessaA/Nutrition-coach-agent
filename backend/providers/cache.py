"""In-memory TTL cache with async locking.

Swap this for Redis in production; the interface is intentionally small
(`get` / `set`) so the registry doesn't care which backend it talks to.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, default_ttl_seconds: int = 60 * 60 * 6) -> None:  # 6h
        self._data: Dict[str, _Entry] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl_seconds

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            if entry.expires_at < time.time():
                self._data.pop(key, None)
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        async with self._lock:
            self._data[key] = _Entry(
                value=value,
                expires_at=time.time() + (ttl_seconds or self._default_ttl),
            )

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)
