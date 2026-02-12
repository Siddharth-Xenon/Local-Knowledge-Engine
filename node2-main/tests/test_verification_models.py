"""Tests for verification domain models."""

from app.verification.models import (
    Claim,
    ClaimList,
    PolicyDecision,
    VerificationOutcome,
    VerificationResult,
    VerifiedResponse,
)


class TestClaim:
    def test_create_with_required_fields(self):
        claim = Claim(
            subject="contract", predicate="allows", object="early termination"
        )
        assert claim.subject == "contract"
        assert claim.predicate == "allows"
        assert claim.object_ == "early termination"

    def test_auto_generates_claim_id(self):
        claim = Claim(subject="s", predicate="p", object="o")
        assert claim.claim_id.startswith("C")
        assert len(claim.claim_id) > 1

    def test_unique_claim_ids(self):
        c1 = Claim(subject="s", predicate="p", object="o")
        c2 = Claim(subject="s", predicate="p", object="o")
        assert c1.claim_id != c2.claim_id

    def test_defaults(self):
        claim = Claim(subject="s", predicate="p", object="o")
        assert claim.qualifiers == {}
        assert claim.evidence_refs == []
        assert claim.source_statement == ""

    def test_with_all_fields(self):
        claim = Claim(
            subject="lending_limit",
            predicate="equals",
            object="$500,000",
            qualifiers={"scope": "SME loans"},
            evidence_refs=["E1", "E3"],
            source_statement="The lending limit is $500K [E1].",
        )
        assert claim.evidence_refs == ["E1", "E3"]
        assert claim.qualifiers["scope"] == "SME loans"

    def test_json_serialization_uses_alias(self):
        claim = Claim(subject="s", predicate="p", object="o")
        data = claim.model_dump(by_alias=True)
        assert "object" in data
        assert "object_" not in data

    def test_from_dict_with_alias(self):
        claim = Claim.model_validate({"subject": "s", "predicate": "p", "object": "o"})
        assert claim.object_ == "o"


class TestClaimList:
    def test_empty(self):
        cl = ClaimList()
        assert cl.claims == []

    def test_with_claims(self):
        c1 = Claim(subject="a", predicate="b", object="c")
        cl = ClaimList(claims=[c1])
        assert len(cl.claims) == 1


class TestVerificationOutcome:
    def test_values(self):
        assert VerificationOutcome.SUPPORTED.value == "supported"
        assert VerificationOutcome.CONTRADICTED.value == "contradicted"
        assert VerificationOutcome.UNSUPPORTED.value == "unsupported"
        assert VerificationOutcome.AMBIGUOUS.value == "ambiguous"

    def test_all_outcomes_present(self):
        assert len(VerificationOutcome) == 4


class TestVerificationResult:
    def test_create(self):
        claim = Claim(subject="s", predicate="p", object="o")
        result = VerificationResult(
            claim=claim,
            outcome=VerificationOutcome.SUPPORTED,
            confidence=0.95,
            evidence_used=["E1"],
            reason="Edge exists in graph",
        )
        assert result.outcome == VerificationOutcome.SUPPORTED
        assert result.confidence == 0.95

    def test_defaults(self):
        claim = Claim(subject="s", predicate="p", object="o")
        result = VerificationResult(
            claim=claim, outcome=VerificationOutcome.UNSUPPORTED
        )
        assert result.confidence == 0.0
        assert result.evidence_used == []
        assert result.reason == ""


class TestPolicyDecision:
    def test_values(self):
        assert PolicyDecision.SERVE.value == "serve"
        assert PolicyDecision.REGENERATE.value == "regenerate"
        assert PolicyDecision.BLOCK.value == "block"
        assert PolicyDecision.ADD_UNCERTAINTY.value == "add_uncertainty"

    def test_all_decisions_present(self):
        assert len(PolicyDecision) == 4


class TestVerifiedResponse:
    def test_default_not_abstained(self):
        resp = VerifiedResponse(final_answer="The limit is $500K.")
        assert not resp.abstained
        assert resp.abstention_reason == ""

    def test_abstained(self):
        resp = VerifiedResponse(
            abstained=True,
            abstention_reason="Contradicted claims detected",
        )
        assert resp.abstained
        assert resp.final_answer == ""

    def test_with_claims(self):
        claim = Claim(subject="s", predicate="p", object="o")
        result = VerificationResult(claim=claim, outcome=VerificationOutcome.SUPPORTED)
        resp = VerifiedResponse(final_answer="Answer", claims_with_results=[result])
        assert len(resp.claims_with_results) == 1

    def test_json_round_trip(self):
        claim = Claim(subject="s", predicate="p", object="o")
        result = VerificationResult(
            claim=claim,
            outcome=VerificationOutcome.SUPPORTED,
            confidence=0.9,
        )
        resp = VerifiedResponse(
            final_answer="test",
            claims_with_results=[result],
            audit_summary={"regen_count": 0},
        )
        data = resp.model_dump()
        restored = VerifiedResponse.model_validate(data)
        assert restored.final_answer == "test"
        assert restored.audit_summary["regen_count"] == 0
