import redis
import json
from typing import Any, Optional
from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class RedisCache:
    @staticmethod
    def set(key: str, value: Any, expire: int = 3600) -> bool:
        """Set a value in Redis with optional expiration"""
        try:
            serialized_value = json.dumps(value)
            return redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a value from Redis"""
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete a key from Redis"""
        try:
            return bool(redis_client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    @staticmethod
    def exists(key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(redis_client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False


cache = RedisCache()
