"""Domain models for the verification subsystem.

Defines the core data structures used throughout the verification pipeline:
claims, outcomes, results, and the final verified response.
"""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field


def _coerce_to_str(v: Any) -> str:
    """Coerce non-string values (int, float, bool) from LLM output to str."""
    return str(v) if not isinstance(v, str) else v


class Claim(BaseModel):
    """An atomic factual assertion extracted from an LLM response.

    Each claim is independently verifiable against the knowledge graph.
    Follows GOAL.md §10.2.1 — subject/predicate/object structure.
    """

    claim_id: str = Field(default_factory=lambda: f"C{uuid.uuid4().hex[:6]}")
    subject: str = Field(description="Entity or concept the claim is about")
    predicate: str = Field(description="Relationship or action asserted")
    object_: Annotated[str, BeforeValidator(_coerce_to_str)] = Field(
        description="Target entity, value, or condition",
        alias="object",
    )
    qualifiers: dict[str, str] = Field(
        default_factory=dict,
        description="Optional context: time, conditions, scope",
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence IDs cited for this claim, e.g. ['E1', 'E3']",
    )
    source_statement: str = Field(
        default="",
        description="Original sentence from which this claim was extracted",
    )

    model_config = {"populate_by_name": True}


class AnswerStatement(BaseModel):
    """A single factual statement from the LLM's structured response."""

    statement: str
    evidence_ids: list[str] = Field(default_factory=list)


class UncertaintyNote(BaseModel):
    """An uncertainty flagged by the LLM about its answer."""

    statement: str
    reason: str = ""


class GeneratedAnswer(BaseModel):
    """Structured LLM response — parsed from JSON, rendered to clean text.

    Matches the JSON schema requested by GROUNDED_GENERATION_PROMPT.
    """

    answer: list[AnswerStatement] = Field(default_factory=list)
    uncertainties: list[UncertaintyNote] = Field(default_factory=list)

    def to_text(self) -> str:
        """Assemble a clean, human-readable answer from structured parts."""
        if not self.answer:
            return ""

        result = " ".join(s.statement for s in self.answer)

        if self.uncertainties:
            notes = []
            for u in self.uncertainties:
                note = f"- {u.statement}"
                if u.reason:
                    note += f" ({u.reason})"
                notes.append(note)
            if notes:
                result += "\n\n⚠️ **Uncertainties:**\n" + "\n".join(notes)

        return result


class ClaimList(BaseModel):
    """Container for structured output from the claim extractor."""

    claims: list[Claim] = Field(default_factory=list)


class VerificationOutcome(StrEnum):
    """Possible outcomes of verifying a single claim.

    Per GOAL.md §11.2 — only SUPPORTED passes silently.
    """

    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"


class VerificationResult(BaseModel):
    """Result of verifying a single claim against evidence."""

    claim: Claim
    outcome: VerificationOutcome
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Verification confidence 0–1"
    )
    evidence_used: list[str] = Field(
        default_factory=list,
        description="Evidence IDs actually checked during verification",
    )
    reason: str = Field(
        default="", description="Human-readable explanation of the outcome"
    )


class PolicyDecision(StrEnum):
    """Action decided by the verification policy.

    Per GOAL.md §11.4 — policy-driven, not model-driven.
    """

    SERVE = "serve"
    REGENERATE = "regenerate"
    BLOCK = "block"
    ADD_UNCERTAINTY = "add_uncertainty"


class VerifiedResponse(BaseModel):
    """Final pipeline output — a verified, auditable answer."""

    final_answer: str = Field(default="", description="The verified answer text")
    claims_with_results: list[VerificationResult] = Field(
        default_factory=list,
        description="All claims and their verification outcomes",
    )
    abstained: bool = Field(
        default=False, description="True if the system refused to answer"
    )
    abstention_reason: str = Field(default="", description="Why the system abstained")
    audit_summary: dict = Field(
        default_factory=dict,
        description="Audit trail: retrieval stats, regen count, timings",
    )
