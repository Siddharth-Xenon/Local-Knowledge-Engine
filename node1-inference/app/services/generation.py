"""Generation Service for Node 1."""

import logging
from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import Node1Error


logger = logging.getLogger("node1.inference")


class GenerationService:
    """Service for handling LLM generation logic."""

    def __init__(self) -> None:
        pass

    async def generate(
        self,
        prompt: str,
        model: str,
    ) -> dict[str, Any]:
        """
        Orchestrate generation:
        1. Audit log
        2. Call Ollama
        """
        if not prompt:
            raise Node1Error("Missing prompt")

        # 1. Audit Logging
        logger.info(
            "AUDIT: INFERENCE | model=%s | len=%d",
            model,
            len(prompt),
        )

        # 2. Call Ollama
        # Use settings.default_model if none provided
        target_model = model or settings.default_model

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": target_model,
                        "prompt": prompt,
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
