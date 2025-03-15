from typing import Dict, Optional, Any

class ConversationRepository:
    """
    Repository for managing conversation data.

    This repository handles conversation-related data operations.
    """
    def __init__(self):
        # In-memory storage for conversations
        self._storage: Dict[str, Any] = {}

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """
        Retrieve a conversation by ID.

        Args:
            conversation_id: The unique identifier for the conversation

        Returns:
            The conversation data or None if not found
        """
        return self._storage.get(conversation_id)

    def save_conversation(self, conversation_id: str, data: dict) -> None:
        """
        Save conversation data.

        Args:
            conversation_id: The unique identifier for the conversation
            data: The conversation data to save
        """
        self._storage[conversation_id] = data

    def create_session(self, session_data: dict) -> dict:
        """
        Create a new conversation session.

        Args:
            session_data: Initial data for the session

        Returns:
            The created session data
        """
        conversation_id = session_data.get("id", f"session-{len(self._storage) + 1}")
        self._storage[conversation_id] = {
            "id": conversation_id,
            "messages": [],
            **session_data
        }
        return self._storage[conversation_id]
