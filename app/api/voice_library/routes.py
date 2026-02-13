from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.voice_library.schemas import (
    APIResponse,
    CreateMyVoiceData,
    CreateMyVoiceRequest,
    FavoritesUpdateData,
    FavoritesUpdateRequest,
    VoicesListData,
    VoiceLibraryVoice,
)
from app.voice_library.catalog import top_fixed_voice_ids_by_language
from app.voice_library.repository import ExploreParams, get_voice_repository
from app.voice_library.semantic import (
    get_semantic_searcher,
    semantic_enabled,
    semantic_top_k_default,
    SemanticQuery,
)
from app.voice_library.state import get_voice_library_state
from app.voice_library.user_voices import get_user_voices_by_ids
from app.voice_library.preview import ensure_preview_mp3


router = APIRouter(prefix="/api/v1/voice-library", tags=["voice-library"])

_state = get_voice_library_state()
_repo = get_voice_repository()
_semantic = get_semantic_searcher()


def _user_id_from_auth(authorization: Optional[str] = Header(default=None), x_user_id: Optional[str] = Header(default=None)) -> Optional[str]:
    if x_user_id:
        return x_user_id
    if not authorization:
        return None
    # Very lightweight placeholder auth: "Bearer <user_id>"
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
        return parts[1].strip()
    return None


def _require_user(user_id: Optional[str]) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


def _preview_url_for_voice_id(voice_id: str) -> str:
    vid = str(voice_id or "").strip()
    return f"/api/v1/voice-library/preview/{vid}.mp3"


def _preview_url_for_voice(v: dict) -> str:
    vid = str(v.get("voice_id") or "").strip()
    if vid.startswith("user_"):
        meta = v.get("meta") or {}
        if isinstance(meta, dict):
            base = str(meta.get("base_voice_id") or meta.get("baseVoiceId") or "").strip()
            if base:
                # For user voices, use the base voice preview so it can be fetched without auth headers.
                return _preview_url_for_voice_id(base)
    return _preview_url_for_voice_id(vid)


def _attach_preview_urls(voices: List[dict]) -> List[dict]:
    out: List[dict] = []
    for v in voices:
        vv = dict(v)
        if not vv.get("url"):
            vv["url"] = _preview_url_for_voice(vv)
        out.append(vv)
    return out


@router.api_route("/preview/{voice_id}.mp3", methods=["GET", "HEAD"])
async def voice_preview_mp3(
    voice_id: str,
    user_id: Optional[str] = Depends(_user_id_from_auth),
):
    """Serve (and lazily generate) an mp3 preview for a voice.

    - Built-in voices: public.
    - user_* voices: requires X-User-Id (or Bearer <user_id>) so we can resolve base_voice_id.
    """
    try:
        p = ensure_preview_mp3(voice_id=voice_id, user_id=user_id)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voice not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(p, media_type="audio/mpeg", filename=f"{voice_id}.mp3")


async def _apply_favorites(voices: List[dict], user_id: Optional[str]) -> List[dict]:
    if not user_id:
        return voices
    fav = await _state.favorites_get(user_id)
    out = []
    for v in voices:
        vv = dict(v)
        vv["is_favorited"] = str(vv.get("voice_id")) in fav
        out.append(vv)
    return out


async def _get_known_voices_for_user(voice_ids: List[str], user_id: str) -> List[dict]:
    # Built-in/public voices from repository
    fetched = await _repo.get_by_voice_ids(voice_ids)
    known = {str(v.get("voice_id")) for v in fetched}

    # Include user-owned voices when using builtin/local storage.
    # (For Postgres repo, user voices may already be included in repo.get_by_voice_ids depending on schema, but this is safe.)
    missing = [vid for vid in voice_ids if str(vid) not in known]
    if missing:
        fetched.extend(get_user_voices_by_ids(user_id, missing))
    return fetched


