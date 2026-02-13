from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class VoiceMeta(BaseModel):
    text: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    scene: Optional[List[str]] = None
    emotion: Optional[List[str]] = None


class VoiceLibraryVoice(BaseModel):
    id: int
    voice_id: str
    display_name: str

    voice_type: Literal["built-in", "user"] = "built-in"
    labels: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None

    meta: Dict[str, Any] = Field(default_factory=dict)

    is_public: bool = True
    url: Optional[str] = None
    fallbackurl: Optional[str] = None

    is_favorited: bool = False

    language: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    scene: List[str] = Field(default_factory=list)
    emotion: List[str] = Field(default_factory=list)

    voice_description: Optional[str] = None
    creation_mode: Literal["public", "private"] = "public"
    can_delete: bool = False
    create_time: int


class VoicesListData(BaseModel):
    total_count: int
    voices: List[VoiceLibraryVoice]


class FavoritesUpdateRequest(BaseModel):
    voice_ids: List[str] = Field(..., min_length=1, max_length=50)
    is_favorite: bool


class FavoritesUpdateData(BaseModel):
    success_count: int
    failed_count: int
    failed_voice_ids: Optional[List[str]] = None


class CreateMyVoiceRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=80)
    base_voice_id: Optional[str] = Field(default=None, description="Base voice_id to use for conversion")
    voice_description: Optional[str] = Field(default=None, max_length=400)
    language_type: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    scene: Optional[List[str]] = None
    emotion: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None
    is_public: bool = False


class CreateMyVoiceData(BaseModel):
    voice: VoiceLibraryVoice
