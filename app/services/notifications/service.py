"""通知服务，当前输出日志占位，后续可接入邮件或消息队列。"""

from __future__ import annotations

from typing import Optional

from app.core.logging import logger
from app.models.tenant import Tenant
from app.models.tenant_application import TenantApplication


class NotificationService:
    """封装站内信/邮件发送逻辑（占位实现）。"""

    def __init__(self) -> None:
        self._logger = logger.bind(component="notification")

    def send_application_approved(
        self,
        application: TenantApplication,
        tenant: Optional[Tenant] = None,
    ) -> None:
        """通知申请人租户审核通过。"""

        self._logger.warning(
            "租户申请审核通过，待接入邮件通知",
            application_id=str(application.id),
            company=application.company_name,
            tenant_id=str(getattr(tenant, "id", "")) if tenant else None,
        )

    def send_application_rejected(self, application: TenantApplication) -> None:
        """通知申请人租户审核被拒绝。"""

        self._logger.warning(
            "租户申请审核拒绝，待接入邮件通知",
            application_id=str(application.id),
            company=application.company_name,
        )
