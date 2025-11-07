"""
Redis-backed state storage for WeChat authentication.
Falls back to in-memory storage if Redis is not available.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app


class StateStorage:
    """Abstract base for state storage"""
    
    def set(self, key: str, value: Dict[str, Any], expire_seconds: int = 600):
        """Store state with expiration"""
        raise NotImplementedError
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve state"""
        raise NotImplementedError
    
    def delete(self, key: str):
        """Delete state"""
        raise NotImplementedError
    
    def cleanup_expired(self):
        """Clean up expired states (for in-memory storage)"""
        pass


class RedisStateStorage(StateStorage):
    """Redis-backed state storage"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def set(self, key: str, value: Dict[str, Any], expire_seconds: int = 600):
        """Store state in Redis with expiration"""
        self.redis.setex(
            f"wechat:state:{key}",
            timedelta(seconds=expire_seconds),
            json.dumps(value)
        )
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve state from Redis"""
        data = self.redis.get(f"wechat:state:{key}")
        if data:
            return json.loads(data)
        return None
    
    def delete(self, key: str):
        """Delete state from Redis"""
        self.redis.delete(f"wechat:state:{key}")


class InMemoryStateStorage(StateStorage):
    """Fallback in-memory state storage"""
    
    def __init__(self):
        self._storage = {}
    
    def set(self, key: str, value: Dict[str, Any], expire_seconds: int = 600):
        """Store state in memory with expiration"""
        self._storage[key] = {
            'data': value,
            'expires_at': datetime.utcnow() + timedelta(seconds=expire_seconds)
        }
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve state from memory"""
        entry = self._storage.get(key)
        if entry:
            if datetime.utcnow() < entry['expires_at']:
                return entry['data']
            else:
                # Expired, remove it
                self._storage.pop(key, None)
        return None
    
    def delete(self, key: str):
        """Delete state from memory"""
        self._storage.pop(key, None)
    
    def cleanup_expired(self):
        """Remove expired state entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._storage.items()
            if now >= entry['expires_at']
        ]
        for key in expired_keys:
            self._storage.pop(key, None)


def create_state_storage() -> StateStorage:
    """
    Create state storage instance.
    Tries Redis first, falls back to in-memory if Redis is not available.
    """
    redis_host = os.getenv('REDIS_HOST')
    
    if redis_host:
        try:
            import redis
            redis_client = redis.Redis(
                host=redis_host,
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD') or None,
                decode_responses=False,
                socket_connect_timeout=5
            )
            # Test connection
            redis_client.ping()
            current_app.logger.info("Using Redis for WeChat state storage")
            return RedisStateStorage(redis_client)
        except Exception as e:
            current_app.logger.warning(f"Failed to connect to Redis, falling back to in-memory storage: {e}")
    
    current_app.logger.warning("Redis not configured, using in-memory state storage (not suitable for production)")
    return InMemoryStateStorage()
