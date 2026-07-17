"""管理员后台测试（使用 premium_token fixture）"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, admin_token):
    token = await admin_token()
    res = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_user_by_admin(client: AsyncClient, admin_token):
    token = await admin_token()
    res = await client.post("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}, json={
        "email": "created@test.com", "username": "created_user", "password": "Test123456",
        "tier": "premium",
    })
    assert res.status_code == 201
    assert res.json()["tier"] == "premium"


@pytest.mark.asyncio
async def test_update_user_tier(client: AsyncClient, admin_token, normal_token):
    admin_tok = await admin_token()
    await normal_token()  # ensure user exists
    users = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_tok}"})
    normal_id = [u["id"] for u in users.json()["items"] if u["tier"] == "normal"][0]

    patch = await client.patch(f"/api/v1/admin/users/{normal_id}", headers={"Authorization": f"Bearer {admin_tok}"},
                               json={"tier": "premium"})
    assert patch.status_code == 200
    assert patch.json()["tier"] == "premium"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, admin_token, normal_token):
    admin_tok = await admin_token()
    await normal_token()
    users = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_tok}"})
    victim_id = [u["id"] for u in users.json()["items"] if u["username"] == "normal_test"][0]
    res = await client.delete(f"/api/v1/admin/users/{victim_id}", headers={"Authorization": f"Bearer {admin_tok}"})
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_group_crud(client: AsyncClient, admin_token):
    token = await admin_token()
    cr = await client.post("/api/v1/admin/groups", headers={"Authorization": f"Bearer {token}"}, json={
        "name": "测试组", "tier": "premium", "description": "desc"
    })
    assert cr.status_code == 201
    gid = cr.json()["id"]

    lst = await client.get("/api/v1/admin/groups", headers={"Authorization": f"Bearer {token}"})
    assert lst.status_code == 200
    assert any(g["name"] == "测试组" for g in lst.json())

    up = await client.patch(f"/api/v1/admin/groups/{gid}", headers={"Authorization": f"Bearer {token}"},
                            json={"name": "测试组-已改"})
    assert up.status_code == 200
    assert up.json()["name"] == "测试组-已改"

    dl = await client.delete(f"/api/v1/admin/groups/{gid}", headers={"Authorization": f"Bearer {token}"})
    assert dl.status_code == 204


@pytest.mark.asyncio
async def test_assign_group(client: AsyncClient, admin_token, normal_token):
    admin_tok = await admin_token()
    g = await client.post("/api/v1/admin/groups", headers={"Authorization": f"Bearer {admin_tok}"}, json={
        "name": "高级VIP组", "tier": "premium"
    })
    gid = g.json()["id"]

    tok = await normal_token()
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tok}"})
    uid = me.json()["id"]

    res = await client.post("/api/v1/admin/users/assign-group", headers={"Authorization": f"Bearer {admin_tok}"},
                            json={"user_ids": [uid], "group_id": gid})
    assert res.status_code == 200
    assert "affected" in res.json()

    me2 = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tok}"})
    assert me2.json()["tier"] == "premium"
    assert me2.json()["group"]["name"] == "高级VIP组"