"""Query API endpoint - user-facing retrieval interface."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.retrieval.models import StructuredContext
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str = Field(description="User's question or search query")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    context: StructuredContext = Field(description="Packaged evidence for LLM")


def get_retrieval_service() -> RetrievalService:
    """Dependency to get the retrieval service from app state.

    Raises:
        HTTPException: If service not initialized.
    """
    from app.main import app

    if not hasattr(app.state, "retrieval_service"):
        raise HTTPException(
            status_code=503,
            detail="Retrieval service not initialized",
        )
    return app.state.retrieval_service


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    service: RetrievalService = Depends(get_retrieval_service),
) -> QueryResponse:
    """Query the knowledge base for relevant evidence.

    This endpoint:
    1. Retrieves evidence via neo4j-graphrag retrievers
    2. Packages evidence into LLM-consumable format
    3. Returns structured context with evidence IDs for tracing

    **Phase 3:** Will be extended to call Node 1 for LLM generation.
    **Phase 4:** Will add claim verification before returning.
    """
    context = service.retrieve_and_package(query=request.query)
    return QueryResponse(context=context)
