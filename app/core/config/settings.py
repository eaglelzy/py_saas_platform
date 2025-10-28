"""应用配置加载模块。"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """读取环境变量并提供默认配置。"""

    # 基础信息配置
    project_name: str = Field("SaaS Platform API", description="项目名称")
    api_v1_prefix: str = Field("/api/v1", description="API 版本前缀")

    # 运行时参数
    debug: bool = Field(False, description="是否开启调试模式")
    fast_api_debug: bool = Field(False, description="是否开启 FastAPI 调试模式")
    environment: str = Field("development", description="当前运行环境")
    log_level: str = Field("INFO", description="日志级别")

    # 数据库与中间件
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/saas_platform_dev",
        description="数据库连接串",
    )
    redis_url: str = Field("redis://localhost:6379/0", description="Redis 连接串")
    rabbitmq_url: str = Field("amqp://guest:guest@localhost:5672/", description="RabbitMQ 连接串")

    # 身份认证配置
    jwt_secret_key: str = Field("dev-secret-key", description="JWT 签名密钥")
    jwt_algorithm: str = Field("HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(60, description="Access Token 过期时间（分钟）")
    refresh_token_expire_days: int = Field(7, description="Refresh Token 过期时间（天）")

    # 业务参数
    rate_limit_per_minute: int = Field(120, description="每分钟请求限流阈值")
    invite_token_expire_hours: int = Field(48, description="邀请链接过期时间（小时）")
    activation_token_expire_hours: int = Field(48, description="账号激活链接过期时间（小时）")
    frontend_activation_url: str = Field("http://localhost:3000/activate", description="前端激活链接基础 URL")
    frontend_password_reset_url: str = Field("http://localhost:3000/reset-password", description="前端密码重置链接基础 URL")
    frontend_invitation_url: str = Field("http://localhost:3000/invitations/accept", description="前端成员邀请接受链接基础 URL")
    default_owner_permissions: tuple[str, ...] = Field(("tenant:member:manage", "tenant:subscription:manage", "tenant:setting:view"), description="Owner 默认权限")
    default_admin_permissions: tuple[str, ...] = Field(("tenant:member:manage", "tenant:setting:view"), description="Admin 默认权限")
    default_member_permissions: tuple[str, ...] = Field(("tenant:setting:view",), description="普通成员默认权限")
    permission_cache_ttl_seconds: int = Field(15 * 60, description="租户权限缓存时长（秒）")

    # CORS 配置
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="CORS 允许的源列表"
    )

    # 监控端点
    prometheus_endpoint: str = Field("http://localhost:9090", description="Prometheus 地址")
    grafana_endpoint: str = Field("http://localhost:3000", description="Grafana 地址")

    # Pydantic 设置类配置
    model_config = SettingsConfigDict(
        case_sensitive=False,  # 允许通过大写环境变量注入配置
        env_file=os.getenv("ENV_FILE", "env/.env.development"),
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未声明的环境变量以提升兼容性
    )


@lru_cache()
def get_settings() -> Settings:
    """使用缓存避免重复实例化设置对象。"""

    return Settings()  # type: ignore[call-arg]


settings: Settings = get_settings()
