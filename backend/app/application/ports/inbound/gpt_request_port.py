from typing import Protocol
from dataclasses import dataclass
from pydantic import BaseModel, Field
from app.domain.models.gpt_response import GPTResponse

@dataclass
class SubmitRequestCommand:
    """Command object for submitting GPT requests"""
    prompt: str
    max_tokens: int
    user_id: str

    def __post_init__(self):
        """Validate command parameters"""
        if not self.prompt:
            raise ValueError("Prompt cannot be empty")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")

class GPTRequestPort(Protocol):
    """
    Inbound port for handling GPT request operations.
    This port defines the interface for submitting requests to the GPT service.
    """

    async def submit_request(self, command: SubmitRequestCommand) -> GPTResponse:
        """
        Submit a GPT request and return the response.

        Args:
            command: The command containing request parameters

        Returns:
            GPTResponse: The response from the GPT service

        Raises:
            ValueError: If the command parameters are invalid
        """
        ...
