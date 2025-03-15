"""
Tests for the Cache Service in the application layer.
"""

import pytest
from unittest.mock import Mock, patch
import json
import time
from datetime import datetime, timedelta

from app.application.services.cache_service import CacheService
from app.domain.models.cached_response import CachedResponse
from app.infrastructure.adapters.cache.cache_adapter import InMemoryCacheAdapter


class TestCacheService:
    """
    Unit tests for the CacheService.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_CacheService_GetNonExistent_ReturnsNone(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)

        # Act
        result = cache_service.get("non-existent-key")

        # Assert
        assert result is None

    def test_CacheService_SetAndGet_ReturnsCachedResponse(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        key = "test-key"
        value = {"data": "test-value"}

        # Act
        cached_response = cache_service.set(key, value)
        result = cache_service.get(key)

        # Assert
        assert isinstance(cached_response, CachedResponse)
        assert isinstance(result, CachedResponse)
        assert result.key == key
        assert result.content == value

    def test_CacheService_SetWithTTL_ExpiresCorrectly(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        key = "expiring-key"
        value = {"data": "expiring-value"}
        ttl_seconds = 0.1  # 100ms for quick testing

        # Act
        cache_service.set(key, value, ttl_seconds=ttl_seconds)
        result_before_expiry = cache_service.get(key)
        time.sleep(ttl_seconds * 2)  # Wait until after expiration
        result_after_expiry = cache_service.get(key)

        # Assert
        assert result_before_expiry is not None
        assert result_before_expiry.content == value
        assert result_after_expiry is None

    def test_CacheService_Delete_RemovesKey(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        key = "to-delete-key"
        value = {"data": "to-delete-value"}
        cache_service.set(key, value)

        # Act
        before_delete = cache_service.get(key)
        cache_service.delete(key)
        after_delete = cache_service.get(key)

        # Assert
        assert before_delete is not None
        assert before_delete.content == value
        assert after_delete is None

    def test_CacheService_Clear_RemovesAllKeys(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")

        # Act
        cache_service.clear()

        # Assert
        assert cache_service.get("key1") is None
        assert cache_service.get("key2") is None

    def test_CacheService_GenerateKey_CreatesConsistentKey(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        prefix = "test"
        data = {"id": 123, "name": "Test Item"}

        # Act
        key1 = cache_service.generate_key(prefix, data)
        key2 = cache_service.generate_key(prefix, data)

        # Assert
        assert key1 == key2  # Same data should produce same key
        assert key1.startswith(f"{prefix}:")  # Key should start with prefix

    def test_CacheService_GenerateKey_DifferentDataProducesDifferentKeys(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        prefix = "test"
        data1 = {"id": 123, "name": "Test Item"}
        data2 = {"id": 456, "name": "Different Item"}

        # Act
        key1 = cache_service.generate_key(prefix, data1)
        key2 = cache_service.generate_key(prefix, data2)

        # Assert
        assert key1 != key2  # Different data should produce different keys

    def test_CacheService_SetWithMetadata_IncludesMetadataInResponse(self):
        # Arrange
        cache_adapter = InMemoryCacheAdapter()
        cache_service = CacheService(cache_adapter)
        key = "meta-key"
        value = {"data": "meta-value"}
        metadata = {"source": "test", "version": "1.0"}

        # Act
        cached_response = cache_service.set(key, value, metadata=metadata)
        result = cache_service.get(key)

        # Assert
        assert cached_response.metadata == metadata
        assert result.metadata == metadata
