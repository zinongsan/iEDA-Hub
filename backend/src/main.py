"""FastAPI 应用入口"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
try:
    from slowapi.errors import RateLimitExceeded
    _HAS_SLOWAPI = True
except ImportError:
    RateLimitExceeded = Exception  # type: ignore
    _HAS_SLOWAPI = False
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .api.router import api_router
from .core.config import settings
from .core.ratelimit import limiter
from .core.security import decode_token, hash_password
from .db.base import Base  # noqa: F401 - 触发模型注册
from .db.redis_client import close_redis, ensure_redis, get_redis
from .db.session import get_engine, get_async_session_factory, reset_engine
from .models.group import Group
from .models.user import User, UserTier


async def _init_data() -> None:
    """启动时确保默认管理员和默认用户组存在（幂等，多 worker 并发安全）。

    使用 ON CONFLICT DO NOTHING，避免多 worker 同时启动时
    select-then-insert 导致的 UniqueViolation。
    兼容 PostgreSQL 与 SQLite（测试用）。
    """
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")

    def _conflict_insert(model, values, conflict_col):
        """根据数据库方言返回 ON CONFLICT DO NOTHING 语句。"""
        if is_sqlite:
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            return sqlite_insert(model).values(**values).on_conflict_do_nothing(index_elements=[conflict_col])
        return pg_insert(model).values(**values).on_conflict_do_nothing(index_elements=[conflict_col])

    async with get_async_session_factory()() as db:
        # 默认两个用户组
        for name, tier, desc in [
            ("普通组", UserTier.NORMAL, "普通用户默认所在组"),
            ("高级组", UserTier.PREMIUM, "高级用户组，享受所有高级功能"),
        ]:
            await db.execute(_conflict_insert(Group, {"name": name, "tier": tier, "description": desc}, "name"))
        await db.commit()

        # 默认管理员（email 唯一）
        admin_pwd_hash = await asyncio.to_thread(hash_password, settings.ADMIN_PASSWORD)
        await db.execute(_conflict_insert(User, {
            "email": settings.ADMIN_EMAIL,
            "username": "admin",
            "hashed_password": admin_pwd_hash,
            "tier": UserTier.PREMIUM,
            "is_admin": True,
            "is_active": True,
            "email_verified": True,
            "password_changed_at": datetime.now(timezone.utc),
        }, "email"))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化默认数据；建表由 alembic upgrade head 完成（见 compose 启动命令）。
    # 不再用 Base.metadata.create_all，避免与 alembic 迁移历史冲突 / 掩盖遗漏的迁移。
    await ensure_redis()
    await _init_data()
    yield
    await close_redis()
    engine = get_engine()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 加速：开启 gzip 压缩（对 HTML/CSS/JS/JSON 平均压缩率 70%+） ----------
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=512, compresslevel=6)


# ---------- 加速：为静态资源添加缓存与 ETag 头 ----------
from starlette.middleware.base import BaseHTTPMiddleware


class StaticCacheMiddleware(BaseHTTPMiddleware):
    """给静态资源（css/js/png/jpg/svg/woff）加上长缓存头"""
    _STATIC_EXTS = (".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".gif",
                    ".woff", ".woff2", ".ttf", ".ico", ".webp")

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path.lower()
        if path.endswith(self._STATIC_EXTS):
            # 静态资源缓存 1 天，stale-while-revalidate 7 天
            response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
        elif path.endswith(".html"):
            # HTML 不缓存（每次校验），避免登录态过期
            response.headers["Cache-Control"] = "no-cache"
        return response


app.add_middleware(StaticCacheMiddleware)


# ---------- 安全响应头：CSP / 防点击劫持 / nosniff / Referrer-Policy / HSTS(仅HTTPS) ----------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """统一注入安全响应头。

    - CSP: connect-src 'self' 可阻断 XSS 把数据外泄到第三方域；frame-ancestors 'self' 防点击劫持。
      iedahub 为内联脚本单体，script-src 暂需 'unsafe-inline'（待模块化重构后收紧为 nonce/hash）。
    - HSTS 仅在 HTTPS 下下发（HTTP 下浏览器本就忽略）。
    """
    _CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = self._CSP
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)


if _HAS_SLOWAPI:
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(status_code=429, content={"detail": "请求过于频繁，请稍后再试"})


@app.get("/health")
async def health():
    """健康检查：探测 DB 与 Redis。ok 返回 200，降级返回 503。"""
    checks: dict = {"status": "ok"}
    try:
        async with get_async_session_factory()() as db:
            await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {type(e).__name__}"
        checks["status"] = "degraded"
    try:
        await get_redis().ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"
        checks["status"] = "degraded"
    return JSONResponse(checks, status_code=200 if checks["status"] == "ok" else 503)


app.include_router(api_router)

# 静态文件服务（替代 Nginx）
import os as _os
from fastapi.responses import HTMLResponse

_STATIC_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "frontend")
_MAIN_HTML = _os.path.join(_STATIC_DIR, "iedahub.html")
_LOGIN_HTML = _os.path.join(_STATIC_DIR, "login.html")
_REGISTER_HTML = _os.path.join(_STATIC_DIR, "register.html")
_COMPLETE_PROFILE_HTML = _os.path.join(_STATIC_DIR, "complete-profile.html")
_PROFILE_HTML = _os.path.join(_STATIC_DIR, "profile.html")
_ADMIN_HTML = _os.path.join(_STATIC_DIR, "admin.html")
_FORGOT_HTML = _os.path.join(_STATIC_DIR, "forgot-password.html")
_RESET_HTML = _os.path.join(_STATIC_DIR, "reset-password.html")
_VERIFY_HTML = _os.path.join(_STATIC_DIR, "verify-email.html")
_AUTH_SCRIPT = '<script src="/frontend/assets/js/auth-guard.js"></script>'


async def _is_authed(request: Request) -> bool:
    """服务端登录态探测：access_token cookie 能解码、未拉黑即视为已登录。

    仅用于受保护页面的"是否下发 HTML 壳"判断；真正的鉴权仍由 API（get_current_user）做。
    不查 DB，避免每个页面加载都打库；账号被禁用等会在客户端 /users/me 二次校验时拦截。
    """
    token = request.cookies.get("access_token")
    if not token:
        return False
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return False
    try:
        if await get_redis().get(f"blacklist:{token}"):
            return False
    except Exception:
        pass
    return True


def _inject_auth_guard(html: str) -> str:
    """在受保护页面中注入：CDN 本地化 + 鉴权脚本"""
    # 1. 把 FontAwesome cdnjs 替换为本地资源（避免 Windows 客户端跨网拉取慢）
    html = html.replace(
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css",
        "/frontend/assets/vendor/fontawesome/all.min.css",
    )
    # 2. 注入鉴权脚本到 </body> 前
    if _AUTH_SCRIPT not in html:
        if "</body>" in html:
            html = html.replace("</body>", _AUTH_SCRIPT + "\n</body>", 1)
        else:
            html += _AUTH_SCRIPT
    return html


def _serve_html(path: str) -> HTMLResponse:
    """读取并返回指定 HTML 文件"""
    if not _os.path.isfile(path):
        return HTMLResponse("<h1>Page not found</h1>", status_code=404)
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ---------- 干净 URL 路由（不带 .html 后缀） ----------
@app.get("/login", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    return _serve_html(_LOGIN_HTML)


@app.get("/register", response_class=HTMLResponse)
async def register_page() -> HTMLResponse:
    return _serve_html(_REGISTER_HTML)


@app.get("/complete-profile", response_class=HTMLResponse)
async def complete_profile_page() -> HTMLResponse:
    return _serve_html(_COMPLETE_PROFILE_HTML)


@app.get("/profile", response_class=HTMLResponse)
async def profile_page() -> HTMLResponse:
    return _serve_html(_PROFILE_HTML)


@app.get("/logs", response_class=HTMLResponse)
async def logs_page() -> HTMLResponse:
    """操作日志页面"""
    logs_html = _os.path.join(_STATIC_DIR, "logs.html")
    if not _os.path.isfile(logs_html):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "logs.html not found")
    with open(logs_html, encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/admin", response_class=HTMLResponse)
async def admin_page() -> HTMLResponse:
    return _serve_html(_ADMIN_HTML)


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page() -> HTMLResponse:
    return _serve_html(_FORGOT_HTML)


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page() -> HTMLResponse:
    return _serve_html(_RESET_HTML)


@app.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page() -> HTMLResponse:
    return _serve_html(_VERIFY_HTML)


@app.get("/app/iedahub", response_class=HTMLResponse)
async def iedahub_page(request: Request) -> HTMLResponse:
    """返回 iedahub.html 并注入鉴权脚本（服务端登录态拦截，未登录跳登录页）"""
    if not await _is_authed(request):
        return RedirectResponse(url="/login?next=/app/iedahub", status_code=302)
    if not _os.path.isfile(_MAIN_HTML):
        return HTMLResponse("<h1>iedahub.html not found</h1>", status_code=404)
    with open(_MAIN_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(_inject_auth_guard(html))


# ---------- 兼容旧 .html 路由（重定向到干净 URL） ----------
@app.get("/frontend/login.html")
async def login_redirect():
    return RedirectResponse(url="/login", status_code=301)


@app.get("/frontend/register.html")
async def register_redirect():
    return RedirectResponse(url="/register", status_code=301)


@app.get("/frontend/profile.html")
async def profile_redirect():
    return RedirectResponse(url="/profile", status_code=301)


@app.get("/frontend/admin.html")
async def admin_redirect():
    return RedirectResponse(url="/admin", status_code=301)


@app.get("/app/iedahub.html")
async def iedahub_redirect():
    return RedirectResponse(url="/app/iedahub", status_code=301)


@app.get("/app/iedahub_vip")
async def iedahub_vip_redirect():
    return RedirectResponse(url="/app/iedahub?page=pricing", status_code=301)


@app.get("/terms")
async def terms_page():
    """用户服务协议"""
    terms_file = Path(_STATIC_DIR) / "terms.html"
    if terms_file.exists():
        return FileResponse(terms_file)
    return HTMLResponse(content="<h1>协议文件未找到</h1>", status_code=404)


@app.get("/privacy")
async def privacy_page():
    """用户隐私协议"""
    privacy_file = Path(_STATIC_DIR) / "privacy.html"
    if privacy_file.exists():
        return FileResponse(privacy_file)
    return HTMLResponse(content="<h1>协议文件未找到</h1>", status_code=404)


@app.get("/app/iedahub_vip.html")
async def iedahub_vip_html_redirect():
    return RedirectResponse(url="/app/iedahub?page=pricing", status_code=301)


if _os.path.isdir(_STATIC_DIR):
    app.mount("/frontend", StaticFiles(directory=_STATIC_DIR, html=True), name="frontend")
    # 受保护页面挂载到 /app/ 路径下
    app.mount("/app", StaticFiles(directory=_STATIC_DIR, html=True), name="app")

# 挂载上传文件目录
from pathlib import Path as _Path
uploads_dir = _Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/")
async def root():
    return RedirectResponse(url="/login")
