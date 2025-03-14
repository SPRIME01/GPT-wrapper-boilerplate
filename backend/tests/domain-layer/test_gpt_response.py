import pytest
from app.domain.models.gpt_response import GPTResponse

class TestGPTResponse:
    def test_create_gpt_response_with_valid_data(self):
        """Test creating a GPTResponse with valid data"""
        response_data = {
            "user_id": "user123",
            "request_id": "req456",
            "text": "Here's a joke: Why did the programmer quit his job? Because he didn't get arrays.",
            "tokens_used": 42,
            "finish_reason": "stop"
        }

        response = GPTResponse(**response_data)

        assert response.user_id == "user123"
        assert response.request_id == "req456"
        assert response.text == "Here's a joke: Why did the programmer quit his job? Because he didn't get arrays."
        assert response.tokens_used == 42
        assert response.finish_reason == "stop"
        assert response.response_id is not None  # Should auto-generate an ID
        assert response.timestamp is not None  # Should set current time

    def test_gpt_response_validation_errors(self):
        """Test validation errors when creating GPTResponse with invalid data"""
        with pytest.raises(ValueError):
            # Test empty text
            GPTResponse(user_id="user123", request_id="req456", text="", tokens_used=42)

        with pytest.raises(ValueError):
            # Test invalid tokens_used (negative)
            GPTResponse(user_id="user123", request_id="req456", text="Some text", tokens_used=-5)

    def test_gpt_response_default_values(self):
        """Test default values are set correctly when not provided"""
        response = GPTResponse(user_id="user123", request_id="req456", text="Some response")

        assert response.tokens_used == 0  # Default tokens_used
        assert response.finish_reason == "stop"  # Default finish_reason

    def test_gpt_response_equality(self):
        """Test that two responses with same response_id are considered equal"""
        response1 = GPTResponse(user_id="user123", request_id="req1", text="Hello", response_id="res123")
        response2 = GPTResponse(user_id="user456", request_id="req2", text="Different", response_id="res123")
        response3 = GPTResponse(user_id="user123", request_id="req1", text="Hello")

        assert response1 == response2  # Same response_id
        assert response1 != response3  # Different response_id
