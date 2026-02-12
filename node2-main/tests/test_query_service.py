"""Tests for QueryService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.query_service import QueryService
from app.verification.models import (
    Claim,
    VerificationOutcome,
    VerificationResult,
    VerifiedResponse,
)


class TestQueryService:
    @pytest.fixture
    def mock_pipeline(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_pipeline):
        return QueryService(pipeline=mock_pipeline)

    async def test_successful_query(self, service, mock_pipeline):
        mock_pipeline.ainvoke.return_value = {
            "final_answer": "The limit is $500K.",
            "verification_results": [],
            "abstained": False,
            "audit_trail": {"status": "served"},
        }

        result = await service.query("What is the lending limit?")
        assert isinstance(result, VerifiedResponse)
        assert result.final_answer == "The limit is $500K."
        assert not result.abstained

    async def test_abstained_query(self, service, mock_pipeline):
        mock_pipeline.ainvoke.return_value = {
            "final_answer": None,
            "verification_results": [],
            "abstained": True,
            "audit_trail": {
                "status": "abstained",
                "abstention_reason": "Contradicted claims",
            },
        }

        result = await service.query("Bad question")
        assert result.abstained
        assert "Contradicted" in result.abstention_reason

    async def test_pipeline_error_returns_abstention(self, service, mock_pipeline):
        mock_pipeline.ainvoke.side_effect = RuntimeError("Pipeline exploded")

        result = await service.query("test")
        assert result.abstained
        assert "error" in result.abstention_reason.lower()

    async def test_pipeline_timeout_returns_abstention(self, service, mock_pipeline):
        async def slow_pipeline(*args, **kwargs):
            import asyncio

            await asyncio.sleep(999)

        mock_pipeline.ainvoke.side_effect = slow_pipeline
        service._pipeline = mock_pipeline

        # Use a very short timeout for testing
        from app.services import query_service

        original = query_service.PIPELINE_TIMEOUT
        query_service.PIPELINE_TIMEOUT = 0.01

        result = await service.query("test")

        query_service.PIPELINE_TIMEOUT = original
        assert result.abstained
        assert "timed out" in result.abstention_reason.lower()
