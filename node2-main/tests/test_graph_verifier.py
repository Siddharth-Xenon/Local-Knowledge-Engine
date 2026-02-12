"""Tests for GraphVerifier — mocked Neo4j driver."""

from unittest.mock import MagicMock, patch

import pytest

from app.verification.graph_verifier import GraphVerifier
from app.verification.models import Claim, VerificationOutcome


def _make_claim(subject: str, predicate: str, obj: str) -> Claim:
    return Claim(subject=subject, predicate=predicate, object=obj)


class TestGraphVerifier:
    @pytest.fixture
    def mock_driver(self):
        return MagicMock()

    @pytest.fixture
    def verifier(self, mock_driver):
        return GraphVerifier(driver=mock_driver)

    def _mock_query_results(self, verifier, forward=None, reverse=None):
        """Mock _run_query to return different results for forward/reverse."""
        forward = forward or []
        reverse = reverse or []
        call_count = 0

        def side_effect(query, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return forward
            return reverse

        verifier._run_query = MagicMock(side_effect=side_effect)

    async def test_supported_when_edge_matches(self, verifier):
        self._mock_query_results(
            verifier,
            forward=[
                {
                    "rel_type": "OWNS_ACCOUNT",
                    "source": "Customer_001",
                    "target": "ACC_001",
                }
            ],
        )
        claim = _make_claim("Customer_001", "OWNS_ACCOUNT", "ACC_001")
        result = await verifier.verify(claim)

        assert result.outcome == VerificationOutcome.SUPPORTED
        assert result.confidence > 0.9

    async def test_unsupported_when_no_edges(self, verifier):
        self._mock_query_results(verifier, forward=[], reverse=[])
        claim = _make_claim("Customer_001", "OWNS_ACCOUNT", "NONEXISTENT")
        result = await verifier.verify(claim)

        assert result.outcome == VerificationOutcome.UNSUPPORTED
        assert result.confidence == 0.0

    async def test_ambiguous_when_edge_type_mismatch(self, verifier):
        self._mock_query_results(
            verifier,
            forward=[
                {"rel_type": "HAS_LOAN", "source": "Customer_001", "target": "ACC_001"}
            ],
        )
        claim = _make_claim("Customer_001", "OWNS_ACCOUNT", "ACC_001")
        result = await verifier.verify(claim)

        assert result.outcome == VerificationOutcome.AMBIGUOUS

    async def test_contradicted_when_reverse_direction(self, verifier):
        self._mock_query_results(
            verifier,
            forward=[],
            reverse=[
                {
                    "rel_type": "OWNS_ACCOUNT",
                    "source": "ACC_001",
                    "target": "Customer_001",
                }
            ],
        )
        claim = _make_claim("Customer_001", "OWNS_ACCOUNT", "ACC_001")
        result = await verifier.verify(claim)

        assert result.outcome == VerificationOutcome.CONTRADICTED
        assert result.confidence > 0.5

    async def test_handles_driver_errors(self, verifier):
        verifier._run_query = MagicMock(side_effect=Exception("Connection lost"))
        claim = _make_claim("s", "p", "o")
        result = await verifier.verify(claim)

        assert result.outcome == VerificationOutcome.UNSUPPORTED
        assert "error" in result.reason.lower()


class TestPredicateMatching:
    def test_exact_match(self):
        assert GraphVerifier._predicate_matches("OWNS_ACCOUNT", "OWNS_ACCOUNT")

    def test_case_insensitive(self):
        assert GraphVerifier._predicate_matches("owns_account", "OWNS_ACCOUNT")

    def test_space_to_underscore(self):
        assert GraphVerifier._predicate_matches("owns account", "OWNS_ACCOUNT")

    def test_partial_match(self):
        assert GraphVerifier._predicate_matches("owns", "OWNS_ACCOUNT")

    def test_no_match(self):
        assert not GraphVerifier._predicate_matches("deletes", "OWNS_ACCOUNT")
