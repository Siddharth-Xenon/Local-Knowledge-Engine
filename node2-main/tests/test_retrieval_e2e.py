"""Tests for RetrievalService with library retrievers."""

import pytest
from unittest.mock import MagicMock

from app.retrieval.models import EvidenceSet, StructuredContext
from app.services.retrieval_service import RetrievalService


class MockRetrieverResultItem:
    """Mock for neo4j_graphrag RetrieverResultItem."""

    def __init__(self, content: str, metadata: dict | None = None):
        self.content = content
        self.metadata = metadata or {}


class MockRetrieverResult:
    """Mock for neo4j_graphrag RetrieverResult."""

    def __init__(self, items: list[MockRetrieverResultItem]):
        self.items = items


def _make_mock_retriever(items: list[MockRetrieverResultItem]):
    """Create a mock retriever with predictable results."""
    mock = MagicMock()
    mock.search.return_value = MockRetrieverResult(items=items)
    return mock


class TestRetrievalService:
    def test_retrieve_converts_to_evidence_set(self):
        items = [
            MockRetrieverResultItem(
                content="High-value transaction rule",
                metadata={"node_id": "rule_1", "node_type": "Rule", "score": 0.95},
            ),
            MockRetrieverResultItem(
                content="AML Policy v2",
                metadata={"node_id": "policy_1", "node_type": "Policy", "score": 0.87},
            ),
        ]
        retriever = _make_mock_retriever(items)
        service = RetrievalService(retriever=retriever)

        result = service.retrieve("fraud detection")

        assert isinstance(result, EvidenceSet)
        assert len(result.nodes) == 2
        assert result.nodes[0].node_id == "rule_1"
        assert result.nodes[0].content == "High-value transaction rule"
        assert result.nodes[1].node_id == "policy_1"

    def test_retrieve_and_package_returns_structured_context(self):
        items = [
            MockRetrieverResultItem(
                content="Test content",
                metadata={"node_id": "n1", "node_type": "Rule", "score": 0.9},
            ),
        ]
        retriever = _make_mock_retriever(items)
        service = RetrievalService(retriever=retriever)

        result = service.retrieve_and_package("test query")

        assert isinstance(result, StructuredContext)
        assert "E1:" in result.formatted
        assert "Test content" in result.formatted
        assert len(result.evidence_ids) == 1

    def test_empty_results(self):
        retriever = _make_mock_retriever([])
        service = RetrievalService(retriever=retriever)

        result = service.retrieve("empty query")

        assert isinstance(result, EvidenceSet)
        assert len(result.nodes) == 0

    def test_items_without_metadata(self):
        items = [
            MockRetrieverResultItem(content="Some content"),
        ]
        retriever = _make_mock_retriever(items)
        service = RetrievalService(retriever=retriever)

        result = service.retrieve("query")

        assert result.nodes[0].node_id == "n0"
        assert result.nodes[0].node_type == "Unknown"
        assert result.nodes[0].content == "Some content"
