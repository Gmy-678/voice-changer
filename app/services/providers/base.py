from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, Literal


OutputFormat = Literal["mp3", "wav"]


@dataclass
class VoiceChangeResult:
    audio_bytes: bytes
    mime: str
    meta: Dict[str, Any] = field(default_factory=dict)


class VoiceChangerProvider(Protocol):
    name: str

    def convert(
        self,
        *,
        voice_id: str,
        audio_path: str,
        model_id: Optional[str],
        stability: int,       # 1-10
        similarity: int,      # 1-10
        output_format: OutputFormat,
        # 扩展位：先不启用，但预留
        remove_background_noise: Optional[bool] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> VoiceChangeResult:
        ...