"""
Cache Service for the GPT Wrapper Boilerplate.

This module provides a high-level caching service that coordinates between
the domain models and infrastructure-level cache adapters.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from app.domain.models.cached_response import CachedResponse
from app.infrastructure.adapters.cache.cache_adapter import CacheAdapter


T = TypeVar('T')


class CacheService:
    """
    Application service for managing cached data.

    This service provides a high-level interface for caching operations,
    abstracting away the details of the underlying cache implementation.
    """

    def __init__(self, cache_adapter: CacheAdapter):
        """
        Initialize the cache service.

        Args:
            cache_adapter: The underlying cache adapter implementation to use
        """
        self._cache_adapter = cache_adapter

    def get(self, key: str) -> Optional[CachedResponse]:
        """
        Retrieve a value from the cache and wrap it in a CachedResponse.

        Args:
            key: The cache key to retrieve

        Returns:
            A CachedResponse if found and valid, None otherwise
        """
        # Try to get the raw cached data
        raw_data = self._cache_adapter.get(key)
        if raw_data is None:
            return None

        # If we have a dict with the expected metadata format, convert to CachedResponse
        if isinstance(raw_data, dict) and 'content' in raw_data and 'metadata' in raw_data:
            created_at = datetime.fromtimestamp(raw_data.get('created_at', 0))
            expires_at = None
            if raw_data.get('expires_at'):
                expires_at = datetime.fromtimestamp(raw_data['expires_at'])

            return CachedResponse(
                key=key,
                content=raw_data['content'],
                created_at=created_at,
                expires_at=expires_at,
                metadata=raw_data['metadata']
            )

        # If it's not in our expected format, wrap the raw value
        return CachedResponse.create(
            key=key,
            content=raw_data,
            metadata={'source': 'cache', 'format': 'raw'}
        )

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None) -> CachedResponse:
        """
        Store a value in the cache.

        Args:
            key: The cache key to store the value under
            value: The value to store
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional metadata to associate with the cached response

        Returns:
            A CachedResponse representing the cached data
        """
        # Create a cached response object
        cached_response = CachedResponse.create(
            key=key,
            content=value,
            ttl_seconds=ttl_seconds,
            metadata=metadata or {}
        )

        # Prepare the data for storage
        cache_data = {
            'content': cached_response.content,
            'created_at': cached_response.created_at.timestamp(),
            'metadata': cached_response.metadata
        }

        if cached_response.expires_at:
            cache_data['expires_at'] = cached_response.expires_at.timestamp()

        # Store in the cache adapter
        self._cache_adapter.set(key, cache_data, ttl_seconds)

        return cached_response

    def delete(self, key: str) -> None:
        """
        Remove a value from the cache.

        Args:
            key: The cache key to remove
        """
        self._cache_adapter.delete(key)

    def clear(self) -> None:
        """
        Clear all values from the cache.
        """
        self._cache_adapter.clear()

    def generate_key(self, prefix: str, data: Any) -> str:
        """
        Generate a cache key from a prefix and data.

        Args:
            prefix: A string prefix for the key
            data: Data to hash for the key

        Returns:
            A string key for use with the cache
        """
        # Convert the data to a string representation
        if isinstance(data, str):
            data_str = data
        else:
            try:
                data_str = json.dumps(data, sort_keys=True)
            except (TypeError, ValueError):
                data_str = str(data)

        # Create a hash of the data
        data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()

        # Combine the prefix and hash to form the key
        return f"{prefix}:{data_hash}"
