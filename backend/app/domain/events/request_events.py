from typing import Dict
from app.domain.events.base_event import DomainEvent
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

class RequestInitiatedEvent(DomainEvent):
    """Event emitted when a GPT request is initiated."""

    def __init__(self, request: GPTRequest):
        super().__init__(
            event_type="request_initiated",
            data={
                "request": request,
                "request_id": str(request.request_id)
            }
        )

class RequestCompletedEvent(DomainEvent):
    """Event emitted when a GPT request is completed successfully."""

    def __init__(self, request: GPTRequest, response: GPTResponse):
        super().__init__(
            event_type="request_completed",
            data={
                "request": request,
                "response": response,
                "request_id": str(request.request_id),
                "tokens_used": response.tokens_used
            }
        )
