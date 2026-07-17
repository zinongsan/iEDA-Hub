"""邮箱验证 / 忘记密码 / 重置密码 流程测试，及 P0#1 / P0#2 回归"""
import time

import pytest
from httpx import AsyncClient

from backend.src.api.v1.auth import _RESET_PREFIX, _VERIFY_PREFIX, _store_token


@pytest.mark.asyncio
async def test_register_marks_unverified(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "v1@test.com", "username": "v1user", "password": "Test123456"
    })
    assert res.status_code == 201
    assert res.json()["email_verified"] is False


@pytest.mark.asyncio
async def test_verify_email_single_use(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "v2@test.com", "username": "v2user", "password": "Test123456"
    })
    me = await client.post("/api/v1/auth/login", json={"email": "v2@test.com", "password": "Test123456"})
    uid = me.json()["id"]
    token = "verify-token-xyz"
    await _store_token(_VERIFY_PREFIX, token, uid, 60)
    res = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert res.status_code == 200
    # 单次使用：同一 token 再次验证应失败
    again = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert again.status_code == 400


@pytest.mark.asyncio
async def test_forgot_password_does_not_leak(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "fp@test.com", "username": "fpuser", "password": "Test123456"
    })
    ok = await client.post("/api/v1/auth/forgot-password", json={"email": "fp@test.com"})
    miss = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@test.com"})
    # 防邮箱枚举：两者都 200、消息完全一致，且不暴露 sent 字段；仅已注册才发信
    assert ok.status_code == 200
    assert miss.status_code == 200
    assert ok.json()["message"] == miss.json()["message"]
    assert "sent" not in ok.json()
    assert "sent" not in miss.json()


@pytest.mark.asyncio
async def test_forgot_password_per_email_throttle(client: AsyncClient):
    """per-邮箱限流：同一邮箱命中小时上限后静默丢弃，响应仍一致、计数不再增长。"""
    from backend.src.core.config import settings
    from backend.src.db.redis_client import get_redis

    saved = (settings.RESET_EMAIL_COOLDOWN_SEC,
             settings.RESET_EMAIL_HOUR_MAX,
             settings.RESET_EMAIL_DAY_MAX)
    settings.RESET_EMAIL_COOLDOWN_SEC = 0   # 关掉冷却，专测小时上限
    settings.RESET_EMAIL_HOUR_MAX = 2
    settings.RESET_EMAIL_DAY_MAX = 99
    try:
        await client.post("/api/v1/auth/register", json={
            "email": "throttle@test.com", "username": "throttleuser", "password": "Test123456"
        })
        msgs = set()
        for _ in range(4):
            r = await client.post("/api/v1/auth/forgot-password",
                                  json={"email": "throttle@test.com"})
            assert r.status_code == 200
            msgs.add(r.json()["message"])
        # 4 次请求、小时上限 2 → 仅放行 2 次（计数=2）；响应全部一致（含被限流的）
        hour_n = int((await get_redis().get("pwreset:hour:throttle@test.com")) or 0)
        assert hour_n == 2
        assert len(msgs) == 1
    finally:
        (settings.RESET_EMAIL_COOLDOWN_SEC,
         settings.RESET_EMAIL_HOUR_MAX,
         settings.RESET_EMAIL_DAY_MAX) = saved


@pytest.mark.asyncio
async def test_reset_password_invalidates_old_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "rp@test.com", "username": "rpuser", "password": "Test123456"
    })
    me = await client.post("/api/v1/auth/login", json={"email": "rp@test.com", "password": "Test123456"})
    uid = me.json()["id"]
    token = "reset-token-abc"
    await _store_token(_RESET_PREFIX, token, uid, 60)
    res = await client.post("/api/v1/auth/reset-password",
                            json={"token": token, "new_password": "BrandNew123"})
    assert res.status_code == 200
    # 旧密码登录失败
    bad = await client.post("/api/v1/auth/login", json={"email": "rp@test.com", "password": "Test123456"})
    assert bad.status_code == 401
    # 新密码登录成功
    good = await client.post("/api/v1/auth/login", json={"email": "rp@test.com", "password": "BrandNew123"})
    assert good.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_token_single_use(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "rp2@test.com", "username": "rp2user", "password": "Test123456"
    })
    me = await client.post("/api/v1/auth/login", json={"email": "rp2@test.com", "password": "Test123456"})
    uid = me.json()["id"]
    token = "reset-token-once"
    await _store_token(_RESET_PREFIX, token, uid, 60)
    first = await client.post("/api/v1/auth/reset-password",
                              json={"token": token, "new_password": "BrandNew456"})
    assert first.status_code == 200
    # 重复使用同一 token 应失败
    second = await client.post("/api/v1/auth/reset-password",
                               json={"token": token, "new_password": "BrandNew789"})
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_resend_verification(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "rv@test.com", "username": "rvuser", "password": "Test123456"
    })
    await client.post("/api/v1/auth/login", json={"email": "rv@test.com", "password": "Test123456"})
    # access_token cookie 自动携带，CurrentUser 通过
    res = await client.post("/api/v1/auth/resend-verification", json={})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_refresh_invalidated_after_password_change(client: AsyncClient):
    """P0#1 回归：改密码后旧 refresh token 必须失效"""
    await client.post("/api/v1/auth/register", json={
        "email": "p0@test.com", "username": "p0user", "password": "Test123456"
    })
    await client.post("/api/v1/auth/login", json={"email": "p0@test.com", "password": "Test123456"})
    refresh_val = client.cookies.get("refresh_token")
    assert refresh_val, "登录应下发 refresh cookie"
    access = client.cookies.get("access_token")
    # 跨秒：确保改密发生在登录(iat)之后的下一秒，避开同秒精度窗口
    time.sleep(1.1)
    # 改密码
    ch = await client.post("/api/v1/users/me/password",
                           headers={"Authorization": f"Bearer {access}"},
                           json={"old_password": "Test123456", "new_password": "Changed123"})
    assert ch.status_code == 204
    # 旧 refresh 应被拒（iat 早于 password_changed_at）
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_val})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_response_has_no_tokens(client: AsyncClient):
    """P0#2 回归：登录与刷新响应体均不含令牌"""
    await client.post("/api/v1/auth/register", json={
        "email": "p0b@test.com", "username": "p0buser", "password": "Test123456"
    })
    login = await client.post("/api/v1/auth/login", json={"email": "p0b@test.com", "password": "Test123456"})
    assert "access_token" not in login.json()
    assert "refresh_token" not in login.json()
    refresh = await client.post("/api/v1/auth/refresh", json={})
    assert "access_token" not in refresh.json()
    assert "refresh_token" not in refresh.json()
