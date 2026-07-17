"""应用配置 - 通过 Pydantic Settings 从环境变量加载"""
import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _find_env_file() -> Path:
    """从本文件向上查找 .env，避免依赖 CWD。
    本文件位于 backend/src/core/config.py，向上可找到 app/.env。
    容器内通常没有 .env 文件（环境变量由 compose env_file 注入），找不到则回退 CWD 相对路径。"""
    p = Path(__file__).resolve().parent
    for _ in range(6):
        if (p / ".env").is_file():
            return p / ".env"
        if p.parent == p:
            break
        p = p.parent
    return Path(".env")


_ENV_FILE = _find_env_file()

# 已知的默认/弱密钥——生产环境禁止使用
_WEAK_SECRET_KEYS = {
    "dev-secret-key-please-override",
    "dev-secret-key-change-in-production-to-64-random-chars",
    "change-this-secret",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, case_sensitive=True, extra="ignore")

    # 应用
    APP_NAME: str = "iEDA-Hub"
    APP_ENV: Literal["development", "production", "test"] = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-please-override"

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/guochuang"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 管理员初始化
    ADMIN_EMAIL: str = "admin@guochuang.com"
    ADMIN_PASSWORD: str = "Admin@123456"

    # 限流
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"
    RATE_LIMIT_PASSWORD_RESET: str = "5/minute"   # 防止重置邮件被滥用
    RATE_LIMIT_RESEND_VERIFY: str = "3/minute"

    # 邮件 (SMTP) —— 用于邮箱验证 / 忘记密码发信
    SMTP_HOST: str = "smtp.feishu.cn"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""          # 例: iedahub@nctieda.com
    SMTP_PASSWORD: str = ""      # 飞书邮箱 SMTP 授权码
    SMTP_FROM: str = ""          # 发件人地址；留空则用 SMTP_USER
    SMTP_USE_SSL: bool = True    # 465 端口用 implicit SSL
    SMTP_TIMEOUT: int = 10

    # 邮件内链接的基础地址（用户从邮件点击链接跳转到这里）
    APP_BASE_URL: str = "http://localhost:8080"

    # 邮箱验证
    EMAIL_VERIFICATION_REQUIRED: bool = False   # true=未验证邮箱禁止登录
    VERIFY_TOKEN_TTL_MINUTES: int = 1440        # 验证链接有效期 24h
    RESET_TOKEN_TTL_MINUTES: int = 15           # 重置链接有效期 15min
    # 忘记密码 per-邮箱 限流（防邮件轰炸）：命中上限仍返回相同成功信息但不发信，
    # 既防重复发送，也把对同一邮箱的轰炸压到固定上限（不受攻击者 IP 数量影响）。
    RESET_EMAIL_COOLDOWN_SEC: int = 60          # 同一邮箱两次发信最小间隔
    RESET_EMAIL_HOUR_MAX: int = 3               # 同一邮箱每小时最多发信数
    RESET_EMAIL_DAY_MAX: int = 5                # 同一邮箱每天最多发信数

    # 受信反代 IP（逗号分隔）。仅当请求“直连对端”在此列表时才信任 X-Forwarded-For；
    # 当前 uvicorn 直接对外（无反代）应留空，限流按真实连接 IP 计，防止客户端伪造 XFF 绕过。
    TRUSTED_PROXIES: str = ""

    # CORS 允许来源（逗号分隔）；测试环境默认本机 8080
    ALLOWED_ORIGINS: str = "http://192.168.99.151:8080,http://localhost:8080"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def trusted_proxies(self) -> set[str]:
        return {p.strip() for p in self.TRUSTED_PROXIES.split(",") if p.strip()}

    @property
    def cookie_secure(self) -> bool:
        """仅生产(HTTPS)环境给 cookie 加 secure 标记；HTTP 测试环境不加，否则浏览器不存。"""
        return self.APP_ENV == "production"

    @property
    def smtp_from(self) -> str:
        """发件人地址：优先 SMTP_FROM，否则回退 SMTP_USER。"""
        return self.SMTP_FROM or self.SMTP_USER

    @property
    def smtp_configured(self) -> bool:
        """是否配置了 SMTP（未配置时邮件服务降级为 Noop，不报错）。"""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    # ==================== 短信服务配置 ====================
    SMS_PROVIDER: str = "noop"  # 短信服务商: noop/aliyun/tencent

    # 阿里云短信配置
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = ""
    ALIYUN_SMS_TEMPLATE_CODE: str = ""

    # 腾讯云短信配置
    TENCENT_SECRET_ID: str = ""
    TENCENT_SECRET_KEY: str = ""
    TENCENT_SMS_APP_ID: str = ""
    TENCENT_SMS_SIGN_NAME: str = ""
    TENCENT_SMS_TEMPLATE_ID: str = ""


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # SECRET_KEY 校验：生产环境用弱/默认密钥直接拒启；非生产仅警告
    if s.SECRET_KEY in _WEAK_SECRET_KEYS:
        msg = (
            "SECRET_KEY 为已知默认值(%r)，存在 JWT 被伪造风险。"
            "请生成强随机密钥(如 python -c \"import secrets;print(secrets.token_urlsafe(48))\")写入 .env。"
            % s.SECRET_KEY
        )
        if s.APP_ENV == "production":
            raise RuntimeError(msg)
        logger.warning("[配置告警] %s (当前 APP_ENV=%s，仅警告不阻断启动)", msg, s.APP_ENV)
    return s


settings = get_settings()
