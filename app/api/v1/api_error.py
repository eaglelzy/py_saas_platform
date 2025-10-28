from typing import Any

from fastapi import HTTPException


class ApiError(HTTPException):
    """API 异常。"""

    def __init__(self, status_code: int, code: str,  message: str, detail: Any = None):
        super().__init__(
            status_code=status_code, 
            detail={"code": code, "message": message, "detail": detail}
        )