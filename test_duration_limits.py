#!/usr/bin/env python3
"""Minimal self-contained checks for upload duration limits.

Runs without pytest: uses FastAPI TestClient and monkeypatches duration probing.

Expected behavior (defaults):
- duration <= 5s  -> 400
- 5s < duration < 300s -> 200
- duration >= 300s -> 400

Usage:
  python test_duration_limits.py
"""

from __future__ import annotations

import io
import json
from typing import Optional

from fastapi.testclient import TestClient

import app.api.routes as routes
from app.main import app


def _post_with_fake_wav(duration_sec: Optional[float]) -> int:
    """Post multipart request while patching probe_duration_seconds to return duration_sec."""

    def _fake_probe(_path: str, timeout_sec: int = 10) -> Optional[float]:
        return duration_sec

    original = routes.probe_duration_seconds
    routes.probe_duration_seconds = _fake_probe  # type: ignore[assignment]
    try:
        client = TestClient(app)
        payload = {
            "voice_id": "anime_uncle",
            "stability": 7,
            "similarity": 8,
            "output_format": "wav",
            "preset_id": None,
            "webhook_url": None,
            "options": {},
        }
        files = {
            "file": ("test.wav", io.BytesIO(b"RIFF....WAVE"), "audio/wav"),
        }
        resp = client.post("/voice-changer", files=files, data={"payload": json.dumps(payload)})
        return resp.status_code
    finally:
        routes.probe_duration_seconds = original  # type: ignore[assignment]


def main() -> None:
    cases = [
        (4.0, 400),
        (5.0, 400),
        (5.01, 200),
        (299.99, 200),
        (300.0, 400),
        (301.0, 400),
        (None, 400),
    ]

    failures = 0
    for dur, expected in cases:
        got = _post_with_fake_wav(dur)
        ok = got == expected
        print(f"duration={dur!r} -> status={got} (expected {expected}) {'OK' if ok else 'FAIL'}")
        if not ok:
            failures += 1

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
