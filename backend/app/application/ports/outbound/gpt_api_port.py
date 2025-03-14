from typing import Protocol
from dataclasses import dataclass
from app.domain.models.gpt_response import GPTResponse

@dataclass
class GPTAPIRequest:
    """Data structure for GPT API requests"""
    prompt: str
    max_tokens: int
    user_id: str
    temperature: float = 0.7
    model: str = "gpt-4"

class GPTAPIPort(Protocol):
    """
    Outbound port for GPT API communication.
    This port defines the interface for external GPT API interactions.
    """

    async def generate_completion(self, request: GPTAPIRequest) -> GPTResponse:
        """
        Generate a completion using the GPT API.

        Args:
            request: The GPT API request parameters

        Returns:
            GPTResponse: The response from the GPT API

        Raises:
            ConnectionError: If the API request fails
            ValueError: If the request parameters are invalid
        """
        ...
