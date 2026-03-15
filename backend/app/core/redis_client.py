"""Redis Client for Caching"""
from typing import Optional, Any
import json
import redis
from redis.connection import ConnectionPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def get_redis_url() -> str:
    """Get Redis connection URL"""
    if settings.REDIS_URL:
        return settings.REDIS_URL

    redis_auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{redis_auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool"""
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            get_redis_url(),
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )

    return _redis_pool


def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.Redis(
            connection_pool=get_redis_pool(),
            decode_responses=True,
        )

    return _redis_client


class RedisCache:
    """Redis cache wrapper with common operations"""

    def __init__(self, prefix: str = "flowsync"):
        self.client = get_redis_client()
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create a prefixed key"""
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            value = self.client.get(self._make_key(key))
            if value is None:
                return None

            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error("Redis get failed", extra={"key": key, "error": str(e)})
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value in cache"""
        try:
            # Serialize to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            cache_key = self._make_key(key)

            if ttl:
                return self.client.setex(cache_key, ttl, value)
            else:
                return self.client.set(cache_key, value)

        except Exception as e:
            logger.error("Redis set failed", extra={"key": key, "error": str(e)})
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        try:
            return bool(self.client.delete(self._make_key(key)))
        except Exception as e:
            logger.error("Redis delete failed", extra={"key": key, "error": str(e)})
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        try:
            keys = self.client.keys(f"{self.prefix}:{pattern}")
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Redis delete_pattern failed", extra={"pattern": pattern, "error": str(e)})
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        try:
            return bool(self.client.exists(self._make_key(key)))
        except Exception as e:
            logger.error("Redis exists failed", extra={"key": key, "error": str(e)})
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a value"""
        try:
            return self.client.incr(self._make_key(key), amount)
        except Exception as e:
            logger.error("Redis incr failed", extra={"key": key, "error": str(e)})
            return None

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key"""
        try:
            return bool(self.client.expire(self._make_key(key), ttl))
        except Exception as e:
            logger.error("Redis expire failed", extra={"key": key, "error": str(e)})
            return False

    def ttl(self, key: str) -> int:
        """Get remaining time to live for a key"""
        try:
            return self.client.ttl(self._make_key(key))
        except Exception as e:
            logger.error("Redis ttl failed", extra={"key": key, "error": str(e)})
            return -1


# Default cache instance
cache = RedisCache()


def close_redis_connections():
    """Close all Redis connections"""
    global _redis_client, _redis_pool

    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None

    if _redis_pool:
        try:
            _redis_pool.disconnect()
        except Exception:
            pass
        _redis_pool = None
