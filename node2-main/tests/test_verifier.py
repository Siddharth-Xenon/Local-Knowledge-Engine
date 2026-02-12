"""Tests for multi-layer Verifier."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.verification.models import Claim, VerificationOutcome, VerificationResult
from app.verification.verifier import Verifier


def _make_claim(subject="s", predicate="p", obj="o"):
    return Claim(subject=subject, predicate=predicate, object=obj)


def _make_result(claim, outcome, confidence=0.9, reason=""):
    return VerificationResult(
        claim=claim,
        outcome=outcome,
        confidence=confidence,
        reason=reason,
    )


class TestVerifier:
    @pytest.fixture
    def graph_verifier(self):
        return AsyncMock()

    @pytest.fixture
    def semantic_verifier(self):
        return AsyncMock()

    @pytest.fixture
    def verifier(self, graph_verifier, semantic_verifier):
        return Verifier(
            graph_verifier=graph_verifier,
            semantic_verifier=semantic_verifier,
        )

    async def test_graph_supported_short_circuits(
        self, verifier, graph_verifier, semantic_verifier
    ):
        """Graph SUPPORTED → skip semantic, return result."""
        claim = _make_claim()
        graph_verifier.verify.return_value = _make_result(
            claim, VerificationOutcome.SUPPORTED
        )

        results = await verifier.verify_claims([claim], ["evidence"])
        assert len(results) == 1
        assert results[0].outcome == VerificationOutcome.SUPPORTED
        semantic_verifier.verify.assert_not_called()

    async def test_graph_contradicted_short_circuits(
        self, verifier, graph_verifier, semantic_verifier
    ):
        """Graph CONTRADICTED → skip semantic, return result."""
        claim = _make_claim()
        graph_verifier.verify.return_value = _make_result(
            claim, VerificationOutcome.CONTRADICTED
        )

        results = await verifier.verify_claims([claim], ["evidence"])
        assert results[0].outcome == VerificationOutcome.CONTRADICTED
        semantic_verifier.verify.assert_not_called()

    async def test_graph_unsupported_falls_back_to_semantic(
        self, verifier, graph_verifier, semantic_verifier
    ):
        """Graph UNSUPPORTED → semantic fallback."""
        claim = _make_claim()
        graph_verifier.verify.return_value = _make_result(
            claim,
            VerificationOutcome.UNSUPPORTED,
            confidence=0.0,
        )
        semantic_verifier.verify.return_value = _make_result(
            claim,
            VerificationOutcome.SUPPORTED,
            confidence=0.85,
        )

        results = await verifier.verify_claims([claim], ["evidence text"])
        assert results[0].outcome == VerificationOutcome.SUPPORTED
        semantic_verifier.verify.assert_called_once()

    async def test_both_unsupported(self, verifier, graph_verifier, semantic_verifier):
        """Both graph and semantic UNSUPPORTED → return graph result."""
        claim = _make_claim()
        graph_verifier.verify.return_value = _make_result(
            claim,
            VerificationOutcome.UNSUPPORTED,
            confidence=0.0,
        )
        semantic_verifier.verify.return_value = _make_result(
            claim,
            VerificationOutcome.UNSUPPORTED,
            confidence=0.2,
        )

        results = await verifier.verify_claims([claim], ["evidence"])
        assert results[0].outcome == VerificationOutcome.UNSUPPORTED

    async def test_multiple_claims_parallel(self, verifier, graph_verifier):
        """Multiple claims verified concurrently."""
        claims = [_make_claim(f"s{i}") for i in range(3)]
        graph_verifier.verify.return_value = _make_result(
            claims[0],
            VerificationOutcome.SUPPORTED,
        )

        results = await verifier.verify_claims(claims, [])
        assert len(results) == 3

    async def test_no_evidence_skips_semantic(
        self, verifier, graph_verifier, semantic_verifier
    ):
        """No evidence texts → skip semantic, use graph result."""
        claim = _make_claim()
        graph_verifier.verify.return_value = _make_result(
            claim,
            VerificationOutcome.UNSUPPORTED,
            confidence=0.0,
        )

        results = await verifier.verify_claims([claim], [])
        assert results[0].outcome == VerificationOutcome.UNSUPPORTED
        semantic_verifier.verify.assert_not_called()
