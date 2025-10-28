"""创建或更新平台超级管理员账号。

执行方式：
    uvicorn 运行环境中：`python scripts/create_superuser.py`
依赖环境变量：
    SUPERUSER_EMAIL
    SUPERUSER_PASSWORD
    SUPERUSER_DISPLAY_NAME (可选)
    SUPERUSER_PHONE (可选)
    SUPERUSER_TIMEZONE (可选，默认 Asia/Shanghai)
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

# 将项目根目录加入 sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.saas.db.session import SessionLocal  # noqa: E402
from app.saas.models.user import User  # noqa: E402
from app.saas.core.security.password import get_password_hash  # noqa: E402


def get_env(name: str, *, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"缺少环境变量 {name}")
    return value or ""


def main() -> None:
    email = get_env("SUPERUSER_EMAIL")
    password = get_env("SUPERUSER_PASSWORD")
    display_name = get_env("SUPERUSER_DISPLAY_NAME", required=False, default="Platform Admin")
    phone = get_env("SUPERUSER_PHONE", required=False)
    timezone = get_env("SUPERUSER_TIMEZONE", required=False, default="Asia/Shanghai")

    db: Session = SessionLocal()
    try:
        stmt = select(User).where(User.email == email)
        user = db.execute(stmt).scalars().first()
        hashed_password = get_password_hash(password)
        if user:
            user.hashed_password = hashed_password
            user.display_name = display_name
            user.phone_number = phone
            user.timezone = timezone
            user.is_superuser = True
            user.is_active = True
            db.add(user)
            action = "update"
        else:
            user = User(
                email=email,
                hashed_password=hashed_password,
                display_name=display_name,
                phone_number=phone,
                timezone=timezone,
                is_superuser=True,
                is_active=True,
            )
            db.add(user)
            action = "create"

        db.commit()
        print(f"Superuser {action}d successfully: {email}")
    except Exception as exc:
        db.rollback()
        raise RuntimeError("创建超级管理员失败") from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
