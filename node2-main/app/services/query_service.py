"""Query service — high-level wrapper around the LangGraph pipeline.

Provides a clean interface for the API layer to invoke the pipeline.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.verification.models import VerifiedResponse

logger = logging.getLogger(__name__)

PIPELINE_TIMEOUT = 18000.0


class QueryService:
    """Service wrapping the LangGraph verification pipeline.

    Provides error handling, timeout, and response construction.
    """

    def __init__(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    async def query(self, text: str) -> VerifiedResponse:
        """Run a query through the full verification pipeline.

        Args:
            text: User's question.

        Returns:
            VerifiedResponse with verified answer or abstention.
        """
        initial_state = {
            "query": text,
            "regeneration_count": 0,
            "per_claim_retries": {},
            "failed_claims": [],
            "evidence_nodes": [],
            "claims": [],
            "verification_results": [],
            "abstained": False,
            "audit_trail": {},
        }

        try:
            result = await asyncio.wait_for(
                self._pipeline.ainvoke(initial_state),
                timeout=PIPELINE_TIMEOUT,
            )

            return VerifiedResponse(
                final_answer=result.get("final_answer") or "",
                claims_with_results=result.get("verification_results", []),
                abstained=result.get("abstained", False),
                abstention_reason=result.get("audit_trail", {}).get(
                    "abstention_reason", ""
                ),
                audit_summary=result.get("audit_trail", {}),
            )

        except TimeoutError:
            logger.error(
                "Pipeline timed out after %ss for query: %s", PIPELINE_TIMEOUT, text
            )
            return VerifiedResponse(
                abstained=True,
                abstention_reason=f"Pipeline timed out after {PIPELINE_TIMEOUT}s",
                audit_summary={"status": "timeout", "query": text},
            )

        except Exception as e:
            logger.error("Pipeline error: %s", e, exc_info=True)
            return VerifiedResponse(
                abstained=True,
                abstention_reason=f"Pipeline error: {e}",
                audit_summary={"status": "error", "error": str(e)},
            )
