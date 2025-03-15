"""
Rate Limiter Service for the GPT Wrapper Boilerplate.

This module provides a high-level rate limiting service that coordinates between
the domain models and infrastructure-level rate limiter adapters.
"""

from typing import Dict, Optional, Callable, Any

from app.domain.models.rate_limit_quota import RateLimitQuota, RateLimitResult
from app.infrastructure.adapters.rate_limiting.rate_limiter import (
    RateLimiter,
    RateLimitExceededError
)


class RateLimiterService:
    """
    Application service for managing rate limiting.

    This service provides a high-level interface for rate limiting operations,
    abstracting away the details of the underlying rate limiter implementation.
    """

    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize the rate limiter service.

        Args:
            rate_limiter: The underlying rate limiter adapter implementation to use
        """
        self._rate_limiter = rate_limiter

        # Default limits for different resources
        self._default_limits = {
            'api': {
                'max_requests': 100,
                'window_seconds': 60
            },
            'gpt': {
                'max_requests': 10,
                'window_seconds': 60
            }
        }

    def check_and_update(self, key: str, resource_type: str = 'api') -> RateLimitResult:
        """
        Check if the rate limit for a key has been exceeded and increment the counter.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            resource_type: The type of resource being limited (default: 'api')

        Returns:
            A RateLimitResult indicating whether the request is allowed and quota information

        Raises:
            ValueError: If the resource_type is not recognized
        """
        if resource_type not in self._default_limits:
            raise ValueError(f"Unknown resource type: {resource_type}")

        limits = self._default_limits[resource_type]
        return self._rate_limiter.check_limit(
            key=f"{resource_type}:{key}",
            max_requests=limits['max_requests'],
            window_seconds=limits['window_seconds']
        )

    def get_quota(self, key: str, resource_type: str = 'api') -> RateLimitQuota:
        """
        Get the current rate limit quota for a key without incrementing the counter.

        Args:
            key: The rate limit key (user ID, API client ID, IP, etc.)
            resource_type: The type of resource being limited (default: 'api')

        Returns:
            The current RateLimitQuota for the key

        Raises:
            ValueError: If the resource_type is not recognized
        """
        if resource_type not in self._default_limits:
            raise ValueError(f"Unknown resource type: {resource_type}")

        limits = self._default_limits[resource_type]
        return self._rate_limiter.get_quota(
            key=f"{resource_type}:{key}",
            max_requests=limits['max_requests'],
            window_seconds=limits['window_seconds']
        )

    def reset_limit(self, key: str, resource_type: Optional[str] = None) -> None:
        """
        Reset the rate limit for a specific key.

        Args:
            key: The rate limit key to reset
            resource_type: The type of resource to reset (if None, resets all resources)
        """
        if resource_type:
            prefix = f"{resource_type}:{key}"
        else:
            prefix = key

        self._rate_limiter.reset_limit(prefix)

    def update_limit_config(self, resource_type: str, max_requests: int, window_seconds: int) -> None:
        """
        Update the default limits for a resource type.

        Args:
            resource_type: The type of resource being limited
            max_requests: Maximum number of requests allowed in the window
            window_seconds: The time window in seconds
        """
        self._default_limits[resource_type] = {
            'max_requests': max_requests,
            'window_seconds': window_seconds
        }

    def with_rate_limiting(
        self,
        func: Callable,
        key_func: Callable[[Any], str],
        resource_type: str = 'api',
        raise_on_limit: bool = False
    ) -> Callable:
        """
        Decorator factory to apply rate limiting to a function.

        Args:
            func: The function to wrap with rate limiting
            key_func: A function that extracts the rate limit key from the function arguments
            resource_type: The type of resource being limited (default: 'api')
            raise_on_limit: Whether to raise an exception when limit is exceeded (default: False)

        Returns:
            A wrapped function that applies rate limiting
        """
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = key_func(*args, **kwargs)
            result = self.check_and_update(key, resource_type)

            if not result.allowed:
                if raise_on_limit:
                    raise RateLimitExceededError(result.quota)
                return None

            return func(*args, **kwargs)

        return wrapper
