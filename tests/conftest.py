"""pytest 异步 fixtures"""
import os
import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# 先覆盖 settings 防止提前加载真实 DB URL
import backend.src.core.config as cfg_mod
TEST_DB_FILE = "/tmp/guochuang_test.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
cfg_mod.settings.DATABASE_URL = TEST_DB_URL  # type: ignore[assignment]

from backend.src.db.session import Base, get_engine, reset_engine
from backend.src.db.redis_client import use_memory_redis, reset_redis
from backend.src.core.email import use_noop_mailer, reset_mailer
from backend.src.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_test_db():
    """每次测试前重新建表并使用内存 Redis"""
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    cfg_mod.settings.DATABASE_URL = TEST_DB_URL  # type: ignore[assignment]
    reset_engine()
    reset_redis()
    use_memory_redis()
    use_noop_mailer()  # 测试不发真实邮件

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()
    reset_engine()
    reset_mailer()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def admin_token(client: AsyncClient):
    """手动创建管理员并登录"""
    async def _login():
        from backend.src.db.session import get_async_session_factory
        from backend.src.models.user import User, UserTier
        from backend.src.core.security import hash_password
        from sqlalchemy import select

        async with get_async_session_factory()() as db:
            existing = (await db.execute(select(User).where(User.email == "admin@test.com"))).scalar_one_or_none()
            if not existing:
                db.add(User(
                    email="admin@test.com", username="admin_test",
                    hashed_password=hash_password("Admin123456"),
                    tier=UserTier.PREMIUM, is_admin=True, is_active=True,
                ))
                await db.commit()
        login = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com", "password": "Admin123456"
        })
        return client.cookies.get("access_token")
    return _login


@pytest.fixture
def normal_token(client: AsyncClient):
    async def _login():
        reg = await client.post("/api/v1/auth/register", json={
            "email": "normal@test.com", "username": "normal_test", "password": "Normal123456"
        })
        if reg.status_code not in (200, 201, 409):
            raise AssertionError(f"register failed: {reg.status_code} {reg.text}")
        login = await client.post("/api/v1/auth/login", json={
            "email": "normal@test.com", "password": "Normal123456"
        })
        return client.cookies.get("access_token")
    return _login


@pytest.fixture
def premium_token(client: AsyncClient):
    """创建高级用户"""
    async def _login():
        from backend.src.db.session import get_async_session_factory
        from backend.src.models.user import User, UserTier
        from backend.src.core.security import hash_password
        from sqlalchemy import select

        async with get_async_session_factory()() as db:
            existing = (await db.execute(select(User).where(User.email == "premium@test.com"))).scalar_one_or_none()
            if not existing:
                db.add(User(
                    email="premium@test.com", username="premium_test",
                    hashed_password=hash_password("Premium123456"),
                    tier=UserTier.PREMIUM, is_admin=False, is_active=True,
                ))
                await db.commit()
        login = await client.post("/api/v1/auth/login", json={
            "email": "premium@test.com", "password": "Premium123456"
        })
        return client.cookies.get("access_token")
    return _login