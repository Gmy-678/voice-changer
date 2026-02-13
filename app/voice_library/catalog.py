from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

from app.services.providers.funny_voice import FunnyVoiceProvider


def top_fixed_voice_ids_by_language() -> Dict[str, List[str]]:
    """
    Mimics the "dictionary table" top_fixed_voices.

    Override with env TOP_FIXED_VOICES_JSON, e.g.:
    {"en": ["anime_uncle", "uwu_anime"], "zh": ["mamba"]}
    """
    default = {
        "en": ["anime_uncle", "uwu_anime", "gender_swap", "mamba", "nerd_bro"],
        "zh": ["mamba", "nerd_bro", "anime_uncle", "uwu_anime", "gender_swap"],
        "ja": ["uwu_anime", "anime_uncle", "gender_swap", "mamba", "nerd_bro"],
    }

    raw = os.getenv("TOP_FIXED_VOICES_JSON")
    if not raw:
        return default
    try:
        import json

        data = json.loads(raw)
        if isinstance(data, dict):
            out: Dict[str, List[str]] = {}
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, list):
                    out[k] = [str(x) for x in v]
            return out or default
    except Exception:
        return default
    return default


def _stable_id(voice_id: str) -> int:
    # Stable-ish positive id for voice_id
    return abs(hash(f"voice:{voice_id}")) % 1_000_000_000


def _now_ts() -> int:
    return int(time.time())


def builtin_voice_detail(voice_id: str, language: Optional[str] = None) -> Optional[dict]:
    if voice_id not in FunnyVoiceProvider.SUPPORTED_VOICES:
        return None

    names = {
        "anime_uncle": "Anime Uncle",
        "uwu_anime": "UwU Anime",
        "gender_swap": "Gender Swap",
        "mamba": "Mamba",
        "nerd_bro": "Nerd Bro",
    }
    descs = {
        "anime_uncle": "A dramatic, punchy low voice (anime uncle vibe)",
        "uwu_anime": "A cute, sparkly higher voice (uwu anime)",
        "gender_swap": "A noticeable pitch shift (gender swap)",
        "mamba": "An energetic, hype voice (mamba mode)",
        "nerd_bro": "A slightly nasal, snappy voice (nerd bro)",
    }

    # Metadata used by /api/v1/voice-library/explore filters.
    # Keep values aligned with the React UI filter labels (case-insensitive matching).
    lang = (language or "en").strip().lower() or "en"

    # Provide richer tags so common UI filters yield results even in builtin-only mode.
    per_voice = {
        "anime_uncle": {
            "gender": "male",
            "age": "middle_age",
            "scene": ["Social Video", "Podcast", "Audiobook", "Gaming & Fiction"],
            "emotion": ["Surprise", "joyful", "Calm"],
        },
        "uwu_anime": {
            "gender": "female",
            "age": "young",
            "scene": ["Social Video", "Gaming & Fiction", "Advertising / Commercial"],
            "emotion": ["joyful", "Surprise", "Calm"],
        },
        "gender_swap": {
            "gender": "unknown",
            "age": "young",
            "scene": ["Social Video", "eCommerce", "Education"],
            "emotion": ["Surprise", "Calm"],
        },
        "mamba": {
            "gender": "male",
            "age": "young",
            "scene": ["Social Video", "Podcast", "Advertising / Commercial"],
            "emotion": ["joyful", "Angry", "Surprise"],
        },
        "nerd_bro": {
            "gender": "male",
            "age": "young",
            "scene": ["Social Video", "Education", "Podcast"],
            "emotion": ["Calm", "joyful"],
        },
    }
    tags = per_voice.get(voice_id, {})

    meta = {
        "text": "Hello, nice to meet you.",
        "language": lang,
        "gender": tags.get("gender", "unknown"),
        "age": tags.get("age", "unknown"),
        "scene": tags.get("scene", ["Social Video"]),
        "emotion": tags.get("emotion", ["Calm"]),
    }

    return {
        "id": _stable_id(voice_id),
        "voice_id": voice_id,
        "display_name": names.get(voice_id, voice_id),
        "voice_type": "built-in",
        "labels": [],
        "file_path": None,
        "meta": meta,
        "is_public": True,
        "url": None,
        "fallbackurl": None,
        "language": meta.get("language"),
        "age": meta.get("age"),
        "gender": meta.get("gender"),
        "scene": meta.get("scene") or [],
        "emotion": meta.get("emotion") or [],
        "voice_description": descs.get(voice_id),
        "creation_mode": "public",
        "can_delete": False,
        "create_time": _now_ts(),
    }


def list_builtin_voices(language: Optional[str] = None) -> List[dict]:
    out = []
    for vid in FunnyVoiceProvider.SUPPORTED_VOICES:
        d = builtin_voice_detail(vid, language=language)
        if d:
            out.append(d)
    return out
