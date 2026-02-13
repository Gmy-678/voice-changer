from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set

from app.voice_library.cache import TTLCache
from app.voice_library.storage import (
    add_recent_used as local_add_recent_used,
    get_favorites as local_get_favorites,
    get_recent_used as local_get_recent_used,
    update_favorites as local_update_favorites,
)

try:
    import redis as _redis

    redis_async = getattr(_redis, "asyncio", None)
except Exception:  # pragma: no cover
    redis_async = None


def _redis_url() -> Optional[str]:
    return (
        os.getenv("VOICE_LIBRARY_REDIS_URL")
        or os.getenv("REDIS_URL")
        or os.getenv("UPSTASH_REDIS_REST_URL")
        or None
    )


class VoiceLibraryState:
    async def cache_get_json(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def cache_set_json(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        raise NotImplementedError

    async def favorites_get(self, user_id: str) -> Set[str]:
        raise NotImplementedError

    async def favorites_update(self, user_id: str, voice_ids: Sequence[str], is_favorite: bool) -> None:
        raise NotImplementedError

    async def recent_add(self, user_id: str, voice_id: str) -> None:
        raise NotImplementedError

    async def recent_get_ids(self, user_id: str, limit: int) -> List[str]:
        raise NotImplementedError


@dataclass
class LocalState(VoiceLibraryState):
    _cache: TTLCache

    async def cache_get_json(self, key: str) -> Optional[Dict[str, Any]]:
        v = self._cache.get(key)
        if v is None:
            return None
        return dict(v)

    async def cache_set_json(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        self._cache.set(key, dict(value), ttl_seconds=ttl_seconds)

    async def favorites_get(self, user_id: str) -> Set[str]:
        return local_get_favorites(user_id)

    async def favorites_update(self, user_id: str, voice_ids: Sequence[str], is_favorite: bool) -> None:
        local_update_favorites(user_id, list(voice_ids), is_favorite)

    async def recent_add(self, user_id: str, voice_id: str) -> None:
        local_add_recent_used(user_id, voice_id)

    async def recent_get_ids(self, user_id: str, limit: int) -> List[str]:
        items = local_get_recent_used(user_id, limit=limit)
        return [str(it.get("voice_id")) for it in items if it.get("voice_id")]


class RedisState(VoiceLibraryState):
    def __init__(self, url: str):
        if redis_async is None:
            raise RuntimeError("redis package not installed")
        self._redis = redis_async.Redis.from_url(url, decode_responses=True)

    def _cache_key(self, key: str) -> str:
        return f"vl:cache:{key}"

    def _fav_key(self, user_id: str) -> str:
        return f"vl:fav:{user_id}"

    def _recent_key(self, user_id: str) -> str:
        return f"vl:recent:{user_id}"

    async def cache_get_json(self, key: str) -> Optional[Dict[str, Any]]:
        raw = await self._redis.get(self._cache_key(key))
        if not raw:
            return None
        try:
            v = json.loads(raw)
            if isinstance(v, dict):
                return v
        except Exception:
            return None
        return None

    async def cache_set_json(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        raw = json.dumps(value, ensure_ascii=False)
        await self._redis.set(self._cache_key(key), raw, ex=int(ttl_seconds))

    async def favorites_get(self, user_id: str) -> Set[str]:
        members = await self._redis.smembers(self._fav_key(user_id))
        return {str(x) for x in (members or set())}

    async def favorites_update(self, user_id: str, voice_ids: Sequence[str], is_favorite: bool) -> None:
        key = self._fav_key(user_id)
        ids = [str(x) for x in voice_ids if str(x)]
        if not ids:
            return
        if is_favorite:
            await self._redis.sadd(key, *ids)
        else:
            await self._redis.srem(key, *ids)
        # Keep favorites around for a long time.
        await self._redis.expire(key, 60 * 60 * 24 * 365)

    async def recent_add(self, user_id: str, voice_id: str) -> None:
        key = self._recent_key(user_id)
        ts = int(time.time())
        await self._redis.zadd(key, {str(voice_id): ts})
        # Keep last 500 by score (oldest are lowest scores).
        await self._redis.zremrangebyrank(key, 0, -501)
        await self._redis.expire(key, 60 * 60 * 24 * 90)

    async def recent_get_ids(self, user_id: str, limit: int) -> List[str]:
        ids = await self._redis.zrevrange(self._recent_key(user_id), 0, int(limit) - 1)
        return [str(x) for x in (ids or []) if str(x)]


@dataclass
class HybridState(VoiceLibraryState):
    primary: VoiceLibraryState
    fallback: VoiceLibraryState

    async def cache_get_json(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.primary.cache_get_json(key)
        except Exception:
            return await self.fallback.cache_get_json(key)

    async def cache_set_json(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        try:
            await self.primary.cache_set_json(key, value, ttl_seconds)
        except Exception:
            await self.fallback.cache_set_json(key, value, ttl_seconds)

    async def favorites_get(self, user_id: str) -> Set[str]:
        try:
            return await self.primary.favorites_get(user_id)
        except Exception:
            return await self.fallback.favorites_get(user_id)

    async def favorites_update(self, user_id: str, voice_ids: Sequence[str], is_favorite: bool) -> None:
        try:
            await self.primary.favorites_update(user_id, voice_ids, is_favorite)
        except Exception:
            await self.fallback.favorites_update(user_id, voice_ids, is_favorite)

    async def recent_add(self, user_id: str, voice_id: str) -> None:
        try:
            await self.primary.recent_add(user_id, voice_id)
        except Exception:
            await self.fallback.recent_add(user_id, voice_id)

    async def recent_get_ids(self, user_id: str, limit: int) -> List[str]:
        try:
            return await self.primary.recent_get_ids(user_id, limit)
        except Exception:
            return await self.fallback.recent_get_ids(user_id, limit)


_state: Optional[VoiceLibraryState] = None


def get_voice_library_state() -> VoiceLibraryState:
    global _state
    if _state is not None:
        return _state

    local = LocalState(_cache=TTLCache())

    url = _redis_url()
    if url and redis_async is not None and not url.startswith("http"):
        try:
            primary = RedisState(url)
            _state = HybridState(primary=primary, fallback=local)
            return _state
        except Exception:
            pass

    _state = local
    return _state
