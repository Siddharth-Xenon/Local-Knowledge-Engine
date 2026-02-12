"""LangGraph pipeline node functions.

Each node takes PipelineState and returns a partial state dict.
LangGraph merges the returned dict into the full state.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.pipeline.prompts import (
    ANTI_PATTERN_PHRASES,
    GROUNDED_GENERATION_PROMPT,
    REGENERATION_PROMPT,
)
from app.pipeline.state import PipelineState
from app.verification.models import (
    VerificationOutcome,
    VerifiedResponse,
)
from app.verification.policy import VerificationPolicy

logger = logging.getLogger(__name__)

# Max total regeneration passes
MAX_REGENERATIONS = 3
# Max retries per individual claim
MAX_PER_CLAIM_RETRIES = 2


class PipelineNodes:
    """Container for all pipeline node functions.

    Dependencies are injected at construction time so each node
    is a simple method call.
    """

    def __init__(
        self,
        retrieval_service: Any,
        llm: Any,
        claim_extractor: Any,
        verifier: Any,
        policy: VerificationPolicy | None = None,
    ) -> None:
        self._retrieval = retrieval_service
        self._llm = llm
        self._extractor = claim_extractor
        self._verifier = verifier
        self._policy = policy or VerificationPolicy()

    async def retrieve(self, state: PipelineState) -> dict:
        """Retrieve evidence from the knowledge graph."""
        start = time.monotonic()
        query = state["query"]

        context = await self._retrieval.aretrieve_and_package(query)

        elapsed = time.monotonic() - start
        logger.info(
            "Retrieved %d evidence items in %.2fs", len(context.evidence_ids), elapsed
        )

        return {
            "evidence_nodes": [
                {"id": eid, "content": ""} for eid in context.evidence_ids
            ],
            "structured_context": context.formatted,
            "evidence_ids": context.evidence_ids,
            "audit_trail": {
                **state.get("audit_trail", {}),
                "retrieval_time": round(elapsed, 3),
                "evidence_count": len(context.evidence_ids),
            },
        }

    async def generate(self, state: PipelineState) -> dict:
        """Generate an answer using the LLM with grounded prompt."""
        start = time.monotonic()

        prompt = GROUNDED_GENERATION_PROMPT.format(
            context=state.get("structured_context", ""),
            query=state["query"],
        )

        # If regenerating, use the regeneration prompt instead
        failed_claims = state.get("failed_claims", [])
        if failed_claims:
            failed_text = "\n".join(
                f"- {c.subject} {c.predicate} {c.object_}" for c in failed_claims
            )
            failure_reasons = "\n".join(
                f"- {r.reason}"
                for r in state.get("verification_results", [])
                if r.outcome != VerificationOutcome.SUPPORTED
            )
            prompt = REGENERATION_PROMPT.format(
                failed_claims=failed_text,
                failure_reasons=failure_reasons,
                context=state.get("structured_context", ""),
                query=state["query"],
            )

        response = await self._llm.ainvoke(prompt)
        raw = response.content if hasattr(response, "content") else str(response)

        # Check for anti-patterns
        raw_lower = raw.lower()
        anti_patterns_found = [
            phrase for phrase in ANTI_PATTERN_PHRASES if phrase in raw_lower
        ]
        if anti_patterns_found:
            logger.warning("Anti-patterns detected: %s", anti_patterns_found)

        elapsed = time.monotonic() - start
        logger.info("Generated response in %.2fs (%d chars)", elapsed, len(raw))

        return {
            "raw_response": raw,
            "audit_trail": {
                **state.get("audit_trail", {}),
                "generation_time": round(elapsed, 3),
                "anti_patterns": anti_patterns_found,
            },
        }

    async def extract_claims(self, state: PipelineState) -> dict:
        """Extract atomic claims from the generated response."""
        start = time.monotonic()

        claims = await self._extractor.extract(
            state.get("raw_response", ""),
            evidence_ids=state.get("evidence_ids", []),
        )

        elapsed = time.monotonic() - start
        logger.info("Extracted %d claims in %.2fs", len(claims), elapsed)

        return {
            "claims": claims,
            "audit_trail": {
                **state.get("audit_trail", {}),
                "claim_count": len(claims),
                "extraction_time": round(elapsed, 3),
            },
        }

    async def verify(self, state: PipelineState) -> dict:
        """Verify all extracted claims."""
        start = time.monotonic()

        claims = state.get("claims", [])
        context = state.get("structured_context", "")
        evidence_texts = [line for line in context.split("\n") if line.strip()]

        results = await self._verifier.verify_claims(claims, evidence_texts)

        elapsed = time.monotonic() - start
        outcomes = [r.outcome.value for r in results]
        logger.info("Verified %d claims in %.2fs: %s", len(results), elapsed, outcomes)

        return {
            "verification_results": results,
            "audit_trail": {
                **state.get("audit_trail", {}),
                "verification_time": round(elapsed, 3),
                "outcomes": outcomes,
            },
        }

    def decide(self, state: PipelineState) -> str:
        """Run verification policy and return routing decision."""
        results = state.get("verification_results", [])
        regen_count = state.get("regeneration_count", 0)
        retries_remaining = regen_count < MAX_REGENERATIONS

        decision = self._policy.decide(results, retries_remaining=retries_remaining)
        logger.info(
            "Policy decision: %s (regen=%d/%d)",
            decision.value,
            regen_count,
            MAX_REGENERATIONS,
        )

        return decision.value

    async def regenerate(self, state: PipelineState) -> dict:
        """Prepare state for regeneration — increment counter, collect failed claims."""
        results = state.get("verification_results", [])
        per_claim = dict(state.get("per_claim_retries", {}))
        regen_count = state.get("regeneration_count", 0) + 1

        failed = []
        for r in results:
            if r.outcome != VerificationOutcome.SUPPORTED:
                cid = r.claim.claim_id
                current_retries = per_claim.get(cid, 0)
                if current_retries < MAX_PER_CLAIM_RETRIES:
                    per_claim[cid] = current_retries + 1
                    failed.append(r.claim)

        logger.info(
            "Regenerating: %d failed claims, pass %d/%d",
            len(failed),
            regen_count,
            MAX_REGENERATIONS,
        )

        return {
            "regeneration_count": regen_count,
            "per_claim_retries": per_claim,
            "failed_claims": failed,
        }

    async def add_uncertainty(self, state: PipelineState) -> dict:
        """Annotate ambiguous claims with uncertainty markers."""
        raw = state.get("raw_response", "")
        results = state.get("verification_results", [])

        ambiguous = [r for r in results if r.outcome == VerificationOutcome.AMBIGUOUS]

        if ambiguous:
            uncertainty_note = (
                "\n\n⚠️ **Note:** The following aspects have limited evidence:\n"
            )
            for r in ambiguous:
                uncertainty_note += (
                    f"- {r.claim.source_statement or r.claim.subject}: {r.reason}\n"
                )
            raw += uncertainty_note

        return {"raw_response": raw}

    async def create_response(self, state: PipelineState) -> dict:
        """Build the final verified response."""
        response = VerifiedResponse(
            final_answer=state.get("raw_response", ""),
            claims_with_results=state.get("verification_results", []),
            abstained=False,
            audit_summary=state.get("audit_trail", {}),
        )

        return {
            "final_answer": response.final_answer,
            "abstained": False,
            "audit_trail": {
                **state.get("audit_trail", {}),
                "regeneration_count": state.get("regeneration_count", 0),
                "status": "served",
            },
        }

    async def abstain(self, state: PipelineState) -> dict:
        """Build an abstention response."""
        results = state.get("verification_results", [])

        contradicted = [
            r for r in results if r.outcome == VerificationOutcome.CONTRADICTED
        ]

        reason = "Unable to provide a verified answer."
        if contradicted:
            reason = (
                "Evidence contradicts some claims. Cannot provide a reliable answer."
            )

        return {
            "final_answer": None,
            "abstained": True,
            "audit_trail": {
                **state.get("audit_trail", {}),
                "regeneration_count": state.get("regeneration_count", 0),
                "status": "abstained",
                "abstention_reason": reason,
            },
        }
