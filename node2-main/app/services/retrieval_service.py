"""Retrieval service - orchestrates the full retrieval pipeline."""

from app.retrieval.base import Retriever
from app.retrieval.context_packager import ContextPackager
from app.retrieval.models import EvidenceSet, StructuredContext


class RetrievalService:
    """High-level orchestrator for the retrieval pipeline.

    Composes retriever + packager for end-to-end query handling.
    Ready for Phase 4 extension with verification service.
    """

    def __init__(
        self,
        retriever: Retriever,
        packager: ContextPackager | None = None,
    ):
        """Initialize retrieval service.

        Args:
            retriever: Retriever implementation (graph, semantic, or hybrid).
            packager: Optional context packager. Creates default if not provided.
        """
        self._retriever = retriever
        self._packager = packager or ContextPackager()

    async def retrieve(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int | None = None,
    ) -> EvidenceSet:
        """Retrieve evidence without packaging.

        Args:
            query: User's question.
            entity_ids: Optional pre-extracted entity IDs.
            max_nodes: Maximum nodes to retrieve.

        Returns:
            Raw EvidenceSet from retriever.
        """
        return await self._retriever.retrieve(
            query=query,
            entity_ids=entity_ids,
            max_nodes=max_nodes,
        )

    async def retrieve_and_package(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int | None = None,
    ) -> StructuredContext:
        """Retrieve evidence and package for LLM consumption.

        Args:
            query: User's question.
            entity_ids: Optional pre-extracted entity IDs.
            max_nodes: Maximum nodes to retrieve.

        Returns:
            StructuredContext ready for LLM.
        """
        evidence = await self.retrieve(
            query=query,
            entity_ids=entity_ids,
            max_nodes=max_nodes,
        )
        return self._packager.package(evidence)
