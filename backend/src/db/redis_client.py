"""Redis 客户端单例 - 测试或无 Redis 环境下自动降级为内存字典"""
import time

import redis.asyncio as redis

from ..core.config import settings

_redis = None


class _MemoryRedis:
    """轻量级内存替代品（仅供测试或无 Redis 场景），不持久化、不跨进程"""
    def __init__(self):
        self._store: dict[str, tuple[str, float | None]] = {}

    async def get(self, key):
        item = self._store.get(key)
        if not item:
            return None
        value, expire = item
        if expire and expire < time.time():
            self._store.pop(key, None)
            return None
        return value

    async def setex(self, key, ttl, value):
        self._store[key] = (str(value), time.time() + ttl)

    async def set(self, key, value, ex=None):
        expire = time.time() + ex if ex else None
        self._store[key] = (str(value), expire)

    async def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)

    async def incr(self, key):
        item = self._store.get(key)
        if item:
            val, expire = item
            cur = int(val) + 1
            self._store[key] = (str(cur), expire)
        else:
            cur = 1
            self._store[key] = ("1", None)
        return cur

    async def expire(self, key, ttl):
        item = self._store.get(key)
        if item is None:
            return False
        val, _ = item
        self._store[key] = (val, time.time() + ttl if ttl and ttl > 0 else None)
        return True

    async def ping(self):
        return True

    async def close(self):
        self._store.clear()


def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=200,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        except Exception:
            _redis = _MemoryRedis()
    return _redis


async def ensure_redis() -> None:
    """启动时主动 ping 一次：连不上则降级为内存实现，避免运行时抛 500。

    在异步 lifespan 中调用。仅当尚未被测试显式设为内存模式时执行。
    """
    global _redis
    if isinstance(_redis, _MemoryRedis):
        return
    client = get_redis()
    try:
        await client.ping()
    except Exception:
        # 连接失败 → 降级内存（不持久、不跨进程，但保证服务可用）
        _redis = _MemoryRedis()
        # 同步把 slowapi 限流器存储也切到内存，保持与应用 redis 降级一致
        try:
            from ..core.ratelimit import limiter as _limiter
            from limits.storage import MemoryStorage
            _limiter._storage = MemoryStorage()
        except Exception:
            pass
        import logging
        logging.getLogger(__name__).warning(
            "Redis 不可用(%s)，已降级为内存实现：限流/黑名单将不跨进程、重启即失效。", settings.REDIS_URL
        )


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.close()
        except Exception:
            pass
        _redis = None


def reset_redis():
    """测试用：强制重新创建"""
    global _redis
    _redis = None


def use_memory_redis():
    """显式切换到内存 Redis，供测试使用"""
    global _redis
    _redis = _MemoryRedis()
