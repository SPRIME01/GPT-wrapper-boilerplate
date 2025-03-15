"""
Tests for the Rate Limiter Service in the application layer.
"""

import pytest
from unittest.mock import Mock, patch, call
import time
from datetime import datetime, timedelta

from app.application.services.rate_limiter_service import RateLimiterService
from app.domain.models.rate_limit_quota import RateLimitQuota, RateLimitResult
from app.infrastructure.adapters.rate_limiting.rate_limiter import (
    InMemoryRateLimiter,
    RateLimitExceededError
)


class TestRateLimiterService:
    """
    Unit tests for the RateLimiterService.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_RateLimiterService_CheckAndUpdate_WithinLimit_ReturnsAllowed(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        key = "test_user"

        # Act
        result = service.check_and_update(key)

        # Assert
        assert result.allowed is True
        assert result.remaining == service._default_limits['api']['max_requests'] - 1

    def test_RateLimiterService_CheckAndUpdate_DifferentResourceTypes_TrackedSeparately(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        key = "test_user"

        # Act - Use up some of the API quota
        for i in range(5):
            service.check_and_update(key, resource_type='api')

        # Use up some of the GPT quota
        for i in range(3):
            service.check_and_update(key, resource_type='gpt')

        # Get the current quotas
        api_quota = service.get_quota(key, resource_type='api')
        gpt_quota = service.get_quota(key, resource_type='gpt')

        # Assert
        assert api_quota.used == 5
        assert gpt_quota.used == 3

    def test_RateLimiterService_CheckAndUpdate_ExceedsLimit_ReturnsDenied(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        key = "test_user"

        # Set a very low limit for testing
        service.update_limit_config('api', 3, 60)

        # Act - Use up the entire quota
        for i in range(3):
            service.check_and_update(key)

        # This should exceed the limit
        result = service.check_and_update(key)

        # Assert
        assert result.allowed is False
        assert result.remaining == 0

    def test_RateLimiterService_GetQuota_ReturnsCorrectValues(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        key = "test_user"

        # Use some of the quota
        used_requests = 5
        for i in range(used_requests):
            service.check_and_update(key)

        # Act
        quota = service.get_quota(key)

        # Assert
        assert quota.used == used_requests
        assert quota.max_requests == service._default_limits['api']['max_requests']
        assert quota.remaining == service._default_limits['api']['max_requests'] - used_requests

    def test_RateLimiterService_ResetLimit_ClearsUsage(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        key = "test_user"

        # Use some of the quota
        for i in range(5):
            service.check_and_update(key)

        # Act
        service.reset_limit(key, resource_type='api')
        quota = service.get_quota(key)

        # Assert
        assert quota.used == 0
        assert quota.remaining == service._default_limits['api']['max_requests']

    def test_RateLimiterService_UpdateLimitConfig_ChangesLimits(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        key = "test_user"

        # Set new limits
        new_max = 50
        new_window = 30

        # Act
        service.update_limit_config('api', new_max, new_window)

        # Use the service with the new limits
        result = service.check_and_update(key)
        quota = service.get_quota(key)

        # Assert
        assert quota.max_requests == new_max
        assert quota.window_seconds == new_window
        assert result.remaining == new_max - 1

    def test_RateLimiterService_WithRateLimiting_DecoratesFunction(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)

        # Define a test function and key extractor
        def test_func(user_id, data=None):
            return f"Success for {user_id}"

        def key_extractor(user_id, data=None):
            return user_id

        # Act - Create a rate-limited function
        limited_func = service.with_rate_limiting(
            test_func,
            key_extractor,
            resource_type='api'
        )

        # Call the decorated function
        result = limited_func("user123", {"test": "data"})

        # Assert
        assert result == "Success for user123"

        # Verify rate limiting was applied
        quota = service.get_quota("user123")
        assert quota.used == 1

    def test_RateLimiterService_WithRateLimiting_ExceedsLimit_ReturnsNone(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        service.update_limit_config('api', 1, 60)  # Set limit to 1 request

        # Define a test function and key extractor
        def test_func(user_id):
            return f"Success for {user_id}"

        def key_extractor(user_id):
            return user_id

        # Act - Create a rate-limited function
        limited_func = service.with_rate_limiting(
            test_func,
            key_extractor,
            resource_type='api',
            raise_on_limit=False
        )

        # Call the function once (should succeed)
        first_result = limited_func("user123")

        # Call it again (should be rate limited)
        second_result = limited_func("user123")

        # Assert
        assert first_result == "Success for user123"
        assert second_result is None

    def test_RateLimiterService_WithRateLimiting_ExceedsLimit_RaisesException(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        service = RateLimiterService(rate_limiter)
        service.update_limit_config('api', 1, 60)  # Set limit to 1 request

        # Define a test function and key extractor
        def test_func(user_id):
            return f"Success for {user_id}"

        def key_extractor(user_id):
            return user_id

        # Act - Create a rate-limited function that raises exceptions
        limited_func = service.with_rate_limiting(
            test_func,
            key_extractor,
            resource_type='api',
            raise_on_limit=True
        )

        # Call the function once (should succeed)
        first_result = limited_func("user123")

        # Assert
        assert first_result == "Success for user123"

        # Call it again (should raise exception)
        with pytest.raises(RateLimitExceededError):
            limited_func("user123")
