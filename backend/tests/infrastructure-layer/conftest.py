import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dependency_injector import containers, providers
from app.infrastructure.container import Container
from app.domain.models.gpt_response import GPTResponse
from app.domain.models.gpt_request import GPTRequest

@pytest.fixture
def mock_gpt_service():
    """Create a mock GPT service"""
    mock = AsyncMock()
    mock.generate_completion = AsyncMock(return_value=GPTResponse(
        text="This is a test response",
        tokens_used=10,
        finish_reason="stop",
        user_id="test_user",
        request_id="test_request"
    ))
    return mock

@pytest.fixture
def mock_conversation_repo():
    """Create a mock conversation repository"""
    mock = AsyncMock()
    mock.save_conversation = AsyncMock()
    mock.get_conversation = AsyncMock(return_value={
        "id": "default",
        "messages": [
            {"role": "user", "content": "test prompt"},
            {"role": "assistant", "content": "test response"}
        ]
    })
    mock.create_session = AsyncMock(return_value={
        "id": "test-session-1",
        "created_at": "2024-01-01T00:00:00Z",
        "user_id": "test_user",
        "messages": []
    })
    mock.get_conversations_by_user = AsyncMock(return_value=[
        {
            "id": "test_convo",
            "messages": [
                {"role": "user", "content": "test prompt"},
                {"role": "assistant", "content": "test response"}
            ]
        }
    ])
    return mock

@pytest.fixture
def mock_submit_use_case():
    """Create a mock submit request use case"""
    mock = AsyncMock()
    mock.submit_request = AsyncMock(return_value=GPTResponse(
        text="Test response for prompt",
        tokens_used=42,
        finish_reason="stop",
        user_id="test_user",
        request_id="test-123"
    ))
    mock.execute = AsyncMock(return_value={
        "data": {
            "response": "Test response for prompt",
            "tokens_used": 42,
            "finish_reason": "stop"
        }
    })
    return mock

@pytest.fixture
def mock_session_use_case():
    """Create a mock session lifecycle use case"""
    mock = AsyncMock()
    mock.create_session = AsyncMock(return_value={
        "session_id": "test-session-1",
        "user_id": "test_user"
    })
    return mock

class TestContainer:
    """Test container that provides mock dependencies through static methods."""
    _instance = None
    _mocks = {}

    @classmethod
    def set_mocks(cls, mocks):
        """Set mock instances that will be returned by provider methods"""
        cls._mocks = mocks

    @classmethod
    def reset(cls):
        """Reset all mocks"""
        cls._mocks = {}

    @classmethod
    def gpt_service(cls):
        return cls._mocks.get('gpt_service')

    @classmethod
    def gpt_api(cls):
        return cls._mocks.get('gpt_api')

    @classmethod
    def conversation_repository(cls):
        return cls._mocks.get('conversation_repository')

    @classmethod
    def submit_use_case(cls):
        return cls._mocks.get('submit_use_case')

    @classmethod
    def submit_request_use_case(cls):
        return cls._mocks.get('submit_use_case')

    @classmethod
    def session_use_case(cls):
        return cls._mocks.get('session_use_case')

    @classmethod
    def wire(cls, modules):
        """Mock wire method"""
        pass

    @classmethod
    def unwire(cls):
        """Mock unwire method"""
        cls.reset()

@pytest.fixture
def mock_container(mock_conversation_repo, mock_gpt_service, mock_submit_use_case, mock_session_use_case):
    """Create a container with mock dependencies for tests"""
    # Set up mocks in the test container
    TestContainer.set_mocks({
        'gpt_service': mock_gpt_service,
        'gpt_api': mock_gpt_service,
        'conversation_repository': mock_conversation_repo,
        'submit_use_case': mock_submit_use_case,
        'session_use_case': mock_session_use_case
    })

    return TestContainer

@pytest.fixture
def test_client(mock_container):
    """Create a FastAPI test client with mocked dependencies"""
    from app.main import app

    # Patch all container references to use our TestContainer
    patches = [
        patch('app.main.Container', mock_container),
        patch('app.infrastructure.adapters.http.graphql_schema.Container', mock_container),
        patch('app.infrastructure.adapters.http.fastapi_controllers.Container', mock_container)
    ]

    # Start all patches
    for p in patches:
        p.start()

    # Create test client
    with TestClient(app) as client:
        yield client

    # Stop all patches
    for p in patches:
        p.stop()

    # Reset container
    mock_container.reset()

@pytest.fixture
def mock_schema_container(mock_container):
    """Create a container specifically for GraphQL schema tests"""
    from app.infrastructure.adapters.http.graphql_schema import schema

    # Update schema's container references
    patches = [
        patch('app.infrastructure.adapters.http.graphql_schema.Container', mock_container)
    ]

    # Start all patches
    for p in patches:
        p.start()

    yield mock_container

    # Stop all patches
    for p in patches:
        p.stop()
