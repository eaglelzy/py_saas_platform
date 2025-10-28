"""审计日志服务，负责持久化关键操作记录。"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.saas.core.logging import logger
from app.saas.models.audit_log import AuditLog


class AuditService:
    """记录关键业务操作审计日志。"""

    def __init__(self) -> None:
        self._logger = logger.bind(component="audit")

    def log_event(
        self,
        db: Session,
        *,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        action: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        """持久化审计事件，失败时退回日志记录。"""

        try:
            payload = metadata or {}
            record = AuditLog(
                user_id=_to_uuid(user_id),
                tenant_id=_to_uuid(tenant_id),
                action=action,
                payload=payload,
            )
            db.add(record)
            db.commit()
        except Exception as exc:  # noqa: BLE001 - 捕获所有异常写日志
            db.rollback()
            event_time = datetime.now(timezone.utc).isoformat()
            self._logger.error(
                "审计日志写入失败",
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                metadata=metadata or {},
                event_time=event_time,
                error=str(exc),
            )


def _to_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None
