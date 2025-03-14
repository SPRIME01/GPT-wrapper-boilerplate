import pytest
from datetime import datetime
from app.domain.models.gpt_request import GPTRequest

class TestGPTRequest:
    def test_create_gpt_request_with_valid_data(self):
        """Test creating a GPTRequest with valid data"""
        request_data = {
            "user_id": "user123",
            "prompt": "Tell me a joke",
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9,
            "stream": False
        }

        request = GPTRequest(**request_data)

        assert request.user_id == "user123"
        assert request.prompt == "Tell me a joke"
        assert request.temperature == 0.7
        assert request.max_tokens == 100
        assert request.top_p == 0.9
        assert request.stream is False
        assert request.request_id is not None  # Should auto-generate an ID
        assert request.timestamp is not None  # Should set current time

    def test_gpt_request_validation_errors(self):
        """Test validation errors when creating GPTRequest with invalid data"""
        with pytest.raises(ValueError):
            # Test empty prompt
            GPTRequest(user_id="user123", prompt="", temperature=0.7)

        with pytest.raises(ValueError):
            # Test invalid temperature (outside valid range)
            GPTRequest(user_id="user123", prompt="Hello", temperature=2.0)

        with pytest.raises(ValueError):
            # Test invalid max_tokens (negative)
            GPTRequest(user_id="user123", prompt="Hello", max_tokens=-10)

    def test_gpt_request_default_values(self):
        """Test default values are set correctly when not provided"""
        request = GPTRequest(user_id="user123", prompt="Hello GPT")

        assert request.temperature == 0.7  # Default temperature
        assert request.max_tokens == 150  # Default max_tokens
        assert request.top_p == 1.0  # Default top_p
        assert request.stream is False  # Default stream

    def test_gpt_request_equality(self):
        """Test that two requests with same request_id are considered equal"""
        request1 = GPTRequest(user_id="user123", prompt="Hello", request_id="abc123")
        request2 = GPTRequest(user_id="user456", prompt="Different", request_id="abc123")
        request3 = GPTRequest(user_id="user123", prompt="Hello")

        assert request1 == request2  # Same request_id
        assert request1 != request3  # Different request_id
