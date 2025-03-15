import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import time

# Import the interfaces and implementations that will be created
from app.infrastructure.adapters.cache.cache_adapter import CacheAdapter, InMemoryCacheAdapter, RedisCacheAdapter

class TestCacheAdapter:
    """
    Tests for the cache adapter implementations.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_InMemoryCache_SetGet_ReturnsStoredValue(self):
        # Arrange
        cache = InMemoryCacheAdapter()
        key = "test_key"
        value = {"data": "test_value"}

        # Act
        cache.set(key, value)
        result = cache.get(key)

        # Assert
        assert result == value

    def test_InMemoryCache_GetNonExistentKey_ReturnsNone(self):
        # Arrange
        cache = InMemoryCacheAdapter()
        key = "non_existent_key"

        # Act
        result = cache.get(key)

        # Assert
        assert result is None

    def test_InMemoryCache_SetWithTTL_ExpiresAfterTTL(self):
        # Arrange
        cache = InMemoryCacheAdapter()
        key = "expiring_key"
        value = {"data": "will_expire"}
        ttl_seconds = 0.1  # 100ms for quick testing

        # Act
        cache.set(key, value, ttl_seconds=ttl_seconds)
        result_before_expiry = cache.get(key)
        time.sleep(ttl_seconds * 2)  # Wait until after expiration
        result_after_expiry = cache.get(key)

        # Assert
        assert result_before_expiry == value
        assert result_after_expiry is None

    def test_InMemoryCache_Delete_RemovesKey(self):
        # Arrange
        cache = InMemoryCacheAdapter()
        key = "to_be_deleted"
        value = {"data": "delete_me"}
        cache.set(key, value)

        # Act
        before_delete = cache.get(key)
        cache.delete(key)
        after_delete = cache.get(key)

        # Assert
        assert before_delete == value
        assert after_delete is None

    def test_InMemoryCache_Clear_RemovesAllKeys(self):
        # Arrange
        cache = InMemoryCacheAdapter()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Act
        cache.clear()

        # Assert
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    @pytest.mark.parametrize("key,value", [
        ("string_key", "string_value"),
        ("dict_key", {"nested": "value"}),
        ("list_key", [1, 2, 3]),
        ("int_key", 42),
        ("bool_key", True),
    ])
    def test_InMemoryCache_VariousDataTypes_PreservesType(self, key, value):
        # Arrange
        cache = InMemoryCacheAdapter()

        # Act
        cache.set(key, value)
        result = cache.get(key)

        # Assert
        assert result == value
        assert type(result) == type(value)

    # Redis Cache Adapter tests would be more complex and might require mocking
    # This is a simplified test with mocks
    def test_RedisCache_SetGet_ReturnsStoredValue(self):
        # Arrange
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = b'{"data": "test_value"}'
        cache = RedisCacheAdapter(redis_client=mock_redis_client)
        key = "test_key"
        value = {"data": "test_value"}

        # Act
        cache.set(key, value)
        result = cache.get(key)

        # Assert
        mock_redis_client.set.assert_called_once()
        mock_redis_client.get.assert_called_once()
        assert result == value
