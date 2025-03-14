import pytest
from app.application.ports.outbound.gpt_api_port import GPTAPIPort, GPTAPIRequest
from app.domain.models.gpt_request import GPTRequest
from app.domain.models.gpt_response import GPTResponse

class MockGPTAPIAdapter(GPTAPIPort):
    def __init__(self):
        self.call_count = 0
        self.last_request = None
        self.should_fail = False
        self.mock_response = GPTResponse(
            text="Mocked API response",
            tokens_used=50,
            user_id="test_user",
            request_id="test_req_123"
        )

    async def generate_completion(self, request: GPTAPIRequest) -> GPTResponse:
        if self.should_fail:
            raise ConnectionError("API connection failed")
        self.call_count += 1
        self.last_request = request
        return self.mock_response

class TestGPTAPIPort:
    @pytest.fixture
    def port(self) -> MockGPTAPIAdapter:
        return MockGPTAPIAdapter()

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, port: MockGPTAPIAdapter):
        # Arrange
        api_request = GPTAPIRequest(
            prompt="Test prompt",
            max_tokens=100,
            user_id="test_user"
        )

        # Act
        response = await port.generate_completion(api_request)

        # Assert
        assert port.call_count == 1
        assert port.last_request == api_request
        assert response.text == "Mocked API response"
        assert response.tokens_used == 50

    @pytest.mark.asyncio
    async def test_generate_completion_handles_api_failure(self, port: MockGPTAPIAdapter):
        # Arrange
        port.should_fail = True
        api_request = GPTAPIRequest(
            prompt="Test prompt",
            max_tokens=100,
            user_id="test_user"
        )

        # Act & Assert
        with pytest.raises(ConnectionError):
            await port.generate_completion(api_request)
