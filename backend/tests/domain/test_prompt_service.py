import pytest
from typing import Dict
from app.domain.services.prompt_service import PromptService
from app.domain.models.gpt_request import GPTRequest

class TestPromptService:
    def test_format_prompt_with_template(self):
        # Arrange
        prompt_service = PromptService()
        template = "You are a {role}. Help {user} with {task}."
        context: Dict[str, str] = {
            "role": "helpful assistant",
            "user": "John",
            "task": "writing code"
        }

        # Act
        formatted_prompt = prompt_service.format_prompt(template, context)

        # Assert
        expected = "You are a helpful assistant. Help John with writing code."
        assert formatted_prompt == expected

    def test_format_prompt_with_missing_context(self):
        # Arrange
        prompt_service = PromptService()
        template = "You are a {role}. Help with {task}."
        context: Dict[str, str] = {
            "role": "helpful assistant"
        }

        # Act & Assert
        with pytest.raises(KeyError) as exc_info:
            prompt_service.format_prompt(template, context)
        assert "task" in str(exc_info.value)

    def test_validate_prompt_length(self):
        # Arrange
        prompt_service = PromptService()
        max_length = 10
        prompt = "This is a very long prompt that exceeds the maximum length"

        # Act
        is_valid = prompt_service.validate_prompt_length(prompt, max_length)

        # Assert
        assert not is_valid
