"""Generation Service for Node 1."""

import logging
from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import Node1Error
from app.prompts.engine import JinjaPromptEngine

logger = logging.getLogger("node1.inference")


class GenerationService:
    """Service for handling LLM generation logic."""

    def __init__(self, prompt_engine: JinjaPromptEngine) -> None:
        self.prompt_engine = prompt_engine

    async def generate(
        self,
        prompt: str | None,
        prompt_key: str | None,
        version: str | None,
        variables: dict[str, Any] | None,
        model: str,
    ) -> dict[str, Any]:
        """
        Orchestrate generation:
        1. Resolve prompt (raw vs managed)
        2. Audit log
        3. Call Ollama
        """
        final_prompt = prompt

        # 1. Resolve Prompt via Engine
        if prompt_key:
            try:
                final_prompt = self.prompt_engine.render(
                    prompt_key=prompt_key,
                    version=version or "1.0.0",
                    variables=variables or {},
                )
                # 2. Audit Logging
                logger.info(
                    "AUDIT: PROMPT RENDERED | key=%s | ver=%s | model=%s | len=%d",
                    prompt_key,
                    version,
                    model,
                    len(final_prompt),
                )
            except Exception as e:
                # Re-raise as domain error or let it bubble up if it's already specific
                raise Node1Error(f"Prompt render failed: {str(e)}")

        if not final_prompt:
            raise Node1Error("Missing source: provide 'prompt' or 'prompt_key'")

        # 3. Call Ollama
        # Use settings.default_model if none provided, but here we expect 'model' arg
        target_model = model or settings.default_model

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": target_model,
                        "prompt": final_prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "response": data.get("response", ""),
                    "model": target_model,
                    "done": data.get("done", True),
                }

        except httpx.TimeoutException:
            raise Node1Error("Ollama request timed out")
        except httpx.RequestError as e:
            raise Node1Error(f"Ollama unavailable: {e}")
