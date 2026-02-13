from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


def _base_dir() -> str:
    # Persist lightweight state under tmp/ (works locally; in production you likely want Redis/DB)
    root = os.getenv("VOICE_LIBRARY_STATE_DIR")
    if root:
        return os.path.abspath(root)
    return os.path.abspath(os.path.join(os.getcwd(), "tmp", "voice_library"))


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _user_dir(user_id: str) -> str:
    safe = "".join(c for c in user_id if c.isalnum() or c in ("-", "_", "."))
    d = os.path.join(_base_dir(), safe)
    _ensure_dir(d)
    return d


def _read_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data: Any) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def get_favorites(user_id: str) -> Set[str]:
    p = os.path.join(_user_dir(user_id), "favorites.json")
    raw = _read_json(p, {"voice_ids": []})
    ids = raw.get("voice_ids") if isinstance(raw, dict) else []
    if not isinstance(ids, list):
        return set()
    return {str(x) for x in ids}


def set_favorites(user_id: str, voice_ids: Set[str]) -> None:
    p = os.path.join(_user_dir(user_id), "favorites.json")
    _write_json(p, {"voice_ids": sorted(list(voice_ids))})


def update_favorites(user_id: str, voice_ids: List[str], is_favorite: bool) -> None:
    current = get_favorites(user_id)
    if is_favorite:
        current.update({str(v) for v in voice_ids})
    else:
        current.difference_update({str(v) for v in voice_ids})
    set_favorites(user_id, current)


def get_recent_used(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    p = os.path.join(_user_dir(user_id), "recent_used.json")
    raw = _read_json(p, {"items": []})
    items = raw.get("items") if isinstance(raw, dict) else []
    if not isinstance(items, list):
        return []
    # items are dicts: {voice_id, ts}
    items = [x for x in items if isinstance(x, dict) and x.get("voice_id")]
    items.sort(key=lambda x: int(x.get("ts") or 0), reverse=True)

    seen = set()
    deduped: List[Dict[str, Any]] = []
    for it in items:
        vid = str(it.get("voice_id"))
        if vid in seen:
            continue
        seen.add(vid)
        deduped.append({"voice_id": vid, "ts": int(it.get("ts") or 0)})
        if len(deduped) >= limit:
            break
    return deduped


def add_recent_used(user_id: str, voice_id: str) -> None:
    p = os.path.join(_user_dir(user_id), "recent_used.json")
    raw = _read_json(p, {"items": []})
    items = raw.get("items") if isinstance(raw, dict) else []
    if not isinstance(items, list):
        items = []
    items.append({"voice_id": str(voice_id), "ts": int(time.time())})
    _write_json(p, {"items": items[-500:]})
