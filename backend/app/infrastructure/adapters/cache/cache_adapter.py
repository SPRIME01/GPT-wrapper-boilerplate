"""
Cache adapter implementations for the GPT Wrapper Boilerplate.

This module provides interfaces and implementations for caching mechanisms
used throughout the application to improve performance and reduce unnecessary
API calls to the GPT service.
"""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Union


class CacheAdapter(ABC):
    """
    Abstract base class for cache implementations.

    This interface defines the contract for all cache adapters in the system,
    allowing for different implementations (in-memory, Redis, etc.) while
    maintaining a consistent API.
    """

    @abstractmethod
    def get(self, key: str) -> Any:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found, None otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key to store the value under
            value: The value to store
            ttl_seconds: Optional time-to-live in seconds after which the value expires
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Remove a value from the cache.

        Args:
            key: The cache key to remove
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        pass


class InMemoryCacheAdapter(CacheAdapter):
    """
    In-memory implementation of the cache adapter.

    This implementation stores cache values in a Python dictionary.
    It's suitable for single-instance deployments or testing.

    Note: This implementation is not shared across multiple instances
    of the application and should not be used in a distributed environment.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Any:
        """
        Retrieve a value from the in-memory cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]

        # Check if entry has expired
        if 'expires_at' in cache_entry and cache_entry['expires_at'] <= time.time():
            # Entry has expired, remove it
            del self._cache[key]
            return None

        return cache_entry['value']

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
        Store a value in the in-memory cache.

        Args:
            key: The cache key to store the value under
            value: The value to store
            ttl_seconds: Optional time-to-live in seconds after which the value expires
        """
        cache_entry = {
            'value': value
        }

        if ttl_seconds is not None:
            cache_entry['expires_at'] = time.time() + ttl_seconds

        self._cache[key] = cache_entry

    def delete(self, key: str) -> None:
        """
        Remove a value from the in-memory cache.

        Args:
            key: The cache key to remove
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """
        Clear all values from the in-memory cache.
        """
        self._cache.clear()


class RedisCacheAdapter(CacheAdapter):
    """
    Redis implementation of the cache adapter.

    This implementation uses Redis as the underlying cache store.
    It's suitable for distributed environments where cache needs
    to be shared across multiple instances of the application.
    """

    def __init__(self, redis_client):
        """
        Initialize the Redis cache adapter.

        Args:
            redis_client: An initialized Redis client instance
        """
        self.redis = redis_client

    def get(self, key: str) -> Any:
        """
        Retrieve a value from the Redis cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found, None otherwise
        """
        value = self.redis.get(key)
        if value is None:
            return None

        # Deserialize the JSON-encoded value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # If it's not JSON, return the raw value
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
        Store a value in the Redis cache.

        Args:
            key: The cache key to store the value under
            value: The value to store
            ttl_seconds: Optional time-to-live in seconds after which the value expires
        """
        # Serialize the value as JSON
        serialized_value = json.dumps(value)

        if ttl_seconds is not None:
            self.redis.setex(key, int(ttl_seconds), serialized_value)
        else:
            self.redis.set(key, serialized_value)

    def delete(self, key: str) -> None:
        """
        Remove a value from the Redis cache.

        Args:
            key: The cache key to remove
        """
        self.redis.delete(key)

    def clear(self) -> None:
        """
        Clear all values from the Redis cache.

        Note: This method is potentially dangerous as it flushes the entire Redis database.
        Use with caution, especially in shared environments.
        """
        self.redis.flushdb()
