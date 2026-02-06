from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.exceptions import Node1Error
from app.services.generation import GenerationService

# Initialize Dependencies
_generation_service = GenerationService()


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

    prompt: str = Field(..., min_length=1)
    model: str = Field(default="deepseek-r1:8b-llama-distill-q4_K_M")
    stream: bool = Field(default=False)


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
