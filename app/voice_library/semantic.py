from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.voice_library.catalog import list_builtin_voices

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None

try:
    from rapidfuzz import fuzz, process  # type: ignore
except Exception:  # pragma: no cover
    fuzz = None
    process = None


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    v = raw.strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def semantic_top_k_default() -> int:
    try:
        return int(os.getenv("VOICE_LIBRARY_SEMANTIC_TOP_K", "50"))
    except Exception:
        return 50


def semantic_enabled() -> bool:
    return _env_bool("VOICE_LIBRARY_SEMANTIC_ENABLED", default=False)


def semantic_mode() -> str:
    # Currently supported:
    # - "fuzzy": lexical fuzzy match fallback (no embeddings)
    # - "disabled": force disabled
    return (os.getenv("VOICE_LIBRARY_SEMANTIC_MODE") or "fuzzy").strip().lower()


def synonyms_enabled() -> bool:
    return _env_bool("VOICE_LIBRARY_SYNONYMS_ENABLED", default=True)


def _default_synonyms() -> Dict[str, List[str]]:
    # Lightweight product-oriented synonyms.
    # Keep this SMALL and controllable; can be overridden via VOICE_LIBRARY_SYNONYMS_JSON.
    return {
        # gender
        "女性": ["女声", "女生", "女"],
        "女声": ["女性", "女生"],
        "男性": ["男声", "男"],
        "男声": ["男性"],
        # emotion
        "开心": ["快乐", "高兴"],
        "快乐": ["开心", "高兴"],
        "高兴": ["开心", "快乐"],
        "愤怒": ["生气", "暴怒"],
        "生气": ["愤怒", "暴怒"],
        # language
        "英文": ["英语", "english"],
        "英语": ["英文", "english"],
        "中文": ["汉语", "普通话"],
        "日文": ["日语", "japanese"],
        "日语": ["日文", "japanese"],
        # common voice style hints
        "温柔": ["治愈", "柔和"],
        "治愈": ["温柔", "疗愈"],
    }


def load_synonyms() -> Dict[str, List[str]]:
    mode = (os.getenv("VOICE_LIBRARY_SYNONYMS_MODE") or "merge").strip().lower()
    base = {} if mode == "replace" else _default_synonyms()

    raw = os.getenv("VOICE_LIBRARY_SYNONYMS_JSON")
    if not raw:
        return base

    try:
        import json

        data = json.loads(raw)
        if not isinstance(data, dict):
            return base

        out = dict(base)
        for k, v in data.items():
            if not isinstance(k, str):
                continue
            if isinstance(v, list):
                vals = [str(x).strip().lower() for x in v if str(x).strip()]
            else:
                vals = [str(v).strip().lower()] if str(v).strip() else []

            key = k.strip().lower()
            if not key:
                continue
            existing = out.get(key, [])
            # Merge unique while keeping order.
            seen = set(existing)
            merged = list(existing)
            for x in vals:
                if x not in seen:
                    seen.add(x)
                    merged.append(x)
            out[key] = merged
        return out
    except Exception:
        return base


def expand_keyword_with_synonyms(keyword: str) -> str:
    if not keyword:
        return keyword
    if not synonyms_enabled():
        return keyword

    syn = load_synonyms()
    tokens = keyword_tokens(keyword)
    if not tokens:
        return keyword

    expanded: List[str] = []
    seen = set()

    def add_term(t: str) -> None:
        tt = t.strip().lower()
        if not tt or tt in seen:
            return
        seen.add(tt)
        expanded.append(tt)

    for t in tokens:
        add_term(t)
        for s in syn.get(t.strip().lower(), []):
            add_term(s)

    # If keyword had separators, we return expanded tokens joined by spaces.
    # If keyword had no separators, tokens==[keyword], expanding is still safe.
    return " ".join(expanded)


_SPLIT_RE = re.compile(r"[\s,，]+", re.UNICODE)


def keyword_tokens(keyword: Optional[str]) -> List[str]:
    if not keyword:
        return []
    kw = keyword.strip()
    if not kw:
        return []

    # Only split when separators exist; otherwise keep as a single token.
    if not _SPLIT_RE.search(kw):
        return [kw.lower()]

    parts = [p.strip().lower() for p in _SPLIT_RE.split(kw) if p.strip()]
    return parts


@dataclass(frozen=True)
class SemanticQuery:
    keyword: str
    top_k: int = 50
    # Scope control
    only_owner_user_id: Optional[str] = None
    # Optional structured filters (best-effort)
    language_type: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    scene_csv: Optional[str] = None
    emotion_csv: Optional[str] = None


class SemanticSearcher:
    async def search_voice_ids(self, q: SemanticQuery) -> List[str]:
        raise NotImplementedError


class DisabledSemanticSearcher(SemanticSearcher):
    async def search_voice_ids(self, q: SemanticQuery) -> List[str]:
        return []


