"""
Tests for error handling in CopilotKit GraphQL schema components.

This module tests the error handling mechanisms in the GraphQL schema designed for CopilotKit integration.
"""

import pytest
import strawberry
from strawberry.test import client
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import test fixtures with fallback mechanism
try:
    from backend.tests.fixtures.conversation_fixtures import (
        sample_conversation_history,
        mock_conversation_db,
        Conversation,
        ConversationMessage
    )
except ImportError:
    from ..fixtures.conversation_fixtures import (
        sample_conversation_history,
        mock_conversation_db,
        Conversation,
        ConversationMessage
    )

# GraphQL Message Type
@strawberry.type
class GraphQLConversationMessage:
    """GraphQL type for conversation messages."""
    id: str
    role: str
    content: str
    timestamp: datetime
    conversation_id: str = strawberry.field(name="conversationId")

# GraphQL Conversation Type
@strawberry.type
class GraphQLConversation:
    """GraphQL type for conversations."""
    id: str
    title: str
    created_at: datetime = strawberry.field(name="createdAt")
    updated_at: datetime = strawberry.field(name="updatedAt")
    messages: List[GraphQLConversationMessage]

    @strawberry.field
    def message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages)

# Input Types
@strawberry.input
class CreateConversationInput:
    """Input type for creating a new conversation."""
    user_id: str = strawberry.field(name="userId")
    title: str
    initial_message: Optional[str] = strawberry.field(
        default=None,
        name="initialMessage"
    )
    metadata: Optional[Dict[str, Any]] = None

@strawberry.input
class AddMessageInput:
    """Input type for adding a message to a conversation."""
    conversation_id: str = strawberry.field(name="conversationId")
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

@strawberry.input
class ChatRequestInput:
    """Input type for submitting a chat request."""
    conversation_id: str = strawberry.field(name="conversationId")
    message: str
    stream: bool = True
    context_data: Optional[Dict[str, Any]] = strawberry.field(
        default=None,
        name="contextData"
    )

# Response Types
@strawberry.type
class ChatRequestResponse:
    """Response type for chat requests."""
    request_id: str = strawberry.field(name="requestId")
    status: str

@pytest.fixture
def error_handling_schema():
    """Create a schema with error handling for testing."""
    @strawberry.type
    class Query:
        @strawberry.field
        def placeholder(self) -> str:
            return "placeholder"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_conversation(self, input: CreateConversationInput) -> GraphQLConversation:
            if input.user_id == "error-user":
                raise ValueError("Error creating conversation")
            return GraphQLConversation(
                id="new-conv-123",
                title=input.title,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[]
            )

        @strawberry.mutation
        def add_message(self, input: AddMessageInput) -> GraphQLConversationMessage:
            if input.conversation_id == "error-conv":
                raise ValueError("Error adding message")
            return GraphQLConversationMessage(
                id="msg-123",
                role=input.role,
                content=input.content,
                timestamp=datetime.now(),
                conversation_id=input.conversation_id
            )

        @strawberry.mutation
        async def submit_chat_request(self, input: ChatRequestInput) -> ChatRequestResponse:
            if input.conversation_id == "error-conv":
                raise ValueError("Error submitting chat request")
            return ChatRequestResponse(
                request_id="req-12345",
                status="processing"
            )

    return strawberry.Schema(query=Query, mutation=Mutation)

@pytest.mark.asyncio
async def test_create_conversation_mutation_raises_error_when_user_id_is_invalid(
    error_handling_schema
):
    """Test that the createConversation mutation raises an error for invalid user ID."""
    # Arrange
    mutation = """
    mutation CreateConversation($input: CreateConversationInput!) {
        createConversation(input: $input) {
            id
            title
        }
    }
    """
    variables = {"input": {"userId": "error-user", "title": "Test Conversation"}}

    # Act
    result = await client.query(
        error_handling_schema,
        mutation,
        variables=variables
    )

    # Assert
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert "Error creating conversation" in result["errors"][0]["message"]

@pytest.mark.asyncio
async def test_add_message_mutation_raises_error_when_conversation_id_is_invalid(
    error_handling_schema
):
    """Test that the addMessage mutation raises an error for invalid conversation ID."""
    # Arrange
    mutation = """
    mutation AddMessage($input: AddMessageInput!) {
        addMessage(input: $input) {
            id
            role
            content
        }
    }
    """
    variables = {"input": {"conversationId": "error-conv", "role": "user", "content": "Test message"}}

    # Act
    result = await client.query(
        error_handling_schema,
        mutation,
        variables=variables
    )

    # Assert
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert "Error adding message" in result["errors"][0]["message"]

@pytest.mark.asyncio
async def test_submit_chat_request_mutation_raises_error_when_conversation_id_is_invalid(
    error_handling_schema
):
    """Test that the submitChatRequest mutation raises an error for invalid conversation ID."""
    # Arrange
    mutation = """
    mutation SubmitChatRequest($input: ChatRequestInput!) {
        submitChatRequest(input: $input) {
            requestId
            status
        }
    }
    """
    variables = {"input": {"conversationId": "error-conv", "message": "Test message"}}

    # Act
    result = await client.query(
        error_handling_schema,
        mutation,
        variables=variables
    )

    # Assert
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert "Error submitting chat request" in result["errors"][0]["message"]
