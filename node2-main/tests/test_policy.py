"""Tests for VerificationPolicy."""

from app.verification.models import (
    Claim,
    PolicyDecision,
    VerificationOutcome,
    VerificationResult,
)
from app.verification.policy import VerificationPolicy


def _make_result(outcome, subject="s"):
    claim = Claim(subject=subject, predicate="p", object="o")
    return VerificationResult(claim=claim, outcome=outcome)


class TestVerificationPolicy:
    def setup_method(self):
        self.policy = VerificationPolicy()

    def test_all_supported_serves(self):
        results = [_make_result(VerificationOutcome.SUPPORTED) for _ in range(3)]
        assert self.policy.decide(results) == PolicyDecision.SERVE

    def test_any_contradicted_blocks(self):
        results = [
            _make_result(VerificationOutcome.SUPPORTED),
            _make_result(VerificationOutcome.CONTRADICTED),
        ]
        assert self.policy.decide(results) == PolicyDecision.BLOCK

    def test_unsupported_with_retries_regenerates(self):
        results = [
            _make_result(VerificationOutcome.SUPPORTED),
            _make_result(VerificationOutcome.UNSUPPORTED),
        ]
        assert (
            self.policy.decide(results, retries_remaining=True)
            == PolicyDecision.REGENERATE
        )

    def test_unsupported_no_retries_blocks(self):
        results = [
            _make_result(VerificationOutcome.SUPPORTED),
            _make_result(VerificationOutcome.UNSUPPORTED),
        ]
        assert (
            self.policy.decide(results, retries_remaining=False) == PolicyDecision.BLOCK
        )

    def test_ambiguous_adds_uncertainty(self):
        results = [
            _make_result(VerificationOutcome.SUPPORTED),
            _make_result(VerificationOutcome.AMBIGUOUS),
        ]
        assert self.policy.decide(results) == PolicyDecision.ADD_UNCERTAINTY

    def test_all_ambiguous_adds_uncertainty(self):
        results = [_make_result(VerificationOutcome.AMBIGUOUS) for _ in range(2)]
        assert self.policy.decide(results) == PolicyDecision.ADD_UNCERTAINTY

    def test_empty_results_blocks(self):
        assert self.policy.decide([]) == PolicyDecision.BLOCK

    def test_contradicted_wins_over_unsupported(self):
        results = [
            _make_result(VerificationOutcome.UNSUPPORTED),
            _make_result(VerificationOutcome.CONTRADICTED),
        ]
        assert self.policy.decide(results) == PolicyDecision.BLOCK
