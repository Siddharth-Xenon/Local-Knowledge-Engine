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

CLAIM_TIMEOUT_SECONDS = 2.0


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

        Each claim is verified with a per-claim timeout.
        """
        tasks = [self._verify_single(claim, evidence_texts) for claim in claims]
        return await asyncio.gather(*tasks)

    async def _verify_single(
        self,
        claim: Claim,
        evidence_texts: list[str],
    ) -> VerificationResult:
        """Verify a single claim with timeout."""
        try:
            return await asyncio.wait_for(
                self._verify_with_fallback(claim, evidence_texts),
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

    async def _verify_with_fallback(
        self,
        claim: Claim,
        evidence_texts: list[str],
    ) -> VerificationResult:
        """Graph first, semantic fallback."""
        graph_result = await self._graph.verify(claim)

        # If graph is definitive (SUPPORTED or CONTRADICTED), trust it
        if graph_result.outcome in {
            VerificationOutcome.SUPPORTED,
            VerificationOutcome.CONTRADICTED,
        }:
            return graph_result

        # Graph inconclusive — try semantic
        if evidence_texts:
            semantic_result = await self._semantic.verify(claim, evidence_texts)

            # Semantic can upgrade UNSUPPORTED to SUPPORTED/AMBIGUOUS
            if semantic_result.outcome != VerificationOutcome.UNSUPPORTED:
                return semantic_result

        return graph_result
