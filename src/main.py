from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.config import settings

# 从新的 saas/ 目录中导入平台模块的 API 路由器
from src.saas.users import api as users_api
from src.saas.auth import api as auth_api
from src.saas.tenants import api as tenants_api
# from src.saas.subscriptions import api as subscriptions_api # 如果存在则取消注释

# 未来应用层的模块将从这里导入
# from src.app.profiles import api as profiles_api

from src.core.logging import get_logger, init_logging_from_env
from src.core.exceptions import BaseAPIException
init_logging_from_env()

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加自定义异常处理器
@app.exception_handler(BaseAPIException)
async def custom_exception_handler(request: Request, exc: BaseAPIException):
    """处理自定义API异常"""
    logger.error(
        f"API异常: {exc.message}",
        extra={
            'extra_info': {
                'error_code': exc.error_code,
                'status_code': exc.status_code,
                'path': request.url.path,
                'method': request.method,
                'details': exc.details
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    # 将错误信息转换为可序列化的格式
    serializable_errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
        }
        if "ctx" in error and error["ctx"]:
            # 将上下文中的异常对象转换为字符串
            ctx = {}
            for key, value in error["ctx"].items():
                if hasattr(value, '__str__'):
                    ctx[key] = str(value)
                else:
                    ctx[key] = value
            serializable_error["ctx"] = ctx
        serializable_errors.append(serializable_error)
    
    logger.warning(
        f"请求验证失败: {request.url.path}",
        extra={
            'extra_info': {
                'path': request.url.path,
                'method': request.method,
                'errors': serializable_errors
            }
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "请求数据验证失败",
            "error_code": "VALIDATION_ERROR",
            "errors": serializable_errors
        }
    )

# --- 插入“平台”模块的路由 ---
# 这是将模块功能“插入”主应用的关键步骤
app.include_router(auth_api.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(users_api.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(tenants_api.router, prefix=f"{settings.API_V1_STR}/tenants", tags=["Tenants"])
# app.include_router(subscriptions_api.router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["Subscriptions"])


# --- 插入“应用”模块的路由 ---
# app.include_router(profiles_api.router, prefix=f"{settings.API_V1_STR}/profiles", tags=["Profiles"])


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
