"""
Tests for CopilotKit GraphQL schema components.

This module tests the GraphQL schema designed for CopilotKit integration,
including types, queries, and mutations for conversation management and
chat functionality.
"""
import pytest
from strawberry.test import execute_async_query
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock
import strawberry
from typing import List, Dict, Any, Optional

# Import fixtures
from backend.tests.fixtures.conversation_fixtures import (
    sample_conversation_history,
    mock_conversation_db,
    Conversation,
    ConversationMessage
)


@strawberry.type
class GraphQLConversationMessage:
    """GraphQL type for conversation messages."""
    id: str
    role: str
    content: str
    timestamp: datetime
    conversation_id: str = strawberry.field(name="conversationId")


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
    request_id: str = strawberry.field(name="requestId")
    status: str


class TestCopilotKitGraphQLSchema:
    """Test suite for CopilotKit GraphQL schema components."""

    @pytest.fixture
    def graphql_context(self, mock_conversation_db):
        """
        Create a mock GraphQL context for testing.

        Args:
            mock_conversation_db: Mock conversation database

        Returns:
            dict: Context dictionary with necessary components
        """
        # Create mock container
        class MockContainer:
            def __init__(self):
                self.conversation_db = mock_conversation_db

            def get_conversation_repository(self):
                return self.conversation_db

            def get_submit_request_use_case(self):
                mock_use_case = AsyncMock()
                mock_use_case.execute.return_value = {
                    "request_id": "req-12345",
                    "status": "processing"
                }
                return mock_use_case

        return {
            "container": MockContainer(),
            "user": {"id": "test-user-1"}
        }

    @pytest.mark.asyncio
    async def test_ConversationsQuery_ReturnsUserConversations_WhenValidUserIdProvided(
        self, graphql_context, mock_conversation_db, sample_conversation_history
    ):
        """
        Test that the conversations query returns all conversations for a user.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            sample_conversation_history: Sample conversation data
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

        # Mock schema for testing
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

        schema = strawberry.Schema(query=Query)

        # Act
        result = await execute_async_query(
            schema,
            query,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"
        assert "conversations" in result.data
        conversations = result.data["conversations"]
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

    @pytest.mark.asyncio
    async def test_ConversationsQuery_ReturnsEmptyList_WhenUserHasNoConversations(
        self, graphql_context, mock_conversation_db
    ):
        """
        Test that the conversations query returns an empty list when no conversations exist.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
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

        schema = strawberry.Schema(query=Query)

        # Act
        result = await execute_async_query(
            schema,
            query,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"
        assert "conversations" in result.data
        assert len(result.data["conversations"]) == 0

    @pytest.mark.asyncio
    async def test_ConversationQuery_ReturnsConversationDetails_WhenValidIdProvided(
        self, graphql_context, mock_conversation_db, sample_conversation_history
    ):
        """
        Test that the conversation query returns details for a specific conversation.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            sample_conversation_history: Sample conversation data
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

        schema = strawberry.Schema(query=Query)

        # Act
        result = await execute_async_query(
            schema,
            query,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"
        assert "conversation" in result.data

        conversation = result.data["conversation"]
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
    async def test_ConversationQuery_RaisesError_WhenInvalidIdProvided(
        self, graphql_context, mock_conversation_db
    ):
        """
        Test that the conversation query raises an error when an invalid ID is provided.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
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
                    messages=[]
                )

        schema = strawberry.Schema(query=Query)

        # Act
        result = await execute_async_query(
            schema,
            query,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is not None
        assert len(result.errors) > 0
        assert "Conversation not found" in str(result.errors[0])

    @pytest.mark.asyncio
    async def test_CreateConversationMutation_CreatesAndReturnsNewConversation_WhenValidInputProvided(
        self, graphql_context, mock_conversation_db
    ):
        """
        Test that the createConversation mutation creates and returns a new conversation.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
        """
        # Arrange
        mutation = """
        mutation CreateNewConversation($input: CreateConversationInput!) {
            createConversation(input: $input) {
                id
                title
                createdAt
                updatedAt
                messageCount
            }
        }
        """

        variables = {
            "input": {
                "userId": "test-user-1",
                "title": "New Test Conversation",
                "initialMessage": "Hello, this is a test."
            }
        }

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def create_conversation(self, input: CreateConversationInput) -> GraphQLConversation:
                """Create a new conversation."""
                repository = graphql_context["container"].get_conversation_repository()

                # Create the conversation
                conversation = repository["create_conversation"](
                    input.user_id,
                    input.title,
                    input.metadata
                )

                # Add the initial message if provided
                if input.initial_message:
                    repository["add_message"](
                        conversation.id,
                        "user",
                        input.initial_message
                    )

                # Retrieve the updated conversation
                updated_conv = repository["get_conversation"](conversation.id)

                return GraphQLConversation(
                    id=updated_conv.id,
                    title=updated_conv.title,
                    created_at=updated_conv.created_at,
                    updated_at=updated_conv.updated_at,
                    messages=[
                        GraphQLConversationMessage(
                            id=msg.id,
                            role=msg.role,
                            content=msg.content,
                            timestamp=msg.timestamp,
                            conversation_id=msg.conversation_id
                        )
                        for msg in updated_conv.messages
                    ]
                )

        schema = strawberry.Schema(mutation=Mutation)

        # Get initial conversation count
        initial_conversations = mock_conversation_db["all_conversations"]()
        initial_count = len(initial_conversations)

        # Act
        result = await execute_async_query(
            schema,
            mutation,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"
        assert "createConversation" in result.data

        created_conv = result.data["createConversation"]
        assert created_conv["id"] is not None
        assert created_conv["title"] == "New Test Conversation"
        assert created_conv["createdAt"] is not None
        assert created_conv["updatedAt"] is not None
        assert created_conv["messageCount"] == 1

        # Verify conversation was added to the database
        current_conversations = mock_conversation_db["all_conversations"]()
        assert len(current_conversations) == initial_count + 1

        # Find the new conversation
        new_conv = mock_conversation_db["get_conversation"](created_conv["id"])
        assert new_conv is not None
        assert len(new_conv.messages) == 1
        assert new_conv.messages[0].content == "Hello, this is a test."

    @pytest.mark.asyncio
    async def test_AddMessageMutation_AddsMessageToConversation_WhenValidInputProvided(
        self, graphql_context, mock_conversation_db, sample_conversation_history
    ):
        """
        Test that the addMessage mutation adds a message to an existing conversation.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            sample_conversation_history: Sample conversation data
        """
        # Arrange
        mutation = """
        mutation AddMessageToConversation($input: AddMessageInput!) {
            addMessage(input: $input) {
                id
                role
                content
                timestamp
                conversationId
            }
        }
        """

        variables = {
            "input": {
                "conversation_id": "conv-weather-123",
                "role": "user",
                "content": "Is it going to rain tomorrow?",
                "metadata": {"source": "web"}
            }
        }

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def add_message(self, input: AddMessageInput) -> GraphQLConversationMessage:
                """Add a message to a conversation."""
                repository = graphql_context["container"].get_conversation_repository()

                # Get initial message count
                conversation = repository["get_conversation"](input.conversation_id)
                if not conversation:
                    raise ValueError(f"Conversation not found: {input.conversation_id}")

                # Add the message
                message = repository["add_message"](
                    input.conversation_id,
                    input.role,
                    input.content,
                    input.metadata
                )

                return GraphQLConversationMessage(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    timestamp=message.timestamp,
                    conversation_id=message.conversation_id
                )

        schema = strawberry.Schema(mutation=Mutation)

        # Get initial message count
        conversation = mock_conversation_db["get_conversation"]("conv-weather-123")
        initial_message_count = len(conversation.messages)

        # Act
        result = await execute_async_query(
            schema,
            mutation,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"
        assert "addMessage" in result.data

        message = result.data["addMessage"]
        assert message["id"] is not None
        assert message["role"] == "user"
        assert message["content"] == "Is it going to rain tomorrow?"
        assert message["conversationId"] == "conv-weather-123"
        assert message["timestamp"] is not None

        # Verify message was added to conversation
        updated_conversation = mock_conversation_db["get_conversation"]("conv-weather-123")
        assert len(updated_conversation.messages) == initial_message_count + 1
        assert any(msg.content == "Is it going to rain tomorrow?" for msg in updated_conversation.messages)

    @pytest.mark.asyncio
    async def test_SubmitChatRequestMutation_CallsUseCaseWithCorrectParameters_WhenValidInputProvided(
        self, graphql_context, mock_conversation_db
    ):
        """
        Test that the submitChatRequest mutation calls the use case with correct parameters.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
        """
        # Arrange
        mutation = """
        mutation SubmitChatRequest($input: ChatRequestInput!) {
            submitChatRequest(input: $input) {
                requestId
                status
            }
        }
        """

        variables = {
            "input": {
                "conversation_id": "conv-weather-123",
                "message": "Is it going to rain tomorrow?",
                "stream": True,
                "context_data": {
                    "userId": "test-user-1",
                    "location": "New York"
                }
            }
        }

        use_case_mock = graphql_context["container"].get_submit_request_use_case()

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            async def submit_chat_request(self, input: ChatRequestInput) -> ChatRequestResponse:
                """Submit a chat request."""
                # In a real implementation, we would create a domain object here
                from dataclasses import dataclass

                @dataclass
                class ChatRequest:
                    conversation_id: str
                    message: str
                    stream: bool
                    context_data: Dict[str, Any]

                request = ChatRequest(
                    conversation_id=input.conversation_id,
                    message=input.message,
                    stream=input.stream,
                    context_data=input.context_data or {}
                )

                # Get the use case from the container
                use_case = graphql_context["container"].get_submit_request_use_case()
                result = await use_case.execute(request)

                return ChatRequestResponse(
                    request_id=result["request_id"],
                    status=result["status"]
                )

        schema = strawberry.Schema(mutation=Mutation)

        # Act
        result = await execute_async_query(
            schema,
            mutation,
            variable_values=variables,
            context_value=graphql_context
        )

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"
        assert "submitChatRequest" in result.data

        response = result.data["submitChatRequest"]
        assert response["requestId"] == "req-12345"
        assert response["status"] == "processing"

        # Verify the use case was called with correct parameters
        use_case_mock.execute.assert_called_once()
        call_args = use_case_mock.execute.call_args[0][0]
        assert call_args.conversation_id == "conv-weather-123"
        assert call_args.message == "Is it going to rain tomorrow?"
        assert call_args.stream is True
        assert "userId" in call_args.context_data
        assert call_args.context_data["userId"] == "test-user-1"
        assert call_args.context_data["location"] == "New York"

    @pytest.mark.asyncio
    async def test_Schema_IntrospectionQuery_ReturnsAllExpectedTypes(self):
        """Test that the schema introspection query returns all expected types."""
        # Arrange
        @strawberry.type
        class Query:
            @strawberry.field
            def conversations(self, user_id: str) -> List[GraphQLConversation]:
                """Get conversations for a user."""
                return []

            @strawberry.field
            def conversation(self, id: str) -> Optional[GraphQLConversation]:
                """Get a conversation by ID."""
                return None

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def create_conversation(self, input: CreateConversationInput) -> GraphQLConversation:
                """Create a new conversation."""
                return GraphQLConversation(
                    id="test-id",
                    title="Test",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    messages=[]
                )

            @strawberry.mutation
            def add_message(self, input: AddMessageInput) -> GraphQLConversationMessage:
                """Add a message to a conversation."""
                return GraphQLConversationMessage(
                    id="test-msg-id",
                    role="user",
                    content="Test content",
                    timestamp=datetime.now(),
                    conversation_id="test-conv-id"
                )

            @strawberry.mutation
            async def submit_chat_request(self, input: ChatRequestInput) -> ChatRequestResponse:
                """Submit a chat request."""
                return ChatRequestResponse(
                    request_id="test-req-id",
                    status="processing"
                )

        schema = strawberry.Schema(query=Query, mutation=Mutation)

        query = """
        {
            __schema {
                types {
                    name
                    kind
                }
            }
        }
        """

        # Act
        result = await execute_async_query(schema, query)

        # Assert
        assert result.errors is None, f"GraphQL errors: {result.errors}"

        type_names = [t["name"] for t in result.data["__schema"]["types"]]

        # Check that all our defined types are present
        expected_types = [
            "Query",
            "Mutation",
            "GraphQLConversation",
            "GraphQLConversationMessage",
            "CreateConversationInput",
            "AddMessageInput",
            "ChatRequestInput",
            "ChatRequestResponse"
        ]

        for expected_type in expected_types:
            assert expected_type in type_names, f"Expected type {expected_type} not found in schema"
