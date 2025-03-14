from typing import Optional
from app.domain.models.gpt_response import GPTResponse
from app.domain.events.response_events import ResponseReceivedEvent
from app.application.ports.outbound.conversation_persistence_port import (
    ConversationPersistencePort,
    ConversationQuery
)

class ProcessResponseUseCase:
    """
    Use case for processing GPT responses, including any post-processing,
    validation, and event emission.
    """

    def __init__(
        self,
        persistence: ConversationPersistencePort,
        event_publisher: Optional[callable] = None
    ):
        self.persistence = persistence
        self.event_publisher = event_publisher or (lambda x: None)

    async def process_response(self, response: GPTResponse) -> GPTResponse:
        """
        Process a GPT response:
        1. Validate response content
        2. Apply any post-processing
        3. Emit ResponseReceivedEvent
        4. Return processed response

        Args:
            response: The raw GPT response to process

        Returns:
            GPTResponse: The processed response

        Raises:
            ValueError: If the response is invalid
        """
        # Validate response
        if not response.text.strip():
            raise ValueError("Empty response received")

        # Here we could add more post-processing like:
        # - Content filtering
        # - Response formatting
        # - Context enrichment
        # For now, we'll keep it simple

        # Emit response received event
        self.event_publisher(ResponseReceivedEvent(response=response))

        return response
