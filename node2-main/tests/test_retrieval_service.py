"""Unit tests for RetrievalService using real neo4j-graphrag types.

No mocks for data objects — uses real RetrieverResultItem/RetrieverResult
to ensure tests catch edge cases like metadata=None.
"""

from unittest.mock import MagicMock

import pytest
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem

from app.retrieval.models import EvidenceSet, StructuredContext
from app.services.retrieval_service import RetrievalService


def _make_service(items: list[RetrieverResultItem]) -> RetrievalService:
    """Create a RetrievalService with a mock retriever returning real types."""
    mock_retriever = MagicMock()
    mock_retriever.search.return_value = RetrieverResult(items=items)
    return RetrievalService(retriever=mock_retriever)


class TestToEvidenceSet:
    """Tests for _to_evidence_set conversion logic."""

    def test_full_metadata(self):
        items = [
            RetrieverResultItem(
                content="High-value transaction rule",
                metadata={"node_id": "rule_1", "node_type": "Rule", "score": 0.95},
            ),
            RetrieverResultItem(
                content="AML Policy v2",
                metadata={"node_id": "policy_1", "node_type": "Policy", "score": 0.87},
            ),
        ]
        service = _make_service(items)
        result = service.retrieve("fraud detection")

        assert isinstance(result, EvidenceSet)
        assert len(result.nodes) == 2
        assert result.nodes[0].node_id == "rule_1"
        assert result.nodes[0].content == "High-value transaction rule"
        assert result.nodes[0].node_type == "Rule"
        assert result.nodes[0].score == 0.95
        assert result.nodes[1].node_id == "policy_1"

    def test_none_metadata(self):
        """The exact scenario that caused the production crash.

        neo4j-graphrag sets metadata=None when the record has no metadata key.
        This must not raise AttributeError.
        """
        items = [
            RetrieverResultItem(content="Some content", metadata=None),
        ]
        service = _make_service(items)
        result = service.retrieve("query")

        assert result.nodes[0].node_id == "n0"
        assert result.nodes[0].node_type == "Unknown"
        assert result.nodes[0].score == 0.0
        assert result.nodes[0].content == "Some content"

    def test_missing_metadata_field(self):
        """RetrieverResultItem defaults metadata to None when omitted."""
        items = [
            RetrieverResultItem(content="Bare content"),
        ]
        service = _make_service(items)
        result = service.retrieve("query")

        assert result.nodes[0].node_id == "n0"
        assert result.nodes[0].node_type == "Unknown"
        assert result.nodes[0].content == "Bare content"

    def test_partial_metadata(self):
        """Metadata dict present but missing some expected keys."""
        items = [
            RetrieverResultItem(
                content="Partial",
                metadata={"node_id": "p1"},
            ),
        ]
        service = _make_service(items)
        result = service.retrieve("query")

        assert result.nodes[0].node_id == "p1"
        assert result.nodes[0].node_type == "Unknown"
        assert result.nodes[0].score == 0.0

    def test_empty_results(self):
        service = _make_service([])
        result = service.retrieve("empty query")

        assert isinstance(result, EvidenceSet)
        assert len(result.nodes) == 0
        assert result.semantic_count == 0


class TestRetrievalPipeline:
    """Tests for the full retrieve + package pipeline."""

    def test_retrieve_and_package(self):
        items = [
            RetrieverResultItem(
                content="Test content",
                metadata={"node_id": "n1", "node_type": "Rule", "score": 0.9},
            ),
        ]
        service = _make_service(items)
        result = service.retrieve_and_package("test query")

        assert isinstance(result, StructuredContext)
        assert "E1:" in result.formatted
        assert "Test content" in result.formatted
        assert len(result.evidence_ids) == 1

    @pytest.mark.asyncio
    async def test_aretrieve(self):
        items = [
            RetrieverResultItem(
                content="Async content",
                metadata={"node_id": "a1", "node_type": "Policy", "score": 0.8},
            ),
        ]
        service = _make_service(items)
        result = await service.aretrieve("async query")

        assert isinstance(result, EvidenceSet)
        assert result.nodes[0].node_id == "a1"
        assert result.nodes[0].content == "Async content"

    @pytest.mark.asyncio
    async def test_aretrieve_and_package(self):
        items = [
            RetrieverResultItem(
                content="Async packaged",
                metadata={"node_id": "ap1", "node_type": "Entity", "score": 0.75},
            ),
        ]
        service = _make_service(items)
        result = await service.aretrieve_and_package("async query")

        assert isinstance(result, StructuredContext)
        assert "Async packaged" in result.formatted
