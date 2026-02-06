"""Retriever protocol and base classes."""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from app.retrieval.models import EvidenceSet


@runtime_checkable
class Retriever(Protocol):
    """Protocol for evidence retrieval strategies.

    All implementations must be async and non-blocking.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int = 50,
        **kwargs,
    ) -> EvidenceSet:
        """Retrieve evidence for a query.

        Args:
            query: User's question or search query.
            entity_ids: Optional pre-extracted entity IDs for graph traversal.
            max_nodes: Maximum number of nodes to return.
            **kwargs: Implementation-specific options.

        Returns:
            EvidenceSet containing retrieved nodes.
        """
        ...
