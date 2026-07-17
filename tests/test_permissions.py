"""权限分级测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_normal_cannot_access_premium_api(client: AsyncClient, normal_token):
    token = await normal_token()
    res = await client.get("/api/v1/premium/feature", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_premium_can_access_premium_api(client: AsyncClient, premium_token):
    token = await premium_token()
    res = await client.get("/api/v1/premium/feature", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "message" in res.json()


@pytest.mark.asyncio
async def test_normal_cannot_access_admin_api(client: AsyncClient, normal_token):
    token = await normal_token()
    res = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_premium_cannot_access_admin_api(client: AsyncClient, premium_token):
    token = await premium_token()
    res = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, normal_token):
    token = await normal_token()
    # 修改密码
    res = await client.post("/api/v1/users/me/password", headers={"Authorization": f"Bearer {token}"},
                             json={"old_password": "Normal123456", "new_password": "NewPass123456"})
    assert res.status_code == 204
    # 老密码失效
    bad = await client.post("/api/v1/auth/login", json={"email": "normal@test.com", "password": "Normal123456"})
    assert bad.status_code == 401
    # 新密码生效
    good = await client.post("/api/v1/auth/login", json={"email": "normal@test.com", "password": "NewPass123456"})
    assert good.status_code == 200