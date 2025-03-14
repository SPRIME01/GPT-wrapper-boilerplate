from typing import Dict

class PromptService:
    def format_prompt(self, template: str, context: Dict[str, str]) -> str:
        """
        Formats a prompt template using the provided context.

        Args:
            template: A string containing placeholders in {variable} format
            context: A dictionary containing values for the placeholders

        Returns:
            Formatted prompt string

        Raises:
            KeyError: If a required placeholder is missing from the context
        """
        try:
            return template.format(**context)
        except KeyError as e:
            raise KeyError(f"Missing required context variable: {str(e)}")

    def validate_prompt_length(self, prompt: str, max_length: int) -> bool:
        """
        Validates that a prompt doesn't exceed the maximum length.

        Args:
            prompt: The prompt string to validate
            max_length: Maximum allowed length

        Returns:
            bool: True if prompt length is valid, False otherwise
        """
        return len(prompt) <= max_length
