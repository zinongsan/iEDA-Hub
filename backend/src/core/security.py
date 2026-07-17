"""密码哈希与 JWT 令牌相关工具"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# 优先使用 bcrypt（生产推荐），若运行环境没有 bcrypt（例如 Python 3.14 暂未提供 wheel），
# 自动降级到内置 pbkdf2_sha256，保持代码可运行。
try:
    import bcrypt  # noqa: F401
    # passlib 1.7.4 加载 bcrypt 后端时会读 bcrypt.__about__.__version__，
    # 而 bcrypt 4.x 移除了 __about__，导致每次哈希都打印 AttributeError 告警。
    # 这里补一个 shim 消除噪音（哈希/校验功能不受影响）。
    if not hasattr(bcrypt, "__about__"):
        import types
        bcrypt.__about__ = types.SimpleNamespace(__version__=getattr(bcrypt, "__version__", "4.x"))
    pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
except ImportError:
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(subject: str | int, expires_delta: timedelta, token_type: str, extra: dict | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
        "jti": uuid.uuid4().hex,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
        extra,
    )


def create_refresh_token(subject: str | int) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def token_ttl(payload: dict) -> int:
    """根据 token payload 计算剩余有效期(秒)，用于黑名单 TTL；过期返回 0。"""
    exp = payload.get("exp", 0)
    try:
        ttl = int(exp - datetime.now(timezone.utc).timestamp())
    except (TypeError, ValueError):
        return 0
    return max(ttl, 0)
