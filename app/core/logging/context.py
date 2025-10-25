"""日志上下文工具，基于 ContextVar 注入请求范围的租户/用户信息。"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Dict

# 通过 ContextVar 保存请求范围的上下文，默认值使用 "-" 代表未知
_tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="-")
_user_id_var: ContextVar[str] = ContextVar("user_id", default="-")
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def set_log_context(*, tenant_id: str | None = None, user_id: str | None = None, request_id: str | None = None) -> None:
    """更新当前协程的日志上下文，在认证或路由处理中调用。

    Args:
        tenant_id: 当前请求关联的租户标识。
        user_id: 当前请求关联的用户标识。
        request_id: 当前请求生成的追踪 ID。
    """

    if tenant_id is not None:
        _tenant_id_var.set(tenant_id)
    if user_id is not None:
        _user_id_var.set(user_id)
    if request_id is not None:
        _request_id_var.set(request_id)


def get_log_context() -> Dict[str, Any]:
    """读取当前协程内保存的日志上下文。"""

    return {
        "tenant_id": _tenant_id_var.get(),
        "user_id": _user_id_var.get(),
        "request_id": _request_id_var.get(),
    }


def reset_log_context() -> None:
    """重置日志上下文，避免跨请求数据串联。"""

    _tenant_id_var.set("-")
    _user_id_var.set("-")
    _request_id_var.set("-")
