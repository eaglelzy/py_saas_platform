"""统一封装 Redis 连接与常用操作，供各服务复用。"""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from typing import Any, Generator

import redis
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

from app.saas.core.config.settings import settings
from app.saas.core.logging import logger


class RedisBackendError(RuntimeError):
    """Redis 使用过程中的通用异常基类。"""


class RedisUnavailableError(RedisBackendError):
    """Redis 服务不可达时抛出的异常。"""


class RedisOperationError(RedisBackendError):
    """Redis 操作执行失败时抛出的异常。"""


_client: Redis | None = None


def _create_client() -> Redis:
    """按配置初始化 Redis 客户端。"""

    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def get_redis() -> Redis:
    """返回进程级 Redis 客户端，按需懒加载。"""

    global _client
    if _client is None:
        _client = _create_client()
    return _client


def close_redis() -> None:
    """关闭全局 Redis 连接。"""

    global _client
    if _client is None:
        return

    try:
        _client.close()
    except RedisError as exc:
        logger.bind(component="redis").warning("关闭 Redis 连接失败", error=str(exc))
    finally:
        _client = None


def ping_redis() -> bool:
    """执行 PING 检查 Redis 是否存活。"""

    try:
        return bool(get_redis().ping())
    except RedisConnectionError:
        logger.bind(component="redis").error("Redis 连接不可用")
        return False
    except RedisError as exc:
        logger.bind(component="redis").warning("Redis PING 失败", error=str(exc))
        return False


class RedisClient:
    """对 redis-py 的轻量包装，统一异常与日志。"""

    def __init__(self, client: Redis | None = None) -> None:
        self._client = client or get_redis()

    def set(
        self,
        key: str,
        value: Any,
        *,
        expire_seconds: int | None = None,
        only_if_absent: bool = False,
        only_if_exists: bool = False,
    ) -> bool:
        """写入 Key，支持 TTL 及 NX/XX 语义。"""

        try:
            return bool(
                self._client.set(
                    name=key,
                    value=value,
                    ex=expire_seconds,
                    nx=only_if_absent,
                    xx=only_if_exists,
                )
            )
        except RedisConnectionError as exc:
            logger.bind(component="redis", key=key).error("Redis SET 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", key=key).error("Redis SET 异常", error=str(exc))
            raise RedisOperationError("Redis set operation failed") from exc

    def get(self, key: str) -> Any:
        """读取指定 Key 的值。"""

        try:
            return self._client.get(name=key)
        except RedisConnectionError as exc:
            logger.bind(component="redis", key=key).error("Redis GET 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", key=key).error("Redis GET 异常", error=str(exc))
            raise RedisOperationError("Redis get operation failed") from exc

    def delete(self, *keys: str) -> int:
        """删除一个或多个 Key。"""

        try:
            return int(self._client.delete(*keys))
        except RedisConnectionError as exc:
            logger.bind(component="redis", keys=list(keys)).error("Redis DELETE 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", keys=list(keys)).error("Redis DELETE 异常", error=str(exc))
            raise RedisOperationError("Redis delete operation failed") from exc

    def incr(self, key: str, amount: int = 1) -> int:
        """自增指定 Key 的数值，默认增量为 1。"""

        try:
            return int(self._client.incr(name=key, amount=amount))
        except RedisConnectionError as exc:
            logger.bind(component="redis", key=key).error("Redis INCR 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", key=key).error("Redis INCR 异常", error=str(exc))
            raise RedisOperationError("Redis increment operation failed") from exc

    def expire(self, key: str, seconds: int) -> bool:
        """为 Key 设置过期时间。"""

        try:
            return bool(self._client.expire(name=key, time=seconds))
        except RedisConnectionError as exc:
            logger.bind(component="redis", key=key).error("Redis EXPIRE 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", key=key).error("Redis EXPIRE 异常", error=str(exc))
            raise RedisOperationError("Redis expire operation failed") from exc

    def ttl(self, key: str) -> int:
        """获取 Key 剩余 TTL（秒）。"""

        try:
            return int(self._client.ttl(name=key))
        except RedisConnectionError as exc:
            logger.bind(component="redis", key=key).error("Redis TTL 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", key=key).error("Redis TTL 异常", error=str(exc))
            raise RedisOperationError("Redis ttl operation failed") from exc

    @contextmanager
    def pipeline(self, *, transaction: bool = True) -> Generator[Any, None, None]:
        """提供 Pipeline 上下文管理器，离开时自动执行。"""

        pipe = self._client.pipeline(transaction=transaction)
        try:
            yield pipe
            pipe.execute()
        except RedisConnectionError as exc:
            pipe.reset()
            logger.bind(component="redis").error("Redis PIPELINE 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            pipe.reset()
            logger.bind(component="redis").error("Redis PIPELINE 异常", error=str(exc))
            raise RedisOperationError("Redis pipeline execution failed") from exc

    def mget(self, keys: Iterable[str]) -> list[Any]:
        """批量读取多个 Key。"""

        keys_list = list(keys)
        try:
            return list(self._client.mget(keys_list))
        except RedisConnectionError as exc:
            logger.bind(component="redis", keys=keys_list).error("Redis MGET 连接失败")
            raise RedisUnavailableError("Redis connection failed") from exc
        except RedisError as exc:
            logger.bind(component="redis", keys=keys_list).error("Redis MGET 异常", error=str(exc))
            raise RedisOperationError("Redis mget operation failed") from exc


__all__ = (
    "RedisBackendError",
    "RedisClient",
    "RedisOperationError",
    "RedisUnavailableError",
    "close_redis",
    "get_redis",
    "ping_redis",
)
