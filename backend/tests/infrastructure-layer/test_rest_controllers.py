import pytest
from unittest.mock import AsyncMock
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

@pytest.mark.asyncio
async def test_health_check(test_client):
    # Act
    response = test_client.get("/api/health")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_submit_prompt_success(test_client, mock_submit_use_case):
    # Arrange
    test_data = {
        "prompt": "test prompt",
        "max_tokens": 100,
        "user_id": "test_user"
    }

    # Configure specific response for this test
    mock_submit_use_case.execute.return_value = {
        "data": {
            "response": "Test response for prompt",
            "tokens_used": 42,
            "finish_reason": "stop"
        }
    }

    # Act
    response = test_client.post("/api/v1/gpt/prompt", json=test_data)

    # Print response for debugging if test fails
    if response.status_code != 200:
        print(f"Response error: {response.json()}")

    # Assert
    assert response.status_code == 200
    assert "text" in response.json()
    assert "tokens_used" in response.json()
    assert "finish_reason" in response.json()

@pytest.mark.asyncio
async def test_submit_prompt_validation_error(test_client):
    # Arrange - Test with missing required fields
    test_data = {
        "prompt": "test prompt"
        # missing max_tokens and user_id
    }

    # Act
    response = test_client.post("/api/v1/gpt/prompt", json=test_data)

    # Assert
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_create_session_success(test_client, mock_conversation_repo):
    # Arrange
    test_data = {
        "user_id": "test_user",
        "preferences": {
            "language": "en",
            "model": "gpt-4"
        }
    }

    # Configure specific response for this test
    mock_conversation_repo.create_session.return_value = {
        "id": "test-session-1",
        "created_at": "2024-01-01T00:00:00Z",
        "user_id": test_data["user_id"]
    }

    # Act
    response = test_client.post("/api/v1/session", json=test_data)

    # Print response for debugging if test fails
    if response.status_code != 201:
        print(f"Response error: {response.json()}")

    # Assert
    assert response.status_code == 201
    assert "session_id" in response.json()
    assert "user_id" in response.json()

@pytest.mark.asyncio
async def test_get_history(test_client, mock_conversation_repo):
    # Arrange
    user_id = "test_user"
    test_request = GPTRequest(prompt="test prompt", user_id=user_id)
    test_response = GPTResponse(
        text="test response",
        tokens_used=10,
        user_id=user_id,
        request_id="test_request"
    )

    # Configure specific response for this test
    mock_conversation_repo.get_conversations_by_user.return_value = [
        {
            "id": "test_convo",
            "messages": [
                {"role": "user", "content": test_request.prompt},
                {"role": "assistant", "content": test_response.text}
            ]
        }
    ]

    # Act
    response = test_client.get(f"/api/v1/history/{user_id}")

    # Print response for debugging if test fails
    if response.status_code != 200:
        print(f"Response error: {response.json()}")

    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == user_id
    assert "conversations" in response.json()
