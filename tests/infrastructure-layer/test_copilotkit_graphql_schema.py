import pytest
from typing import Dict, List
from strawberry.types import Info
from app.infrastructure.graphql.schema import Conversation, Message, ConversationInput

@pytest.fixture
def sample_conversation_data() -> Dict:
    return {
        "id": "conv_123",
        "title": "Test Conversation",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }

@pytest.fixture
def mock_context(mocker):
    return mocker.Mock(
        conversations_repository=mocker.Mock(
            get_conversation=mocker.AsyncMock(),
            list_conversations=mocker.AsyncMock(),
            create_conversation=mocker.AsyncMock()
        )
    )

class TestConversationQueries:
    async def test_get_conversation_by_id(self, mock_context, sample_conversation_data):
        mock_context.conversations_repository.get_conversation.return_value = sample_conversation_data

        info = Info(context=mock_context)
        result = await Conversation.resolve_conversation(self, info, "conv_123")

        assert result.id == "conv_123"
        assert result.title == "Test Conversation"
        assert len(result.messages) == 2

    async def test_list_conversations(self, mock_context):
        mock_context.conversations_repository.list_conversations.return_value = [
            {"id": "conv_1", "title": "First Conv"},
            {"id": "conv_2", "title": "Second Conv"}
        ]

        info = Info(context=mock_context)
        result = await Conversation.resolve_conversations(self, info)

        assert len(result) == 2
        assert result[0].id == "conv_1"
        assert result[1].id == "conv_2"

class TestConversationMutations:
    async def test_create_conversation(self, mock_context):
        input_data = ConversationInput(
            title="New Conversation",
            system_prompt="You are a helpful assistant"
        )

        mock_context.conversations_repository.create_conversation.return_value = {
            "id": "new_conv_123",
            "title": input_data.title,
            "system_prompt": input_data.system_prompt,
            "messages": []
        }

        info = Info(context=mock_context)
        result = await Conversation.resolve_create_conversation(self, info, input_data)

        assert result.id == "new_conv_123"
        assert result.title == "New Conversation"
