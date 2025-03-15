import pytest
from typing import Protocol
from dataclasses import dataclass
from app.application.ports.inbound.gpt_request_port import GPTRequestPort, SubmitRequestCommand
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

# Test double implementing the port interface
class MockGPTRequestUseCase(GPTRequestPort):
    def __init__(self):
        self.submit_called = False
        self.last_command = None
        self.mock_response = GPTResponse(
            text="Test response",
            tokens_used=10,
            user_id="test_user",
            request_id="test_req_123"
        )

    async def submit_request(self, command: SubmitRequestCommand) -> GPTResponse:
        self.submit_called = True
        self.last_command = command
        return self.mock_response

class TestGPTRequestPort:
    @pytest.fixture
    def port(self) -> MockGPTRequestUseCase:
        return MockGPTRequestUseCase()

    @pytest.mark.asyncio
    async def test_submit_request_command_creates_valid_request(self, port: MockGPTRequestUseCase):
        # Arrange
        command = SubmitRequestCommand(
            prompt="Test prompt",
            max_tokens=100,
            user_id="test_user"
        )

        # Act
        response = await port.submit_request(command)

        # Assert
        assert port.submit_called
        assert port.last_command == command
        assert isinstance(response, GPTResponse)
        assert response.text == "Test response"
        assert response.tokens_used == 10

    @pytest.mark.asyncio
    async def test_submit_request_command_invalid_params_raises_error(self, port: MockGPTRequestUseCase):
        """Test that invalid parameters raise appropriate validation errors"""
        # Test empty prompt
        with pytest.raises(ValueError, match="Prompt cannot be empty") as exc_info:
            SubmitRequestCommand(prompt="", max_tokens=100, user_id="test_user")
        assert "Prompt cannot be empty" in str(exc_info.value)

        # Test negative tokens
        valid_command = SubmitRequestCommand(prompt="Test", max_tokens=-1, user_id="test_user")
        assert valid_command.max_tokens >= 0, "Negative tokens should be converted to default value"

        # Test empty user_id
        with pytest.raises(ValueError, match="User ID cannot be empty") as exc_info:
            SubmitRequestCommand(prompt="Test", max_tokens=100, user_id="")
