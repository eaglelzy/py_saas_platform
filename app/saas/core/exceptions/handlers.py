"""全局异常处理器。"""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.saas.api.v1.api_error import ApiError
from app.saas.core.redis import RedisBackendError
from app.saas.schemas.common import ErrorResponse, ValidationErrorResponse, FieldError
from app.saas.services.exceptions import ServiceError
from app.saas.core.logging import logger


def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    logger.bind(
        component="server_error",
        path=str(request.url.path), 
        status=exc.status_code,
        error=f"[{exc.code} : {str(exc)}]"
    ).warning("服务层异常")
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    logger.bind(
        component="api_error",
        path=str(request.url.path), 
        status=exc.status_code,
        error=str(exc.detail)
    ).warning("API 异常")
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.bind(
        component="generic_error",
        path=str(request.url.path), 
        status=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
        error=str(exc)
    ).exception("未捕获异常")
    payload = ErrorResponse(message="Internal server error", code="internal_error")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())

def redis_error_handler(request: Request, exc: RedisBackendError) -> JSONResponse:
    logger.bind(
        component="redis_error",
        path=str(request.url.path), 
        status=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
        error=str(exc)
    ).exception("Redis 异常")
    payload = ErrorResponse(message=str(exc), code="redis_error")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())

def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求体验证错误，输出中文友好提示。"""

    logger.bind(component="api", path=str(request.url.path), status=422).warning(
        "请求验证失败", errors=exc.errors()
    )

    field_errors: list[FieldError] = []
    logger.debug(f"exc.errors(): {exc.errors()}")
    for error in exc.errors():
        loc = error.get("loc", [])
        # 过滤掉 ('body',) 前缀，只保留字段路径
        field_path = ".".join(str(item) for item in loc if item not in {"body", "query", "path"})
        ctx = error.get("ctx")
        if ctx and ctx.get("error"):
            message = str(ctx["error"])
        else:
            message = error.get("msg", "请求参数不合法")
        field_errors.append(FieldError(field=field_path or "__root__", message=message))

    payload = ValidationErrorResponse(
        message="请求验证失败，请检查输入字段",
        code="invalid_request",
        detail=field_errors,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump())
