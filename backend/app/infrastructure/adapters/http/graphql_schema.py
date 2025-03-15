import strawberry
from typing import List, Dict, Any, Optional
from dependency_injector.wiring import Provide, inject
from app.infrastructure.container import Container
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse
from app.domain.conversation_repository import ConversationRepository
from app.use_cases.submit_request_use_case import SubmitRequestUseCase

# GraphQL Types
@strawberry.type(name="Message")
class Message:
    """A message in a conversation"""
    role: str
    content: str

@strawberry.type(name="Conversation")
class Conversation:
    """A conversation containing messages"""
    id: str
    messages: List[Message]

@strawberry.type(name="GPTResponse")
class GPTResponseType:
    """Response from the GPT model"""
    text: str
    tokens_used: int = strawberry.field(name="tokensUsed")
    finish_reason: str | None = strawberry.field(name="finishReason", default=None)

@strawberry.input(name="GPTRequestInput")
class GPTRequestInput:
    """Input for a GPT request"""
    prompt: str
    user_id: str = strawberry.field(name="userId")
    conversation_id: Optional[str] = "default"

@strawberry.input(name="SessionInput")
class SessionInput:
    """Input for creating a new session"""
    name: Optional[str] = None
    user_id: str = strawberry.field(name="userId")

# Query and Mutations
@strawberry.type(name="Query")
class Query:
    @strawberry.field(description="Get conversation history by ID")
    async def conversation_history(self, conversation_id: str = "default") -> Conversation:
        repository = Container.conversation_repository()
        conversation = await repository.get_conversation(conversation_id)

        if not conversation:
            # Return empty conversation if not found
            return Conversation(id=conversation_id, messages=[])

        return Conversation(
            id=conversation["id"],
            messages=[Message(role=msg["role"], content=msg["content"])
                     for msg in conversation.get("messages", [])]
        )

@strawberry.type(name="Mutation")
class Mutation:
    @strawberry.mutation(description="Submit a request to GPT")
    async def submit_gpt_request(self, request: GPTRequestInput) -> GPTResponseType:
        use_case = Container.submit_request_use_case()
        request_dict = {
            "prompt": request.prompt,
            "user_id": request.user_id,
            "conversation_id": request.conversation_id
        }
        result = await use_case.execute(request_dict)

        return GPTResponseType(
            text=result["data"]["response"],
            tokens_used=result["data"]["tokens_used"],
            finish_reason=result["data"]["finish_reason"]
        )

    @strawberry.mutation(description="Create a new conversation session")
    async def create_session(self, session_input: SessionInput) -> Conversation:
        repository = Container.conversation_repository()
        session_data = {
            "user_id": session_input.user_id,
            "name": session_input.name
        }
        conversation = await repository.create_session(session_data)

        return Conversation(
            id=conversation["id"],
            messages=[Message(role=msg["role"], content=msg["content"])
                     for msg in conversation.get("messages", [])]
        )

# Schema instance
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)
