from datetime import datetime, UTC
from typing import Optional
from app.application.ports.inbound.gpt_request_port import GPTRequestPort, SubmitRequestCommand
from app.application.ports.outbound.gpt_api_port import GPTAPIPort, GPTAPIRequest
from app.application.ports.outbound.conversation_persistence_port import (
    ConversationPersistencePort,
    ConversationEntry
)
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse
from app.domain.events.request_events import RequestInitiatedEvent, RequestCompletedEvent

class SubmitRequestUseCase(GPTRequestPort):
    """
    Use case for submitting GPT requests and handling responses.
    Implements the inbound GPTRequestPort interface.
    """

    def __init__(
        self,
        gpt_api: GPTAPIPort,
        persistence: ConversationPersistencePort,
        event_publisher: Optional[callable] = None
    ):
        self.gpt_api = gpt_api
        self.persistence = persistence
        self.event_publisher = event_publisher or (lambda x: None)  # No-op if no publisher provided

    async def submit_request(self, command: SubmitRequestCommand) -> GPTResponse:
        """
        Process a GPT request from start to finish:
        1. Create and emit RequestInitiatedEvent
        2. Call GPT API
        3. Save conversation to persistence
        4. Emit RequestCompletedEvent
        5. Return response

        Args:
            command: The command containing request parameters

        Returns:
            GPTResponse: The processed response from GPT

        Raises:
            ValueError: If the command parameters are invalid
            ConnectionError: If the GPT API call fails
        """
        # Create domain model from command
        request = GPTRequest(
            prompt=command.prompt,
            max_tokens=command.max_tokens,
            user_id=command.user_id
        )

        # Emit request initiated event
        self.event_publisher(RequestInitiatedEvent(request=request))

        # Call GPT API
        api_request = GPTAPIRequest(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            user_id=request.user_id
        )
        response = await self.gpt_api.generate_completion(api_request)

        # Save conversation entry
        entry = ConversationEntry(
            user_id=command.user_id,
            request=request,
            response=response,
            timestamp=datetime.now(UTC)
        )
        await self.persistence.save_conversation(entry)

        # Emit completion event
        self.event_publisher(RequestCompletedEvent(
            request=request,
            response=response
        ))

        return response
