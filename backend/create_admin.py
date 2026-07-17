"""一次性脚本：创建或更新管理员账户"""
import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from src.core.config import settings
from src.db.base import *  # noqa: F401, F403 - 触发所有模型注册
from src.db.session import get_async_session_factory
from src.models.user import User, UserTier
from src.core.security import hash_password


# 管理员账号统一来自 settings（即 .env），与 src/main.py 的 _init_data 保持一致，
# 避免“两套密码”问题。改密码请改 .env 的 ADMIN_EMAIL/ADMIN_PASSWORD 后重跑本脚本。
EMAIL = settings.ADMIN_EMAIL
USERNAME = "admin"
PASSWORD = settings.ADMIN_PASSWORD


async def main() -> int:
    async with get_async_session_factory()() as db:
        existing = (
            await db.execute(select(User).where(User.email == EMAIL))
        ).scalar_one_or_none()

        if existing:
            existing.hashed_password = hash_password(PASSWORD)
            existing.is_admin = True
            existing.is_active = True
            existing.tier = UserTier.PREMIUM
            existing.email_verified = True
            existing.password_changed_at = datetime.now(timezone.utc)
            await db.commit()
            print(f"[OK] 已更新管理员账户 id={existing.id} email={EMAIL}")
        else:
            user = User(
                email=EMAIL,
                username=USERNAME,
                hashed_password=hash_password(PASSWORD),
                tier=UserTier.PREMIUM,
                is_admin=True,
                is_active=True,
                email_verified=True,
                password_changed_at=datetime.now(timezone.utc),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"[OK] 已创建管理员账户 id={user.id} email={EMAIL} username={USERNAME}")

    print(f"[OK] 登录信息: email={EMAIL}  password={PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
