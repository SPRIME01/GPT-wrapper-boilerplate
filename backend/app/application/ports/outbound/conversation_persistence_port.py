from typing import List, Protocol
from dataclasses import dataclass
from datetime import datetime
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

@dataclass
class ConversationEntry:
    """A single conversation exchange between user and GPT"""
    user_id: str
    request: GPTRequest
    response: GPTResponse
    timestamp: datetime

@dataclass
class ConversationQuery:
    """Query parameters for retrieving conversation history"""
    user_id: str
    start_time: datetime
    limit: int = 10

class ConversationPersistencePort(Protocol):
    """
    Outbound port for conversation persistence.
    This port defines the interface for storing and retrieving conversation history.
    """

    async def save_conversation(self, entry: ConversationEntry) -> None:
        """
        Save a conversation exchange to persistent storage.

        Args:
            entry: The conversation entry to save

        Raises:
            ValueError: If the entry is invalid
            RuntimeError: If the save operation fails
        """
        ...

    async def get_conversation_history(self, query: ConversationQuery) -> List[ConversationEntry]:
        """
        Retrieve conversation history for a user.

        Args:
            query: Query parameters for filtering conversation history

        Returns:
            List[ConversationEntry]: List of conversation entries matching the query

        Raises:
            ValueError: If the query parameters are invalid
            RuntimeError: If the retrieval operation fails
        """
        ...
