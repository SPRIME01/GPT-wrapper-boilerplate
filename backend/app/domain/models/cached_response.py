"""
Cached Response model for the GPT Wrapper Boilerplate.

This module defines the CachedResponse domain model which represents
a cached response from the GPT API or other services.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Union


@dataclass
class CachedResponse:
    """
    Domain model representing a cached response.

    This class encapsulates the data and metadata for a cached response,
    including the response content, cache key, and expiration information.
    """

    key: str
    """The cache key under which the response is stored."""

    content: Any
    """The actual cached content."""

    created_at: datetime
    """Timestamp when the cache entry was created."""

    expires_at: Optional[datetime] = None
    """Timestamp when the cache entry expires, if applicable."""

    metadata: Dict[str, Any] = None
    """Optional metadata associated with the cached response."""

    @property
    def is_expired(self) -> bool:
        """
        Check if the cached response has expired.

        Returns:
            bool: True if the response has expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def time_to_live(self) -> Optional[float]:
        """
        Calculate the remaining time to live in seconds.

        Returns:
            Optional[float]: The time to live in seconds, or None if no expiration.
        """
        if self.expires_at is None:
            return None

        ttl = (self.expires_at - datetime.now()).total_seconds()
        return max(0.0, ttl)  # Ensure we don't return negative values

    @classmethod
    def create(cls, key: str, content: Any, ttl_seconds: Optional[float] = None,
               metadata: Optional[Dict[str, Any]] = None) -> 'CachedResponse':
        """
        Factory method to create a new CachedResponse.

        Args:
            key: The cache key
            content: The content to cache
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional metadata to associate with the response

        Returns:
            A new CachedResponse instance.
        """
        now = datetime.now()
        expires_at = None

        if ttl_seconds is not None:
            expires_at = now.fromtimestamp(now.timestamp() + ttl_seconds)

        return cls(
            key=key,
            content=content,
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {}
        )
