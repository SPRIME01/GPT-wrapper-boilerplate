"""
Test fixtures for conversation data used in CopilotKit integration testing.

This module provides fixtures for creating sample conversation data
to use in tests related to chat history and context management.
"""
from typing import Dict, List, Any, Optional
import pytest
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel, Field
import json


class ConversationMessage(BaseModel):
    """Model representing a message in a conversation."""
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    """Model representing a conversation history."""
    id: str
    title: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessage]
    metadata: Optional[Dict[str, Any]] = None


@pytest.fixture
def sample_conversation_history() -> List[Conversation]:
    """
    Creates sample conversation histories for testing.

    Returns:
        List[Conversation]: A list of sample conversations
    """
    now = datetime.now()

    # First conversation - about weather
    weather_conversation = Conversation(
        id="conv-weather-123",
        title="Weather Inquiry",
        user_id="test-user-1",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(hours=23),
        messages=[
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-weather-123",
                role="user",
                content="What's the weather like in New York today?",
                timestamp=now - timedelta(days=1, minutes=30)
            ),
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-weather-123",
                role="assistant",
                content="I don't have real-time weather data. To get the current weather in New York, you would need to check a weather service or app.",
                timestamp=now - timedelta(days=1, minutes=29)
            ),
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-weather-123",
                role="user",
                content="Can you recommend a good weather app?",
                timestamp=now - timedelta(days=1, minutes=25)
            ),
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-weather-123",
                role="assistant",
                content="Some popular weather apps include AccuWeather, The Weather Channel, Weather Underground, and Dark Sky. Many people also use the default weather apps on their phones, like Apple Weather or Google Weather.",
                timestamp=now - timedelta(days=1, minutes=24)
            )
        ]
    )

    # Second conversation - about programming
    programming_conversation = Conversation(
        id="conv-programming-456",
        title="Python Programming Help",
        user_id="test-user-1",
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=4),
        messages=[
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-programming-456",
                role="user",
                content="How do I read a JSON file in Python?",
                timestamp=now - timedelta(hours=5)
            ),
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-programming-456",
                role="assistant",
                content="To read a JSON file in Python, you can use the built-in `json` module. Here's an example:\n\n```python\nimport json\n\nwith open('data.json', 'r') as file:\n    data = json.load(file)\n\nprint(data)  # Now you can work with your JSON data\n```\n\nThis opens the file, parses the JSON content, and loads it into a Python dictionary.",
                timestamp=now - timedelta(hours=4, minutes=58)
            ),
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-programming-456",
                role="user",
                content="What if the JSON file is very large?",
                timestamp=now - timedelta(hours=4, minutes=30)
            ),
            ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id="conv-programming-456",
                role="assistant",
                content="For very large JSON files, loading the entire file into memory might not be efficient. You have a few options:\n\n1. Use streaming JSON parsing with libraries like `ijson` which parse incrementally\n2. Use memory-mapped files\n3. Process the JSON in chunks\n\nHere's an example with `ijson`:\n\n```python\nimport ijson\n\nwith open('large_file.json', 'rb') as f:\n    # Process objects one by one\n    for item in ijson.items(f, 'item'):\n        process_item(item)  # Do something with each item\n```\n\nThis way, you don't need to load the entire file into memory at once.",
                timestamp=now - timedelta(hours=4, minutes=28)
            )
        ]
    )

    return [weather_conversation, programming_conversation]


@pytest.fixture
def mock_conversation_db(sample_conversation_history):
    """
    Creates a mock conversation database for testing.

    Args:
        sample_conversation_history: Sample conversation history from fixture

    Returns:
        dict: A dictionary with functions to interact with mock conversation data
    """
    conversations = {conv.id: conv for conv in sample_conversation_history}

    def get_conversation(conversation_id):
        return conversations.get(conversation_id)

    def get_user_conversations(user_id):
        return [conv for conv in conversations.values() if conv.user_id == user_id]

    def add_message(conversation_id, role, content, metadata=None):
        if conversation_id not in conversations:
            return None

        message = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )

        conversations[conversation_id].messages.append(message)
        conversations[conversation_id].updated_at = datetime.now()
        return message

    def create_conversation(user_id, title="New Conversation", metadata=None):
        conv_id = f"conv-{uuid.uuid4()}"
        now = datetime.now()
        conversation = Conversation(
            id=conv_id,
            title=title,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata
        )
        conversations[conv_id] = conversation
        return conversation

    return {
        "get_conversation": get_conversation,
        "get_user_conversations": get_user_conversations,
        "add_message": add_message,
        "create_conversation": create_conversation,
        "all_conversations": lambda: list(conversations.values())
    }
