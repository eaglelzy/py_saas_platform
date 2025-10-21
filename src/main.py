from fastapi import FastAPI
from src.core.config import settings

# 从新的 saas/ 目录中导入平台模块的 API 路由器
from src.saas.users import api as users_api
from src.saas.auth import api as auth_api
from src.saas.tenants import router as tenants_router
# from src.saas.subscriptions import api as subscriptions_api # 如果存在则取消注释

# 未来应用层的模块将从这里导入
# from src.app.profiles import api as profiles_api

from src.core.logging import get_logger, init_logging_from_env
init_logging_from_env()

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- 插入“平台”模块的路由 ---
# 这是将模块功能“插入”主应用的关键步骤
app.include_router(auth_api.router, prefix=settings.API_V1_STR, tags=["Auth"])
app.include_router(users_api.router, prefix=settings.API_V1_STR, tags=["Users"])
app.include_router(tenants_router, prefix=settings.API_V1_STR, tags=["Tenants"])
# app.include_router(subscriptions_api.router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["Subscriptions"])


# --- 插入“应用”模块的路由 ---
# app.include_router(profiles_api.router, prefix=f"{settings.API_V1_STR}/profiles", tags=["Profiles"])


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