@router.get("/top-fixed-voices", response_model=APIResponse)
async def top_fixed_voices(
    language: str = Query(..., description="language code: en/zh/ja"),
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    # Cache the base list (without favorites) 5 minutes.
    lang = (language or "").strip().lower() or "en"
    cache_key = f"top_fixed:{lang}"
    cached = await _state.cache_get_json(cache_key)

    if cached is None:
        mapping = top_fixed_voice_ids_by_language()
        ids = mapping.get(lang) or mapping.get("en") or []

        fetched = await _repo.get_by_voice_ids(ids)
        all_voices = {str(v.get("voice_id")): v for v in fetched}
        ordered = [all_voices[vid] for vid in ids if vid in all_voices]

        cached = {
            "total_count": len(ordered),
            "voices": ordered,
        }
        await _state.cache_set_json(cache_key, cached, ttl_seconds=300)

    voices = await _apply_favorites(list(cached["voices"]), user_id)
    voices = _attach_preview_urls(voices)
    data = VoicesListData(total_count=len(voices), voices=[VoiceLibraryVoice.model_validate(v) for v in voices])
    return APIResponse(code=0, message="success", data=data)


@router.get("/explore", response_model=APIResponse)
async def explore(
    keyword: Optional[str] = Query(default=None),
    voice_ids: Optional[str] = Query(default=None, description="comma-separated"),
    language: Optional[str] = Query(default=None, description="sorting preference"),
    language_type: Optional[str] = Query(default=None),
    age: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    scene: Optional[str] = Query(default=None, description="comma-separated"),
    emotion: Optional[str] = Query(default=None, description="comma-separated"),
    sort: str = Query(default="mostUsers"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    # NOTE: This is a simplified implementation.
    # - Level 1/2/3, Milvus, hot caches, etc. are stubbed into a single in-process cache.

    lang = (language or "").strip().lower() or None
    has_filters = any([keyword, voice_ids, language_type, age, gender, scene, emotion])

    if sort == "latest" and not has_filters:
        cache_ttl = 60
    else:
        cache_ttl = 30 if has_filters else 300
    cache_key = f"explore:{keyword}:{voice_ids}:{language}:{language_type}:{age}:{gender}:{scene}:{emotion}:{sort}:{skip}:{limit}"
    cached = await _state.cache_get_json(cache_key)

    if cached is None:
        params = ExploreParams(
            keyword=keyword,
            voice_ids_csv=voice_ids,
            language=lang,
            language_type=language_type,
            age=age,
            gender=gender,
            scene_csv=scene,
            emotion_csv=emotion,
            sort=sort,
            skip=skip,
            limit=limit,
        )

        total, page = await _repo.explore(params)

        # Semantic fallback: only when keyword is provided and exact search yields 0.
        if keyword and int(total) == 0 and semantic_enabled():
            top_k = semantic_top_k_default()
            sem_cache_key = f"semantic:explore:{keyword}:{language_type}:{age}:{gender}:{scene}:{emotion}:{sort}:{top_k}"
            sem_cached = await _state.cache_get_json(sem_cache_key)
            if sem_cached is None:
                q = SemanticQuery(
                    keyword=str(keyword),
                    top_k=top_k,
                    only_owner_user_id=None,
                    language_type=language_type,
                    age=age,
                    gender=gender,
                    scene_csv=scene,
                    emotion_csv=emotion,
                )
                sem_ids = await _semantic.search_voice_ids(q)
                sem_cached = {"voice_ids": sem_ids}
                # Short TTL to limit cost; semantic result is a candidate set.
                await _state.cache_set_json(sem_cache_key, sem_cached, ttl_seconds=30)

            sem_ids = list(sem_cached.get("voice_ids") or [])
            if sem_ids:
                sem_voices = await _repo.get_by_voice_ids(sem_ids)
                by_id = {str(v.get("voice_id")): v for v in sem_voices}
                ordered = [by_id[vid] for vid in sem_ids if vid in by_id]
                total = len(ordered)
                page = ordered[skip : skip + limit]

        # Exclude top-fixed voices when browsing by language without filters, to avoid duplicates.
        if not has_filters and lang:
            mapping = top_fixed_voice_ids_by_language()
            top_ids = set(mapping.get(lang) or mapping.get("en") or [])
            page = [v for v in page if str(v.get("voice_id")) not in top_ids]

        cached = {"total_count": total, "voices": page}
        await _state.cache_set_json(cache_key, cached, ttl_seconds=cache_ttl)

    voices = await _apply_favorites(list(cached["voices"]), user_id)
    voices = _attach_preview_urls(voices)
    data = VoicesListData(total_count=int(cached["total_count"]), voices=[VoiceLibraryVoice.model_validate(v) for v in voices])
    return APIResponse(code=0, message="success", data=data)


@router.get("/my-voices", response_model=APIResponse)
async def my_voices(
    keyword: Optional[str] = Query(default=None),
    voice_ids: Optional[str] = Query(default=None),
    language_type: Optional[str] = Query(default=None),
    age: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    scene: Optional[str] = Query(default=None),
    emotion: Optional[str] = Query(default=None),
    sort: str = Query(default="latest"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    uid = _require_user(user_id)
    params = ExploreParams(
        keyword=keyword,
        voice_ids_csv=voice_ids,
        language=None,
        language_type=language_type,
        age=age,
        gender=gender,
        scene_csv=scene,
        emotion_csv=emotion,
        sort=sort,
        skip=skip,
        limit=limit,
    )
    total, voices = await _repo.explore(params, only_owner_user_id=uid)

    # Semantic fallback: only when keyword is provided and exact search yields 0.
    if keyword and int(total) == 0 and semantic_enabled():
        top_k = semantic_top_k_default()
        sem_cache_key = f"semantic:my:{uid}:{keyword}:{language_type}:{age}:{gender}:{scene}:{emotion}:{sort}:{top_k}"
        sem_cached = await _state.cache_get_json(sem_cache_key)
        if sem_cached is None:
            q = SemanticQuery(
                keyword=str(keyword),
                top_k=top_k,
                only_owner_user_id=uid,
                language_type=language_type,
                age=age,
                gender=gender,
                scene_csv=scene,
                emotion_csv=emotion,
            )
            sem_ids = await _semantic.search_voice_ids(q)
            sem_cached = {"voice_ids": sem_ids}
            await _state.cache_set_json(sem_cache_key, sem_cached, ttl_seconds=30)

        sem_ids = list(sem_cached.get("voice_ids") or [])
        if sem_ids:
            sem_voices = await _repo.get_by_voice_ids(sem_ids)
            by_id = {str(v.get("voice_id")): v for v in sem_voices}
            ordered = [by_id[vid] for vid in sem_ids if vid in by_id]
            total = len(ordered)
            voices = ordered[skip : skip + limit]
    voices = await _apply_favorites(voices, uid)
    voices = _attach_preview_urls(voices)
    data = VoicesListData(total_count=total, voices=[VoiceLibraryVoice.model_validate(v) for v in voices])
    return APIResponse(code=0, message="success", data=data)


@router.post("/my-voices", response_model=APIResponse)
async def create_my_voice(
    body: CreateMyVoiceRequest,
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    uid = _require_user(user_id)

    meta = dict(body.meta or {})
    # For now, My voices are "virtual": they map to a base funny voice for conversion.
    # This ensures the created voice can be used immediately.
    meta.setdefault("base_voice_id", "anime_uncle")

    v = {
        "display_name": body.display_name,
        "voice_description": body.voice_description,
        "voice_type": "user",
        "labels": list(body.labels or []),
        "meta": meta,
        "is_public": bool(body.is_public),
        "language": body.language_type,
        "age": body.age,
        "gender": body.gender,
        "scene": list(body.scene or []),
        "emotion": list(body.emotion or []),
        "creation_mode": "public" if body.is_public else "private",
        "can_delete": True,
    }

    created = await _repo.create_user_voice(uid, v)
    created = (await _apply_favorites([created], uid))[0]
    created = _attach_preview_urls([created])[0]
    data = CreateMyVoiceData(voice=VoiceLibraryVoice.model_validate(created))
    return APIResponse(code=0, message="success", data=data)


@router.get("/favorites", response_model=APIResponse)
async def favorites(
    keyword: Optional[str] = Query(default=None),
    voice_ids: Optional[str] = Query(default=None),
    language_type: Optional[str] = Query(default=None),
    age: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    scene: Optional[str] = Query(default=None),
    emotion: Optional[str] = Query(default=None),
    sort: str = Query(default="latest"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    uid = _require_user(user_id)
    fav = await _state.favorites_get(uid)

    voices = await _get_known_voices_for_user(sorted(list(fav)), uid)
    if language_type:
        lt = language_type.strip().lower()
        voices = [v for v in voices if str(v.get("language") or "").lower() == lt]
    if keyword:
        kw = keyword.strip().lower()
        voices = [
            v
            for v in voices
            if kw in str(v.get("display_name", "")).lower()
            or kw in str(v.get("voice_description", "")).lower()
            or kw in str((v.get("meta") or {}).get("text", "")).lower()
        ]

    if sort == "latest":
        voices.sort(key=lambda v: int(v.get("create_time") or 0), reverse=True)
    else:
        voices.sort(key=lambda v: str(v.get("voice_id")))

    total = len(voices)
    page = voices[skip : skip + limit]
    page = await _apply_favorites(page, uid)
    page = _attach_preview_urls(page)
    data = VoicesListData(total_count=total, voices=[VoiceLibraryVoice.model_validate(v) for v in page])
    return APIResponse(code=0, message="success", data=data)


@router.post("/favorites", response_model=APIResponse)
async def update_favorites_route(
    body: FavoritesUpdateRequest,
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    uid = _require_user(user_id)

    # Only allow updating known voices (including user-owned voices).
    fetched = await _get_known_voices_for_user(list(body.voice_ids), uid)
    known = {str(v.get("voice_id")) for v in fetched}

    ok: List[str] = []
    failed: List[str] = []
    for vid in body.voice_ids:
        if str(vid) in known:
            ok.append(str(vid))
        else:
            failed.append(str(vid))

    if ok:
        await _state.favorites_update(uid, ok, body.is_favorite)

    data = FavoritesUpdateData(
        success_count=len(ok),
        failed_count=len(failed),
        failed_voice_ids=failed or None,
    )
    return APIResponse(code=0, message="success", data=data)


@router.get("/recent-used", response_model=APIResponse)
async def recent_used(
    limit: int = Query(default=5, ge=1, le=50),
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    uid = _require_user(user_id)
    ids = await _state.recent_get_ids(uid, limit=limit)
    wanted = set(ids)

    voices = await _get_known_voices_for_user(list(wanted), uid)

    # Order by recent-used
    order = {vid: i for i, vid in enumerate(ids)}
    voices.sort(key=lambda v: order.get(str(v.get("voice_id")), 10**9))

    voices = await _apply_favorites(voices, uid)
    voices = _attach_preview_urls(voices)
    data = VoicesListData(total_count=len(voices), voices=[VoiceLibraryVoice.model_validate(v) for v in voices])
    return APIResponse(code=0, message="success", data=data)


@router.get("/get-voices-by-ids", response_model=APIResponse)
async def get_voices_by_ids(
    voice_ids: str = Query(..., description="comma-separated"),
    user_id: Optional[str] = Depends(_user_id_from_auth),
) -> APIResponse:
    wanted = [x.strip() for x in voice_ids.split(",") if x.strip()]
    wanted_set = set(wanted)

    voices = await _repo.get_by_voice_ids(wanted)

    voices = await _apply_favorites(voices, user_id)
    voices = _attach_preview_urls(voices)
    data = VoicesListData(total_count=len(voices), voices=[VoiceLibraryVoice.model_validate(v) for v in voices])
    return APIResponse(code=0, message="success", data=data)


# Helper hook for other parts of the app to record recent usage.
# You can call this from /voice-changer when you have a user id.

async def record_voice_used(user_id: str, voice_id: str) -> None:
    if not user_id:
        return
    await _state.recent_add(user_id, voice_id)
