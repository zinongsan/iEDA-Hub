"""认证路由：注册、登录、刷新、登出、邮箱验证、忘记/重置密码"""
import secrets
from io import BytesIO
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from captcha.image import ImageCaptcha

from ...core.config import settings
from ...core.deps import CurrentUser, DbSession, reject_if_password_changed
from ...core.email import send_reset_email, send_verification_email, send_email_code
from ...core.ratelimit import limiter
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    token_ttl,
)
from ...db.redis_client import get_redis
from ...schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from ...schemas.user import UserOut
from ...services.user_service import UserService
from ...services.log_service import LogService

router = APIRouter(prefix="/auth", tags=["auth"])

# Redis token 前缀（验证 / 重置），单次使用、自带 TTL
_VERIFY_PREFIX = "emailverify:"
_RESET_PREFIX = "pwreset:"


async def _blacklist_token(token: str) -> None:
    """将单个 token 加入 Redis 黑名单（按剩余有效期设 TTL）。失败时静默(fail-open)。"""
    if not token:
        return
    payload = decode_token(token)
    if not payload:
        return
    ttl = token_ttl(payload)
    if ttl > 0:
        try:
            await get_redis().setex(f"blacklist:{token}", ttl, "1")
        except Exception:
            # Redis 不可用时 fail-open：不阻塞登出
            pass


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    """下发 access / refresh / logged_in 三个 cookie。

    - access_token:  HttpOnly，后端 deps.py 读取用于鉴权。
    - refresh_token: HttpOnly，path 限定到 /api/v1/auth，仅 refresh/logout 接口可见。
    - logged_in:     非 HttpOnly，仅作前端“是否已登录”的 UI 判断（无安全敏感性），
                     因为 HttpOnly cookie 前端不可读，无法用它做客户端登录态判断。
    令牌不再返回到响应体，杜绝 XSS 读取；前端统一靠 cookie。
    """
    response.set_cookie(
        "access_token", access,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True, samesite="lax", secure=settings.cookie_secure,
    )
    response.set_cookie(
        "refresh_token", refresh,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True, samesite="lax", secure=settings.cookie_secure,
        path="/api/v1/auth",
    )
    response.set_cookie(
        "logged_in", "1",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=False, samesite="lax", secure=settings.cookie_secure,
    )


# ---------- 一次性 token（Redis）----------
async def _store_token(prefix: str, token: str, user_id: int, ttl_minutes: int) -> None:
    await get_redis().setex(f"{prefix}{token}", ttl_minutes * 60, str(user_id))


async def _consume_token(prefix: str, token: str) -> int | None:
    """取出并删除 token（单次使用）。返回 user_id 或 None（无效/过期/Redis故障）。"""
    try:
        r = get_redis()
        key = f"{prefix}{token}"
        val = await r.get(key)
        if not val:
            return None
        await r.delete(key)
    except Exception:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


async def _reset_email_throttled(email: str) -> bool:
    """忘记密码 per-邮箱 限流：命中冷却/小时/日上限则跳过发信（返回 True=被限流）。

    - 未被限流时顺带记账（INCR 计数 + 设冷却）。
    - 被限流的请求不计数，避免攻击者用大量请求把计数刷爆、锁死正常用户的重置。
    - Redis 故障时 fail-open（放行发信），不阻塞业务。
    """
    r = get_redis()
    e = email.lower()
    cooldown_key = f"pwreset:cooldown:{e}"
    hour_key = f"pwreset:hour:{e}"
    day_key = f"pwreset:day:{e}"
    cooldown = settings.RESET_EMAIL_COOLDOWN_SEC
    try:
        if cooldown > 0 and await r.get(cooldown_key):
            return True
        hour_n = int((await r.get(hour_key)) or 0)
        day_n = int((await r.get(day_key)) or 0)
        if hour_n >= settings.RESET_EMAIL_HOUR_MAX or day_n >= settings.RESET_EMAIL_DAY_MAX:
            return True
        # 放行：仅在实际发信时计数
        hn = await r.incr(hour_key)
        if hn == 1:
            await r.expire(hour_key, 3600)
        dn = await r.incr(day_key)
        if dn == 1:
            await r.expire(day_key, 86400)
        if cooldown > 0:
            await r.setex(cooldown_key, cooldown, "1")
    except Exception:
        return False  # Redis 故障 fail-open
    return False


