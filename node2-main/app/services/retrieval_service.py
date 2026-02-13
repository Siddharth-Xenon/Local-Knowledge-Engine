"""Retrieval service — orchestrates retrieval + context packaging.

Adapts neo4j-graphrag RetrieverResult into internal EvidenceSet/StructuredContext.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.retrieval.context_packager import ContextPackager
from app.retrieval.models import EvidenceSet, NodeResult, StructuredContext

if TYPE_CHECKING:
    from neo4j_graphrag.retrievers import (
        HybridCypherRetriever,
        Text2CypherRetriever,
        VectorCypherRetriever,
    )

logger = logging.getLogger(__name__)

# Type alias
Retriever = "VectorCypherRetriever | Text2CypherRetriever | HybridCypherRetriever"


class RetrievalService:
    """High-level orchestrator for the retrieval pipeline.

    Bridges neo4j-graphrag retrievers with internal ContextPackager.
    """

    def __init__(
        self,
        retriever: VectorCypherRetriever | Text2CypherRetriever | HybridCypherRetriever,
        packager: ContextPackager | None = None,
    ) -> None:
        self._retriever = retriever
        self._packager = packager or ContextPackager()

    def retrieve(self, query: str, top_k: int = 10) -> EvidenceSet:
        """Retrieve evidence synchronously and convert to EvidenceSet."""
        result = self._retriever.search(query_text=query, top_k=top_k)
        return self._to_evidence_set(query, result)

    async def aretrieve(self, query: str, top_k: int = 10) -> EvidenceSet:
        """Retrieve evidence asynchronously and convert to EvidenceSet."""
        # result = self._retriever.search(query_text=query, top_k=top_k)

        result = self._retriever.search(query_text=query)
        return self._to_evidence_set(query, result)

    def retrieve_and_package(
        self, query: str, top_k: int = 10, **kwargs
    ) -> StructuredContext:
        """Retrieve + package for LLM consumption (sync)."""
        evidence = self.retrieve(query, top_k=top_k)
        return self._packager.package(evidence)

    async def aretrieve_and_package(
        self, query: str, top_k: int = 10, **kwargs
    ) -> StructuredContext:
        """Retrieve + package for LLM consumption (async)."""
        evidence = await self.aretrieve(query, top_k=top_k)
        return self._packager.package(evidence)

    @staticmethod
    def _to_evidence_set(query: str, result) -> EvidenceSet:
        """Convert neo4j-graphrag RetrieverResult to internal EvidenceSet."""
        nodes: list[NodeResult] = []
        for item in result.items:
            content = getattr(item, "content", None) or str(item)
            metadata = getattr(item, "metadata", None) or {}
            nodes.append(
                NodeResult(
                    node_id=metadata.get("node_id", f"n{len(nodes)}"),
                    content=content,
                    node_type=metadata.get("node_type", "Unknown"),
                    score=metadata.get("score", 0.0),
                    source="library",
                )
            )
        return EvidenceSet(
            nodes=nodes,
            query=query,
            graph_count=0,
            semantic_count=len(nodes),
            metadata=result.metadata,
        )
