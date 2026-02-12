"""Tests for SemanticVerifier — mocked embedder."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from app.verification.models import Claim, VerificationOutcome
from app.verification.semantic_verifier import (
    AMBIGUOUS_THRESHOLD,
    SUPPORTED_THRESHOLD,
    SemanticVerifier,
)


def _make_claim(text: str = "test claim") -> Claim:
    return Claim(subject=text, predicate="states", object=text)


def _make_embedder(claim_vec, evidence_vecs):
    """Create a mock embedder returning specific vectors."""
    embedder = MagicMock()
    call_count = 0

    def embed_side_effect(text):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return claim_vec
        idx = call_count - 2
        if idx < len(evidence_vecs):
            return evidence_vecs[idx]
        return claim_vec

    embedder.embed_query.side_effect = embed_side_effect
    return embedder


class TestSemanticVerifier:
    async def test_supported_high_similarity(self):
        vec = [1.0, 0.0, 0.0]
        embedder = _make_embedder(vec, [vec])  # identical = 1.0
        verifier = SemanticVerifier(embedder=embedder)

        result = await verifier.verify(_make_claim(), ["evidence text"])
        assert result.outcome == VerificationOutcome.SUPPORTED
        assert result.confidence >= SUPPORTED_THRESHOLD

    async def test_unsupported_low_similarity(self):
        claim_vec = [1.0, 0.0, 0.0]
        evidence_vec = [0.0, 1.0, 0.0]  # orthogonal = 0.0
        embedder = _make_embedder(claim_vec, [evidence_vec])
        verifier = SemanticVerifier(embedder=embedder)

        result = await verifier.verify(_make_claim(), ["unrelated evidence"])
        assert result.outcome == VerificationOutcome.UNSUPPORTED

    async def test_ambiguous_medium_similarity(self):
        claim_vec = [1.0, 0.0, 0.0]
        # Vector giving ~0.7 similarity
        evidence_vec = [0.7, 0.71, 0.0]
        embedder = _make_embedder(claim_vec, [evidence_vec])
        verifier = SemanticVerifier(embedder=embedder)

        result = await verifier.verify(_make_claim(), ["partly related"])
        sim = result.confidence
        assert AMBIGUOUS_THRESHOLD <= sim < SUPPORTED_THRESHOLD
        assert result.outcome == VerificationOutcome.AMBIGUOUS

    async def test_no_evidence(self):
        embedder = MagicMock()
        verifier = SemanticVerifier(embedder=embedder)

        result = await verifier.verify(_make_claim(), [])
        assert result.outcome == VerificationOutcome.UNSUPPORTED
        assert "No evidence" in result.reason

    async def test_best_match_among_multiple(self):
        claim_vec = [1.0, 0.0, 0.0]
        vecs = [
            [0.0, 1.0, 0.0],  # low similarity
            [1.0, 0.0, 0.0],  # perfect match
            [0.0, 0.0, 1.0],  # low similarity
        ]
        embedder = _make_embedder(claim_vec, vecs)
        verifier = SemanticVerifier(embedder=embedder)

        result = await verifier.verify(_make_claim(), ["a", "b", "c"])
        assert result.outcome == VerificationOutcome.SUPPORTED
        assert "semantic:1" in result.evidence_used[0]

    async def test_handles_embedder_error(self):
        embedder = MagicMock()
        embedder.embed_query.side_effect = RuntimeError("GPU OOM")
        verifier = SemanticVerifier(embedder=embedder)

        result = await verifier.verify(_make_claim(), ["evidence"])
        assert result.outcome == VerificationOutcome.UNSUPPORTED
        assert "error" in result.reason.lower()


class TestCosinesimilarity:
    def test_identical_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        assert SemanticVerifier._cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        assert SemanticVerifier._cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector(self):
        a = np.array([1.0, 0.0])
        z = np.array([0.0, 0.0])
        assert SemanticVerifier._cosine_similarity(a, z) == 0.0
