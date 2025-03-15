import pytest
import json
from typing import Dict, Any
from app.infrastructure.adapters.http.graphql_schema import schema
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

@pytest.fixture
def client():
    # Using schema directly for testing
    return schema

class TestGraphQLResolvers:
    @pytest.mark.asyncio
    async def test_submit_prompt_mutation(self, client, mock_schema_container, mock_submit_use_case):
        # Arrange
        prompt = "test prompt"
        user_id = "test_user"

        # Act
        mutation = """
            mutation($request: GPTRequestInput!) {
                submitGptRequest(request: $request) {
                    text
                    tokensUsed
                    finishReason
                }
            }
        """

        result = await client.execute(
            mutation,
            variable_values={"request": {"prompt": prompt, "userId": user_id}}
        )

        # Assert - properly handle ExecutionResult
        assert result.errors is None or len(result.errors) == 0
        assert result.data is not None
        assert "submitGptRequest" in result.data
        assert "text" in result.data["submitGptRequest"]
        assert "tokensUsed" in result.data["submitGptRequest"]

    @pytest.mark.asyncio
    async def test_get_conversation_history_query(self, client, mock_schema_container, mock_conversation_repo):
        # Arrange
        conversation_id = "test_conversation"

        # Setup mock response for this specific test
        mock_conversation_repo.get_conversation.return_value = {
            "id": conversation_id,
            "messages": [
                {"role": "user", "content": "test prompt"},
                {"role": "assistant", "content": "test response"}
            ]
        }

        # Act
        query = """
            query($conversationId: String!) {
                conversationHistory(conversationId: $conversationId) {
                    id
                    messages {
                        role
                        content
                    }
                }
            }
        """

        result = await client.execute(
            query,
            variable_values={"conversationId": conversation_id}
        )

        # Assert - properly handle ExecutionResult
        assert result.errors is None or len(result.errors) == 0
        assert result.data is not None
        assert "conversationHistory" in result.data
        assert "id" in result.data["conversationHistory"]
        assert "messages" in result.data["conversationHistory"]

    @pytest.mark.asyncio
    async def test_create_session_mutation(self, client, mock_schema_container, mock_conversation_repo):
        # Arrange
        user_id = "test_user"
        name = "Test Session"

        # Setup mock response for this specific test
        mock_conversation_repo.create_session.return_value = {
            "id": "test-session",
            "userId": user_id,
            "name": name,
            "messages": []
        }

        # Act
        mutation = """
            mutation($sessionInput: SessionInput!) {
                createSession(sessionInput: $sessionInput) {
                    id
                    messages {
                        role
                        content
                    }
                }
            }
        """

        result = await client.execute(
            mutation,
            variable_values={"sessionInput": {"userId": user_id, "name": name}}
        )

        # Assert - properly handle ExecutionResult
        assert result.errors is None or len(result.errors) == 0
        assert result.data is not None
        assert "createSession" in result.data
        assert "id" in result.data["createSession"]
        assert "messages" in result.data["createSession"]

@pytest.mark.asyncio
async def test_conversation_history_query(mock_schema_container, mock_conversation_repo):
    # Arrange
    user_id = "test_user"
    test_request = GPTRequest(prompt="test prompt", user_id=user_id)
    test_response = GPTResponse(
        text="test response",
        tokens_used=10,
        user_id=user_id,
        request_id="test_request"
    )

    # Setup mock response for this specific test
    mock_conversation_repo.get_conversation.return_value = {
        "id": "default",
        "messages": [
            {"role": "user", "content": test_request.prompt},
            {"role": "assistant", "content": test_response.text}
        ]
    }

    # Act
    query = """
        query {
            conversationHistory(conversationId: "default") {
                id
                messages {
                    role
                    content
                }
            }
        }
    """

    result = await schema.execute(query)

    # Assert
    assert result.errors is None or len(result.errors) == 0
    assert result.data is not None
    assert result.data["conversationHistory"]["id"] == "default"
    assert len(result.data["conversationHistory"]["messages"]) == 2
    assert result.data["conversationHistory"]["messages"][0]["role"] == "user"
    assert result.data["conversationHistory"]["messages"][0]["content"] == test_request.prompt

@pytest.mark.asyncio
async def test_submit_gpt_request_mutation(mock_schema_container, mock_submit_use_case):
    # Arrange
    test_prompt = "test prompt"
    test_user_id = "test_user"

    # Act
    mutation = """
        mutation($request: GPTRequestInput!) {
            submitGptRequest(request: $request) {
                text
                tokensUsed
                finishReason
            }
        }
    """

    result = await schema.execute(
        mutation,
        variable_values={
            "request": {
                "prompt": test_prompt,
                "userId": test_user_id
            }
        }
    )

    # Assert
    assert result.errors is None or len(result.errors) == 0
    assert result.data is not None
    assert "submitGptRequest" in result.data
    assert "text" in result.data["submitGptRequest"]
    assert "tokensUsed" in result.data["submitGptRequest"]
