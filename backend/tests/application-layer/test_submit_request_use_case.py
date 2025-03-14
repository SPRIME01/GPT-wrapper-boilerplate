import pytest
from datetime import datetime, UTC
from uuid import uuid4
from app.application.use_cases.submit_request_use_case import SubmitRequestUseCase
from app.application.ports.inbound.gpt_request_port import SubmitRequestCommand
from app.application.ports.outbound.gpt_api_port import GPTAPIPort, GPTAPIRequest
from app.application.ports.outbound.conversation_persistence_port import (
    ConversationPersistencePort,
    ConversationEntry
)
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse
from app.domain.events.request_events import RequestInitiatedEvent, RequestCompletedEvent

class MockGPTAPIPort:
    def __init__(self):
        self.call_count = 0
        self.last_request = None
        self.should_fail = False

    async def generate_completion(self, request: GPTAPIRequest) -> GPTResponse:
        self.call_count += 1
        self.last_request = request
        if self.should_fail:
            raise ConnectionError("API Error")
        return GPTResponse(
            text="Mocked response",
            tokens_used=10,
            user_id=request.user_id,
            request_id=str(uuid4())
        )

class MockConversationPersistence:
    def __init__(self):
        self.saved_entries = []

    async def save_conversation(self, entry: ConversationEntry) -> None:
        self.saved_entries.append(entry)

    async def get_conversation_history(self, query):
        return self.saved_entries

class TestSubmitRequestUseCase:
    @pytest.fixture
    def gpt_api(self) -> MockGPTAPIPort:
        return MockGPTAPIPort()

    @pytest.fixture
    def persistence(self) -> MockConversationPersistence:
        return MockConversationPersistence()

    @pytest.fixture
    def use_case(self, gpt_api, persistence) -> SubmitRequestUseCase:
        return SubmitRequestUseCase(gpt_api=gpt_api, persistence=persistence)

    @pytest.mark.asyncio
    async def test_submit_request_successful_execution(self, use_case, gpt_api, persistence):
        # Arrange
        command = SubmitRequestCommand(
            prompt="Test prompt",
            max_tokens=100,
            user_id="test_user"
        )

        # Act
        response = await use_case.submit_request(command)

        # Assert
        assert gpt_api.call_count == 1
        assert gpt_api.last_request.prompt == "Test prompt"
        assert response.text == "Mocked response"
        assert len(persistence.saved_entries) == 1
        saved_entry = persistence.saved_entries[0]
        assert saved_entry.user_id == "test_user"
        assert isinstance(saved_entry.request, GPTRequest)
        assert isinstance(saved_entry.response, GPTResponse)

    @pytest.mark.asyncio
    async def test_submit_request_handles_api_failure(self, use_case, gpt_api):
        # Arrange
        gpt_api.should_fail = True
        command = SubmitRequestCommand(
            prompt="Test prompt",
            max_tokens=100,
            user_id="test_user"
        )

        # Act & Assert
        with pytest.raises(ConnectionError):
            await use_case.submit_request(command)

    @pytest.mark.asyncio
    async def test_submit_request_emits_events(self, use_case, gpt_api):
        # Arrange
        command = SubmitRequestCommand(
            prompt="Test prompt",
            max_tokens=100,
            user_id="test_user"
        )

        # Act
        response = await use_case.submit_request(command)

        # Assert
        # Note: In a real implementation, we'd verify events were published
        # This test structure assumes events are tracked within the use case
        # We'll need to implement event tracking/verification later
        pass
