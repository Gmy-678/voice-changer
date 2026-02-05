from typing import Optional, Dict, Any, Literal
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