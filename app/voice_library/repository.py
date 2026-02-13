from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.voice_library.catalog import list_builtin_voices
from app.voice_library.semantic import keyword_tokens
from app.voice_library.user_voices import get_user_voices_by_ids, list_user_voices, upsert_user_voice

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None


def _db_url() -> Optional[str]:
    return os.getenv("VOICE_LIBRARY_DB_URL") or os.getenv("DATABASE_URL") or None


def _split_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    parts = [x.strip() for x in value.split(",") if x.strip()]
    return parts or None


def _tokenize_keyword(keyword: Optional[str]) -> List[str]:
    return keyword_tokens(keyword)


@dataclass(frozen=True)
class ExploreParams:
    keyword: Optional[str] = None
    voice_ids_csv: Optional[str] = None
    language: Optional[str] = None
    language_type: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    scene_csv: Optional[str] = None
    emotion_csv: Optional[str] = None
    sort: str = "mostUsers"
    skip: int = 0
    limit: int = 20


class VoiceRepository:
    async def explore(self, p: ExploreParams, *, only_owner_user_id: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        raise NotImplementedError

    async def get_by_voice_ids(self, voice_ids: Sequence[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def create_user_voice(self, user_id: str, voice: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


def _apply_filters(voices: List[Dict[str, Any]], p: ExploreParams) -> List[Dict[str, Any]]:
    wanted_ids = set(_split_csv(p.voice_ids_csv) or [])
    if wanted_ids:
        voices = [v for v in voices if str(v.get("voice_id")) in wanted_ids]

    tokens = _tokenize_keyword(p.keyword)
    if tokens:
        def hay(v: Dict[str, Any]) -> str:
            meta = v.get("meta") or {}
            return " ".join(
                [
                    str(v.get("display_name") or ""),
                    str(v.get("voice_description") or ""),
                    str(meta.get("text") or ""),
                ]
            ).lower()

        voices = [v for v in voices if all(t in hay(v) for t in tokens)]

    if p.language_type:
        lt = p.language_type.strip().lower()
        voices = [v for v in voices if str(v.get("language") or "").lower() == lt]
    if p.age:
        a = p.age.strip().lower()
        voices = [v for v in voices if str(v.get("age") or "").lower() == a]
    if p.gender:
        g = p.gender.strip().lower()
        voices = [v for v in voices if str(v.get("gender") or "").lower() == g]

    if p.scene_csv:
        scenes = {x.strip().lower() for x in p.scene_csv.split(",") if x.strip()}
        voices = [v for v in voices if scenes.intersection({str(x).lower() for x in (v.get("scene") or [])})]
    if p.emotion_csv:
        emos = {x.strip().lower() for x in p.emotion_csv.split(",") if x.strip()}
        voices = [v for v in voices if emos.intersection({str(x).lower() for x in (v.get("emotion") or [])})]

    if p.sort == "latest":
        voices.sort(key=lambda v: int(v.get("create_time") or 0), reverse=True)
    else:
        voices.sort(key=lambda v: str(v.get("voice_id")))

    return voices


class BuiltinVoiceRepository(VoiceRepository):
    async def explore(self, p: ExploreParams, *, only_owner_user_id: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        if only_owner_user_id:
            voices = list_user_voices(str(only_owner_user_id))
        else:
            # For the builtin repository, callers typically use language_type as the primary filter.
            # If we don't propagate it here, builtin voices will default to "en" and language_type
            # filters will always return empty.
            voices = list_builtin_voices(language=(p.language_type or p.language or None))

        voices = _apply_filters(list(voices), p)
        total = len(voices)
        page = voices[p.skip : p.skip + p.limit]
        return (total, page)

    async def get_by_voice_ids(self, voice_ids: Sequence[str]) -> List[Dict[str, Any]]:
        wanted = {str(x) for x in voice_ids if str(x)}
        if not wanted:
            return []
        voices = list_builtin_voices()
        return [v for v in voices if str(v.get("voice_id")) in wanted]

    async def create_user_voice(self, user_id: str, voice: Dict[str, Any]) -> Dict[str, Any]:
        uid = str(user_id)
        now = int(time.time())
        v = dict(voice)
        v.setdefault("id", int(time.time() * 1000))
        v.setdefault("voice_id", f"user_{uid}_{uuid.uuid4().hex[:8]}")
        v.setdefault("display_name", v.get("voice_id"))
        v.setdefault("voice_type", "user")
        v.setdefault("labels", [])
        v.setdefault("meta", {})
        v.setdefault("is_public", False)
        v.setdefault("url", None)
        v.setdefault("fallbackurl", None)
        v.setdefault("is_favorited", False)
        v.setdefault("language", None)
        v.setdefault("age", None)
        v.setdefault("gender", None)
        v.setdefault("scene", [])
        v.setdefault("emotion", [])
        v.setdefault("voice_description", None)
        v.setdefault("creation_mode", "private")
        v.setdefault("can_delete", True)
        v.setdefault("create_time", now)
        return upsert_user_voice(uid, v)


class PostgresVoiceRepository(VoiceRepository):
    def __init__(self, dsn: str):
        if asyncpg is None:
            raise RuntimeError("asyncpg package not installed")
        self._dsn = dsn
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=1, max_size=5)
        return self._pool

    async def explore(self, p: ExploreParams, *, only_owner_user_id: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        pool = await self._get_pool()

        tokens = _tokenize_keyword(p.keyword)
        voice_ids = _split_csv(p.voice_ids_csv) or []
        scenes = _split_csv(p.scene_csv) or []
        emotions = _split_csv(p.emotion_csv) or []

        where = ["1=1"]
        args: List[Any] = []

        if only_owner_user_id:
            where.append("owner_user_id = $%d" % (len(args) + 1))
            args.append(str(only_owner_user_id))

        if voice_ids:
            where.append("voice_id = ANY($%d::text[])" % (len(args) + 1))
            args.append([str(x) for x in voice_ids])

        if p.language_type:
            where.append("lower(language_type) = $%d" % (len(args) + 1))
            args.append(p.language_type.strip().lower())

        if p.age:
            where.append("lower(age) = $%d" % (len(args) + 1))
            args.append(p.age.strip().lower())

        if p.gender:
            where.append("lower(gender) = $%d" % (len(args) + 1))
            args.append(p.gender.strip().lower())

        if scenes:
            where.append("scene && $%d::text[]" % (len(args) + 1))
            args.append([str(x).lower() for x in scenes])

        if emotions:
            where.append("emotion && $%d::text[]" % (len(args) + 1))
            args.append([str(x).lower() for x in emotions])

        # Token AND search across display_name/description/meta_text.
        for t in tokens:
            where.append("(lower(display_name) LIKE $%d OR lower(coalesce(voice_description,'')) LIKE $%d OR lower(coalesce(meta_text,'')) LIKE $%d)" % (len(args) + 1, len(args) + 2, len(args) + 3))
            like = f"%{t}%"
            args.extend([like, like, like])

        where_sql = " AND ".join(where)

        order_sql = "create_time DESC" if p.sort == "latest" else "use_count DESC NULLS LAST, voice_id ASC"

        count_sql = f"SELECT count(*)::bigint AS c FROM voice_library_voices WHERE {where_sql}"
        page_sql = (
            "SELECT id, voice_id, display_name, voice_type, labels, file_path, meta_json, is_public, url, fallbackurl, "
            "language_type, age, gender, scene, emotion, voice_description, creation_mode, can_delete, create_time "
            f"FROM voice_library_voices WHERE {where_sql} ORDER BY {order_sql} OFFSET $%d LIMIT $%d"
            % (len(args) + 1, len(args) + 2)
        )

        async with pool.acquire() as conn:
            total = int(await conn.fetchval(count_sql, *args) or 0)
            rows = await conn.fetch(page_sql, *(args + [int(p.skip), int(p.limit)]))

        def row_to_voice(r: Any) -> Dict[str, Any]:
            meta = r.get("meta_json") or {}
            # Normalize to main-site schema fields.
            return {
                "id": int(r.get("id")),
                "voice_id": str(r.get("voice_id")),
                "display_name": str(r.get("display_name")),
                "voice_type": str(r.get("voice_type") or "built-in"),
                "labels": list(r.get("labels") or []),
                "file_path": r.get("file_path"),
                "meta": dict(meta) if isinstance(meta, dict) else {},
                "is_public": bool(r.get("is_public")),
                "url": r.get("url"),
                "fallbackurl": r.get("fallbackurl"),
                "language": r.get("language_type"),
                "age": r.get("age"),
                "gender": r.get("gender"),
                "scene": list(r.get("scene") or []),
                "emotion": list(r.get("emotion") or []),
                "voice_description": r.get("voice_description"),
                "creation_mode": str(r.get("creation_mode") or "public"),
                "can_delete": bool(r.get("can_delete")),
                "create_time": int(r.get("create_time") or 0),
            }

        voices = [row_to_voice(r) for r in rows]

        # If the DB has no matching results (common in local/dev when the table isn't fully tagged),
        # fall back to the builtin catalog so UI filters still demonstrate end-to-end wiring.
        if total == 0 and not only_owner_user_id:
            builtin = list_builtin_voices(language=(p.language_type or p.language or None))
            builtin = _apply_filters(list(builtin), p)
            total = len(builtin)
            page = builtin[p.skip : p.skip + p.limit]
            return (total, page)

        return (total, voices)

    async def get_by_voice_ids(self, voice_ids: Sequence[str]) -> List[Dict[str, Any]]:
        ids = [str(x) for x in voice_ids if str(x)]
        if not ids:
            return []

        pool = await self._get_pool()
        sql = (
            "SELECT id, voice_id, display_name, voice_type, labels, file_path, meta_json, is_public, url, fallbackurl, "
            "language_type, age, gender, scene, emotion, voice_description, creation_mode, can_delete, create_time "
            "FROM voice_library_voices WHERE voice_id = ANY($1::text[])"
        )
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, ids)

        out: List[Dict[str, Any]] = []
        for r in rows:
            meta = r.get("meta_json") or {}
            out.append(
                {
                    "id": int(r.get("id")),
                    "voice_id": str(r.get("voice_id")),
                    "display_name": str(r.get("display_name")),
                    "voice_type": str(r.get("voice_type") or "built-in"),
                    "labels": list(r.get("labels") or []),
                    "file_path": r.get("file_path"),
                    "meta": dict(meta) if isinstance(meta, dict) else {},
                    "is_public": bool(r.get("is_public")),
                    "url": r.get("url"),
                    "fallbackurl": r.get("fallbackurl"),
                    "language": r.get("language_type"),
                    "age": r.get("age"),
                    "gender": r.get("gender"),
                    "scene": list(r.get("scene") or []),
                    "emotion": list(r.get("emotion") or []),
                    "voice_description": r.get("voice_description"),
                    "creation_mode": str(r.get("creation_mode") or "public"),
                    "can_delete": bool(r.get("can_delete")),
                    "create_time": int(r.get("create_time") or 0),
                }
            )
        return out

    async def create_user_voice(self, user_id: str, voice: Dict[str, Any]) -> Dict[str, Any]:
        pool = await self._get_pool()
        uid = str(user_id)
        now = int(time.time())
        v = dict(voice)

        v.setdefault("id", int(time.time() * 1000))
        v.setdefault("voice_id", f"user_{uid}_{uuid.uuid4().hex[:8]}")
        v.setdefault("display_name", v.get("voice_id"))
        v.setdefault("voice_type", "user")
        v.setdefault("labels", [])
        v.setdefault("file_path", None)
        v.setdefault("meta", {})
        v.setdefault("is_public", False)
        v.setdefault("url", None)
        v.setdefault("fallbackurl", None)
        v.setdefault("language", v.get("language") or None)
        v.setdefault("age", v.get("age") or None)
        v.setdefault("gender", v.get("gender") or None)
        v.setdefault("scene", v.get("scene") or [])
        v.setdefault("emotion", v.get("emotion") or [])
        v.setdefault("voice_description", v.get("voice_description") or None)
        v.setdefault("creation_mode", "private")
        v.setdefault("can_delete", True)
        v.setdefault("create_time", now)

        sql = (
            "INSERT INTO voice_library_voices (id, voice_id, display_name, voice_type, owner_user_id, labels, file_path, meta_json, meta_text, "
            "is_public, url, fallbackurl, language_type, age, gender, scene, emotion, voice_description, creation_mode, can_delete, create_time) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21) "
            "ON CONFLICT (voice_id) DO UPDATE SET display_name=EXCLUDED.display_name, labels=EXCLUDED.labels, meta_json=EXCLUDED.meta_json, meta_text=EXCLUDED.meta_text, "
            "is_public=EXCLUDED.is_public, url=EXCLUDED.url, fallbackurl=EXCLUDED.fallbackurl, language_type=EXCLUDED.language_type, age=EXCLUDED.age, gender=EXCLUDED.gender, "
            "scene=EXCLUDED.scene, emotion=EXCLUDED.emotion, voice_description=EXCLUDED.voice_description, creation_mode=EXCLUDED.creation_mode, can_delete=EXCLUDED.can_delete"
        )

        meta = v.get("meta") if isinstance(v.get("meta"), dict) else {}
        meta_text = ""
        try:
            meta_text = str(meta.get("text") or "")
        except Exception:
            meta_text = ""

        async with pool.acquire() as conn:
            await conn.execute(
                sql,
                int(v["id"]),
                str(v["voice_id"]),
                str(v["display_name"]),
                str(v["voice_type"]),
                uid,
                list(v.get("labels") or []),
                v.get("file_path"),
                meta,
                meta_text,
                bool(v.get("is_public")),
                v.get("url"),
                v.get("fallbackurl"),
                v.get("language"),
                v.get("age"),
                v.get("gender"),
                [str(x).lower() for x in (v.get("scene") or [])],
                [str(x).lower() for x in (v.get("emotion") or [])],
                v.get("voice_description"),
                str(v.get("creation_mode")),
                bool(v.get("can_delete")),
                int(v.get("create_time") or now),
            )

        # Normalize to API schema fields.
        return {
            "id": int(v.get("id")),
            "voice_id": str(v.get("voice_id")),
            "display_name": str(v.get("display_name")),
            "voice_type": "user",
            "labels": list(v.get("labels") or []),
            "file_path": v.get("file_path"),
            "meta": meta,
            "is_public": bool(v.get("is_public")),
            "url": v.get("url"),
            "fallbackurl": v.get("fallbackurl"),
            "language": v.get("language"),
            "age": v.get("age"),
            "gender": v.get("gender"),
            "scene": list(v.get("scene") or []),
            "emotion": list(v.get("emotion") or []),
            "voice_description": v.get("voice_description"),
            "creation_mode": str(v.get("creation_mode")),
            "can_delete": bool(v.get("can_delete")),
            "create_time": int(v.get("create_time") or now),
        }


_repo: Optional[VoiceRepository] = None


def get_voice_repository() -> VoiceRepository:
    global _repo
    if _repo is not None:
        return _repo

    dsn = _db_url()
    if dsn and asyncpg is not None and dsn.startswith("postgres"):
        try:
            _repo = PostgresVoiceRepository(dsn)
            return _repo
        except Exception:
            pass

    _repo = BuiltinVoiceRepository()
    return _repo
