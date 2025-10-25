"""系统级基础路由。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check() -> dict[str, str]:
    """返回 API 在线状态。"""

    return {"status": "ok"}
