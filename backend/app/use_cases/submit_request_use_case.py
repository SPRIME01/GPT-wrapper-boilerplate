from typing import Any, Protocol

class GPTServicePort(Protocol):
    """Protocol for GPT service"""
    def process_request(self, prompt: str) -> str:
        ...

class ConversationRepositoryPort(Protocol):
    """Protocol for conversation repository"""
    def save_conversation(self, conversation_id: str, data: dict) -> None:
        ...
    def get_conversation(self, conversation_id: str) -> dict:
        ...

class SubmitRequestUseCase:
    """
    Use case for submitting requests to GPT.

    This class coordinates the process of sending prompts to GPT and saving responses.
    """
    def __init__(
        self,
        gpt_service: GPTServicePort,
        conversation_repository: ConversationRepositoryPort
    ):
        self.gpt_service = gpt_service
        self.conversation_repository = conversation_repository

    def execute(self, request_data: dict) -> dict:
        # Extract prompt from request data
        prompt = request_data.get("prompt", "")
        conversation_id = request_data.get("conversation_id", "default")

        # Process request through GPT service
        response = self.gpt_service.process_request(prompt)

        # Save to conversation history
        conversation = self.conversation_repository.get_conversation(conversation_id) or {"id": conversation_id, "messages": []}
        conversation["messages"].append({
            "role": "user",
            "content": prompt
        })
        conversation["messages"].append({
            "role": "assistant",
            "content": response
        })

        self.conversation_repository.save_conversation(conversation_id, conversation)

        # Return response
        return {
            "status": "success",
            "data": {
                "prompt": prompt,
                "response": response,
                "conversation_id": conversation_id
            }
        }
