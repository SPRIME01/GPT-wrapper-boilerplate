from typing import Dict, Any
from app.domain.events.base_event import DomainEvent

class ErrorOccurredEvent(DomainEvent):
    """Event emitted when an error occurs during request processing."""

    def __init__(self, error: Exception, context: Dict[str, Any]):
        super().__init__(
            event_type="error_occurred",
            data={
                "error": error,
                "error_type": error.__class__.__name__,
                "error_message": str(error),
                "context": context
            }
        )
