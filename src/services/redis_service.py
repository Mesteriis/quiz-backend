"""
Redis Service for Quiz App.

This module provides Redis-based caching, session management,
and real-time data storage for improved performance.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Optional
import uuid
import asyncio

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheKey(str, Enum):
    """Cache key patterns."""

    SURVEY_DATA = "survey:{survey_id}"
    USER_SESSION = "session:{user_id}"
    SURVEY_RESPONSES = "responses:{survey_id}"
    USER_ANALYTICS = "analytics:{user_id}"
    TELEGRAM_STATE = "telegram_state:{user_id}"
    RATE_LIMIT = "rate_limit:{key}"
    WEBSOCKET_CONNECTION = "ws_conn:{user_id}"
    SURVEY_STATISTICS = "stats:{survey_id}"
    RECENT_SURVEYS = "recent_surveys:{user_id}"
    POPULAR_SURVEYS = "popular_surveys"


@dataclass
class CacheItem:
    """Cache item wrapper."""

    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RedisService:
    """Redis-based caching and session management service."""

    def __init__(self):
        self.redis: Optional[Redis] = None
        self.connection_pool = None
        self.connected = False
        self.default_ttl = 3600  # 1 hour
        self.max_retries = 3
        self.retry_delay = 1

    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - running in memory-only mode")
            return False

        try:
            # Configure Redis connection
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")

            self.redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self.redis.ping()
            self.connected = True

            logger.info("Redis connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.aclose()
            self.connected = False
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.connected:
            return None

        try:
            value = await self.redis.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Set value in cache."""
        if not self.connected:
            return False

        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)

            # Set with TTL
            cache_ttl = ttl or self.default_ttl

            if nx:
                # Set only if not exists
                result = await self.redis.set(
                    key, serialized_value, ex=cache_ttl, nx=True
                )
            else:
                result = await self.redis.set(key, serialized_value, ex=cache_ttl)

            return bool(result)

        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete keys from cache."""
        if not self.connected or not keys:
            return 0

        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting cache keys {keys}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.connected:
            return False

        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if not self.connected:
            return False

        try:
            return bool(await self.redis.expire(key, seconds))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if not self.connected:
            return -1

        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1

    async def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.connected:
            return False

        try:
            await self.redis.ping()
            return True
        except Exception:
            self.connected = False
            return False

    # Hash operations
    async def set_hash(
        self, key: str, mapping: dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Set hash fields."""
        if not self.connected:
            return False

        try:
            # Serialize values
            serialized_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[field] = json.dumps(value, default=str)
                else:
                    serialized_mapping[field] = str(value)

            await self.redis.hset(key, mapping=serialized_mapping)

            if ttl:
                await self.redis.expire(key, ttl)

            return True
        except Exception as e:
            logger.error(f"Error setting hash {key}: {e}")
            return False

    async def get_hash(self, key: str) -> Optional[dict[str, Any]]:
        """Get hash fields."""
        if not self.connected:
            return None

        try:
            data = await self.redis.hgetall(key)
            if not data:
                return None

            # Try to deserialize JSON values
            result = {}
            for field, value in data.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value

            return result
        except Exception as e:
            logger.error(f"Error getting hash {key}: {e}")
            return None

    # User state management
    async def set_user_state(
        self, user_id: int, state: str, data: dict[str, Any] = None
    ) -> bool:
        """Set user state with optional data."""
        state_key = CacheKey.TELEGRAM_STATE.format(user_id=user_id)

        state_data = {
            "state": state,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        }

        return await self.set(state_key, state_data, ttl=3600)  # 1 hour

    async def get_user_state(self, user_id: int) -> Optional[dict[str, Any]]:
        """Get user state and data."""
        state_key = CacheKey.TELEGRAM_STATE.format(user_id=user_id)
        return await self.get(state_key)

    async def clear_user_state(self, user_id: int) -> bool:
        """Clear user state."""
        state_key = CacheKey.TELEGRAM_STATE.format(user_id=user_id)
        return bool(await self.delete(state_key))

    # Survey caching
    async def cache_survey_data(
        self, survey_id: int, survey_data: dict[str, Any]
    ) -> bool:
        """Cache survey data."""
        cache_key = CacheKey.SURVEY_DATA.format(survey_id=survey_id)
        return await self.set(cache_key, survey_data, ttl=1800)  # 30 minutes

    async def get_survey_data(self, survey_id: int) -> Optional[dict[str, Any]]:
        """Get cached survey data."""
        cache_key = CacheKey.SURVEY_DATA.format(survey_id=survey_id)
        return await self.get(cache_key)

    async def invalidate_survey_cache(self, survey_id: int) -> bool:
        """Invalidate survey cache."""
        cache_key = CacheKey.SURVEY_DATA.format(survey_id=survey_id)
        responses_key = CacheKey.SURVEY_RESPONSES.format(survey_id=survey_id)
        stats_key = CacheKey.SURVEY_STATISTICS.format(survey_id=survey_id)

        deleted = await self.delete(cache_key, responses_key, stats_key)
        return deleted > 0

    # Session management
    async def create_user_session(
        self, user_id: int, session_data: dict[str, Any]
    ) -> str:
        """Create user session and return session ID."""
        session_id = str(uuid.uuid4())
        session_key = CacheKey.USER_SESSION.format(user_id=user_id)

        session_info = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "data": session_data,
        }

        await self.set(session_key, session_info, ttl=86400)  # 24 hours
        return session_id

    async def get_user_session(self, user_id: int) -> Optional[dict[str, Any]]:
        """Get user session."""
        session_key = CacheKey.USER_SESSION.format(user_id=user_id)
        return await self.get(session_key)

    async def update_user_session(
        self, user_id: int, session_data: dict[str, Any]
    ) -> bool:
        """Update user session."""
        session_key = CacheKey.USER_SESSION.format(user_id=user_id)

        current_session = await self.get(session_key)
        if not current_session:
            return False

        current_session["last_activity"] = datetime.now().isoformat()
        current_session["data"].update(session_data)

        return await self.set(session_key, current_session, ttl=86400)

    async def delete_user_session(self, user_id: int) -> bool:
        """Delete user session."""
        session_key = CacheKey.USER_SESSION.format(user_id=user_id)
        return bool(await self.delete(session_key))

    # Rate limiting
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded."""
        if not self.connected:
            return False

        try:
            rate_key = CacheKey.RATE_LIMIT.format(key=key)
            current_count = await self.redis.get(rate_key)

            if current_count is None:
                await self.redis.setex(rate_key, window, 1)
                return False

            current_count = int(current_count)
            if current_count >= limit:
                return True

            await self.redis.incr(rate_key)
            return False

        except Exception as e:
            logger.error(f"Error checking rate limit for {key}: {e}")
            return False

    async def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for key."""
        rate_key = CacheKey.RATE_LIMIT.format(key=key)
        return bool(await self.delete(rate_key))

    # WebSocket connection management
    async def register_websocket_connection(
        self, user_id: int, connection_id: str
    ) -> bool:
        """Register WebSocket connection."""
        if not self.connected:
            return False

        try:
            ws_key = CacheKey.WEBSOCKET_CONNECTION.format(user_id=user_id)
            connection_data = {
                "connection_id": connection_id,
                "user_id": user_id,
                "connected_at": datetime.now().isoformat(),
                "last_ping": datetime.now().isoformat(),
            }

            return await self.set(ws_key, connection_data, ttl=3600)
        except Exception as e:
            logger.error(f"Error registering WebSocket connection: {e}")
            return False

    async def get_websocket_connection(self, user_id: int) -> Optional[dict[str, Any]]:
        """Get WebSocket connection info."""
        ws_key = CacheKey.WEBSOCKET_CONNECTION.format(user_id=user_id)
        return await self.get(ws_key)

    async def unregister_websocket_connection(self, user_id: int) -> bool:
        """Unregister WebSocket connection."""
        ws_key = CacheKey.WEBSOCKET_CONNECTION.format(user_id=user_id)
        return bool(await self.delete(ws_key))

    # Counter operations
    async def increment_counter(
        self, key: str, by: int = 1, ttl: Optional[int] = None
    ) -> int:
        """Increment counter."""
        if not self.connected:
            return 0

        try:
            result = await self.redis.incrby(key, by)
            if ttl and result == by:  # First increment
                await self.redis.expire(key, ttl)
            return result
        except Exception as e:
            logger.error(f"Error incrementing counter {key}: {e}")
            return 0

    async def get_counter(self, key: str) -> int:
        """Get counter value."""
        if not self.connected:
            return 0

        try:
            value = await self.redis.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Error getting counter {key}: {e}")
            return 0

    async def set_counter(
        self, key: str, value: int, ttl: Optional[int] = None
    ) -> bool:
        """Set counter value."""
        return await self.set(key, value, ttl)

    # Cache statistics
    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self.connected:
            return {"status": "disconnected"}

        try:
            info = await self.redis.info()

            return {
                "status": "connected",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    # Batch operations
    async def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys."""
        if not self.connected or not keys:
            return {}

        try:
            values = await self.redis.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value

            return result
        except Exception as e:
            logger.error(f"Error getting multiple keys: {e}")
            return {}

    async def set_multi(
        self, mapping: dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Set multiple keys."""
        if not self.connected or not mapping:
            return False

        try:
            # Serialize values
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[key] = json.dumps(value, default=str)
                else:
                    serialized_mapping[key] = str(value)

            # Use pipeline for atomic operation
            pipe = self.redis.pipeline()
            pipe.mset(serialized_mapping)

            if ttl:
                for key in mapping.keys():
                    pipe.expire(key, ttl)

            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple keys: {e}")
            return False

    # Pattern operations
    async def get_keys_by_pattern(self, pattern: str) -> list[str]:
        """Get keys matching pattern."""
        if not self.connected:
            return []

        try:
            keys = []
            # Добавляем таймаут для предотвращения зависания
            async with asyncio.timeout(10):  # 10 секунд таймаут
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                    # Ограничиваем количество ключей для предотвращения зависания
                    if len(keys) >= 1000:  # Максимум 1000 ключей
                        logger.warning(
                            f"Reached maximum key limit for pattern {pattern}"
                        )
                        break
            return keys
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting keys by pattern {pattern}")
            return []
        except Exception as e:
            logger.error(f"Error getting keys by pattern {pattern}: {e}")
            return []

    async def delete_by_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        if not self.connected:
            return 0

        try:
            keys = await self.get_keys_by_pattern(pattern)
            if keys:
                return await self.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting keys by pattern {pattern}: {e}")
            return 0

    # Health check
    async def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        if not self.connected:
            return {
                "status": "unhealthy",
                "message": "Redis not connected",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            start_time = datetime.now()

            # Test basic operations
            test_key = f"health_check:{uuid.uuid4()}"
            await self.set(test_key, "test_value", ttl=60)
            retrieved_value = await self.get(test_key)
            await self.delete(test_key)

            if retrieved_value != "test_value":
                raise Exception("Failed to retrieve test value")

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000

            return {
                "status": "healthy",
                "message": "Redis is operational",
                "response_time_ms": round(response_time, 2),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {e!s}",
                "timestamp": datetime.now().isoformat(),
            }

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Global Redis service instance
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """Get global Redis service instance."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.initialize()
    return _redis_service


# Utility functions
async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    service = await get_redis_service()
    return await service.get(key)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache."""
    service = await get_redis_service()
    return await service.set(key, value, ttl)


async def cache_delete(*keys: str) -> int:
    """Delete keys from cache."""
    service = await get_redis_service()
    return await service.delete(*keys)


async def cache_health_check() -> dict[str, Any]:
    """Check cache health."""
    service = await get_redis_service()
    return await service.health_check()


async def flush_cache(pattern: str = "*") -> int:
    """Flush cache by pattern."""
    service = await get_redis_service()
    return await service.delete_by_pattern(pattern)
