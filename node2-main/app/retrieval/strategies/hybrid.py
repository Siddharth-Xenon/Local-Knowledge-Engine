"""Hybrid retriever combining graph and semantic strategies."""

import asyncio

from app.config import settings
from app.retrieval.models import EvidenceSet, NodeResult
from app.retrieval.strategies.graph import GraphRetriever
from app.retrieval.strategies.semantic import SemanticRetriever


class HybridRetriever:
    """Combines graph and semantic retrieval strategies.

    Runs both retrievers in parallel, merges and deduplicates results.
    Non-blocking via asyncio.gather().
    """

    def __init__(
        self,
        graph_retriever: GraphRetriever,
        semantic_retriever: SemanticRetriever,
        max_nodes: int | None = None,
    ):
        """Initialize hybrid retriever.

        Args:
            graph_retriever: Graph traversal retriever.
            semantic_retriever: Semantic similarity retriever.
            max_nodes: Max total nodes to return. Defaults to config value.
        """
        self._graph = graph_retriever
        self._semantic = semantic_retriever
        self._max_nodes = max_nodes or settings.retrieval_max_nodes

    async def retrieve(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int | None = None,
        **kwargs,
    ) -> EvidenceSet:
        """Retrieve evidence using both graph and semantic strategies.

        Runs both in parallel, merges results, deduplicates by node_id.
        """
        limit = max_nodes or self._max_nodes

        # Run both retrievers in parallel
        graph_task = self._graph.retrieve(query, entity_ids, max_nodes=limit)
        semantic_task = self._semantic.retrieve(query, max_nodes=limit)

        graph_result, semantic_result = await asyncio.gather(
            graph_task,
            semantic_task,
            return_exceptions=True,
        )

        # Handle exceptions gracefully
        graph_nodes: list[NodeResult] = []
        semantic_nodes: list[NodeResult] = []

        if isinstance(graph_result, EvidenceSet):
            graph_nodes = graph_result.nodes
        elif isinstance(graph_result, Exception):
            pass  # Log error in production

        if isinstance(semantic_result, EvidenceSet):
            semantic_nodes = semantic_result.nodes
        elif isinstance(semantic_result, Exception):
            pass  # Log error in production

        # Merge and deduplicate
        seen: set[str] = set()
        merged: list[NodeResult] = []

        # Interleave results: 1 from graph, 1 from semantic
        graph_iter = iter(graph_nodes)
        semantic_iter = iter(semantic_nodes)

        while len(merged) < limit:
            added = False

            # Try to add from graph
            for node in graph_iter:
                if node.node_id not in seen:
                    seen.add(node.node_id)
                    merged.append(node)
                    added = True
                    break

            if len(merged) >= limit:
                break

            # Try to add from semantic
            for node in semantic_iter:
                if node.node_id not in seen:
                    seen.add(node.node_id)
                    merged.append(node)
                    added = True
                    break

            if not added:
                break

        return EvidenceSet(
            nodes=merged,
            query=query,
            graph_count=len([n for n in merged if n.source == "graph"]),
            semantic_count=len([n for n in merged if n.source == "semantic"]),
        )
