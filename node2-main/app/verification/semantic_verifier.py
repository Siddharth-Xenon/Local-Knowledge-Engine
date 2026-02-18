from __future__ import annotations

import asyncio
import logging
import time
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

    async def precompute_evidence_embeddings(
        self,
        evidence_texts: list[str],
    ) -> list[np.ndarray]:
        """Pre-compute embeddings for a list of evidence texts."""
        if not evidence_texts:
            return []

        start = time.monotonic()
        embeddings = await asyncio.to_thread(self._batch_embed, evidence_texts)
        duration = time.monotonic() - start
        logger.debug(
            "Precomputed %d evidence embeddings in %.3fs",
            len(evidence_texts),
            duration,
        )
        return embeddings

    def _batch_embed(self, texts: list[str]) -> list[np.ndarray]:
        """Embed a list of texts one by one (since embedder is single-text)."""
        return [
            np.array(self._embedder.embed_query(t), dtype=np.float32) for t in texts
        ]

    async def verify(
        self,
        claim: Claim,
        evidence_texts: list[str],
        precomputed_embeddings: list[np.ndarray] | None = None,
    ) -> VerificationResult:
        """Verify a claim against evidence texts using semantic similarity.

        Args:
            claim: The claim to verify.
            evidence_texts: The raw text of evidence chunks.
            precomputed_embeddings: Optional cached embeddings for evidence_texts.
        """
        if not evidence_texts:
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.UNSUPPORTED,
                confidence=0.0,
                reason="No evidence texts provided",
            )

        start = time.monotonic()
        try:
            claim_text = f"{claim.subject} {claim.predicate} {claim.object_}"

            # Compute embeddings if not provided
            if precomputed_embeddings is None:
                max_sim, best_idx = await asyncio.to_thread(
                    self._compute_max_similarity, claim_text, evidence_texts
                )
            else:
                max_sim, best_idx = await asyncio.to_thread(
                    self._compute_with_precomputed, claim_text, precomputed_embeddings
                )

            outcome, confidence = self._classify(max_sim)

            duration = time.monotonic() - start
            logger.info(
                "Semantic verification for claim %s took %.3fs (score=%.3f)",
                claim.claim_id,
                duration,
                max_sim,
            )

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
        """Compute max cosine similarity (legacy: computes evidence embeddings)."""
        evidence_embeddings = self._batch_embed(evidence_texts)
        return self._compute_with_precomputed(claim_text, evidence_embeddings)

    def _compute_with_precomputed(
        self,
        claim_text: str,
        evidence_embeddings: list[np.ndarray],
    ) -> tuple[float, int]:
        """Compute max cosine similarity using precomputed evidence embeddings."""
        claim_embedding = np.array(
            self._embedder.embed_query(claim_text), dtype=np.float32
        )

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
