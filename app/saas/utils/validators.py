"""常用字段校验工具。"""

from __future__ import annotations

import re
from typing import Pattern


SLUG_PATTERN: Pattern[str] = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# PHONE_PATTERN: Pattern[str] = re.compile(r"^[0-9+\-()\s]{5,32}$")
# 中国手机号正则（支持三大运营商）
CHINESE_PHONE_PATTERN: Pattern[str] = re.compile(r"^1[3-9]\d{9}$")
PASSWORD_PATTERN: Pattern[str] = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*()_+\-=]{8,128}$")


def validate_slug(value: str) -> str:
    """校验租户 Slug，要求小写字母/数字/连字符。"""

    normalized = value.strip().lower()
    if not SLUG_PATTERN.match(normalized):
        raise ValueError("Slug 仅允许小写字母、数字和连字符，且以字母或数字开头和结尾")
    return normalized


def validate_phone(value: str) -> str:
    """校验手机号或电话。"""

    candidate = value.strip()
    if not CHINESE_PHONE_PATTERN.match(candidate):
        raise ValueError("手机号格式不正确，请输入正确的11位手机号")
    return candidate


def validate_password(value: str) -> str:
    """校验密码强度（至少8位，包含字母与数字）。"""

    candidate = value.strip()
    if not PASSWORD_PATTERN.match(candidate):
        raise ValueError("密码需包含字母与数字，长度8-128")
    return candidate