# ---------- 图形验证码 ----------
@router.get("/captcha")
async def get_captcha():
    """
    生成图形验证码

    返回图片，并在响应头中返回captcha_id
    前端需要保存captcha_id，提交时一起发送
    """
    # 生成验证码ID和文本
    captcha_id = secrets.token_urlsafe(16)
    # 使用易识别的字符（排除0、O、I、l等）
    chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    captcha_text = ''.join(secrets.choice(chars) for _ in range(4))

    # 存储到Redis（5分钟过期）
    try:
        await get_redis().setex(f"captcha:{captcha_id}", 300, captcha_text)
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "验证码服务暂时不可用")

    # 生成图片
    image = ImageCaptcha(width=120, height=50, fonts=[])
    data = image.generate(captcha_text)

    return Response(
        content=data.getvalue(),
        media_type="image/png",
        headers={"X-Captcha-Id": captcha_id}
    )


async def _verify_captcha(captcha_id: str, captcha_code: str) -> bool:
    """验证验证码（不区分大小写）"""
    if not captcha_id or not captcha_code:
        return False
    key = f"captcha:{captcha_id}"
    try:
        stored = await get_redis().get(key)
        if not stored:
            return False
        # 一次性使用，验证后删除
        await get_redis().delete(key)
        return stored.decode().upper() == captcha_code.upper()
    except Exception:
        return False


# ---------- 邮箱验证码 ----------
@router.post("/send-email-code", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")  # 每分钟最多3次
async def send_email_verification_code(
    request: Request, email: str, bg: BackgroundTasks
) -> dict:
    """
    发送邮箱验证码（用于注册）

    - 生成6位数字验证码
    - 存储到Redis（5分钟过期）
    - 发送邮件
    - 60秒内不能重复发送
    """
    # 规范化邮箱地址（小写+去空格）
    email = email.strip().lower()

    # 检查是否60秒内已发送
    sent_key = f"email_code_sent:{email}"
    try:
        if await get_redis().get(sent_key):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "请60秒后再试")
    except HTTPException:
        raise
    except Exception:
        pass  # Redis故障不阻止发送

    # 生成6位数字验证码
    code = ''.join(secrets.choice('0123456789') for _ in range(6))

    # 存储到Redis（5分钟过期）
    try:
        await get_redis().setex(f"email_code:{email}", 300, code)
        # 设置60秒发送冷却
        await get_redis().setex(sent_key, 60, "1")
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "验证码服务暂时不可用")

    # 后台发送邮件
    bg.add_task(send_email_code, email, code)

    return {"message": "验证码已发送，请查收邮件"}


async def _verify_email_code(email: str, code: str) -> bool:
    """验证邮箱验证码"""
    import logging
    logger = logging.getLogger(__name__)

    if not email or not code:
        logger.error(f"验证码参数为空 - 邮箱: {email}, 验证码: {code}")
        return False
    # 规范化邮箱地址（小写+去空格）
    email = email.strip().lower()
    key = f"email_code:{email}"

    logger.info(f"验证验证码 - key: {key}, 输入验证码: {code}")

    try:
        r = get_redis()
        stored = await r.get(key)
        if not stored:
            logger.error(f"Redis中未找到验证码 - key: {key}")
            return False

        # 处理bytes或str类型
        stored_code = stored.decode() if isinstance(stored, bytes) else stored
        logger.info(f"Redis中的验证码: {stored_code}, 输入的验证码: {code.strip()}")

        # 验证成功才删除
        if stored_code == code.strip():
            await r.delete(key)  # 一次性使用
            logger.info("验证码验证成功")
            return True

        logger.error(f"验证码不匹配 - 存储: {stored_code}, 输入: {code.strip()}")
        return False
    except Exception as e:
        logger.error(f"验证码验证异常: {e}")
        return False


