"""
Test fixtures for CopilotKit integration testing.

This module provides fixtures for mocking CopilotKit API requests and responses
to facilitate testing without requiring actual CopilotKit API calls.
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
import json
import pytest
from fastapi.testclient import TestClient


class CopilotChatMessage(BaseModel):
    """Model representing a chat message in CopilotKit format."""
    role: Literal["user", "assistant", "system", "function"]
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


class CopilotChatRequest(BaseModel):
    """Model representing a chat request from CopilotKit."""
    messages: List[CopilotChatMessage]
    stream: bool = True
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    functions: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None


class CopilotActionRequest(BaseModel):
    """Model representing an action request from CopilotKit."""
    name: str
    arguments: Dict[str, Any]
    action_id: str = Field(..., alias="actionId")
    context: Optional[Dict[str, Any]] = None


@pytest.fixture
def mock_copilotkit_chat_request() -> CopilotChatRequest:
    """
    Creates a mock CopilotKit chat request.

    Returns:
        CopilotChatRequest: A sample chat request
    """
    return CopilotChatRequest(
        messages=[
            CopilotChatMessage(
                role="system",
                content="You are a helpful AI assistant."
            ),
            CopilotChatMessage(
                role="user",
                content="What is the capital of France?"
            )
        ],
        stream=True,
        model="gpt-4",
        temperature=0.7
    )


@pytest.fixture
def mock_copilotkit_chat_request_with_functions() -> CopilotChatRequest:
    """
    Creates a mock CopilotKit chat request with function definitions.

    Returns:
        CopilotChatRequest: A sample chat request with functions
    """
    return CopilotChatRequest(
        messages=[
            CopilotChatMessage(
                role="system",
                content="You are a helpful AI assistant with tool capabilities."
            ),
            CopilotChatMessage(
                role="user",
                content="Schedule a meeting with John tomorrow at 2pm"
            )
        ],
        stream=True,
        model="gpt-4",
        temperature=0.7,
        functions=[
            {
                "name": "schedule_meeting",
                "description": "Schedule a meeting with someone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "person": {
                            "type": "string",
                            "description": "Name of the person to meet"
                        },
                        "time": {
                            "type": "string",
                            "description": "Time of the meeting in ISO format"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration of meeting in minutes"
                        }
                    },
                    "required": ["person", "time"]
                }
            }
        ]
    )


@pytest.fixture
def mock_copilotkit_action_request() -> CopilotActionRequest:
    """
    Creates a mock CopilotKit action request.

    Returns:
        CopilotActionRequest: A sample action request
    """
    return CopilotActionRequest(
        name="schedule_meeting",
        arguments={
            "person": "John",
            "time": "2023-07-15T14:00:00",
            "duration_minutes": 30
        },
        actionId="action-123456",
        context={
            "user_id": "test-user-123",
            "timezone": "America/New_York"
        }
    )


@pytest.fixture
def mock_copilotkit_streaming_response() -> List[Dict[str, Any]]:
    """
    Creates a mock streaming response in CopilotKit format.

    Returns:
        List[Dict[str, Any]]: A list of streaming response chunks
    """
    return [
        {"delta": {"role": "assistant"}, "finish_reason": None},
        {"delta": {"content": "Paris"}, "finish_reason": None},
        {"delta": {"content": " is"}, "finish_reason": None},
        {"delta": {"content": " the"}, "finish_reason": None},
        {"delta": {"content": " capital"}, "finish_reason": None},
        {"delta": {"content": " of"}, "finish_reason": None},
        {"delta": {"content": " France"}, "finish_reason": None},
        {"delta": {"content": "."}, "finish_reason": None},
        {"delta": {}, "finish_reason": "stop"}
    ]


@pytest.fixture
def mock_copilotkit_function_call_response() -> List[Dict[str, Any]]:
    """
    Creates a mock streaming response with function call in CopilotKit format.

    Returns:
        List[Dict[str, Any]]: A list of streaming response chunks with a function call
    """
    return [
        {"delta": {"role": "assistant"}, "finish_reason": None},
        {"delta": {"content": None, "function_call": {"name": "schedule_meeting"}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "{"}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "\n  \"person\": \""}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "John"}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "\",\n  \"time\": \""}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "2023-07-15T14:00:00"}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "\",\n  \"duration_minutes\": "}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "30"}}, "finish_reason": None},
        {"delta": {"function_call": {"arguments": "\n}"}}, "finish_reason": None},
        {"delta": {}, "finish_reason": "function_call"}
    ]


@pytest.fixture
def copilotkit_client(app) -> TestClient:
    """
    Creates a TestClient for testing CopilotKit endpoints.

    Args:
        app: The FastAPI app fixture

    Returns:
        TestClient: A configured TestClient for testing
    """
    from fastapi.testclient import TestClient
    return TestClient(app)
