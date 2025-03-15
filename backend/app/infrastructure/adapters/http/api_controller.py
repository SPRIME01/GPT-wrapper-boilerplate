from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.infrastructure.container import Container
from app.infrastructure.adapters.http.graphql_schema import schema

# FastAPI application
app = FastAPI(title="GPT Wrapper API")

# Models for request/response
class GPTRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = "default"

class MessageModel(BaseModel):
    role: str
    content: str

class ConversationModel(BaseModel):
    id: str
    messages: List[MessageModel]

class GPTResponseModel(BaseModel):
    prompt: str
    response: str
    conversation_id: str

class SessionRequest(BaseModel):
    name: Optional[str] = None

# Routes
@app.post("/api/prompt", response_model=GPTResponseModel, status_code=status.HTTP_200_OK)
async def submit_prompt(request: GPTRequest):
    """Submit a prompt to GPT"""
    try:
        use_case = Container.submit_request_use_case()
        result = use_case.execute(request.model_dump())

        return GPTResponseModel(
            prompt=result["data"]["prompt"],
            response=result["data"]["response"],
            conversation_id=result["data"]["conversation_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@app.get("/api/history/{conversation_id}", response_model=ConversationModel)
async def get_history(conversation_id: str = "default"):
    """Get conversation history"""
    try:
        repository = Container.conversation_repository()
        conversation = repository.get_conversation(conversation_id)

        if not conversation:
            return ConversationModel(id=conversation_id, messages=[])

        return ConversationModel(
            id=conversation["id"],
            messages=[MessageModel(role=msg["role"], content=msg["content"])
                     for msg in conversation.get("messages", [])]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@app.post("/api/session", response_model=ConversationModel, status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionRequest):
    """Create a new conversation session"""
    try:
        repository = Container.conversation_repository()
        session_data = {"name": request.name} if request.name else {}
        conversation = repository.create_session(session_data)

        return ConversationModel(
            id=conversation["id"],
            messages=[MessageModel(role=msg["role"], content=msg["content"])
                     for msg in conversation.get("messages", [])]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

# Mount GraphQL routes
app.add_route("/graphql", schema)
