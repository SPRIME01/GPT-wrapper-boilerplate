from typing import Dict, List, Optional
from app.application.ports.outbound.conversation_persistence_port import ConversationPersistencePort
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

class ConversationRepository(ConversationPersistencePort):
    """In-memory implementation of the conversation repository."""

    def __init__(self):
        self._conversations: Dict[str, List[tuple[GPTRequest, GPTResponse]]] = {}

    async def save_conversation(self, user_id: str, request: GPTRequest, response: GPTResponse) -> None:
        """Save a conversation exchange to the repository."""
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        self._conversations[user_id].append((request, response))

    async def get_conversation_history(self, user_id: str, limit: Optional[int] = None) -> List[tuple[GPTRequest, GPTResponse]]:
        """Retrieve conversation history for a user."""
        history = self._conversations.get(user_id, [])
        if limit is not None:
            return history[-limit:]
        return history

    async def clear_conversation_history(self, user_id: str) -> None:
        """Clear conversation history for a user."""
        if user_id in self._conversations:
            del self._conversations[user_id]
