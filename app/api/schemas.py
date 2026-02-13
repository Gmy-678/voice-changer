from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel, Field, HttpUrl


# -------------------------
# Task Status (future-proof)
# -------------------------

class TaskStatus(str):
    """
    Task lifecycle status.
    Reserved for async pipeline in future.
    """
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


# -------------------------
# Request Schema
# -------------------------

class VoiceChangerRequest(BaseModel):
    """
    Parameters for a single voice changer task.
    This schema is considered a stable API contract.
    """

    voice_id: str = Field(
        ...,
        description="Target voice ID to convert into"
    )

    stability: int = Field(
        default=7,
        ge=1,
        le=10,
        description="Voice stability level (1-10, integer)"
    )

    similarity: int = Field(
        default=8,
        ge=1,
        le=10,
        description="Voice similarity level (1-10, integer)"
    )

    output_format: Literal["mp3", "wav"] = Field(
        default="mp3",
        description="Output audio format"
    )

    preset_id: Optional[str] = Field(
        default=None,
        description="Optional voice effect preset ID"
    )

    webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Webhook callback URL for async processing (reserved)"
    )

    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Reserved extensible options (noise, chunking, debug, etc.)"
    )


# -------------------------
# Response Schema
# -------------------------

class VoiceChangerResponse(BaseModel):
    """
    Response for voice changer task.
    In sync mode, output is returned immediately.
    In async mode, only task_id will be returned.
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier"
    )

    status: str = Field(
        default="success",
        description="Task execution status"
    )

    output_url: Optional[str] = Field(
        default=None,
        description="Download URL or local path of generated audio"
    )

    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra metadata for debugging or extension"
    )


# -------------------------
# Discovery / Capabilities
# -------------------------


class VoiceInfo(BaseModel):
    """A minimal voice description for UI discovery."""

    id: str = Field(..., description="Voice ID to use as voice_id")
    name: str = Field(..., description="Display name")
    role: str = Field(default="", description="Short role tag")
    description: str = Field(default="", description="Longer description")
    category: str = Field(default="public", description="public/private")
    is_verified: bool = Field(default=True, description="Verified flag (UI hint)")
    provider: Optional[str] = Field(default=None, description="Underlying provider name")


class VoicesResponse(BaseModel):
    voices: List[VoiceInfo] = Field(default_factory=list)


class CapabilitiesResponse(BaseModel):
    """Backend self-description so frontends can adapt dynamically."""

    voices: List[VoiceInfo] = Field(default_factory=list)
    output_formats: List[Literal["mp3", "wav"]] = Field(default_factory=lambda: ["mp3", "wav"])

    # Upload constraints / limits (mirrors server-side enforcement)
    upload_max_bytes: int = Field(..., description="Max allowed upload size in bytes")
    allowed_content_types: List[str] = Field(default_factory=list)
    upload_min_duration_sec: float = Field(..., description="Min duration (strictly greater than)")
    upload_max_duration_sec: float = Field(..., description="Max duration (strictly less than)")

    # Execution model
    async_mode: bool = Field(default=False, description="Whether jobs are async")


class TaskInfoResponse(BaseModel):
    task_id: str
    status: str = Field(..., description="success|not_found")
    output_url: Optional[str] = None