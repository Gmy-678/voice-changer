from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Sequence


def _base_dir() -> str:
    # Keep under repo tmp/ by default.
    return os.getenv("VOICE_LIBRARY_LOCAL_DIR") or os.path.join("tmp", "voice_library", "user_voices")


def _path_for_user(user_id: str) -> str:
    safe = "".join(ch for ch in str(user_id) if ch.isalnum() or ch in ("-", "_"))
    if not safe:
        safe = "anonymous"
    return os.path.join(_base_dir(), f"{safe}.json")


def list_user_voices(user_id: str) -> List[Dict[str, Any]]:
    p = _path_for_user(user_id)
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [dict(x) for x in data if isinstance(x, dict)]
    except Exception:
        return []
    return []


def upsert_user_voice(user_id: str, voice: Dict[str, Any]) -> Dict[str, Any]:
    os.makedirs(_base_dir(), exist_ok=True)
    voices = list_user_voices(user_id)
    vid = str(voice.get("voice_id") or "").strip()
    if not vid:
        raise ValueError("voice_id is required")

    now = int(time.time())
    voice = dict(voice)
    voice.setdefault("create_time", now)

    out: List[Dict[str, Any]] = []
    replaced = False
    for v in voices:
        if str(v.get("voice_id")) == vid:
            out.append(voice)
            replaced = True
        else:
            out.append(v)
    if not replaced:
        out.insert(0, voice)

    p = _path_for_user(user_id)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    return voice


def get_user_voices_by_ids(user_id: str, voice_ids: Sequence[str]) -> List[Dict[str, Any]]:
    wanted = {str(x) for x in voice_ids if str(x)}
    if not wanted:
        return []
    voices = list_user_voices(user_id)
    return [v for v in voices if str(v.get("voice_id")) in wanted]
