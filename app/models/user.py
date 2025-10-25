"""用户模型定义，存储平台内的基础用户信息。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    """平台用户表，记录登录身份与基础属性。"""

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="用户主键，使用 UUID 确保跨系统唯一",
    )
    email = Column(String(320), unique=True, nullable=False, comment="用户邮箱，作为登录凭据")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希，使用 PBKDF2 等算法")
    phone_number = Column(String(32), unique=True, comment="手机号，便于短信或多因素认证")
    display_name = Column(String(150), comment="展示名称，用于界面显示昵称")
    full_name = Column(String(150), comment="用户真实姓名或企业联系人姓名")
    avatar_url = Column(String(1024), comment="头像地址，指向对象存储或 CDN")
    is_active = Column(Boolean, nullable=False, default=True, comment="账户是否激活")
    is_superuser = Column(Boolean, nullable=False, default=False, comment="是否为平台管理员")
    is_locked = Column(Boolean, nullable=False, default=False, comment="是否因安全原因临时锁定")
    timezone = Column(String(64), default="UTC", nullable=False, comment="时区信息，便于通知与报表")
    password_updated_at = Column(DateTime(timezone=True), comment="最后一次修改密码时间")
    failed_login_attempts = Column(Integer, nullable=False, default=0, comment="连续登录失败次数")
    last_failed_login_at = Column(DateTime(timezone=True), comment="最近一次登录失败时间")
    last_login_at = Column(DateTime(timezone=True), comment="最后一次登录时间")

    def __repr__(self) -> str:
        """返回调试友好的字符串表示。"""

        return f"<User id={self.id} email={self.email}>"
