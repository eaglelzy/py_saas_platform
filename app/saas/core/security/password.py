"""密码哈希与校验工具。"""

from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Final

ALGORITHM: Final[str] = "pbkdf2_sha256"
ITERATIONS: Final[int] = 600_000
SALT_LENGTH: Final[int] = 16


def get_password_hash(password: str, *, iterations: int = ITERATIONS) -> str:
    """使用 PBKDF2-SHA256 生成密码哈希。"""

    if not password:
        raise ValueError("密码不能为空")
    salt = secrets.token_bytes(SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    encoded_salt = base64.b64encode(salt).decode("utf-8")
    encoded_hash = base64.b64encode(dk).decode("utf-8")
    return f"{ALGORITHM}${iterations}${encoded_salt}${encoded_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """验证密码是否匹配存储的哈希。"""

    try:
        algorithm, iter_str, encoded_salt, encoded_hash = stored_hash.split("$")
        if algorithm != ALGORITHM:
            return False
        iterations = int(iter_str)
        salt = base64.b64decode(encoded_salt)
        expected_hash = base64.b64decode(encoded_hash)
    except (ValueError, TypeError, base64.binascii.Error):
        return False

    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return secrets.compare_digest(new_hash, expected_hash)


__all__ = ("get_password_hash", "verify_password")
