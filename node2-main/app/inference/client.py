"""Inference client for Node 2 to call Node 1."""

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.core import InferenceTimeoutError, InferenceUnavailableError


class GenerateRequest(BaseModel):
    """Request to the inference server."""

    prompt: str = Field(..., min_length=1)
    model: str = Field(default="deepseek-r1:8b-llama-distill-q4_K_M")


class GenerateResponse(BaseModel):
    """Response from the inference server."""

    response: str
    model: str
    done: bool = True


class InferenceClient:
    """
    Client for communicating with Node 1 inference server.

    Features:
    - Configurable timeout (default 60s)
    - Single retry on timeout
    - Proper error propagation
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.base_url = base_url or settings.node1_url
        self.timeout = timeout or settings.inference_timeout

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        retry: bool = True,
    ) -> str:
        """
        Generate text using Node 1 inference server.

        Args:
            prompt: The text prompt to generate from
            model: Optional model override
            retry: Whether to retry on timeout (default True)

        Returns:
            Generated text response
        """
        request = GenerateRequest(
            prompt=prompt,
            model=model or "deepseek-r1:8b-llama-distill-q4_K_M",
        )

        try:
            return await self._make_request(request)
        except InferenceTimeoutError:
            if retry:
                # Single retry on timeout
                return await self._make_request(request)
            raise

    async def _make_request(self, request: GenerateRequest) -> str:
        """Make the actual HTTP request to Node 1."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=request.model_dump(),
                )
                response.raise_for_status()
                data = GenerateResponse.model_validate(response.json())
                return data.response

        except httpx.TimeoutException as e:
            raise InferenceTimeoutError(
                f"Inference timed out after {self.timeout}s",
                {"prompt_preview": request.prompt[:100]},
            ) from e
        except httpx.RequestError as e:
            raise InferenceUnavailableError(
                f"Node 1 unavailable: {e}",
                {"url": self.base_url},
            ) from e

    async def health_check(self) -> bool:
        """Check if Node 1 is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.RequestError:
            return False


# Default client instance
inference_client = InferenceClient()
