# src/core/config.py

import os
from typing import List, Union

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    应用配置管理类。
    """

    # --- 核心项目配置 ---
    PROJECT_NAME: str = "Python SaaS Platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # --- 数据库配置 ---
    DATABASE_URL: str

    # --- 安全与认证配置 (JWT) ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # --- CORS (跨域资源共享) 配置 ---
    # [修改] 将类型从 List[AnyHttpUrl] 改为 List[str] 以允许 '*'
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # [新增] 告诉 Pydantic 忽略 .env 文件中未在上面定义的额外变量
        extra = 'ignore'

# 创建一个全局可用的 settings 实例
settings = Settings()