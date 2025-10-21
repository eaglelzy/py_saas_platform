# src/core/exception_handlers.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.exceptions import BaseAPIException
from src.core.logging import get_logger

logger = get_logger(__name__)


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    处理自定义API异常
    
    Args:
        request: FastAPI请求对象
        exc: 自定义API异常
        
    Returns:
        JSONResponse: 统一格式的错误响应 {'msg': 'error'}
    """
    logger.error(
        f"API异常: {exc.message}",
        extra={
            'extra_info': {
                'error_code': exc.error_code,
                'status_code': exc.status_code,
                'path': str(request.url.path),
                'method': request.method,
                'details': exc.details
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "msg": exc.message
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    处理FastAPI HTTP异常
    
    Args:
        request: FastAPI请求对象
        exc: HTTP异常
        
    Returns:
        JSONResponse: 统一格式的错误响应 {'msg': 'error'}
    """
    logger.warning(
        f"HTTP异常: {exc.detail}",
        extra={
            'extra_info': {
                'status_code': exc.status_code,
                'path': str(request.url.path),
                'method': request.method
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "msg": str(exc.detail)
        }
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理Starlette HTTP异常
    
    Args:
        request: FastAPI请求对象
        exc: Starlette HTTP异常
        
    Returns:
        JSONResponse: 统一格式的错误响应 {'msg': 'error'}
    """
    logger.warning(
        f"Starlette HTTP异常: {exc.detail}",
        extra={
            'extra_info': {
                'status_code': exc.status_code,
                'path': str(request.url.path),
                'method': request.method
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "msg": str(exc.detail)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证异常
    
    Args:
        request: FastAPI请求对象
        exc: 验证异常
        
    Returns:
        JSONResponse: 统一格式的错误响应 {'msg': 'error'}
    """
    logger.warning(
        f"请求验证失败: {exc.errors()}",
        extra={
            'extra_info': {
                'path': str(request.url.path),
                'method': request.method,
                'validation_errors': exc.errors()
            }
        }
    )
    
    # 提取第一个验证错误作为主要错误信息
    first_error = exc.errors()[0] if exc.errors() else {}
    error_msg = first_error.get('msg', '请求数据验证失败')
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "msg": error_msg
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理通用异常
    
    Args:
        request: FastAPI请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse: 统一格式的错误响应 {'msg': 'error'}
    """
    logger.error(
        f"未处理的异常: {str(exc)}",
        extra={
            'extra_info': {
                'path': str(request.url.path),
                'method': request.method,
                'exception_type': type(exc).__name__
            }
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "msg": "服务器内部错误"
        }
    )