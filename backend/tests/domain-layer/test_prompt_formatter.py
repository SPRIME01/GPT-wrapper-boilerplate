import pytest
from app.domain.services.prompt_formatter import PromptFormatter

class TestPromptFormatter:
    def test_basic_formatting(self):
        """Test basic prompt formatting without context"""
        formatter = PromptFormatter()
        input_prompt = "  test prompt  "
        expected = "test prompt"
        assert formatter.format_prompt(input_prompt) == expected

    def test_formatting_with_user_context(self):
        """Test formatting with user context and conversation history"""
        formatter = PromptFormatter(template="User: {prompt}")
        input_prompt = "test prompt"
        assert formatter.format_prompt(input_prompt) == "User: test prompt"

    def test_formatting_with_system_instructions(self):
        """Test formatting with system instructions"""
        formatter = PromptFormatter(system_instructions="Be helpful")
        input_prompt = "test prompt"
        assert formatter.format_prompt(input_prompt) == "test prompt"

    def test_formatting_with_template(self):
        """Test formatting using a custom template"""
        formatter = PromptFormatter(template="Q: {prompt}\nA:")
        input_prompt = "test prompt"
        assert formatter.format_prompt(input_prompt) == "Q: test prompt\nA:"

    def test_truncation_of_long_prompts(self):
        """Test that long prompts get truncated appropriately"""
        formatter = PromptFormatter(max_length=10)
        input_prompt = "this is a very long prompt"
        assert len(formatter.format_prompt(input_prompt)) <= 10

    def test_formatting_with_few_shot_examples(self):
        """Test formatting with few-shot examples"""
        formatter = PromptFormatter()
        input_prompt = "test prompt"
        assert formatter.format_prompt(input_prompt) == "test prompt"
