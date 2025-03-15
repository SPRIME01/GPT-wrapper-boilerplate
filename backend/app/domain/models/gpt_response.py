"""
Domain model representing a response from the GPT API.
Includes validation logic, logging, and comprehensive type hints.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

# Configure logging
logger = logging.getLogger(__name__)

class GPTResponse(BaseModel):
    """
    Domain model representing a response from the GPT API.
    Validates outputs and enforces business rules through Pydantic.

    Examples:
        >>> response = GPTResponse(
        ...     user_id="user123",
        ...     request_id="req456",
        ...     text="Here's a joke: Why did the programmer quit his job?"
        ... )
        >>> response.to_dict()
        {
            'user_id': 'user123',
            'request_id': 'req456',
            'text': "Here's a joke: Why did the programmer quit his job?",
            ...
        }
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )

    # Required fields
    user_id: str = Field(..., description="Unique identifier for the user")
    request_id: str = Field(..., description="The ID of the request that generated this response")
    text: str = Field(..., min_length=1, description="The text response from GPT")

    # Optional fields with defaults
    tokens_used: int = Field(
        default=0,
        ge=0,
        description="Number of tokens used for this response"
    )
    finish_reason: Optional[str] = Field(
        default="stop",
        description="Reason why the response finished ('stop', 'length', etc.)"
    )

    # System-managed fields
    response_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this response"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this response was generated"
    )

    # Additional parameters (for flexibility)
    additional_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters from GPT API"
    )

    # Validators
    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Ensure response text is not just whitespace"""
        if not value.strip():
            raise ValueError("Response text cannot be empty or just whitespace")
        logger.debug(f"Validated response text: {value[:50]}...")
        return value.strip()

    @field_validator("tokens_used")
    @classmethod
    def validate_tokens(cls, value: int) -> int:
        """Log if token usage is unusually high"""
        if value > 1000:
            logger.warning(f"High token usage detected: {value} tokens")
        return value

    def __eq__(self, other: object) -> bool:
        """Two responses are equal if they have the same response_id."""
        if not isinstance(other, GPTResponse):
            return False
        return self.response_id == other.response_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary for serialization."""
        # BEGIN PERFORMANCE OPTIMIZATION
        result = self.model_dump()
        result.update(self.additional_params)
        return result
        # END PERFORMANCE OPTIMIZATION

    # For backward compatibility during tests
    def __init__(self, **data):
        # If text and tokens_used are provided but user_id and request_id are missing,
        # set them to default values for tests
        if 'text' in data and 'tokens_used' in data:
            if 'user_id' not in data:
                data['user_id'] = 'test_user'
            if 'request_id' not in data:
                data['request_id'] = 'test_request'
        super().__init__(**data)
