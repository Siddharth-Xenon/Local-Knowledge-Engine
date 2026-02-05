"""Interfaces for the Prompt Engine."""

from typing import Protocol, Any


class IPromptEngine(Protocol):
    """Protocol for Prompt Engine implementations."""

    def render(
        self,
        prompt_key: str,
        version: str,
        variables: dict[str, Any],
    ) -> str:
        """
        Render a prompt template with the given variables.
        
        Args:
            prompt_key: The family/type of prompt (e.g., 'rag', 'chat')
            version: The semantic version (e.g., '1.0.0')
            variables: Dictionary of variables to inject
            
        Returns:
            Rendered prompt string
            
        Raises:
            PromptNotFoundError: If template not found
            PromptRenderError: If rendering fails
        """
        ...
