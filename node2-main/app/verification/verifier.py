from __future__ import annotations

import asyncio
import logging
import time

from app.config import settings
from app.verification.graph_verifier import GraphVerifier
from app.verification.models import Claim, VerificationOutcome, VerificationResult
from app.verification.semantic_verifier import SemanticVerifier

logger = logging.getLogger(__name__)


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
        start = time.monotonic()

        # 1. Batch Graph Verification (Fast, single round-trip)
        graph_start = time.monotonic()
        graph_results = await self._graph.verify_batch(claims)
        graph_duration = time.monotonic() - graph_start

        # 2. Identify claims needing semantic verification
        # We'll fill this list with results as we get them
        final_results: list[VerificationResult | None] = [None] * len(claims)
        semantic_tasks = []
        semantic_indices = []

        # Pre-compute evidence embeddings ONLY if needed, ONCE for all claims
        needs_semantic = any(
            r.outcome
            not in {VerificationOutcome.SUPPORTED, VerificationOutcome.CONTRADICTED}
            for r in graph_results
        )

        evidence_embeddings = None
        if needs_semantic and evidence_texts:
            evidence_embeddings = await self._semantic.precompute_evidence_embeddings(
                evidence_texts
            )

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
                    self._verify_semantic_with_timeout(
                        claim, evidence_texts, g_result, evidence_embeddings
                    )
                )

        # 3. Run semantic verifications concurrently
        semantic_duration = 0.0
        if semantic_tasks:
            sem_start = time.monotonic()
            semantic_outcomes = await asyncio.gather(*semantic_tasks)
            semantic_duration = time.monotonic() - sem_start

            for i, result in zip(semantic_indices, semantic_outcomes):
                final_results[i] = result

        total_duration = time.monotonic() - start
        logger.info(
            "Total verification time: %.3fs "
            "(Graph: %.3fs, Semantic: %.3fs, Claims: %d, Sem-Claims: %d)",
            total_duration,
            graph_duration,
            semantic_duration,
            len(claims),
            len(semantic_tasks),
        )

        # The list is guaranteed to be fully populated now
        return final_results  # type: ignore

    async def _verify_semantic_with_timeout(
        self,
        claim: Claim,
        evidence_texts: list[str],
        graph_result: VerificationResult,
        evidence_embeddings: list[any] | None = None,
    ) -> VerificationResult:
        """Run semantic verification with timeout, falling back to graph result."""
        timeout = settings.inference_timeout
        try:
            return await asyncio.wait_for(
                self._verify_semantic_logic(
                    claim, evidence_texts, graph_result, evidence_embeddings
                ),
                timeout=timeout,
            )
        except TimeoutError:
            logger.warning("Verification timed out for claim %s", claim.claim_id)
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.AMBIGUOUS,
                confidence=0.0,
                reason=f"Verification timed out after {timeout}s",
            )

    async def _verify_semantic_logic(
        self,
        claim: Claim,
        evidence_texts: list[str],
        graph_result: VerificationResult,
        evidence_embeddings: list[any] | None = None,
    ) -> VerificationResult:
        """Fallback logic: try semantic, else return graph result."""
        if evidence_texts:
            semantic_result = await self._semantic.verify(
                claim, evidence_texts, precomputed_embeddings=evidence_embeddings
            )

            # Semantic can upgrade UNSUPPORTED to SUPPORTED/AMBIGUOUS
            if semantic_result.outcome != VerificationOutcome.UNSUPPORTED:
                return semantic_result

        return graph_result
