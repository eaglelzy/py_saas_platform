"""Tenant context middleware to reset context per request."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config.settings import settings
from app.core.logging import logger
from app.core.tenancy.context import TenantContext


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Ensure tenant context (ContextVar) is reset between requests."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = str(request.url.path)
        api_prefix = settings.api_v1_prefix
        TenantContext.reset()
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            TenantContext.set_active_tenant_id(tenant_header)
            logger.bind(component="tenant_context", tenant_id=tenant_header).debug("请求头设置租户上下文")

        if not path.startswith(api_prefix):
            response = await call_next(request)
            TenantContext.reset()
            return response

        try:
            response = await call_next(request)
            return response
        finally:
            TenantContext.reset()


__all__ = ("TenantContextMiddleware",)
