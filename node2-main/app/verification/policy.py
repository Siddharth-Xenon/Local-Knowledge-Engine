"""Verification policy — decides what to do with verification results.

Policy-driven, not model-driven (GOAL.md §11.4).
"""

from __future__ import annotations

from app.verification.models import (
    PolicyDecision,
    VerificationOutcome,
    VerificationResult,
)


class VerificationPolicy:
    """Decides the pipeline action based on verification results.

    Rules (per GOAL.md §11.4):
    - All SUPPORTED → SERVE
    - Any CONTRADICTED → BLOCK
    - UNSUPPORTED with retries remaining → REGENERATE
    - AMBIGUOUS only → ADD_UNCERTAINTY
    """

    def decide(
        self,
        results: list[VerificationResult],
        retries_remaining: bool = True,
    ) -> PolicyDecision:
        """Determine pipeline action from verification results."""
        if not results:
            return PolicyDecision.BLOCK

        outcomes = {r.outcome for r in results}

        # Any contradiction → hard block
        if VerificationOutcome.CONTRADICTED in outcomes:
            return PolicyDecision.BLOCK

        # All supported → serve immediately
        if outcomes == {VerificationOutcome.SUPPORTED}:
            return PolicyDecision.SERVE

        # Unsupported claims exist → regenerate if retries remain
        if VerificationOutcome.UNSUPPORTED in outcomes:
            if retries_remaining:
                return PolicyDecision.REGENERATE
            return PolicyDecision.BLOCK

        # Only SUPPORTED + AMBIGUOUS → flag uncertainty
        if outcomes <= {VerificationOutcome.SUPPORTED, VerificationOutcome.AMBIGUOUS}:
            return PolicyDecision.ADD_UNCERTAINTY

        # Fallback: if retries remain, try again; otherwise block
        if retries_remaining:
            return PolicyDecision.REGENERATE
        return PolicyDecision.BLOCK
