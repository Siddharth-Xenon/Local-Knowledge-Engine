"""Tests for LangGraph pipeline graph compilation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.pipeline.graph import build_pipeline
from app.pipeline.nodes import PipelineNodes
from app.verification.policy import VerificationPolicy


class TestBuildPipeline:
    @pytest.fixture
    def mock_nodes(self):
        return PipelineNodes(
            retrieval_service=MagicMock(),
            llm=AsyncMock(),
            claim_extractor=MagicMock(),
            verifier=MagicMock(),
            policy=VerificationPolicy(),
        )

    def test_compiles_successfully(self, mock_nodes):
        graph = build_pipeline(mock_nodes)
        assert graph is not None

    def test_graph_has_expected_nodes(self, mock_nodes):
        graph = build_pipeline(mock_nodes)
        mermaid = graph.get_graph().draw_mermaid()

        expected_nodes = [
            "retrieve",
            "generate",
            "extract_claims",
            "verify",
            "regenerate",
            "add_uncertainty",
            "create_response",
            "abstain",
        ]
        for node in expected_nodes:
            assert node in mermaid, (
                f"Expected node '{node}' not found in mermaid diagram"
            )

    def test_graph_has_entry_point(self, mock_nodes):
        graph = build_pipeline(mock_nodes)
        mermaid = graph.get_graph().draw_mermaid()
        # START should connect to retrieve
        assert "retrieve" in mermaid

    def test_graph_has_end_nodes(self, mock_nodes):
        graph = build_pipeline(mock_nodes)
        mermaid = graph.get_graph().draw_mermaid()
        assert "__end__" in mermaid
