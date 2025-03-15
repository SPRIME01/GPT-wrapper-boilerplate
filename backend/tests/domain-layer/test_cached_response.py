"""
Tests for the CachedResponse domain model.
"""

import pytest
from datetime import datetime, timedelta
import time
from app.domain.models.cached_response import CachedResponse


class TestCachedResponse:
    """
    Unit tests for the CachedResponse domain model.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_CachedResponse_Create_ReturnsValidInstance(self):
        # Arrange
        key = "test-key"
        content = {"data": "test-value"}

        # Act
        cached_response = CachedResponse.create(key, content)

        # Assert
        assert cached_response.key == key
        assert cached_response.content == content
        assert isinstance(cached_response.created_at, datetime)
        assert cached_response.expires_at is None
        assert cached_response.metadata == {}

    def test_CachedResponse_CreateWithTTL_SetsExpirationTime(self):
        # Arrange
        key = "test-key"
        content = {"data": "test-value"}
        ttl_seconds = 3600  # 1 hour

        # Act
        cached_response = CachedResponse.create(key, content, ttl_seconds=ttl_seconds)

        # Assert
        assert cached_response.key == key
        assert cached_response.content == content
        assert cached_response.expires_at is not None
        # Should expire approximately ttl_seconds in the future
        expected_expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        # Allow for small timing differences (within 5 seconds)
        assert abs((cached_response.expires_at - expected_expiry).total_seconds()) < 5

    def test_CachedResponse_IsExpired_ReturnsFalseForNonExpired(self):
        # Arrange
        cached_response = CachedResponse.create("test-key", "test-value", ttl_seconds=3600)

        # Act
        is_expired = cached_response.is_expired

        # Assert
        assert is_expired is False

    def test_CachedResponse_IsExpired_ReturnsTrueForExpired(self):
        # Arrange
        # Create a response that's already expired by setting a past expiration time
        now = datetime.now()
        expired_time = now - timedelta(seconds=10)  # 10 seconds in the past

        cached_response = CachedResponse(
            key="test-key",
            content="test-value",
            created_at=now - timedelta(seconds=20),  # 20 seconds in the past
            expires_at=expired_time,
            metadata={}
        )

        # Act
        is_expired = cached_response.is_expired

        # Assert
        assert is_expired is True

    def test_CachedResponse_TimeToLive_ReturnsCorrectValue(self):
        # Arrange
        ttl_seconds = 3600  # 1 hour
        cached_response = CachedResponse.create("test-key", "test-value", ttl_seconds=ttl_seconds)

        # Act
        remaining_ttl = cached_response.time_to_live

        # Assert
        # Should be close to the original ttl (allow for small timing differences)
        assert abs(remaining_ttl - ttl_seconds) < 5

    def test_CachedResponse_TimeToLive_ReturnsNoneForNoExpiration(self):
        # Arrange
        cached_response = CachedResponse.create("test-key", "test-value")

        # Act
        remaining_ttl = cached_response.time_to_live

        # Assert
        assert remaining_ttl is None

    def test_CachedResponse_TimeToLive_ReturnsZeroForExpired(self):
        # Arrange
        # Create a response that's already expired
        now = datetime.now()
        cached_response = CachedResponse(
            key="test-key",
            content="test-value",
            created_at=now - timedelta(seconds=20),
            expires_at=now - timedelta(seconds=10),  # 10 seconds in the past
            metadata={}
        )

        # Act
        remaining_ttl = cached_response.time_to_live

        # Assert
        assert remaining_ttl == 0.0

    def test_CachedResponse_CreateWithMetadata_SetsMetadata(self):
        # Arrange
        key = "test-key"
        content = {"data": "test-value"}
        metadata = {"source": "api", "version": "1.0"}

        # Act
        cached_response = CachedResponse.create(key, content, metadata=metadata)

        # Assert
        assert cached_response.metadata == metadata
