from app.domain.events.base_event import DomainEvent
from app.domain.models.gpt_response import GPTResponse

class ResponseReceivedEvent(DomainEvent):
    """Event emitted when a response is received from the GPT API."""

    def __init__(self, response: GPTResponse):
        super().__init__(
            event_type="response_received",
            data={
                "response": response,
                "tokens_used": response.tokens_used,
                "finish_reason": response.finish_reason
            }
        )
