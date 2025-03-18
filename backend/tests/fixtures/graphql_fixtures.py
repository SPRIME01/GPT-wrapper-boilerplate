"""
GraphQL test fixtures for CopilotKit integration testing.

This module provides fixtures for testing GraphQL schema components,
including mock context, resolvers, and sample data.
"""
import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import strawberry
from strawberry.types import Info

from backend.tests.fixtures.conversation_fixtures import (
    sample_conversation_history,
    mock_conversation_db,
    Conversation,
    ConversationMessage
)


@pytest.fixture
def graphql_test_context(mock_conversation_db):
    """
    Creates a mock GraphQL context for testing.

    Args:
        mock_conversation_db: The mock conversation database fixture

    Returns:
        dict: A dictionary representing a GraphQL context object
    """
    # Create a mock container for dependency injection
    class MockContainer:
        def __init__(self, conversation_db):
            self.conversation_db = conversation_db

        def get_conversation_repository(self):
            """Returns the mock conversation repository."""
            return self.conversation_db

        def get_submit_request_use_case(self):
            """Returns a mock submit request use case."""
            from unittest.mock import AsyncMock

            async_mock = AsyncMock()
            async_mock.execute.return_value = {"request_id": "mock-request-id", "status": "success"}

            return async_mock

    # Create a mock info object
    class MockInfo:
        def __init__(self, context):
            self.context = context

    # Create the context object
    container = MockContainer(mock_conversation_db)
    context = {"container": container, "user": {"id": "test-user-1"}}

    return context


@strawberry.type
class GraphQLConversationMessage:
    """GraphQL type for conversation messages."""
    id: str
    role: str
    content: str
    timestamp: datetime
    conversation_id: str

    @classmethod
    def from_domain(cls, message: ConversationMessage) -> "GraphQLConversationMessage":
        """Convert domain model to GraphQL type."""
        return cls(
            id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            conversation_id=message.conversation_id
        )


@strawberry.type
class GraphQLConversation:
    """GraphQL type for conversations."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[GraphQLConversationMessage]

    @classmethod
    def from_domain(cls, conversation: Conversation) -> "GraphQLConversation":
        """Convert domain model to GraphQL type."""
        return cls(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[GraphQLConversationMessage.from_domain(msg) for msg in conversation.messages]
        )

    @property
    def message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages)


@strawberry.input
class CreateConversationInput:
    """Input type for creating a new conversation."""
    user_id: str
    title: str
    initial_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@strawberry.input
class AddMessageInput:
    """Input type for adding a message to a conversation."""
    conversation_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


@strawberry.input
class ChatRequestInput:
    """Input type for submitting a chat request."""
    conversation_id: str
    message: str
    stream: bool = True
    context_data: Optional[Dict[str, Any]] = None


@strawberry.type
class ChatRequestResponse:
    """Response type for chat requests."""
    request_id: str
    status: str
