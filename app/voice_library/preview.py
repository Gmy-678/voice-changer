from __future__ import annotations

import os
import re
import wave
from dataclasses import dataclass
from typing import Optional

from app.config.settings import OUTPUTS_DIR
from app.services.providers.funny_voice import FunnyVoiceProvider
from app.voice_library.user_voices import get_user_voices_by_ids


_SAFE_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def _safe_name(s: str) -> str:
    s = str(s or "").strip() or "voice"
    return _SAFE_RE.sub("_", s)


def _preview_dir() -> str:
    return os.path.join(OUTPUTS_DIR, "voice_previews")


def _ref_wav_path() -> str:
    # Store under tmp (not outputs) since it's an implementation detail.
    return os.path.join("tmp", "voice_library", "preview_ref.wav")


def _ensure_ref_wav() -> str:
    p = _ref_wav_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.isfile(p):
        return p

    # Generate a short reference tone (2.2s) at 48k to match pipeline expectations.
    # Keep it simple: a sine-like waveform using a two-level square-ish approximation.
    sr = 48000
    duration_sec = 2.2
    freq = 220.0
    amp = 0.20

    n = int(sr * duration_sec)

    with wave.open(p, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)

        for i in range(n):
            t = i / sr
            # Square-ish wave to avoid importing math (fast + deterministic)
            v = amp if (int(t * freq * 2) % 2 == 0) else -amp
            samp = int(max(-1.0, min(1.0, v)) * 32767)
            wf.writeframesraw(int(samp).to_bytes(2, byteorder="little", signed=True))

    return p


@dataclass(frozen=True)
class PreviewResolve:
    effect_voice_id: str
    source_voice_id: str


def resolve_effect_voice_id(*, voice_id: str, user_id: Optional[str]) -> PreviewResolve:
    vid = str(voice_id or "").strip()
    if not vid:
        raise ValueError("voice_id is required")

    # Built-in funny voices
    if FunnyVoiceProvider.is_funny_voice(vid):
        return PreviewResolve(effect_voice_id=vid, source_voice_id=vid)

    # User voices resolve to their meta.base_voice_id
    if vid.startswith("user_"):
        if not user_id:
            raise PermissionError("Unauthorized")
        found = get_user_voices_by_ids(str(user_id), [vid])
        if not found:
            raise FileNotFoundError("User voice not found")
        meta = found[0].get("meta") or {}
        base_voice_id = ""
        if isinstance(meta, dict):
            base_voice_id = str(meta.get("base_voice_id") or meta.get("baseVoiceId") or "").strip()
        if not base_voice_id:
            raise ValueError("User voice missing base_voice_id")
        if not FunnyVoiceProvider.is_funny_voice(base_voice_id):
            raise ValueError("User voice base_voice_id is not supported")
        return PreviewResolve(effect_voice_id=base_voice_id, source_voice_id=vid)

    raise ValueError("Unsupported voice_id")


def preview_output_path(*, voice_id: str, fmt: str = "mp3") -> str:
    safe = _safe_name(voice_id)
    os.makedirs(_preview_dir(), exist_ok=True)
    return os.path.join(_preview_dir(), f"{safe}.{fmt}")


def ensure_preview_mp3(*, voice_id: str, user_id: Optional[str]) -> str:
    """Returns absolute filesystem path to an mp3 preview file (generates if missing)."""
    resolved = resolve_effect_voice_id(voice_id=voice_id, user_id=user_id)
    out_path = preview_output_path(voice_id=resolved.source_voice_id, fmt="mp3")

    if os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
        return out_path

    ref = _ensure_ref_wav()

    provider = FunnyVoiceProvider()
    result = provider.convert(voice_id=resolved.effect_voice_id, audio_path=ref, output_format="mp3")

    tmp_path = out_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(result.audio_bytes)

    os.replace(tmp_path, out_path)
    return out_path
