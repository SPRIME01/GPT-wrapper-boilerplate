from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.infrastructure.container import Container

# Create API router
router = APIRouter()

# --- Models ---
class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    user_id: str

class SessionRequest(BaseModel):
    user_id: str
    preferences: Optional[Dict[str, Any]] = None

# --- API Endpoints ---
@router.get("/api/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy"}

@router.post("/api/v1/gpt/prompt")
async def submit_prompt(request: PromptRequest):
    """Submit a prompt to GPT model"""
    try:
        use_case = Container.submit_request_use_case()
        result = await use_case.execute({
            "prompt": request.prompt,
            "user_id": request.user_id,
            "max_tokens": request.max_tokens
        })

        return {
            "text": result["data"]["response"],
            "tokens_used": result["data"]["tokens_used"],
            "finish_reason": result["data"]["finish_reason"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@router.post("/api/v1/session", status_code=201)
async def create_session(request: SessionRequest):
    """Create a new conversation session"""
    try:
        repository = Container.conversation_repository()
        session_data = {
            "user_id": request.user_id,
            "preferences": request.preferences
        }
        conversation = await repository.create_session(session_data)

        return {
            "session_id": conversation["id"],
            "created_at": conversation.get("created_at", None),
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )

@router.get("/api/v1/history/{user_id}")
async def get_history(user_id: str):
    """Get conversation history for a user"""
    try:
        repository = Container.conversation_repository()
        conversations = await repository.get_conversations_by_user(user_id)

        return {
            "user_id": user_id,
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving history: {str(e)}"
        )
