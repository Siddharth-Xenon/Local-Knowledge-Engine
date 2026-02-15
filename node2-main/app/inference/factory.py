"""Factory for creating LLM instances."""

from typing import Any

from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.llm.openai_llm import OpenAILLM

from app.config import settings
from app.inference.gemini_llm import GeminiLLM


class LLMFactory:
    """Factory for creating LLM instances based on model name."""

    @staticmethod
    def create(model_name: str, **kwargs: Any) -> LLMInterface:
        """Create an LLM instance based on the model name.

        Args:
            model_name: Name of the model (e.g., "gemini-pro", "gpt-4o").
            **kwargs: Additional arguments for the LLM constructor.

        Returns:
            An instance of LLMInterface.
        """
        if model_name.startswith("gemini"):
            return GeminiLLM(model_name=model_name, **kwargs)
        else:
            return OpenAILLM(
                model_name=model_name, api_key=settings.openai_api_key, **kwargs
            )
