"""Query API endpoint — user-facing verified query interface."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.retrieval.models import StructuredContext
from app.services.query_service import QueryService
from app.services.retrieval_service import RetrievalService
from app.services.text_highlighter import TextHighlighter
from app.verification.models import VerifiedResponse

router = APIRouter(prefix="/query", tags=["query"])

# Instantiate highlighter
highlighter = TextHighlighter()


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str = Field(description="User's question or search query")
    mode: str = Field(
        default="pipeline",
        description="Query mode: 'pipeline' (verified) or 'retrieval' (raw context)",
    )


class RetrievalResponse(BaseModel):
    """Response for retrieval-only mode (backward compat)."""

    context: StructuredContext = Field(description="Packaged evidence for LLM")


class PipelineResponse(BaseModel):
    """Response for pipeline mode (verified answer)."""

    answer: str = Field(default="", description="Verified answer text")
    abstained: bool = Field(default=False, description="Whether the system refused")
    abstention_reason: str = Field(default="", description="Why it refused")
    claims: list[dict] = Field(
        default_factory=list, description="Claims with verification results"
    )
    audit: dict = Field(default_factory=dict, description="Audit trail")


def get_retrieval_service() -> RetrievalService:
    """Dependency to get the retrieval service from app state."""
    from app.main import app

    if not hasattr(app.state, "retrieval_service"):
        raise HTTPException(
            status_code=503,
            detail="Retrieval service not initialized",
        )
    return app.state.retrieval_service


def get_query_service() -> QueryService:
    """Dependency to get the query service from app state."""
    from app.main import app

    if not hasattr(app.state, "query_service"):
        raise HTTPException(
            status_code=503,
            detail="Query service not initialized — pipeline not ready",
        )
    return app.state.query_service


@router.post("", response_model=PipelineResponse | RetrievalResponse)
async def query(
    request: QueryRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    query_service: QueryService = Depends(get_query_service),
) -> PipelineResponse | RetrievalResponse:
    """Query the knowledge base.

    Modes:
    - **pipeline** (default): Full verified pipeline — retrieve, generate,
      extract claims, verify, and return verified answer or abstention.
    - **retrieval**: Raw context retrieval only (backward compatible).
    """
    if request.mode == "retrieval":
        context = retrieval_service.retrieve_and_package(query=request.query)
        return RetrievalResponse(context=context)

    result: VerifiedResponse = await query_service.query(request.query)

    claims_dicts = []
    for vr in result.claims_with_results:
        claims_dicts.append(
            {
                "claim_id": vr.claim.claim_id,
                "subject": vr.claim.subject,
                "predicate": vr.claim.predicate,
                "object": vr.claim.object_,
                "outcome": vr.outcome.value,
                "confidence": vr.confidence,
                "reason": vr.reason,
            }
        )

    # Augment with highlights
    claims_dicts = highlighter.align_claims(result.final_answer, claims_dicts)

    return PipelineResponse(
        answer=result.final_answer,
        abstained=result.abstained,
        abstention_reason=result.abstention_reason,
        claims=claims_dicts,
        audit=result.audit_summary,
    )
