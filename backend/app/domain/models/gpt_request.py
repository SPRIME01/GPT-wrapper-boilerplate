"""
Domain model representing a request to the GPT API.
Includes validation logic, logging, and comprehensive type hints.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class GPTRequest:
    prompt: str
    max_tokens: int
    temperature: float = 1.0
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[list[str]] = None

class GPTRequest(BaseModel):
    """
    Domain model representing a request to the GPT API.
    Validates inputs and enforces business rules through Pydantic.

    Examples:
        >>> request = GPTRequest(user_id="user123", prompt="Tell me a joke")
        >>> request.to_dict()
        {
            'user_id': 'user123',
            'prompt': 'Tell me a joke',
            'temperature': 0.7,
            ...
        }
    """
    # Required fields
    user_id: str = Field(..., description="Unique identifier for the user")
    prompt: str = Field(..., min_length=1, description="The text prompt to send to GPT")

    # Optional fields with defaults
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Controls randomness (0.0-1.0)"
    )
    max_tokens: int = Field(
        default=150,
        gt=0,
        description="Maximum number of tokens to generate"
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Controls diversity via nucleus sampling"
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )

    # System-managed fields
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this request"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this request was created"
    )

    # Additional parameters (for flexibility)
    additional_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for GPT API"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )

    # Validators
    @field_validator("prompt")
    def validate_prompt(cls, v: str) -> str:
        """Ensure prompt is not just whitespace"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or just whitespace")
        logger.debug(f"Validated prompt: {v[:50]}...")
        return v.strip()

    @field_validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Log if temperature is set to extreme values"""
        if v < 0.2:
            logger.warning(f"Very low temperature ({v}) may result in deterministic responses")
        elif v > 0.8:
            logger.warning(f"High temperature ({v}) may result in random responses")
        return v

    def __eq__(self, other: object) -> bool:
        """Two requests are equal if they have the same request_id."""
        if not isinstance(other, GPTRequest):
            return False
        return self.request_id == other.request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert the request to a dictionary for serialization."""
        # BEGIN PERFORMANCE OPTIMIZATION
        result = self.model_dump()
        result.update(self.additional_params)
        return result
        # END PERFORMANCE OPTIMIZATION
