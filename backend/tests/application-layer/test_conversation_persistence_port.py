import pytest
from typing import List, Optional
from datetime import datetime, UTC
from app.application.ports.outbound.conversation_persistence_port import (
    ConversationPersistencePort,
    ConversationEntry,
    ConversationQuery
)
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

class MockConversationRepository(ConversationPersistencePort):
    def __init__(self):
        self.conversations: List[ConversationEntry] = []
        self.last_query: Optional[ConversationQuery] = None

    async def save_conversation(self, entry: ConversationEntry) -> None:
        self.conversations.append(entry)

    async def get_conversation_history(self, query: ConversationQuery) -> List[ConversationEntry]:
        self.last_query = query
        return [conv for conv in self.conversations
                if conv.user_id == query.user_id
                and conv.timestamp >= query.start_time]

class TestConversationPersistencePort:
    @pytest.fixture
    def port(self) -> MockConversationRepository:
        return MockConversationRepository()

    @pytest.mark.asyncio
    async def test_save_conversation_entry(self, port: MockConversationRepository):
        # Arrange
        entry = ConversationEntry(
            user_id="test_user",
            request=GPTRequest(prompt="Test question?", max_tokens=100, user_id="test_user"),
            response=GPTResponse(text="Test answer", tokens_used=50, user_id="test_user", request_id="test_123"),
            timestamp=datetime.now(UTC)
        )

        # Act
        await port.save_conversation(entry)

        # Assert
        assert len(port.conversations) == 1
        assert port.conversations[0] == entry

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, port: MockConversationRepository):
        # Arrange
        user_id = "test_user"
        now = datetime.now(UTC)
        entries = [
            ConversationEntry(
                user_id=user_id,
                request=GPTRequest(prompt=f"Question {i}?", max_tokens=100, user_id=user_id),
                response=GPTResponse(text=f"Answer {i}", tokens_used=50, user_id=user_id, request_id=f"test_{i}"),
                timestamp=now
            )
            for i in range(3)
        ]

        for entry in entries:
            await port.save_conversation(entry)

        query = ConversationQuery(
            user_id=user_id,
            start_time=now,
            limit=10
        )

        # Act
        history = await port.get_conversation_history(query)

        # Assert
        assert len(history) == 3
        assert all(entry in history for entry in entries)
        assert port.last_query == query
