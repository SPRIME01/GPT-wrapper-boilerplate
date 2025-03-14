"""
Prompt Formatter Service

This domain service is responsible for formatting user prompts according to various
requirements, including conversation history, system instructions, templates,
truncation, and few-shot examples.
"""

from typing import List, Dict, Any, Optional, Protocol, runtime_checkable
from typing_extensions import TypedDict
import re
import logging
from app.domain.models.user_context import UserContext
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

class PromptConfig(TypedDict, total=False):
    """Configuration type for prompt formatting"""
    system_instructions: str
    template: str
    max_tokens: int
    style: str
    few_shot_examples: List[Dict[str, str]]

@runtime_checkable
class PromptFormatterProtocol(Protocol):
    """Protocol defining the interface for prompt formatting services"""

    def format_prompt(
        self,
        prompt: str,
        context: Optional[UserContext] = None,
        **kwargs: Any
    ) -> str:
        """Format a user prompt with optional context and customizations"""
        ...

    def format_system_instruction(
        self,
        role: str,
        style: str,
        constraints: Optional[List[str]] = None
    ) -> str:
        """Generate system instructions based on role and style"""
        ...

@dataclass
class PromptFormatter:
    """Default implementation of prompt formatting."""
    system_instructions: str = ""
    template: str = "{prompt}"
    max_length: int = 4000

    def format_prompt(self, prompt: str, context: Optional[dict] = None) -> str:
        """Format the prompt by trimming whitespace, applying template and truncating if needed."""
        formatted = prompt.strip()
        if len(formatted) > self.max_length:
            formatted = formatted[:self.max_length]

        # Apply the template
        result = self.template.format(prompt=formatted)

        return result

class DefaultPromptFormatter:
    """
    Default implementation of the prompt formatting service.
    Handles prompt composition, context integration, and various formatting options.
    """

    def __init__(self, default_template: Optional[str] = None):
        """
        Initialize the formatter with an optional custom template.

        Args:
            default_template: Optional custom template to use instead of the default
        """
        self.default_template = default_template or "{system_instructions}\\n\\n{conversation_history}\\n\\nUser: {prompt}\\nAssistant:"
        logger.debug("Initialized DefaultPromptFormatter with template")

    # BEGIN PERFORMANCE OPTIMIZATION
    def _prepare_conversation_history(self, context: Optional[UserContext]) -> str:
        """Prepare conversation history string from context"""
        if not context or not context.conversation_history:
            return ""
        return "\\n".join(context.conversation_history)
    # END PERFORMANCE OPTIMIZATION

    def _prepare_few_shot_examples(self, examples: List[Dict[str, str]]) -> str:
        """Format few-shot examples for the prompt"""
        if not examples:
            return ""
        formatted_examples = []
        for example in examples:
            formatted_examples.append(
                f"Input: {example['input']}\\nOutput: {example['output']}"
            )
        return "\\n\\nExamples:\\n" + "\\n\\n".join(formatted_examples) + "\\n\\n"

    def format_prompt(
        self,
        prompt: str,
        context: Optional[UserContext] = None,
        system_instructions: str = "",
        template: Optional[str] = None,
        max_tokens: Optional[int] = None,
        few_shot_examples: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        """
        Format a user prompt with optional context and customizations.

        Args:
            prompt: The user's raw prompt text
            context: Optional UserContext with conversation history and preferences
            system_instructions: Optional system instructions to guide the model
            template: Optional custom template for prompt formatting
            max_tokens: Optional maximum token length for truncation
            few_shot_examples: Optional examples for few-shot prompting
            **kwargs: Additional formatting parameters

        Returns:
            Formatted prompt string ready to send to GPT API

        Raises:
            ValueError: If prompt is empty or template is invalid
        """
        try:
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")

            # BEGIN SECURITY CHECKS
            # Basic sanitization
            prompt = prompt.strip()
            # END SECURITY CHECKS

            template_to_use = template or self.default_template
            conversation_history = self._prepare_conversation_history(context)
            examples_text = self._prepare_few_shot_examples(few_shot_examples or [])

            format_params = {
                "prompt": prompt,
                "conversation_history": conversation_history,
                "system_instructions": system_instructions,
                "examples": examples_text,
                **kwargs
            }

            try:
                formatted_prompt = template_to_use.format(**format_params)
            except KeyError as e:
                logger.warning(f"Template format error: {e}. Using fallback template.")
                formatted_prompt = f"{system_instructions}\\n\\n{examples_text}{conversation_history}\\n\\nUser: {prompt}\\nAssistant:"

            # Add examples if they weren't included in the template
            if few_shot_examples and "{examples}" not in template_to_use:
                formatted_prompt = examples_text + formatted_prompt

            # Truncate if needed
            if max_tokens and len(formatted_prompt) > max_tokens * 4:
                logger.warning(f"Truncating prompt from {len(formatted_prompt)} chars to {max_tokens * 4}")
                truncated_length = max_tokens * 4
                formatted_prompt = formatted_prompt[:truncated_length] + "..."

            return formatted_prompt.strip()

        except Exception as e:
            logger.error(f"Error formatting prompt: {str(e)}")
            raise

    def format_system_instruction(
        self,
        role: str,
        style: str,
        constraints: Optional[List[str]] = None
    ) -> str:
        """
        Generate system instructions based on role, style, and constraints.

        Args:
            role: The role the assistant should take (e.g., "teacher", "programmer")
            style: The communication style (e.g., "formal", "friendly")
            constraints: Optional list of constraints to include

        Returns:
            Formatted system instruction string
        """
        try:
            instruction = f"You are a {role} who communicates in a {style} style."

            if constraints:
                constraints_text = " ".join(f"- {constraint}" for constraint in constraints)
                instruction += f"\\n\\nPlease adhere to these constraints:\\n{constraints_text}"

            logger.debug(f"Generated system instruction for role: {role}")
            return instruction

        except Exception as e:
            logger.error(f"Error formatting system instruction: {str(e)}")
            raise
