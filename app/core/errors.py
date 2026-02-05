from fastapi import HTTPException
from typing import Any, Dict


class VoiceChangerException(HTTPException):
    def __init__(self, status_code: int, error_code: str, detail: str, extra: Dict[str, Any] | None = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}