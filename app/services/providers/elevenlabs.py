from __future__ import annotations

import os
import time
import json
from typing import Any, Dict, Optional, Tuple

import requests

try:
    from app.services.providers.base import VoiceChangeResult, OutputFormat
except ModuleNotFoundError:
    # Allow running this file directly: add project/app dir to sys.path
    import sys
    _app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if _app_dir not in sys.path:
        sys.path.insert(0, _app_dir)
    from app.services.providers.base import VoiceChangeResult, OutputFormat


class ElevenLabsProviderError(RuntimeError):
    pass


def _map_ui_1_10_to_0_1_1_0(v: int) -> float:
    """Map UI 1-10 int to provider 0.1-1.0 float."""
    v = max(1, min(10, int(v)))
    return v / 10.0


def _map_output_format(fmt: OutputFormat) -> Tuple[str, str]:
    """Map external mp3/wav to ElevenLabs output enum and MIME."""
    if fmt == "wav":
        return "wav", "audio/wav"
    # conservative default mp3 settings
    return "mp3_44100_128", "audio/mpeg"


class ElevenLabsVoiceChangerHTTP:
    name = "elevenlabs"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_sec: int = 120,
    ) -> None:
        self.api_key = api_key or os.getenv("ELEVEN_API_KEY", "")
        if not self.api_key:
            raise ElevenLabsProviderError("ELEVEN_API_KEY is not set.")

        self.base_url = (base_url or os.getenv("ELEVEN_BASE_URL", "https://api.elevenlabs.io")).rstrip("/")
        self.timeout_sec = timeout_sec

        # default speech-to-speech model
        self.default_model_id = os.getenv("ELEVEN_STS_MODEL_ID", "eleven_multilingual_sts_v2")

    def convert(
        self,
        *,
        voice_id: str,
        audio_path: str,
        model_id: Optional[str],
        stability: int,
        similarity: int,
        output_format: OutputFormat,
        remove_background_noise: Optional[bool] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> VoiceChangeResult:
        model_id = model_id or self.default_model_id

        # map UI params
        stability_f = _map_ui_1_10_to_0_1_1_0(stability)
        similarity_f = _map_ui_1_10_to_0_1_1_0(similarity)

        out_fmt, mime = _map_output_format(output_format)

        url = f"{self.base_url}/v1/speech-to-speech/{voice_id}/convert"

        headers = {
            "xi-api-key": self.api_key,
            "accept": "*/*",
        }

        # send as multipart form fields (provider expects form, not JSON body)
        fields: Dict[str, str] = {
            "model_id": model_id,
            "output_format": out_fmt,
            "voice_settings": json.dumps({
                "stability": stability_f,
                "similarity_boost": similarity_f,
            }),
        }

        if remove_background_noise is not None:
            fields["remove_background_noise"] = "true" if remove_background_noise else "false"

        if extra:
            for k, v in extra.items():
                fields[k] = json.dumps(v) if isinstance(v, (dict, list)) else str(v)

        start = time.time()

        with open(audio_path, "rb") as f:
            files = {
                "audio": (os.path.basename(audio_path), f, "application/octet-stream")
            }
            resp = requests.post(url, headers=headers, data=fields, files=files, timeout=self.timeout_sec)

        if not resp.ok:
            raise ElevenLabsProviderError(
                f"ElevenLabs convert failed: HTTP {resp.status_code}\n{resp.text}"
            )

        latency_ms = int((time.time() - start) * 1000)

        return VoiceChangeResult(
            audio_bytes=resp.content,
            mime=mime,
            meta={
                "provider": self.name,
                "model_id": model_id,
                "output_format": out_fmt,
                "stability": stability_f,
                "similarity_boost": similarity_f,
                "latency_ms": latency_ms,
            },
        )