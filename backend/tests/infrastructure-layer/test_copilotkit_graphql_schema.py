"""
Tests for CopilotKit GraphQL schema components.

This module tests the GraphQL schema designed for CopilotKit integration,
including types, queries, and mtations for conversation management and chat functionality.
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

# Fixed Input Types using JSON scalar
@strawberry.input
class FixedCreateConversationInput:
    """Input type for creating a new conversation with JSON metadata."""
    user_id: str = strawberry.field(name="userId")
    title: str
    initial_message: Optional[str] = strawberry.field(
        default=None,
        name="initialMessage"
    )
    metadata: Optional[JSON] = None

@strawberry.input
class FixedAddMessageInput:
    """Input type for adding a message with JSON metadata."""
    conversation_id: str = strawberry.field(name="conversationId")
    role: str
    content: str
    metadata: Optional[JSON] = None

@strawberry.input
class FixedChatRequestInput:
    """Input type for submitting a chat request with JSON context data."""
    conversation_id: str = strawberry.field(name="conversationId")
    message: str
    stream: bool = True
    context_data: Optional[JSON] = strawberry.field(
        default=None,
        name="contextData"
    )

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

    @pytest.fixture
    def create_conversation_schema(self, graphql_context):
        """
        Create a schema with createConversation mutation for testing.

        Args:
            graphql_context: GraphQL context fixture

        Returns:
            Schema: A Strawberry schema with createConversation mutation
        """
        @strawberry.type
        class Query:
            @strawberry.field
            def placeholder(self) -> str:
                """Placeholder query (GraphQL requires at least one query)."""
                return "placeholder"

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def create_conversation(
                self,
                input: CreateConversationInput
            ) -> GraphQLConversation:
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

        return strawberry.Schema(query=Query, mutation=Mutation)

    @pytest.mark.asyncio
    async def test_create_conversation_mutation_creates_and_returns_new_conversation_when_valid_input_provided(
        self, graphql_context, mock_conversation_db, create_conversation_schema
    ):
        """
        Test that the createConversation mutation creates and returns a new conversation.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            create_conversation_schema: GraphQL schema for testing
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

        # Pass values that match the GraphQL schema field names
        variables = {
            "input": {
                "userId": "test-user-1",
                "title": "New Test Conversation",
                "initialMessage": "Hello, this is a test."
            }
        }

        # Get initial conversation count
        initial_conversations = mock_conversation_db["all_conversations"]()
        initial_count = len(initial_conversations)

        # Act
        # Use the client module directly
        result = await client.query(
            create_conversation_schema,
            mutation,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "createConversation" in result["data"]

        created_conv = result["data"]["createConversation"]
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

    @pytest.fixture
    def add_message_schema(self, graphql_context):
        """
        Create a schema with addMessage mutation for testing.

        Args:
            graphql_context: GraphQL context fixture

        Returns:
            Schema: A Strawberry schema with addMessage mutation
        """
        @strawberry.type
        class Query:
            @strawberry.field
            def placeholder(self) -> str:
                """Placeholder query (GraphQL requires at least one query)."""
                return "placeholder"

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

        return strawberry.Schema(query=Query, mutation=Mutation)

    @pytest.mark.asyncio
    async def test_add_message_mutation_adds_message_to_conversation_when_valid_input_provided(
        self, graphql_context, mock_conversation_db, sample_conversation_history, add_message_schema
    ):
        """
        Test that the addMessage mutation adds a message to an existing conversation.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            sample_conversation_history: Sample conversation data
            add_message_schema: GraphQL schema for testing
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
                "conversationId": "conv-weather-123",
                "role": "user",
                "content": "Is it going to rain tomorrow?",
                "metadata": {"source": "web"}
            }
        }

        # Get initial message count
        conversation = mock_conversation_db["get_conversation"]("conv-weather-123")
        initial_message_count = len(conversation.messages)

        # Act
        # Use the client module directly
        result = await client.query(
            add_message_schema,
            mutation,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "addMessage" in result["data"]

        message = result["data"]["addMessage"]
        assert message["id"] is not None
        assert message["role"] == "user"
        assert message["content"] == "Is it going to rain tomorrow?"
        assert message["conversationId"] == "conv-weather-123"
        assert message["timestamp"] is not None

        # Verify message was added to conversation
        updated_conversation = mock_conversation_db["get_conversation"]("conv-weather-123")
        assert len(updated_conversation.messages) == initial_message_count + 1
        assert any(msg.content == "Is it going to rain tomorrow?" for msg in updated_conversation.messages)

    @pytest.fixture
    def submit_chat_request_schema(self, graphql_context):
        """
        Create a schema with submitChatRequest mutation for testing.

        Args:
            graphql_context: GraphQL context fixture

        Returns:
            Schema: A Strawberry schema with submitChatRequest mutation
        """
        @strawberry.type
        class Query:
            @strawberry.field
            def placeholder(self) -> str:
                """Placeholder query (GraphQL requires at least one query)."""
                return "placeholder"

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

        return strawberry.Schema(query=Query, mutation=Mutation)

    @pytest.mark.asyncio
    async def test_submit_chat_request_mutation_calls_use_case_with_correct_parameters_when_valid_input_provided(
        self, graphql_context, mock_conversation_db, submit_chat_request_schema
    ):
        """
        Test that the submitChatRequest mutation calls the use case with correct parameters.

        Args:
            graphql_context: GraphQL context fixture
            mock_conversation_db: Mock conversation database
            submit_chat_request_schema: GraphQL schema for testing
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
                "conversationId": "conv-weather-123",
                "message": "Is it going to rain tomorrow?",
                "stream": True,
                "contextData": {
                    "userId": "test-user-1",
                    "location": "New York"
                }
            }
        }

        use_case_mock = graphql_context["container"].get_submit_request_use_case()

        # Act
        # Use the client module directly
        result = await client.query(
            submit_chat_request_schema,
            mutation,
            variables=variables,
            context_value=graphql_context
        )

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "submitChatRequest" in result["data"]

        response = result["data"]["submitChatRequest"]
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

    @pytest.fixture
    def schema_introspection_test(self):
        """
        Create a schema for introspection testing.

        Returns:
            Schema: A complete Strawberry schema for introspection testing
        """
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

        return strawberry.Schema(query=Query, mutation=Mutation)

    @pytest.mark.asyncio
    async def test_schema_has_copilotkit_types_when_introspected(self, schema_introspection_test):
        """
        Test that the schema contains the expected CopilotKit-specific types.

        Args:
            schema_introspection_test: GraphQL schema fixture for testing
        """
        # Arrange
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
        # Use the client module directly
        result = await client.query(schema_introspection_test, query)

        # Assert
        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        assert "data" in result
        assert "__schema" in result["data"]
        assert "types" in result["data"]["__schema"]

        type_names = [t["name"] for t in result["data"]["__schema"]["types"]]

        # Check for conversation types
        assert "GraphQLConversation" in type_names
        assert "GraphQLConversationMessage" in type_names

        # Check for input types
        assert "CreateConversationInput" in type_names
        assert "AddMessageInput" in type_names
        assert "ChatRequestInput" in type_names

        # Check for response types
        assert "ChatRequestResponse" in type_names
