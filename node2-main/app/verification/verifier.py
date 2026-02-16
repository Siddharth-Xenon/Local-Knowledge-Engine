"""Multi-layer verifier — orchestrates graph + semantic verification.

Runs graph verification first (high confidence); falls back to semantic
verification for claims the graph cannot resolve.
"""

from __future__ import annotations

import asyncio
import logging

from app.verification.graph_verifier import GraphVerifier
from app.verification.models import Claim, VerificationOutcome, VerificationResult
from app.verification.semantic_verifier import SemanticVerifier

logger = logging.getLogger(__name__)

CLAIM_TIMEOUT_SECONDS = 10.0


class Verifier:
    """Multi-layer claim verifier.

    Strategy: graph check first (structural, high confidence).
    If graph returns UNSUPPORTED, fallback to semantic similarity.
    If graph returns SUPPORTED/CONTRADICTED, trust that result.
    """

    def __init__(
        self,
        graph_verifier: GraphVerifier,
        semantic_verifier: SemanticVerifier,
    ) -> None:
        self._graph = graph_verifier
        self._semantic = semantic_verifier

    async def verify_claims(
        self,
        claims: list[Claim],
        evidence_texts: list[str],
    ) -> list[VerificationResult]:
        """Verify all claims using multi-layer strategy.

        Optimized with batch graph verification.
        """
        # 1. Batch Graph Verification (Fast, single round-trip)
        graph_results = await self._graph.verify_batch(claims)

        # 2. Identify claims needing semantic verification
        # We'll fill this list with results as we get them
        final_results: list[VerificationResult | None] = [None] * len(claims)
        semantic_tasks = []
        semantic_indices = []

        for i, (claim, g_result) in enumerate(zip(claims, graph_results)):
            # If graph is definitive, we're done with this claim
            if g_result.outcome in {
                VerificationOutcome.SUPPORTED,
                VerificationOutcome.CONTRADICTED,
            }:
                final_results[i] = g_result
            else:
                # Graph inconclusive; queue for semantic verification
                semantic_indices.append(i)
                semantic_tasks.append(
                    self._verify_semantic_with_timeout(claim, evidence_texts, g_result)
                )

        # 3. Run semantic verifications concurrently
        if semantic_tasks:
            semantic_outcomes = await asyncio.gather(*semantic_tasks)
            for i, result in zip(semantic_indices, semantic_outcomes):
                final_results[i] = result

        # The list is guaranteed to be fully populated now
        return final_results  # type: ignore

    async def _verify_semantic_with_timeout(
        self,
        claim: Claim,
        evidence_texts: list[str],
        graph_result: VerificationResult,
    ) -> VerificationResult:
        """Run semantic verification with timeout, falling back to graph result."""
        try:
            return await asyncio.wait_for(
                self._verify_semantic_logic(claim, evidence_texts, graph_result),
                timeout=CLAIM_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            logger.warning("Verification timed out for claim %s", claim.claim_id)
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.AMBIGUOUS,
                confidence=0.0,
                reason=f"Verification timed out after {CLAIM_TIMEOUT_SECONDS}s",
            )

    async def _verify_semantic_logic(
        self,
        claim: Claim,
        evidence_texts: list[str],
        graph_result: VerificationResult,
    ) -> VerificationResult:
        """Fallback logic: try semantic, else return graph result."""
        if evidence_texts:
            semantic_result = await self._semantic.verify(claim, evidence_texts)

            # Semantic can upgrade UNSUPPORTED to SUPPORTED/AMBIGUOUS
            if semantic_result.outcome != VerificationOutcome.UNSUPPORTED:
                return semantic_result

        return graph_result
