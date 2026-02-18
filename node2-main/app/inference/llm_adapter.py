"""neo4j-graphrag LLM adapter that routes inference to Node 1 HTTP API."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from neo4j_graphrag.exceptions import LLMGenerationError
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.llm.types import LLMResponse
from neo4j_graphrag.message_history import MessageHistory
from neo4j_graphrag.types import LLMMessage

from app.config import settings
from app.core import InferenceTimeoutError, InferenceUnavailableError
from app.inference.client import InferenceClient

logger = logging.getLogger(__name__)


def _flatten_messages(messages: list[BaseMessage]) -> str:
    """Flatten LangChain messages into a single prompt string."""
    parts: list[str] = []
    for msg in messages:
        role = msg.type.title()
        parts.append(f"[{role}]\n{msg.content}")
    return "\n\n".join(parts)


class Node1LLM(LLMInterface):
    """LLM adapter bridging neo4j-graphrag with Node 1 inference API.

    Sync calls use httpx.Client directly.
    Async calls delegate to InferenceClient (retry + timeout built-in).
    """

    def __init__(
        self,
        model_name: str = "deepseek-r1:8b-llama-distill-q4_K_M",
        model_params: dict[str, Any] | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model_name=model_name,
            model_params=model_params,
            **kwargs,
        )
        self.base_url = base_url or settings.node1_url
        self.timeout = 240
        self._async_client = InferenceClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def _build_prompt(
        self,
        input: str,
        message_history: (list[LLMMessage] | MessageHistory | None) = None,
        system_instruction: str | None = None,
    ) -> str:
        """Flatten system + history + user input into one prompt."""
        parts: list[str] = []

        if system_instruction:
            parts.append(f"[System]\n{system_instruction}")

        if message_history:
            messages = (
                message_history.messages
                if isinstance(message_history, MessageHistory)
                else message_history
            )
            for msg in messages:
                role = msg.get("role", "user").title()
                content = msg.get("content", "")
                parts.append(f"[{role}]\n{content}")

        parts.append(f"[User]\n{input}")
        return "\n\n".join(parts)

    def invoke(
        self,
        input: str,
        message_history: (list[LLMMessage] | MessageHistory | None) = None,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        """Synchronous inference via Node 1 HTTP API."""
        prompt = self._build_prompt(input, message_history, system_instruction)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "prompt": prompt,
                    "model": self.model_name,
                    "stream": False,
                }
                response = client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return LLMResponse(content=data["response"])

        except httpx.TimeoutException as e:
            raise LLMGenerationError(f"Node 1 timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise LLMGenerationError(f"Node 1 unavailable: {e}") from e
        except (KeyError, Exception) as e:
            raise LLMGenerationError(f"Node 1 inference failed: {e}") from e

    async def ainvoke(
        self,
        input: str,
        message_history: (list[LLMMessage] | MessageHistory | None) = None,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        """Async inference via Node 1 (uses InferenceClient)."""
        prompt = self._build_prompt(input, message_history, system_instruction)

        try:
            response_text = await self._async_client.generate(
                prompt=prompt,
                model=self.model_name,
            )
            return LLMResponse(content=response_text)

        except (
            InferenceTimeoutError,
            InferenceUnavailableError,
        ) as e:
            raise LLMGenerationError(str(e)) from e
        except Exception as e:
            raise LLMGenerationError(f"Node 1 inference failed: {e}") from e


class Node1ChatModel(BaseChatModel):
    """LangChain BaseChatModel wrapping Node 1 inference API.

    Use this adapter with LangChain chains and LangGraph workflows.
    For neo4j-graphrag components, use Node1LLM instead.
    """

    model_name: str = "deepseek-r1:8b-llama-distill-q4_K_M"
    base_url: str = settings.node1_url
    timeout: int = settings.inference_timeout

    @property
    def _llm_type(self) -> str:
        return "node1-local"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Synchronous inference via Node 1 HTTP API."""
        prompt = _flatten_messages(messages)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "prompt": prompt,
                    "model": self.model_name,
                    "stream": False,
                }
                response = client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = data["response"]

        except httpx.TimeoutException as e:
            raise LLMGenerationError(f"Node 1 timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise LLMGenerationError(f"Node 1 unavailable: {e}") from e
        except (KeyError, Exception) as e:
            raise LLMGenerationError(f"Node 1 inference failed: {e}") from e

        message = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async inference via Node 1 (uses InferenceClient)."""
        prompt = _flatten_messages(messages)
        async_client = InferenceClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )

        try:
            response_text = await async_client.generate(
                prompt=prompt,
                model=self.model_name,
            )
        except (InferenceTimeoutError, InferenceUnavailableError) as e:
            raise LLMGenerationError(str(e)) from e
        except Exception as e:
            raise LLMGenerationError(f"Node 1 inference failed: {e}") from e

        message = AIMessage(content=response_text)
        return ChatResult(generations=[ChatGeneration(message=message)])
