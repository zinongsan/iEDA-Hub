"""测试注册、登录、刷新、登出"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com", "username": "testuser", "password": "Test123456"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "test@example.com"
    assert data["tier"] == "normal"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "username": "dup1", "password": "Test123456"
    })
    res = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "username": "dup2", "password": "Test123456"
    })
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com", "username": "logintest", "password": "Test123456"
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com", "password": "Test123456"
    })
    assert res.status_code == 200
    data = res.json()
    # P0#2：令牌不在响应体，仅通过 HttpOnly cookie 下发
    assert "access_token" not in data
    assert "refresh_token" not in data
    assert data["email"] == "login@test.com"
    assert client.cookies.get("access_token")
    assert client.cookies.get("refresh_token")


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@test.com", "username": "wrongtest", "password": "Test123456"
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "wrong@test.com", "password": "WrongPassword"
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, normal_token):
    token = await normal_token()
    res = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "normal@test.com"


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "refresh@test.com", "username": "refreshtest", "password": "Test123456"
    })
    await client.post("/api/v1/auth/login", json={
        "email": "refresh@test.com", "password": "Test123456"
    })
    # refresh 走 HttpOnly cookie（path=/api/v1/auth），httpx 自动携带
    res = await client.post("/api/v1/auth/refresh", json={})
    assert res.status_code == 200
    # P0#2：响应体是用户信息，不含令牌
    assert "access_token" not in res.json()
    assert res.json()["email"] == "refresh@test.com"


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, normal_token):
    token = await normal_token()
    res = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 204