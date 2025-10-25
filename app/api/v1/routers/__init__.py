"""汇总 API v1 路由。"""

from fastapi import APIRouter

from .system import router as system_router
from .tenant_applications import router as tenant_applications_router
from .tenants import router as tenants_router
from .members import router as members_router
from .subscription_plans import router as subscription_plans_router
from .tenant_subscriptions import router as tenant_subscriptions_router
from .subscription_orders import router as subscription_orders_router

api_router = APIRouter()
api_router.include_router(system_router, prefix="/system", tags=["system"])
api_router.include_router(tenant_applications_router)
api_router.include_router(tenants_router)
api_router.include_router(members_router)
api_router.include_router(subscription_plans_router)
api_router.include_router(tenant_subscriptions_router)
api_router.include_router(subscription_orders_router)

__all__ = ("api_router",)
