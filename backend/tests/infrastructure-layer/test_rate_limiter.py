"""
Tests for rate limiting functionality.

This module contains unit tests for the rate limiter adapter implementations.
Following AAA pattern (Arrange, Act, Assert) for all tests.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Import the interfaces and implementations that will be created
from app.infrastructure.adapters.rate_limiting.rate_limiter import (
    RateLimiter,
    InMemoryRateLimiter,
    RedisRateLimiter,
    RateLimitExceededError
)


class TestRateLimiter:
    """
    Tests for the rate limiter adapter implementations.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_InMemoryRateLimiter_CheckLimit_WithinLimit_AllowsOperation(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key = "test_user_id"
        max_requests = 5
        window_seconds = 60

        # Act
        for i in range(max_requests):
            result = rate_limiter.check_limit(key, max_requests, window_seconds)

        # Assert
        assert result.allowed is True
        assert result.remaining == 0

    def test_InMemoryRateLimiter_CheckLimit_ExceedsLimit_BlocksOperation(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key = "test_user_id"
        max_requests = 3
        window_seconds = 60

        # Send exactly max_requests requests
        for i in range(max_requests):
            rate_limiter.check_limit(key, max_requests, window_seconds)

        # Act & Assert
        # The next request should be blocked
        result = rate_limiter.check_limit(key, max_requests, window_seconds)
        assert result.allowed is False
        assert result.remaining == 0

    def test_InMemoryRateLimiter_CheckLimit_WindowExpires_ResetsCounter(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key = "test_user_id"
        max_requests = 3
        window_seconds = 0.1  # Short window for testing

        # Use up all requests
        for i in range(max_requests):
            rate_limiter.check_limit(key, max_requests, window_seconds)

        # Act
        # Wait for the window to expire
        time.sleep(window_seconds * 2)
        result = rate_limiter.check_limit(key, max_requests, window_seconds)

        # Assert
        assert result.allowed is True
        assert result.remaining == max_requests - 1

    def test_InMemoryRateLimiter_GetCurrentQuota_ReturnsCorrectValues(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key = "test_user_id"
        max_requests = 10
        window_seconds = 60

        # Make some requests
        used_requests = 3
        for i in range(used_requests):
            rate_limiter.check_limit(key, max_requests, window_seconds)

        # Act
        quota = rate_limiter.get_quota(key, max_requests, window_seconds)

        # Assert
        assert quota.max_requests == max_requests
        assert quota.used == used_requests
        assert quota.remaining == max_requests - used_requests
        assert quota.reset_at is not None  # Should have a reset time

    def test_InMemoryRateLimiter_ResetLimit_ClearsUsage(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key = "test_user_id"
        max_requests = 5
        window_seconds = 60

        # Use some of the quota
        for i in range(3):
            rate_limiter.check_limit(key, max_requests, window_seconds)

        # Act
        rate_limiter.reset_limit(key)
        quota = rate_limiter.get_quota(key, max_requests, window_seconds)

        # Assert
        assert quota.used == 0
        assert quota.remaining == max_requests

    def test_InMemoryRateLimiter_MultipleKeys_TrackSeparately(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key1 = "user_1"
        key2 = "user_2"
        max_requests = 5
        window_seconds = 60

        # Act
        # Use some requests for key1
        for i in range(3):
            rate_limiter.check_limit(key1, max_requests, window_seconds)

        # Use different amount for key2
        for i in range(2):
            rate_limiter.check_limit(key2, max_requests, window_seconds)

        # Get quotas
        quota1 = rate_limiter.get_quota(key1, max_requests, window_seconds)
        quota2 = rate_limiter.get_quota(key2, max_requests, window_seconds)

        # Assert
        assert quota1.used == 3
        assert quota2.used == 2
        assert quota1.remaining == 2
        assert quota2.remaining == 3

    def test_InMemoryRateLimiter_DifferentLimits_AppliedCorrectly(self):
        # Arrange
        rate_limiter = InMemoryRateLimiter()
        key = "api_client"

        # Define two different limit configurations
        standard_limit = 5
        standard_window = 60

        premium_limit = 20
        premium_window = 60

        # Act & Assert
        # Check with standard limit
        for i in range(standard_limit):
            result = rate_limiter.check_limit(key, standard_limit, standard_window)
            assert result.allowed is True

        # This should exceed the standard limit
        result = rate_limiter.check_limit(key, standard_limit, standard_window)
        assert result.allowed is False

        # But with premium limit it should still be allowed
        rate_limiter.reset_limit(key)  # Reset to test with premium limit
        for i in range(premium_limit):
            result = rate_limiter.check_limit(key, premium_limit, premium_window)
            assert result.allowed is True

        # This should exceed the premium limit
        result = rate_limiter.check_limit(key, premium_limit, premium_window)
        assert result.allowed is False

    # Redis Rate Limiter tests would be more complex and require mocking
    # This is a simplified test with mocks
    def test_RedisRateLimiter_CheckLimit_WithinLimit_AllowsOperation(self):
        # Arrange
        mock_redis_client = Mock()

        # Mock pipeline for check_limit method
        mock_pipeline = Mock()
        # Return values from pipe.execute() for:
        # 1. zadd (number of elements added)
        # 2. zremrangebyscore (number of elements removed)
        # 3. zcard (count of elements/used requests)
        # 4. expire (True if set, False otherwise)
        mock_pipeline.execute.return_value = [1, 2, 3, True]
        mock_redis_client.pipeline.return_value = mock_pipeline

        # Mock zrange to return a timestamp for the oldest entry
        # Format: [(value, score)] where score is the timestamp
        now = time.time()
        oldest_timestamp = now - 10  # 10 seconds old
        mock_redis_client.zrange.return_value = [(b'data', oldest_timestamp)]

        # Create rate limiter with our mocked Redis client
        rate_limiter = RedisRateLimiter(redis_client=mock_redis_client)
        key = "test_user_id"
        max_requests = 5
        window_seconds = 60

        # Act
        result = rate_limiter.check_limit(key, max_requests, window_seconds)

        # Assert
        assert result.allowed is True
        assert result.remaining == 2  # 5 max - 3 used = 2 remaining

        # Verify Redis commands were called correctly
        mock_redis_client.pipeline.assert_called_once()
        mock_pipeline.zadd.assert_called_once()
        mock_pipeline.zremrangebyscore.assert_called_once()
        mock_pipeline.zcard.assert_called_once()
        mock_pipeline.expire.assert_called_once()
        mock_redis_client.zrange.assert_called_once()

    def test_RedisRateLimiter_CheckLimit_ExceedsLimit_BlocksOperation(self):
        # Arrange
        mock_redis_client = Mock()

        # Set up pipeline mock to return a count higher than max_requests
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [1, 2, 6, True]  # 6 used requests
        mock_redis_client.pipeline.return_value = mock_pipeline

        # Mock zrange for reset time calculation
        now = time.time()
        mock_redis_client.zrange.return_value = [(b'data', now - 30)]  # 30 seconds old

        rate_limiter = RedisRateLimiter(redis_client=mock_redis_client)
        key = "test_user_id"
        max_requests = 5  # Max is 5, but our mock returns 6 used
        window_seconds = 60

        # Act
        result = rate_limiter.check_limit(key, max_requests, window_seconds)

        # Assert
        assert result.allowed is False
        assert result.remaining == 0

    def test_RedisRateLimiter_GetQuota_ReturnsCorrectValues(self):
        # Arrange
        mock_redis_client = Mock()

        # Mock pipeline for get_quota method
        mock_pipeline = Mock()
        # Return values from pipe.execute() for:
        # 1. zremrangebyscore (number of elements removed)
        # 2. zcard (count of elements/used requests)
        mock_pipeline.execute.return_value = [2, 4]  # 4 used requests
        mock_redis_client.pipeline.return_value = mock_pipeline

        # Mock zrange for reset time calculation
        now = time.time()
        mock_redis_client.zrange.return_value = [(b'data', now - 20)]  # 20 seconds old

        rate_limiter = RedisRateLimiter(redis_client=mock_redis_client)
        key = "test_user_id"
        max_requests = 10
        window_seconds = 60

        # Act
        quota = rate_limiter.get_quota(key, max_requests, window_seconds)

        # Assert
        assert quota.max_requests == max_requests
        assert quota.used == 4
        assert quota.remaining == 6  # 10 max - 4 used
        assert quota.reset_at is not None

    def test_RedisRateLimiter_ResetLimit_DeletesKeys(self):
        # Arrange
        mock_redis_client = Mock()
        mock_redis_client.keys.return_value = ["rate_limit:test_key:10:60", "rate_limit:test_key:5:30"]

        rate_limiter = RedisRateLimiter(redis_client=mock_redis_client)
        key = "test_key"

        # Act
        rate_limiter.reset_limit(key)

        # Assert
        mock_redis_client.keys.assert_called_once_with("rate_limit:test_key:*")
        mock_redis_client.delete.assert_called_once_with(
            "rate_limit:test_key:10:60",
            "rate_limit:test_key:5:30"
        )
