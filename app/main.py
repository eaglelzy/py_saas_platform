"""FastAPI 应用入口。"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import api_router
from app.core.config.settings import settings
from app.core.logging import RequestLoggingMiddleware, configure_logging, logger
from app.core.tenancy import TenantContextMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import (
    service_error_handler,
    generic_error_handler,
    request_validation_error_handler,
)
from app.services.exceptions import ServiceError

configure_logging()


def create_app() -> FastAPI:
    """创建并配置 FastAPI 实例。"""

    app = FastAPI(
        title=settings.project_name,
        debug=settings.fast_api_debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    # 挂载请求日志中间件，统一注入 Request ID 并输出访问日志
    app.add_middleware(TenantContextMiddleware)
    # app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(ServiceError, service_error_handler)
    # app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    logger.bind(component="bootstrap").info("FastAPI app initialized")
    return app


app = create_app()
