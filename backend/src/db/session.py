"""SQLAlchemy 异步会话管理 – 懒加载引擎，支持测试时覆盖"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..core.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_async_session_factory: async_sessionmaker | None = None


def get_engine():
    global _engine
    if _engine is None:
        url = settings.DATABASE_URL
        kwargs: dict = {"echo": settings.DEBUG, "pool_pre_ping": True}
        # SQLite (用于测试) 不支持 pool_size/max_overflow
        if not url.startswith("sqlite"):
            kwargs.update(pool_size=20, max_overflow=40, pool_recycle=3600)
        _engine = create_async_engine(url, **kwargs)
    return _engine


def get_async_session_factory() -> async_sessionmaker:
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


def reset_engine():
    """仅测试使用：重置引擎以便注入 SQLite 等测试数据库"""
    global _engine, _async_session_factory
    _engine = None
    _async_session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()