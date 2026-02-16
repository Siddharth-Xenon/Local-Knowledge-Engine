"""Semantic verifier — verifies claims via embedding similarity.

Layer 2 verification (GOAL.md §11.3): cosine similarity between
claim text and evidence documents.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import numpy as np

from app.verification.models import Claim, VerificationOutcome, VerificationResult

if TYPE_CHECKING:
    from neo4j_graphrag.embeddings import Embedder

logger = logging.getLogger(__name__)

# Thresholds (conservative per GOAL.md)
SUPPORTED_THRESHOLD = 0.7
AMBIGUOUS_THRESHOLD = 0.69999


class SemanticVerifier:
    """Verifies claims via embedding cosine similarity against evidence.

    Conservative thresholds ensure only highly similar evidence = SUPPORTED.
    """

    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder

    async def verify(
        self,
        claim: Claim,
        evidence_texts: list[str],
    ) -> VerificationResult:
        """Verify a claim against evidence texts using semantic similarity."""
        if not evidence_texts:
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.UNSUPPORTED,
                confidence=0.0,
                reason="No evidence texts provided",
            )

        try:
            claim_text = f"{claim.subject} {claim.predicate} {claim.object_}"
            max_sim, best_idx = await asyncio.to_thread(
                self._compute_max_similarity, claim_text, evidence_texts
            )

            outcome, confidence = self._classify(max_sim)

            return VerificationResult(
                claim=claim,
                outcome=outcome,
                confidence=confidence,
                evidence_used=([f"semantic:{best_idx}"] if best_idx >= 0 else []),
                reason=f"Max cosine similarity: {max_sim:.3f}",
            )

        except Exception as e:
            logger.warning(
                "Semantic verification failed for %s: %s",
                claim.claim_id,
                e,
            )
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.UNSUPPORTED,
                confidence=0.0,
                reason=f"Semantic verification error: {e}",
            )

    def _compute_max_similarity(
        self,
        claim_text: str,
        evidence_texts: list[str],
    ) -> tuple[float, int]:
        """Compute max cosine similarity between claim and evidence."""
        claim_embedding = np.array(
            self._embedder.embed_query(claim_text), dtype=np.float32
        )
        evidence_embeddings = [
            np.array(self._embedder.embed_query(text), dtype=np.float32)
            for text in evidence_texts
        ]

        max_sim = -1.0
        best_idx = -1

        for i, ev_emb in enumerate(evidence_embeddings):
            sim = self._cosine_similarity(claim_embedding, ev_emb)
            if sim > max_sim:
                max_sim = sim
                best_idx = i

        return float(max_sim), best_idx

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def _classify(
        similarity: float,
    ) -> tuple[VerificationOutcome, float]:
        """Classify similarity score into verification outcome."""
        if similarity >= SUPPORTED_THRESHOLD:
            return VerificationOutcome.SUPPORTED, similarity
        if similarity >= AMBIGUOUS_THRESHOLD:
            return VerificationOutcome.AMBIGUOUS, similarity
        return VerificationOutcome.UNSUPPORTED, similarity
