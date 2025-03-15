"""
Rate limiter implementations for the GPT Wrapper Boilerplate.

This module provides interfaces and implementations for rate limiting mechanisms
used throughout the application to prevent abuse and ensure fair resource allocation.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import json

from app.domain.models.rate_limit_quota import RateLimitQuota, RateLimitResult


class RateLimitExceededError(Exception):
    """
    Exception raised when a rate limit has been exceeded.

    Contains information about the rate limit and when it will reset.
    """

    def __init__(self, quota: RateLimitQuota):
        """
        Initialize with quota information.

        Args:
            quota: The quota that was exceeded
        """
        self.quota = quota
        reset_seconds = quota.reset_in_seconds
        super().__init__(
            f"Rate limit exceeded for {quota.key}. "
            f"Limit of {quota.max_requests} requests per {quota.window_seconds} seconds reached. "
            f"Try again in {reset_seconds:.1f} seconds."
        )


class RateLimiter(ABC):
    """
    Abstract base class for rate limiter implementations.

    This interface defines the contract for all rate limiter adapters in the system,
    allowing for different implementations (in-memory, Redis, etc.) while
    maintaining a consistent API.
    """

    @abstractmethod
    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> RateLimitResult:
        """
        Check if the rate limit has been exceeded, and increment the counter if allowed.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds

        Returns:
            A RateLimitResult indicating whether the request is allowed and quota information
        """
        pass

    @abstractmethod
    def get_quota(self, key: str, max_requests: int, window_seconds: int) -> RateLimitQuota:
        """
        Get the current rate limit quota for a key without incrementing the counter.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds

        Returns:
            The current RateLimitQuota for the key
        """
        pass

    @abstractmethod
    def reset_limit(self, key: str) -> None:
        """
        Reset the rate limit for a specific key.

        Args:
            key: The rate limit key to reset
        """
        pass


class InMemoryRateLimiter(RateLimiter):
    """
    In-memory implementation of the rate limiter.

    This implementation stores rate limit data in a Python dictionary.
    It's suitable for single-instance deployments or testing.

    Note: This implementation is not shared across multiple instances
    of the application and should not be used in a distributed environment.
    """

    def __init__(self):
        """Initialize the in-memory rate limiter with an empty state."""
        # Structure: {key: {'count': int, 'reset_at': float (timestamp)}}
        self._limits: Dict[str, Dict[str, Any]] = {}

    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> RateLimitResult:
        """
        Check if the rate limit has been exceeded, and increment the counter if allowed.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds

        Returns:
            A RateLimitResult indicating whether the request is allowed and quota information
        """
        now = time.time()
        limit_key = f"{key}:{max_requests}:{window_seconds}"

        # Initialize or get the current limit record
        if limit_key not in self._limits:
            self._limits[limit_key] = {
                'count': 0,
                'reset_at': now + window_seconds
            }

        limit_record = self._limits[limit_key]

        # Check if the window has expired and reset if needed
        if now >= limit_record['reset_at']:
            limit_record['count'] = 0
            limit_record['reset_at'] = now + window_seconds

        # Check if this request would exceed the limit
        if limit_record['count'] >= max_requests:
            # Limit exceeded
            quota = RateLimitQuota(
                key=key,
                max_requests=max_requests,
                used=limit_record['count'],
                window_seconds=window_seconds,
                reset_at=datetime.fromtimestamp(limit_record['reset_at'])
            )
            return RateLimitResult(allowed=False, quota=quota)

        # Increment the counter
        limit_record['count'] += 1

        # Create the quota object for the response
        quota = RateLimitQuota(
            key=key,
            max_requests=max_requests,
            used=limit_record['count'],
            window_seconds=window_seconds,
            reset_at=datetime.fromtimestamp(limit_record['reset_at'])
        )

        return RateLimitResult(allowed=True, quota=quota)

    def get_quota(self, key: str, max_requests: int, window_seconds: int) -> RateLimitQuota:
        """
        Get the current rate limit quota for a key without incrementing the counter.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds

        Returns:
            The current RateLimitQuota for the key
        """
        now = time.time()
        limit_key = f"{key}:{max_requests}:{window_seconds}"

        # If no limit record exists, return a fresh quota
        if limit_key not in self._limits:
            return RateLimitQuota(
                key=key,
                max_requests=max_requests,
                used=0,
                window_seconds=window_seconds,
                reset_at=datetime.fromtimestamp(now + window_seconds)
            )

        limit_record = self._limits[limit_key]

        # Check if the window has expired
        if now >= limit_record['reset_at']:
            return RateLimitQuota(
                key=key,
                max_requests=max_requests,
                used=0,
                window_seconds=window_seconds,
                reset_at=datetime.fromtimestamp(now + window_seconds)
            )

        # Return the current quota
        return RateLimitQuota(
            key=key,
            max_requests=max_requests,
            used=limit_record['count'],
            window_seconds=window_seconds,
            reset_at=datetime.fromtimestamp(limit_record['reset_at'])
        )

    def reset_limit(self, key: str) -> None:
        """
        Reset the rate limit for a specific key.

        Args:
            key: The rate limit key to reset
        """
        # Find all limit keys that start with this key
        keys_to_reset = [
            limit_key for limit_key in self._limits.keys()
            if limit_key.startswith(f"{key}:")
        ]

        # Reset all matching records
        for limit_key in keys_to_reset:
            self._limits[limit_key]['count'] = 0


class RedisRateLimiter(RateLimiter):
    """
    Redis-based implementation of the rate limiter.

    This implementation uses Redis for rate limiting, making it suitable
    for distributed environments where limits need to be shared across
    multiple instances of the application.
    """

    def __init__(self, redis_client):
        """
        Initialize the Redis rate limiter.

        Args:
            redis_client: An initialized Redis client instance
        """
        self.redis = redis_client

    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> RateLimitResult:
        """
        Check if the rate limit has been exceeded, and increment the counter if allowed.

        Uses Redis sorted sets to track request timestamps in a sliding window approach.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds

        Returns:
            A RateLimitResult indicating whether the request is allowed and quota information
        """
        now = time.time()
        redis_key = f"rate_limit:{key}:{max_requests}:{window_seconds}"

        # Start a Redis pipeline
        pipe = self.redis.pipeline()

        # Add current request timestamp to the sorted set
        pipe.zadd(redis_key, {now: now})

        # Remove timestamps outside of the current window
        window_start = now - window_seconds
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count requests in the current window
        pipe.zcard(redis_key)

        # Set expiry on the key to auto-cleanup after the window
        pipe.expire(redis_key, window_seconds)

        # Execute the pipeline
        _, _, used_count, _ = pipe.execute()

        # Calculate when this rate limit will reset
        # Get the oldest timestamp in the sorted set
        oldest = self.redis.zrange(redis_key, 0, 0, withscores=True)
        if oldest:
            # The limit will reset when the oldest timestamp exits the window
            reset_at = datetime.fromtimestamp(oldest[0][1] + window_seconds)
        else:
            # If there are no timestamps, the window resets in window_seconds from now
            reset_at = datetime.fromtimestamp(now + window_seconds)

        # Create the quota object
        quota = RateLimitQuota(
            key=key,
            max_requests=max_requests,
            used=used_count,
            window_seconds=window_seconds,
            reset_at=reset_at
        )

        # Check if the limit is exceeded
        if used_count > max_requests:
            return RateLimitResult(allowed=False, quota=quota)

        return RateLimitResult(allowed=True, quota=quota)

    def get_quota(self, key: str, max_requests: int, window_seconds: int) -> RateLimitQuota:
        """
        Get the current rate limit quota for a key without incrementing the counter.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds

        Returns:
            The current RateLimitQuota for the key
        """
        now = time.time()
        redis_key = f"rate_limit:{key}:{max_requests}:{window_seconds}"

        # Start a Redis pipeline
        pipe = self.redis.pipeline()

        # Remove timestamps outside of the current window
        window_start = now - window_seconds
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count requests in the current window
        pipe.zcard(redis_key)

        # Execute the pipeline
        _, used_count = pipe.execute()

        # Calculate when this rate limit will reset
        # Get the oldest timestamp in the sorted set
        oldest = self.redis.zrange(redis_key, 0, 0, withscores=True)
        if oldest:
            # The limit will reset when the oldest timestamp exits the window
            reset_at = datetime.fromtimestamp(oldest[0][1] + window_seconds)
        else:
            # If there are no timestamps, the window resets in window_seconds from now
            reset_at = datetime.fromtimestamp(now + window_seconds)

        # Create the quota object
        return RateLimitQuota(
            key=key,
            max_requests=max_requests,
            used=used_count,
            window_seconds=window_seconds,
            reset_at=reset_at
        )

    def reset_limit(self, key: str) -> None:
        """
        Reset the rate limit for a specific key.

        Args:
            key: The rate limit key to reset
        """
        # Find all keys matching the pattern and delete them
        pattern = f"rate_limit:{key}:*"
        keys_to_delete = self.redis.keys(pattern)
        if keys_to_delete:
            self.redis.delete(*keys_to_delete)
