"""FastAPI 中间件，统一处理请求日志与上下文注入。"""

from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.saas.core.logging.context import reset_log_context, set_log_context
from app.saas.core.logging.logger import logger
from app.saas.core.config.settings import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录 HTTP 请求生命周期并注入 Request ID。"""

    def __init__(self, app: ASGIApp) -> None:
        """初始化中间件。"""

        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """在请求前后写入日志并设置上下文。"""

        path = str(request.url.path)
        api_prefix = settings.api_v1_prefix
        if not path.startswith(api_prefix):
            # 非 API 路径直接透传，避免无关日志干扰
            return await call_next(request)

        request_id = str(uuid.uuid4())
        set_log_context(request_id=request_id)
        request.state.request_id = request_id  # 允许在业务逻辑中复用

        log_extra = logger.bind(component="http", method=request.method, path=path, params=f"[{request.query_params}]")
        log_extra.info("收到请求. ")

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_extra = log_extra.bind(
                component="http",
                code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
                log_extra.error(f"请求处理异常")
            elif response.status_code >= status.HTTP_400_BAD_REQUEST:
                log_extra.warning(f"请求处理异常")
            else:
                log_extra.info("请求处理完成")
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_extra.bind(
                component="http",
                code=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            ).warning("请求处理异常")
            raise exc
        finally:
            reset_log_context()
