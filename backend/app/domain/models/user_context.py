"""
Domain model representing a user's context in the GPT conversation.
Manages conversation history, preferences, and metadata with validation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

# Configure logging
logger = logging.getLogger(__name__)

class UserContext(BaseModel):
    """
    Domain model representing a user's context in the GPT conversation.
    Manages conversation history and user preferences with validation.

    Examples:
        >>> context = UserContext(
        ...     user_id="user123",
        ...     conversation_history=["Hello", "Hi there!"],
        ...     preferences={"tone": "friendly"}
        ... )
        >>> context.add_to_conversation("How are you?")
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )

    # Required fields
    user_id: str = Field(..., description="Unique identifier for the user")

    # Optional fields with defaults
    conversation_history: List[str] = Field(
        default_factory=list,
        description="List of previous messages in the conversation"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User-specific preferences and settings"
    )

    # System-managed fields
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this context was first created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When this context was last updated"
    )

    # Validators
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        """Ensure user_id is not empty"""
        if not value.strip():
            raise ValueError("User ID cannot be empty")
        return value.strip()

    @field_validator("conversation_history")
    @classmethod
    def validate_conversation_history(cls, value: List[str]) -> List[str]:
        """Ensure conversation history entries are not empty"""
        return [msg.strip() for msg in value if msg.strip()]

    def add_to_conversation(self, message: str) -> None:
        """
        Add a new message to the conversation history.

        Args:
            message: The message to add (will be stripped)

        Raises:
            ValueError: If message is empty after stripping
        """
        if not message.strip():
            raise ValueError("Cannot add empty message to conversation")

        self.conversation_history.append(message.strip())
        self.updated_at = datetime.now()
        logger.debug(f"Added message to conversation for user {self.user_id}")

    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """
        Update the user's preferences by merging with existing preferences.

        Args:
            new_preferences: Dictionary of new preferences to merge
        """
        # BEGIN PERFORMANCE OPTIMIZATION
        self.preferences.update(new_preferences)
        self.updated_at = datetime.now()
        logger.debug(f"Updated preferences for user {self.user_id}")
        # END PERFORMANCE OPTIMIZATION

    def clear_conversation_history(self) -> None:
        """
        Clear the conversation history.
        """
        self.conversation_history = []
        self.updated_at = datetime.now()
        logger.info(f"Cleared conversation history for user {self.user_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the user context to a dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "conversation_history": self.conversation_history,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
