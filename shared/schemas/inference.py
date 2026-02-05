"""Shared inference schemas for Node 1 and Node 2 communication."""

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request schema for /generate endpoint."""

    prompt: str = Field(..., min_length=1, description="The prompt to generate from")
    model: str = Field(
        default="deepseek-r1:8b-llama-distill-q4_K_M",
        description="Model name to use for generation",
    )
    stream: bool = Field(default=False, description="Whether to stream the response")


class GenerateResponse(BaseModel):
    """Response schema from /generate endpoint."""

    response: str = Field(..., description="Generated text response")
    model: str = Field(..., description="Model used for generation")
    done: bool = Field(default=True, description="Whether generation is complete")


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    model: str | None = Field(default=None, description="Active model name")
    ollama: str | None = Field(default=None, description="Ollama connection status")
