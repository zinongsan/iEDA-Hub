"""用户业务逻辑"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import hash_password, verify_password
from ..models.user import User, UserTier


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        # 统一小写后查询：create() 会把 email 存为小写，这里也要小写，
        # 否则注册时用大小写不同的邮箱会绕过去重、撞唯一约束导致 500。
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        """根据手机号查询用户"""
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        username: str,
        password: str,
        phone: str | None = None,
        tier: UserTier = UserTier.NORMAL,
        is_admin: bool = False,
    ) -> User:
        user = User(
            email=email.lower(),
            username=username,
            hashed_password=hash_password(password),
            phone=phone,
            tier=tier,
            is_admin=is_admin,
            password_changed_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        """按邮箱或用户名查找用户（用于支持两种登录方式）"""
        ident = identifier.strip()
        # 邮箱通常包含 @，先按邮箱匹配；否则按用户名匹配；都没匹配再 OR 兜底
        if "@" in ident:
            result = await self.db.execute(select(User).where(User.email == ident.lower()))
        else:
            result = await self.db.execute(select(User).where(User.username == ident))
        user = result.scalar_one_or_none()
        if user:
            return user
        # 兜底：用 OR 再查一次（避免邮箱字段恰好是无 @ 的用户名情况）
        from sqlalchemy import or_
        result = await self.db.execute(
            select(User).where(or_(User.email == ident.lower(), User.username == ident))
        )
        return result.scalar_one_or_none()

    async def authenticate(self, identifier: str, password: str) -> User | None:
        """通过 邮箱 或 用户名 进行认证"""
        user = await self.get_by_email_or_username(identifier)
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        return user

    async def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        if not verify_password(old_password, user.hashed_password):
            return False
        await self.set_password(user, new_password)
        return True

    async def set_password(self, user: User, new_password: str) -> None:
        """直接设置新密码（忘记密码重置用）。更新 password_changed_at 使旧令牌失效。"""
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.db.commit()
