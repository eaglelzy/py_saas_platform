"""通知服务，当前输出日志占位，后续可接入邮件或消息队列。"""

from __future__ import annotations

from typing import Optional

from app.core.logging import logger
from app.core.config.settings import settings
from app.models.tenant import Tenant
from app.models.tenant_application import TenantApplication


class NotificationService:
    """封装站内信/邮件发送逻辑（占位实现）。"""

    def __init__(self) -> None:
        self._logger = logger.bind(component="notification")

    def send_application_approved(
        self,
        application: TenantApplication,
        token: str,
        tenant: Optional[Tenant] = None,
        activation_url: str | None = None,
    ) -> None:
        """通知申请人租户审核通过。"""

        tenant_id = str(getattr(tenant, "id", "")) if tenant else None
        subject = "【SaaS 平台】租户审核通过通知"
        activation_url = activation_url or f"{settings.frontend_activation_url}?token={token}"
        body = (
            f"您好，{application.contact_name}：\n"
            f"\n"
            f"您提交的租户申请《{application.company_name}》已审核通过。"
            f"请使用账号 {application.contact_email} 登入平台并完成后续初始化。\n"
            f"请点击以下链接设置登录密码并激活账号：\n{activation_url}\n"
            f"\n如有疑问，请联系平台管理员。"
        )
        self._logger.warning(
            "租户申请审核通过（邮件占位）",
            application_id=str(application.id),
            company=application.company_name,
            tenant_id=tenant_id,
            subject=subject,
            activation_url=activation_url,
            token=token,
            body_preview=body[:200],
        )

    def send_application_rejected(self, application: TenantApplication) -> None:
        """通知申请人租户审核被拒绝。"""

        subject = "【SaaS 平台】租户审核结果通知"
        reason = application.rejection_reason or "请联系平台了解详情"
        body = (
            f"您好，{application.contact_name}：\n"
            f"\n"
            f"很抱歉，您提交的租户申请《{application.company_name}》未通过审核。"
            f"原因：{reason}\n"
            f"若需补充材料或申请复审，请联系平台管理员。"
        )
        self._logger.warning(
            "租户申请审核拒绝（邮件占位）",
            application_id=str(application.id),
            company=application.company_name,
            subject=subject,
            body_preview=body[:160],
        )

    def send_password_reset(self, *, email: str, reset_url: str) -> None:
        """发送密码重置邮件占位。"""

        subject = "【SaaS 平台】密码重置"
        body = (
            f"您好，\n\n我们收到您重置密码的请求。"
            f"如非本人操作，请忽略此邮件。\n"
            f"点击以下链接设置新的登录密码：\n{reset_url}\n"
            f"此链接将在 24 小时后失效。"
        )
        self._logger.warning(
            "密码重置通知（邮件占位）",
            email=email,
            reset_url=reset_url,
            subject=subject,
            body_preview=body[:200],
        )

    def send_member_invitation(self, *, email: str, invite_url: str, tenant_name: str, role: str) -> None:
        """发送成员邀请邮件占位。"""

        subject = "【SaaS 平台】加入租户邀请"
        body = (
            f"您好，\n\n您收到加入租户《{tenant_name}》的邀请，角色：{role}。\n"
            f"点击以下链接接受邀请并完成账号激活：\n{invite_url}\n"
            f"若不是本人操作，请忽略本邮件。"
        )
        self._logger.warning(
            "成员邀请通知（邮件占位）",
            email=email,
            invite_url=invite_url,
            subject=subject,
            body_preview=body[:200],
        )
