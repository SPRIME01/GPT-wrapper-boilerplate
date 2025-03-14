import pytest
from uuid import uuid4
from pydantic import ValidationError
from app.application.use_cases.process_response_use_case import ProcessResponseUseCase
from app.domain.models.gpt_response import GPTResponse
from app.domain.events.response_events import ResponseReceivedEvent

class MockEventTracker:
    def __init__(self):
        self.published_events = []

    def publish(self, event):
        self.published_events.append(event)

class TestProcessResponseUseCase:
    @pytest.fixture
    def event_tracker(self):
        return MockEventTracker()

    @pytest.fixture
    def use_case(self, event_tracker):
        return ProcessResponseUseCase(
            persistence=None,  # Not needed for current tests
            event_publisher=event_tracker.publish
        )

    @pytest.mark.asyncio
    async def test_process_response_valid_input(self, use_case, event_tracker):
        # Arrange
        response = GPTResponse(
            text="Test response",
            tokens_used=10,
            user_id="test_user",
            request_id="test_123"
        )

        # Act
        processed_response = await use_case.process_response(response)

        # Assert
        assert processed_response == response  # No modifications in current implementation
        assert len(event_tracker.published_events) == 1
        event = event_tracker.published_events[0]
        assert isinstance(event, ResponseReceivedEvent)
        assert event.data["response"] == response

    @pytest.mark.asyncio
    async def test_process_response_empty_response_validation(self):
        # Act & Assert
        with pytest.raises(ValidationError):
            GPTResponse(
                text="   ",  # Empty or whitespace
                tokens_used=0,
                user_id="test_user",
                request_id="test_123"
            )