class FuzzySemanticSearcher(SemanticSearcher):
    """A pragmatic fallback when embeddings/Milvus are unavailable.

    IMPORTANT: This is *not* true semantic similarity; it is fuzzy lexical matching.
    It still follows the product strategy gate:
    - only used when exact token-AND returns 0
    - TopK capped
    """

    def __init__(self) -> None:
        self._pool = None

    def _db_url(self) -> Optional[str]:
        return os.getenv("VOICE_LIBRARY_DB_URL") or os.getenv("DATABASE_URL") or None

    async def _get_pool(self):
        if self._pool is None:
            if asyncpg is None:
                return None
            dsn = self._db_url()
            if not dsn or not dsn.startswith("postgres"):
                return None
            self._pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=3)
        return self._pool

    def _split_csv_set(self, v: Optional[str]) -> Optional[set[str]]:
        if not v:
            return None
        parts = {x.strip().lower() for x in v.split(",") if x.strip()}
        return parts or None

    def _voice_text(self, voice: Dict[str, Any]) -> str:
        meta = voice.get("meta") or {}
        return " ".join(
            [
                str(voice.get("display_name") or ""),
                str(voice.get("voice_description") or ""),
                str(meta.get("text") or ""),
            ]
        ).strip()

    def _apply_structured_filters_local(self, voices: List[Dict[str, Any]], q: SemanticQuery) -> List[Dict[str, Any]]:
        out = voices
        if q.language_type:
            lt = q.language_type.strip().lower()
            out = [v for v in out if str(v.get("language") or "").lower() == lt]
        if q.age:
            a = q.age.strip().lower()
            out = [v for v in out if str(v.get("age") or "").lower() == a]
        if q.gender:
            g = q.gender.strip().lower()
            out = [v for v in out if str(v.get("gender") or "").lower() == g]
        scenes = self._split_csv_set(q.scene_csv)
        if scenes:
            out = [v for v in out if scenes.intersection({str(x).lower() for x in (v.get("scene") or [])})]
        emos = self._split_csv_set(q.emotion_csv)
        if emos:
            out = [v for v in out if emos.intersection({str(x).lower() for x in (v.get("emotion") or [])})]
        return out

    async def _candidates_from_db(self, q: SemanticQuery, limit: int = 2000) -> Optional[List[Tuple[str, str]]]:
        pool = await self._get_pool()
        if pool is None:
            return None

        where = ["1=1"]
        args: List[Any] = []

        # Scope
        if q.only_owner_user_id:
            where.append("owner_user_id = $%d" % (len(args) + 1))
            args.append(str(q.only_owner_user_id))
        else:
            # Explore scope: public + built-in
            where.append("is_public = true")
            where.append("voice_type = 'built-in'")

        if q.language_type:
            where.append("lower(language_type) = $%d" % (len(args) + 1))
            args.append(q.language_type.strip().lower())
        if q.age:
            where.append("lower(age) = $%d" % (len(args) + 1))
            args.append(q.age.strip().lower())
        if q.gender:
            where.append("lower(gender) = $%d" % (len(args) + 1))
            args.append(q.gender.strip().lower())

        scenes = self._split_csv_set(q.scene_csv)
        if scenes:
            where.append("scene && $%d::text[]" % (len(args) + 1))
            args.append(sorted(list(scenes)))

        emos = self._split_csv_set(q.emotion_csv)
        if emos:
            where.append("emotion && $%d::text[]" % (len(args) + 1))
            args.append(sorted(list(emos)))

        where_sql = " AND ".join(where)
        sql = (
            "SELECT voice_id, "
            "trim(coalesce(display_name,'')) || ' ' || trim(coalesce(voice_description,'')) || ' ' || trim(coalesce(meta_text,'')) AS t "
            f"FROM voice_library_voices WHERE {where_sql} "
            "ORDER BY use_count DESC NULLS LAST, create_time DESC "
            "LIMIT $%d" % (len(args) + 1)
        )
        args.append(int(limit))

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
        return [(str(r.get("voice_id")), str(r.get("t") or "")) for r in rows]

    async def _candidates_from_builtin(self, q: SemanticQuery) -> List[Tuple[str, str]]:
        # Builtin scope: only explore (no user-owned voices available).
        if q.only_owner_user_id:
            return []
        voices = list_builtin_voices()
        voices = self._apply_structured_filters_local(voices, q)
        return [(str(v.get("voice_id")), self._voice_text(v)) for v in voices]

    async def search_voice_ids(self, q: SemanticQuery) -> List[str]:
        if process is None or fuzz is None:
            return []

        keyword = (q.keyword or "").strip()
        if not keyword:
            return []

        # Expand with synonyms to approximate semantic intent without embeddings.
        expanded_keyword = expand_keyword_with_synonyms(keyword)

        top_k = max(1, int(q.top_k or 50))

        candidates = await self._candidates_from_db(q)
        if candidates is None:
            candidates = await self._candidates_from_builtin(q)

        if not candidates:
            return []

        # rapidfuzz wants a list of strings; we keep mapping to voice_id.
        texts = [t for _, t in candidates]
        id_by_index = [vid for vid, _ in candidates]

        # Use WRatio for robust partial matches.
        # We run both original and expanded keyword and keep the best score per candidate.
        best_score: Dict[int, float] = {}
        for query in [keyword, expanded_keyword]:
            matches = process.extract(
                query,
                texts,
                scorer=fuzz.WRatio,
                limit=min(top_k, len(texts)),
            )
            for _text, score, idx in matches:
                if score is None:
                    continue
                i = int(idx)
                s = float(score)
                if s > best_score.get(i, -1.0):
                    best_score[i] = s

        # Rank by best score.
        ranked = sorted(best_score.items(), key=lambda kv: kv[1], reverse=True)
        out: List[str] = []
        for idx, score in ranked:
            if score < 30:
                continue
            out.append(id_by_index[idx])
            if len(out) >= top_k:
                break
        return out


_searcher: Optional[SemanticSearcher] = None


def get_semantic_searcher() -> SemanticSearcher:
    global _searcher
    if _searcher is not None:
        return _searcher

    mode = semantic_mode()
    if mode == "disabled":
        _searcher = DisabledSemanticSearcher()
        return _searcher

    # Default/fallback: fuzzy lexical match.
    _searcher = FuzzySemanticSearcher()
    return _searcher
