import pytest
from datetime import datetime
from app.domain.events.base_event import DomainEvent
from app.domain.events.request_events import RequestInitiatedEvent, RequestCompletedEvent
from app.domain.events.response_events import ResponseReceivedEvent
from app.domain.events.error_events import ErrorOccurredEvent
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

class TestDomainEvents:
    def test_base_event_properties(self):
        # Arrange
        event_type = "test_event"
        event_data = {"key": "value"}

        # Act
        event = DomainEvent(event_type=event_type, data=event_data)

        # Assert
        assert event.event_type == event_type
        assert event.data == event_data
        assert isinstance(event.timestamp, datetime)
        assert event.event_id is not None

    def test_request_initiated_event(self):
        # Arrange
        request = GPTRequest(prompt="Test prompt", max_tokens=100, user_id="test_user")

        # Act
        event = RequestInitiatedEvent(request=request)

        # Assert
        assert event.event_type == "request_initiated"
        assert event.data["request"] == request
        assert "timestamp" in event.data

    def test_request_completed_event(self):
        # Arrange
        request = GPTRequest(prompt="Test prompt", max_tokens=100, user_id="test_user")
        response = GPTResponse(
            text="Test response",
            tokens_used=50,
            user_id="test_user",
            request_id=request.request_id
        )

        # Act
        event = RequestCompletedEvent(request=request, response=response)

        # Assert
        assert event.event_type == "request_completed"
        assert event.data["request"] == request
        assert event.data["response"] == response

    def test_response_received_event(self):
        # Arrange
        request = GPTRequest(prompt="Test prompt", max_tokens=100, user_id="test_user")
        response = GPTResponse(
            text="Test response",
            tokens_used=50,
            user_id="test_user",
            request_id=request.request_id
        )

        # Act
        event = ResponseReceivedEvent(response=response)

        # Assert
        assert event.event_type == "response_received"
        assert event.data["response"] == response

    def test_error_occurred_event(self):
        # Arrange
        error = ValueError("Test error")
        context = {"request_id": "123"}

        # Act
        event = ErrorOccurredEvent(error=error, context=context)

        # Assert
        assert event.event_type == "error_occurred"
        assert isinstance(event.data["error"], ValueError)
        assert event.data["context"] == context
        assert "timestamp" in event.data
        assert "error_type" in event.data
