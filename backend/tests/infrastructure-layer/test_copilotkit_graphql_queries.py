"""
Tests for CopilotKit GraphQL queries.

This module tests the GraphQL queries designed for CopilotKit integration,
including types, queries, and functionality for conversation management and chat functionality.
"""

import pytest
import strawberry
from datetime import datetime
from typing import List, Dict, Any, Optional
from strawberry.scalars import JSON
from strawberry.test import client

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
    context_data: Optional[Dict[str, Any]] = strawberry.field(default=None, name="contextData")

@strawberry.type
class ChatRequestResponse:
    """Response type for chat requests."""
    request_id: str = strawberry.field(name="requestId")
    status: str

    @pytest.mark.asyncio
    async def test_conversations_query_raises_error_when_database_error_occurs(
        self, graphql_context, error_handling_schema
    ):
        """Test that the conversations query properly handles database errors."""
        # Arrange
        query = """
        query GetUserConversations($userId: String!) {
            conversations(userId: $userId)
        }
        """
        variables = {"userId": "error-user"}

        # Act
        result = await client.query(
            error_handling_schema,
            query,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Error fetching conversations" in result["errors"][0]["message"]

    @pytest.mark.asyncio
    async def test_conversation_query_raises_error_when_retrieval_error_occurs(
        self, graphql_context, error_handling_schema
    ):
        """Test that the conversation query properly handles retrieval errors."""
        # Arrange
        query = """
        query GetConversation($id: String!) {
            conversation(id: $id)
        }
        """
        variables = {"id": "error-conv"}

        # Act
        result = await client.query(
            error_handling_schema,
            query,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Error fetching conversation" in result["errors"][0]["message"]

    @pytest.fixture
    def validation_schema(self):
        """Create a schema with input validation for testing."""
        @strawberry.type
        class Query:
            @strawberry.field
            def placeholder(self) -> str:
                return "placeholder"

        @strawberry.type
        class ValidationError:
            field: str
            message: str

        @strawberry.type
        class CreateConversationSuccess:
            id: str
            title: str

        @strawberry.type
        class CreateConversationResult:
            @strawberry.field
            def success(self) -> Optional[CreateConversationSuccess]:
                return self._success if hasattr(self, "_success") else None

            @strawberry.field
            def errors(self) -> List[ValidationError]:
                return self._errors if hasattr(self, "_errors") else []

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def create_conversation(self, input: CreateConversationInput) -> CreateConversationResult:
                result = CreateConversationResult()
                errors = []

                # Validate title
                if not input.title or len(input.title) < 3:
                    errors.append(ValidationError(
                        field="title",
                        message="Title must be at least 3 characters long"
                    ))

                # Validate user ID
                if not input.user_id:
                    errors.append(ValidationError(
                        field="userId",
                        message="User ID is required"
                    ))

                if errors:
                    result._errors = errors
                else:
                    result._success = CreateConversationSuccess(
                        id="new-conv-123",
                        title=input.title
                    )

                return result

        return strawberry.Schema(query=Query, mutation=Mutation)

    @pytest.mark.asyncio
    async def test_conversations_query_returns_user_conversations_when_valid_user_id_provided(
        self, graphql_context, mock_conversation_db, sample_conversation_history, conversations_query_schema
    ):
        """
        Test that the conversations query returns all conversations for a specific user.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            sample_conversation_history: Sample conversation data
            conversations_query_schema: GraphQL schema for testing
        """
        # Arrange
        query = """
        query GetUserConversations($userId: String!) {
            conversations(userId: $userId) {
                id
                title
                createdAt
                updatedAt
                messageCount
            }
        }
        """

        variables = {"userId": "test-user-1"}

        # Act
        # Use the client module directly, not as a class
        result = await client.query(
            conversations_query_schema,
            query,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "conversations" in result["data"]
        conversations = result["data"]["conversations"]
        assert len(conversations) == 2

        # Check conversation fields
        for conversation in conversations:
            assert "id" in conversation
            assert "title" in conversation
            assert "createdAt" in conversation
            assert "updatedAt" in conversation
            assert "messageCount" in conversation

        # Verify expected conversations are returned
        titles = [conv["title"] for conv in conversations]
        assert "Weather Inquiry" in titles
        assert "Python Programming Help" in titles

    @pytest.fixture
    def conversations_query_schema(self, graphql_context):
        """
        Create a schema with conversations query for testing.

        Args:
            graphql_context: GraphQL context fixture

        Returns:
            Schema: A Strawberry schema with conversations query
        """
        @strawberry.type
        class Query:
            @strawberry.field
            def conversations(self, user_id: str) -> List[GraphQLConversation]:
                """Get conversations for a user."""
                repository = graphql_context["container"].get_conversation_repository()
                conversations = repository["get_user_conversations"](user_id)
                return [
                    GraphQLConversation(
                        id=conv.id,
                        title=conv.title,
                        created_at=conv.created_at,
                        updated_at=conv.updated_at,
                        messages=[
                            GraphQLConversationMessage(
                                id=msg.id,
                                role=msg.role,
                                content=msg.content,
                                timestamp=msg.timestamp,
                                conversation_id=msg.conversation_id
                            )
                            for msg in conv.messages
                        ]
                    )
                    for conv in conversations
                ]

        return strawberry.Schema(query=Query)

    @pytest.mark.asyncio
    async def test_create_conversation_mutation_returns_validation_errors_when_input_invalid(
        self, validation_schema
    ):
        """Test that the createConversation mutation validates input and returns proper errors."""
        # Arrange
        mutation = """
        mutation TestCreateConversation($input: CreateConversationInput!) {
            createConversation(input: $input) {
                success {
                    id
                    title
                }
                errors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "input": {
                "userId": "",
                "title": "AB",
                "initialMessage": "Hello"
            }
        }

        # Act
        result = await client.query(
            validation_schema,
            mutation,
            variables=variables
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "createConversation" in result["data"]
        response = result["data"]["createConversation"]

        assert response["success"] is None
        assert len(response["errors"]) == 2

        error_fields = [error["field"] for error in response["errors"]]
        assert "title" in error_fields
        assert "userId" in error_fields

    @pytest.mark.asyncio
    async def test_create_conversation_mutation_returns_success_when_input_valid(
        self, validation_schema
    ):
        """Test that the createConversation mutation returns success for valid input."""
        # Arrange
        mutation = """
        mutation TestCreateConversation($input: CreateConversationInput!) {
            createConversation(input: $input) {
                success {
                    id
                    title
                }
                errors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "input": {
                "userId": "test-user-1",
                "title": "Valid Title",
                "initialMessage": "Hello"
            }
        }

        # Act
        result = await client.query(
            validation_schema,
            mutation,
            variables=variables
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "createConversation" in result["data"]
        response = result["data"]["createConversation"]

        assert response["success"] is not None
        assert response["success"]["id"] == "new-conv-123"
        assert response["success"]["title"] == "Valid Title"

        assert len(response["errors"]) == 0

    @pytest.fixture
    def conversations_empty_schema(self, graphql_context):
        """
        Create a schema that returns empty conversations list.

        Args:
            graphql_context: GraphQL context fixture

        Returns:
            Schema: A Strawberry schema with conversations query
        """
        @strawberry.type
        class Query:
            @strawberry.field
            def conversations(self, user_id: str) -> List[GraphQLConversation]:
                """Get conversations for a user."""
                repository = graphql_context["container"].get_conversation_repository()
                conversations = repository["get_user_conversations"](user_id)
                return [
                    GraphQLConversation(
                        id=conv.id,
                        title=conv.title,
                        created_at=conv.created_at,
                        updated_at=conv.updated_at,
                        messages=[
                            GraphQLConversationMessage(
                                id=msg.id,
                                role=msg.role,
                                content=msg.content,
                                timestamp=msg.timestamp,
                                conversation_id=msg.conversation_id
                            )
                            for msg in conv.messages
                        ]
                    )
                    for conv in conversations
                ]

        return strawberry.Schema(query=Query)

    @pytest.mark.asyncio
    async def test_conversations_query_returns_empty_list_when_user_has_no_conversations(
        self, graphql_context, mock_conversation_db, conversations_empty_schema
    ):
        """
        Test that the conversations query returns an empty list when no conversations exist.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            conversations_empty_schema: GraphQL schema for testing
        """
        # Arrange
        query = """
        query GetUserConversations($userId: String!) {
            conversations(userId: $userId) {
                id
                title
            }
        }
        """

        variables = {"userId": "non-existent-user"}

        # Act
        # Use the client module directly
        result = await client.query(
            conversations_empty_schema,
            query,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "conversations" in result["data"]
        assert len(result["data"]["conversations"]) == 0

    @pytest.fixture
    def conversation_detail_schema(self, graphql_context):
        """
        Create a schema with conversation query for testing.

        Args:
            graphql_context: GraphQL context fixture

        Returns:
            Schema: A Strawberry schema with conversation query
        """
        @strawberry.type
        class Query:
            @strawberry.field
            def conversation(self, id: str) -> GraphQLConversation:
                """Get a conversation by ID."""
                repository = graphql_context["container"].get_conversation_repository()
                conversation = repository["get_conversation"](id)
                if not conversation:
                    raise ValueError(f"Conversation not found: {id}")
                return GraphQLConversation(
                    id=conversation.id,
                    title=conversation.title,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    messages=[
                        GraphQLConversationMessage(
                            id=msg.id,
                            role=msg.role,
                            content=msg.content,
                            timestamp=msg.timestamp,
                            conversation_id=msg.conversation_id
                        )
                        for msg in conversation.messages
                    ]
                )

        return strawberry.Schema(query=Query)

    @pytest.mark.asyncio
    async def test_conversation_query_returns_conversation_details_when_valid_id_provided(
        self, graphql_context, mock_conversation_db, sample_conversation_history, conversation_detail_schema
    ):
        """
        Test that the conversation query returns details for a specific conversation.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            sample_conversation_history: Sample conversation data
            conversation_detail_schema: GraphQL schema for testing
        """
        # Arrange
        query = """
        query GetConversationDetails($id: String!) {
            conversation(id: $id) {
                id
                title
                messages {
                    id
                    role
                    content
                    timestamp
                    conversationId
                }
            }
        }
        """

        variables = {"id": "conv-programming-456"}

        # Act
        # Use the client module directly
        result = await client.query(
            conversation_detail_schema,
            query,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result

        conversation = result["data"]["conversation"]
        assert conversation["id"] == "conv-programming-456"
        assert conversation["title"] == "Python Programming Help"

        # Check messages
        assert "messages" in conversation
        messages = conversation["messages"]
        assert len(messages) == 4

        # Verify content of specific messages
        assert any(msg["content"].startswith("How do I read") for msg in messages)
        assert any(msg["content"].startswith("To read a JSON file") for msg in messages)

        # Verify roles are present
        roles = [msg["role"] for msg in messages]
        assert "user" in roles
        assert "assistant" in roles

    @pytest.mark.asyncio
    async def test_conversation_query_raises_error_when_invalid_id_provided(
        self, graphql_context, mock_conversation_db, conversation_detail_schema
    ):
        """
        Test that the conversation query raises an error when an invalid ID is provided.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            conversation_detail_schema: GraphQL schema for testing
        """
        # Arrange
        query = """
        query GetConversationDetails($id: String!) {
            conversation(id: $id) {
                id
                title
            }
        }
        """

        variables = {"id": "non-existent-id"}

        # Act
        # Use the client module directly
        result = await client.query(
            conversation_detail_schema,
            query,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "Conversation not found" in result["errors"][0]["message"]