# ---------- 注册 ----------
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request, payload: RegisterRequest, db: DbSession, bg: BackgroundTasks
) -> UserOut:
    # 规范化邮箱
    email = payload.email.strip().lower()

    # 调试日志
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"注册请求 - 邮箱: {email}, 验证码: {payload.email_code}")

    # 验证邮箱验证码
    if not await _verify_email_code(email, payload.email_code):
        logger.error(f"验证码验证失败 - 邮箱: {email}, 输入验证码: {payload.email_code}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码错误或已过期，请重新获取")

    # 验证协议勾选
    if not payload.agree_terms:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请同意用户协议和隐私政策")

    svc = UserService(db)
    if await svc.get_by_email(email):
        raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已注册")
    if await svc.get_by_username(payload.username):
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已被占用")
    user = await svc.create(email=email, username=payload.username, password=payload.password)

    # 注释掉邮箱验证邮件，因为已经通过邮箱验证码验证过了
    # try:
    #     token = secrets.token_urlsafe(32)
    #     await _store_token(_VERIFY_PREFIX, token, user.id, settings.VERIFY_TOKEN_TTL_MINUTES)
    #     bg.add_task(send_verification_email, user.email, token)
    # except Exception:
    #     pass

    # 记录注册日志
    log_service = LogService(db)
    try:
        await log_service.log_register(
            user_id=user.id,
            email=user.email,
            username=user.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        # 日志记录失败不影响注册
        pass

    return UserOut.model_validate(user)


# ---------- 登录 ----------
@router.post("/login", response_model=UserOut)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request, payload: LoginRequest, db: DbSession, response: Response
) -> UserOut:
    svc = UserService(db)
    identifier = payload.identifier
    if not identifier:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "请提供邮箱或用户名")

    # 检查失败次数
    fail_key = f"login:fail:{identifier}"
    try:
        fail_count = int(await get_redis().get(fail_key) or 0)
    except Exception:
        fail_count = 0

    # 失败5次后锁定30分钟
    if fail_count >= 5:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "登录尝试次数过多，请30分钟后再试")

    # 失败3次后要求验证码
    if fail_count >= 3:
        if not await _verify_captcha(payload.captcha_id or "", payload.captcha_code or ""):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证码错误或已过期")

    # 验证用户
    user = await svc.authenticate(identifier, payload.password)
    if not user:
        # 登录失败，增加计数
        try:
            new_count = await get_redis().incr(fail_key)
            if new_count == 1:
                await get_redis().expire(fail_key, 1800)  # 30分钟
            remaining = 5 - new_count
            if remaining > 0:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"账号或密码错误，还剩{remaining}次机会")
            else:
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "登录尝试次数过多，请30分钟后再试")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号或密码错误")

    # 登录成功，清除失败计数
    try:
        await get_redis().delete(fail_key)
    except Exception:
        pass

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "邮箱未验证，请先查收验证邮件")

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # 记录登录日志
    log_service = LogService(db)
    try:
        await log_service.log_login(
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        # 日志记录失败不影响登录
        pass

    access = create_access_token(user.id, extra={"tier": user.tier.value, "admin": user.is_admin})
    refresh = create_refresh_token(user.id)
    # 令牌仅通过 HttpOnly cookie 下发，不再出现在响应体
    _set_auth_cookies(response, access, refresh)
    return UserOut.model_validate(user)


# ---------- 刷新 ----------
@router.post("/refresh", response_model=UserOut)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
async def refresh_token(
    request: Request, payload: RefreshRequest, db: DbSession, response: Response
) -> UserOut:
    # 浏览器走 HttpOnly cookie 时 body 为空，从 cookie 取 refresh
    refresh = payload.refresh_token or request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "缺少刷新令牌")
    data = decode_token(refresh)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的刷新令牌")
    # 校验 refresh token 是否已被拉黑（登出/轮换后失效）
    try:
        if await get_redis().get(f"blacklist:{refresh}"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "刷新令牌已失效")
    except HTTPException:
        raise
    except Exception:
        # Redis 不可用时 fail-open：放行刷新
        pass
    user_id = int(data["sub"])
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号不可用")
    # P0#1：改密后旧 refresh 同样失效（与 access 令牌一致的 iat 校验）
    reject_if_password_changed(data, user)
    access = create_access_token(user.id, extra={"tier": user.tier.value, "admin": user.is_admin})
    new_refresh = create_refresh_token(user.id)
    # 旧 refresh token 用完即拉黑，防止重复使用
    await _blacklist_token(refresh)
    # 轮换后重发 cookie
    _set_auth_cookies(response, access, new_refresh)
    return UserOut.model_validate(user)


