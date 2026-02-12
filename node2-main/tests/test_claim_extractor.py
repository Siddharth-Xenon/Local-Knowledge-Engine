"""Tests for ClaimExtractor — LLM and regex fallback."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.verification.claim_extractor import ClaimExtractor
from app.verification.models import Claim


class TestRegexFallback:
    """Test the regex-based claim extraction fallback."""

    def setup_method(self):
        mock_llm = MagicMock()
        self.extractor = ClaimExtractor(llm=mock_llm)

    def test_single_sentence(self):
        text = "The lending limit is $500K [E1]."
        claims = self.extractor._extract_with_regex(text, ["E1"])
        assert len(claims) == 1
        assert claims[0].evidence_refs == ["E1"]
        assert "[E1]" not in claims[0].object_

    def test_multiple_sentences(self):
        text = (
            "The lending limit is $500K [E1]. Termination requires 90 days notice [E2]."
        )
        claims = self.extractor._extract_with_regex(text, ["E1", "E2"])
        assert len(claims) == 2
        assert claims[0].evidence_refs == ["E1"]
        assert claims[1].evidence_refs == ["E2"]

    def test_no_evidence_refs(self):
        text = "The contract was signed in 2024."
        claims = self.extractor._extract_with_regex(text, [])
        assert len(claims) == 1
        assert claims[0].evidence_refs == []

    def test_multiple_refs_in_one_sentence(self):
        text = "The limit applies to SME loans [E1] and corporate bonds [E3]."
        claims = self.extractor._extract_with_regex(text, ["E1", "E3"])
        assert len(claims) == 1
        assert set(claims[0].evidence_refs) == {"E1", "E3"}

    def test_skips_short_fragments(self):
        text = "Yes. The limit is $500K [E1]."
        claims = self.extractor._extract_with_regex(text, ["E1"])
        # "Yes." is too short (<10 chars), should be skipped
        assert len(claims) == 1

    def test_preserves_source_statement(self):
        text = "The lending limit is $500K [E1]."
        claims = self.extractor._extract_with_regex(text, ["E1"])
        assert claims[0].source_statement == "The lending limit is $500K [E1]."

    def test_empty_text(self):
        claims = self.extractor._extract_with_regex("", [])
        assert claims == []


class TestJsonParsing:
    """Test JSON response parsing from LLM output."""

    def test_parse_direct_json(self):
        text = json.dumps(
            {
                "claims": [
                    {
                        "subject": "limit",
                        "predicate": "is",
                        "object": "$500K",
                        "evidence_refs": ["E1"],
                    }
                ]
            }
        )
        result = ClaimExtractor._parse_json_response(text)
        assert len(result) == 1
        assert result[0]["subject"] == "limit"

    def test_parse_json_in_markdown_fence(self):
        text = '```json\n{"claims": [{"subject": "s", "predicate": "p", "object": "o"}]}\n```'
        result = ClaimExtractor._parse_json_response(text)
        assert len(result) == 1

    def test_parse_json_array(self):
        text = '[{"subject": "s", "predicate": "p", "object": "o"}]'
        result = ClaimExtractor._parse_json_response(text)
        assert len(result) == 1

    def test_parse_invalid_json(self):
        result = ClaimExtractor._parse_json_response("not json at all")
        assert result == []


class TestExtractAsync:
    """Test the full async extract pipeline."""

    @pytest.fixture
    def mock_llm(self):
        llm = AsyncMock()
        return llm

    async def test_falls_back_to_regex_on_llm_error(self, mock_llm):
        mock_llm.ainvoke.side_effect = Exception("LLM unavailable")
        extractor = ClaimExtractor(llm=mock_llm)

        claims = await extractor.extract(
            "The lending limit is $500K [E1].",
            evidence_ids=["E1"],
        )
        assert len(claims) >= 1
        assert claims[0].evidence_refs == ["E1"]

    async def test_uses_llm_when_available(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = json.dumps(
            {
                "claims": [
                    {
                        "subject": "lending_limit",
                        "predicate": "equals",
                        "object": "$500K",
                        "evidence_refs": ["E1"],
                        "source_statement": "The lending limit is $500K.",
                    }
                ]
            }
        )
        mock_llm.ainvoke.return_value = mock_response
        extractor = ClaimExtractor(llm=mock_llm)

        claims = await extractor.extract("The lending limit is $500K [E1].")
        assert len(claims) == 1
        assert claims[0].subject == "lending_limit"
        mock_llm.ainvoke.assert_called_once()

    async def test_falls_back_when_llm_returns_empty(self, mock_llm):
        mock_response = MagicMock()
        mock_response.content = '{"claims": []}'
        mock_llm.ainvoke.return_value = mock_response
        extractor = ClaimExtractor(llm=mock_llm)

        claims = await extractor.extract(
            "The lending limit is $500K [E1].",
            evidence_ids=["E1"],
        )
        # Should fall back to regex
        assert len(claims) >= 1
