"""LangGraph pipeline state definition.

Holds all data flowing through the verification pipeline as a TypedDict.
Each node reads/writes specific keys; LangGraph merges partial updates.
"""

from __future__ import annotations

from typing import TypedDict

from app.verification.models import Claim, VerificationResult


class PipelineState(TypedDict, total=False):
    """State flowing through the LangGraph verification pipeline.

    All fields are optional (total=False) so nodes can return partial updates.
    """

    # ── Input ──
    query: str

    # ── Retrieval ──
    evidence_nodes: list[dict]
    structured_context: str
    evidence_ids: list[str]

    # ── Generation ──
    raw_response: str

    # ── Claims ──
    claims: list[Claim]

    # ── Verification ──
    verification_results: list[VerificationResult]

    # ── Control ──
    regeneration_count: int
    per_claim_retries: dict[str, int]
    failed_claims: list[Claim]

    # ── Output ──
    final_answer: str | None
    abstained: bool
    audit_trail: dict
