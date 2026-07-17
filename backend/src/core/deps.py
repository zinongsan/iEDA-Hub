"""FastAPI 依赖注入 - 当前用户、权限校验"""
from datetime import timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.redis_client import get_redis
from ..db.session import get_db
from ..models.user import User, UserTier
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    # 兼容从 Authorization 头或 Cookie 中读取 token
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效或过期的令牌")

    # 黑名单校验（登出后失效）。Redis 不可用时 fail-open（放行），避免业务 500。
    try:
        if await get_redis().get(f"blacklist:{token}"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌已失效")
    except HTTPException:
        raise
    except Exception:
        pass

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号不存在或已禁用")
    # 改密码后令旧令牌失效
    reject_if_password_changed(payload, user)
    return user


def reject_if_password_changed(payload: dict, user: User) -> None:
    """改密码后令旧令牌失效：若令牌签发时间(iat)早于 password_changed_at，则拒绝。

    access 与 refresh 令牌均复用此校验（见 auth.refresh_token）。
    iat 是整秒（jose 编码时截断），这里也按整秒比较，避免同秒内 sub-second 精度误判。
    """
    pwd_changed = user.password_changed_at
    if pwd_changed is None:
        return
    ts = pwd_changed.timestamp()
    if pwd_changed.tzinfo is None:
        ts = pwd_changed.replace(tzinfo=timezone.utc).timestamp()
    if payload.get("iat", 0) < int(ts):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌已失效，请重新登录")


async def require_premium(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.tier != UserTier.PREMIUM and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要高级用户权限")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
PremiumUser = Annotated[User, Depends(require_premium)]
AdminUser = Annotated[User, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
