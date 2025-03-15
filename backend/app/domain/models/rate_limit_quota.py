"""
Rate Limit Quota domain model for the GPT Wrapper Boilerplate.

This module defines the RateLimitQuota domain model which represents
rate limiting information for a specific client or resource.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RateLimitQuota:
    """
    Domain model representing rate limit quota information.

    This class encapsulates data about rate limits for a specific key,
    including usage information and reset timing.
    """

    key: str
    """The key this quota applies to (user ID, API client ID, IP, etc.)."""

    max_requests: int
    """The maximum number of requests allowed in the time window."""

    used: int
    """The number of requests used so far in the current window."""

    window_seconds: int
    """The time window in seconds for this rate limit."""

    reset_at: datetime
    """When the current rate limit window expires and count resets."""

    @property
    def remaining(self) -> int:
        """
        Calculate the number of requests remaining in the current window.

        Returns:
            int: The number of remaining requests (minimum 0)
        """
        return max(0, self.max_requests - self.used)

    @property
    def is_exceeded(self) -> bool:
        """
        Check if the rate limit has been exceeded.

        Returns:
            bool: True if the limit is exceeded, False otherwise
        """
        return self.used >= self.max_requests

    @property
    def reset_in_seconds(self) -> float:
        """
        Calculate the number of seconds until the rate limit resets.

        Returns:
            float: Seconds until reset (minimum 0)
        """
        now = datetime.now()
        if now >= self.reset_at:
            return 0.0
        return (self.reset_at - now).total_seconds()


@dataclass
class RateLimitResult:
    """
    Domain model representing the result of a rate limit check.

    Contains information about whether the operation is allowed and remaining quota.
    """

    allowed: bool
    """Whether the operation is allowed under the rate limit."""

    quota: RateLimitQuota
    """The quota information after applying this request."""

    @property
    def remaining(self) -> int:
        """
        Get the number of requests remaining.

        Returns:
            int: The number of remaining requests
        """
        return self.quota.remaining

    @property
    def reset_at(self) -> datetime:
        """
        Get when the rate limit will reset.

        Returns:
            datetime: When the current rate limit window expires
        """
        return self.quota.reset_at
