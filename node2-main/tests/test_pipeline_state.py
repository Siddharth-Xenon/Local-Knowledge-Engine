"""Tests for pipeline state and prompts."""

from app.pipeline.prompts import (
    ANTI_PATTERN_PHRASES,
    CLAIM_EXTRACTION_PROMPT,
    GROUNDED_GENERATION_PROMPT,
    REGENERATION_PROMPT,
)
from app.pipeline.state import PipelineState


class TestPipelineState:
    def test_create_minimal(self):
        state: PipelineState = {"query": "test question"}
        assert state["query"] == "test question"

    def test_create_with_defaults(self):
        state: PipelineState = {
            "query": "test",
            "regeneration_count": 0,
            "abstained": False,
            "evidence_nodes": [],
            "claims": [],
            "verification_results": [],
            "failed_claims": [],
            "per_claim_retries": {},
            "audit_trail": {},
        }
        assert state["regeneration_count"] == 0
        assert state["abstained"] is False

    def test_partial_update(self):
        state: PipelineState = {"query": "test"}
        update: PipelineState = {"raw_response": "some answer"}
        merged = {**state, **update}
        assert merged["query"] == "test"
        assert merged["raw_response"] == "some answer"


class TestGroundedGenerationPrompt:
    def test_contains_grounding_instructions(self):
        prompt_lower = GROUNDED_GENERATION_PROMPT.lower()
        assert "provided context" in prompt_lower
        assert "evidence" in prompt_lower

    def test_contains_citation_instruction(self):
        assert "[E1]" in GROUNDED_GENERATION_PROMPT

    def test_contains_uncertainty_instruction(self):
        prompt_lower = GROUNDED_GENERATION_PROMPT.lower()
        assert "uncertainty" in prompt_lower or "cannot answer" in prompt_lower

    def test_has_placeholders(self):
        assert "{context}" in GROUNDED_GENERATION_PROMPT
        assert "{query}" in GROUNDED_GENERATION_PROMPT

    def test_json_structure_specified(self):
        assert '"answer"' in GROUNDED_GENERATION_PROMPT
        assert '"uncertainties"' in GROUNDED_GENERATION_PROMPT


class TestClaimExtractionPrompt:
    def test_contains_spo_structure(self):
        prompt_lower = CLAIM_EXTRACTION_PROMPT.lower()
        assert "subject" in prompt_lower
        assert "predicate" in prompt_lower
        assert "object" in prompt_lower

    def test_has_placeholder(self):
        assert "{answer_text}" in CLAIM_EXTRACTION_PROMPT

    def test_requests_evidence_refs(self):
        assert "evidence_refs" in CLAIM_EXTRACTION_PROMPT


class TestRegenerationPrompt:
    def test_has_required_placeholders(self):
        assert "{failed_claims}" in REGENERATION_PROMPT
        assert "{failure_reasons}" in REGENERATION_PROMPT
        assert "{context}" in REGENERATION_PROMPT
        assert "{query}" in REGENERATION_PROMPT


class TestAntiPatternPhrases:
    def test_not_empty(self):
        assert len(ANTI_PATTERN_PHRASES) > 0

    def test_all_lowercase(self):
        for phrase in ANTI_PATTERN_PHRASES:
            assert phrase == phrase.lower(), f"'{phrase}' should be lowercase"

    def test_known_patterns_present(self):
        assert "based on my knowledge" in ANTI_PATTERN_PHRASES
        assert "it is likely that" in ANTI_PATTERN_PHRASES
