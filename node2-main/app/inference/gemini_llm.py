"""neo4j-graphrag LLM adapter describing Google Gemini."""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import types
from neo4j_graphrag.exceptions import LLMGenerationError
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.llm.types import LLMResponse
from neo4j_graphrag.message_history import MessageHistory
from neo4j_graphrag.types import LLMMessage

from app.config import settings
from app.inference.types import ThinkingLevel

logger = logging.getLogger(__name__)


class GeminiLLM(LLMInterface):
    """LLM adapter for Google Gemini via google-genai package."""

    def __init__(
        self,
        model_name: str | None = None,
        model_params: dict[str, Any] | None = None,
        api_key: str | None = None,
        thinking_level: str | ThinkingLevel | None = None,
        thinking_budget: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model_name=model_name or settings.gemini_model,
            model_params=model_params,
            **kwargs,
        )
        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise ValueError("Google API Key is required for GeminiLLM")

        self.client = genai.Client(api_key=self.api_key)

        # Configure thinking
        self.thinking_level = thinking_level or settings.gemini_thinking_level
        if isinstance(self.thinking_level, str):
            # Ensure valid enum member if string passed
            try:
                self.thinking_level = ThinkingLevel(self.thinking_level)
            except ValueError:
                # Fallback or strict? Let's be strict but allow case-insensitivity if needed
                # For now, standard Enum behavior
                pass

        self.thinking_budget = thinking_budget or settings.gemini_thinking_budget

    def _build_prompt(
        self,
        input: str,
        message_history: (list[LLMMessage] | MessageHistory | None) = None,
        system_instruction: str | None = None,
    ) -> str:
        """Construct prompt for Gemini.

        Flattening to string for simplicity as per neo4j-graphrag interface patterns.
        """
        parts: list[str] = []

        if system_instruction:
            parts.append(f"System: {system_instruction}")

        if message_history:
            messages = (
                message_history.messages
                if isinstance(message_history, MessageHistory)
                else message_history
            )
            for msg in messages:
                role = msg.get("role", "user").title()
                content = msg.get("content", "")
                parts.append(f"{role}: {content}")

        parts.append(f"User: {input}")
        return "\n\n".join(parts)

    def invoke(
        self,
        input: str,
        message_history: (list[LLMMessage] | MessageHistory | None) = None,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        """Synchronous inference via Google GenAI SDK."""
        prompt = self._build_prompt(input, message_history, system_instruction)

        config = None
        if self.thinking_level:
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False,  # We usually just want the output unless debugging
                    thinking_level=self.thinking_level,
                    thinking_budget=self.thinking_budget,
                )
            )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return LLMResponse(content=response.text)

        except Exception as e:
            if config and (
                "thinking" in str(e).lower() or "unsupported" in str(e).lower()
            ):
                logger.warning(
                    f"Thinking mode not supported by model {self.model_name}, retrying without thinking config. Error: {e}"
                )
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                    )
                    return LLMResponse(content=response.text)
                except Exception as retry_e:
                    raise LLMGenerationError(
                        f"Gemini inference failed (retry): {retry_e}"
                    ) from retry_e
            raise LLMGenerationError(f"Gemini inference failed: {e}") from e

    async def ainvoke(
        self,
        input: str,
        message_history: (list[LLMMessage] | MessageHistory | None) = None,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        """Async inference via Google GenAI SDK."""
        prompt = self._build_prompt(input, message_history, system_instruction)

        config = None
        if self.thinking_level:
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False,
                    thinking_level=self.thinking_level,
                    thinking_budget=self.thinking_budget,
                )
            )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return LLMResponse(content=response.text)

        except Exception as e:
            if config and (
                "thinking" in str(e).lower() or "unsupported" in str(e).lower()
            ):
                logger.warning(
                    f"Thinking mode not supported by model {self.model_name}, retrying without thinking config. Error: {e}"
                )
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                    )
                    return LLMResponse(content=response.text)
                except Exception as retry_e:
                    raise LLMGenerationError(
                        f"Gemini inference failed (retry): {retry_e}"
                    ) from retry_e
            raise LLMGenerationError(f"Gemini inference failed: {e}") from e
