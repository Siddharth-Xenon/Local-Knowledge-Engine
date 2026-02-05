from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import Node1Error
from app.prompts.engine import JinjaPromptEngine
from app.services.generation import GenerationService

# Initialize Dependencies (Singleton-ish for now)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "prompts" / "templates"
# We could use a proper dependency injection provider here
_prompt_engine = JinjaPromptEngine(TEMPLATES_DIR)
_generation_service = GenerationService(_prompt_engine)


def get_generation_service() -> GenerationService:
    return _generation_service


router = APIRouter()


class GenerateResponse(BaseModel):
    """Response schema from /generate endpoint."""

    response: str
    model: str
    done: bool = True


class GenerateRequest(BaseModel):
    """Request schema for /generate endpoint."""

    # Classic raw prompt mode
    prompt: str | None = Field(default=None)

    # Prompt Engine mode
    prompt_key: str | None = Field(default=None)
    version: str | None = Field(default="1.0.0")
    variables: dict[str, Any] | None = Field(default=None)

    model: str = Field(default="deepseek-r1:8b-llama-distill-q4_K_M")
    stream: bool = Field(default=False)

    @field_validator("prompt")
    def validate_prompt_source(cls, v: str | None, info: Any) -> str | None:
        """Ensure either raw prompt OR prompt_key is provided."""
        return v


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    service: GenerationService = Depends(get_generation_service),
) -> GenerateResponse:
    """
    Generate text using Ollama.
    """
    try:
        result = await service.generate(
            prompt=request.prompt,
            prompt_key=request.prompt_key,
            version=request.version,
            variables=request.variables,
            model=request.model,
        )
        return GenerateResponse(**result)

    except Node1Error as e:
        # Map domain errors to HTTP errors
        if "timed out" in str(e):
            raise HTTPException(status_code=504, detail=str(e))
        if "unavailable" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