# ---------- 登出 ----------
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    # 取 access（头或 cookie）与 refresh（body 或 cookie），一律拉黑并清 cookie。
    # 不强制鉴权：access 可能已过期，但 refresh 仍需被拉黑，确保登出真正失效。
    token = request.headers.get("authorization", "").removeprefix("Bearer ").strip() \
        or request.cookies.get("access_token", "")
    await _blacklist_token(token)
    try:
        body = await request.json()
    except Exception:
        body = None
    refresh = (body.get("refresh_token") if isinstance(body, dict) else None) \
        or request.cookies.get("refresh_token", "")
    await _blacklist_token(refresh)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    response.delete_cookie("logged_in")


# ---------- 邮箱验证 ----------
@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(payload: VerifyEmailRequest, db: DbSession) -> dict:
    user_id = await _consume_token(_VERIFY_PREFIX, payload.token)
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "验证链接无效或已过期")
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "账号不存在")
    user.email_verified = True
    await db.commit()
    return {"message": "邮箱验证成功，现在可以登录了"}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_RESEND_VERIFY)
async def resend_verification(
    request: Request, current: CurrentUser, bg: BackgroundTasks
) -> dict:
    if current.email_verified:
        return {"message": "邮箱已验证，无需重复操作"}
    try:
        token = secrets.token_urlsafe(32)
        await _store_token(_VERIFY_PREFIX, token, current.id, settings.VERIFY_TOKEN_TTL_MINUTES)
        bg.add_task(send_verification_email, current.email, token)
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "验证邮件发送失败，请稍后重试")
    return {"message": "验证邮件已重新发送，请查收"}


# ---------- 忘记 / 重置密码 ----------
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_PASSWORD_RESET)
async def forgot_password(
    request: Request, payload: ForgotPasswordRequest, db: DbSession, bg: BackgroundTasks
) -> dict:
    svc = UserService(db)
    user = await svc.get_by_email(payload.email)
    # 防邮箱枚举：无论邮箱是否已注册，统一返回相同成功信息；仅已注册才真正发信。
    # 不在响应中暴露 sent 字段，避免攻击者据此探测邮箱是否已注册。
    if user and user.is_active:
        try:
            # per-邮箱限流：未命中上限才生成 token 并发信（命中则静默丢弃，响应不变）
            if not await _reset_email_throttled(user.email):
                token = secrets.token_urlsafe(32)
                await _store_token(_RESET_PREFIX, token, user.id, settings.RESET_TOKEN_TTL_MINUTES)
                bg.add_task(send_reset_email, user.email, token)
        except Exception:
            pass
    return {"message": "若该邮箱已注册，重置密码链接已发送至该邮箱"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest, db: DbSession) -> dict:
    user_id = await _consume_token(_RESET_PREFIX, payload.token)
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "重置链接无效或已过期")
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "账号不可用")
    # 设置新密码；password_changed_at 更新会使改密前的所有 access/refresh 令牌失效
    await svc.set_password(user, payload.new_password)
    return {"message": "密码已重置，请使用新密码登录"}
