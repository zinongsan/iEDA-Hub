"""基于 slowapi 的限流（背后用 Redis 共享计数）。
若环境未安装 slowapi（例如 Python 3.14 暂无 wheel），则降级为 no-op，
保持代码可运行。生产环境强烈建议安装 slowapi。"""
try:
    from slowapi import Limiter

    from .config import settings

    def _get_real_ip(request) -> str:
        """获取客户端真实 IP 用于限流。

        只有当“直连对端”是受信反代(settings.TRUSTED_PROXIES)时，才采用
        X-Forwarded-For / CF-Connecting-IP；否则一律用 request.client.host。
        这样在 uvicorn 直接对外（无反代）时，客户端无法通过伪造 XFF 头绕过限流。
        """
        peer = request.client.host if request.client else ""
        if peer and peer in settings.trusted_proxies:
            xff = request.headers.get("x-forwarded-for", "")
            if xff:
                # XFF 形如 "client, proxy1, proxy2"，取第一个（最原始客户端）
                return xff.split(",")[0].strip()
            cf = request.headers.get("cf-connecting-ip", "")
            if cf:
                return cf.strip()
        return peer or "unknown"

    limiter = Limiter(
        key_func=_get_real_ip,
        storage_uri=settings.REDIS_URL,
        strategy="fixed-window",
        swallow_errors=True,  # Redis 故障时 fail-open，避免限流把 register/login 打成 500
    )
except ImportError:  # pragma: no cover - 仅作降级
    class _NoopLimiter:
        def limit(self, *_args, **_kwargs):
            def _decorator(func):
                return func
            return _decorator

    limiter = _NoopLimiter()
