"""Vector index protocol and base classes."""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class VectorIndex(Protocol):
    """Protocol for vector index implementations.

    All implementations must be async and non-blocking.
    CPU-bound operations should use asyncio.run_in_executor().
    """

    @property
    @abstractmethod
    def size(self) -> int:
        """Return the number of vectors in the index."""
        ...

    @abstractmethod
    async def add(self, node_id: str, vector: NDArray[np.float32]) -> None:
        """Add a single vector to the index.

        Args:
            node_id: Unique identifier for the vector.
            vector: Float32 numpy array of shape (dimension,).
        """
        ...

    @abstractmethod
    async def add_batch(
        self,
        node_ids: list[str],
        vectors: NDArray[np.float32],
    ) -> None:
        """Add multiple vectors to the index.

        Args:
            node_ids: List of unique identifiers.
            vectors: Float32 numpy array of shape (n, dimension).
        """
        ...

    @abstractmethod
    async def search(
        self,
        query_vector: NDArray[np.float32],
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search for k nearest neighbors.

        Args:
            query_vector: Float32 numpy array of shape (dimension,).
            k: Number of neighbors to return.

        Returns:
            List of (node_id, score) tuples, sorted by score descending.
        """
        ...

    @abstractmethod
    async def save(self, path: str) -> None:
        """Persist index to disk.

        Args:
            path: File path to save to.
        """
        ...

    @abstractmethod
    async def load(self, path: str) -> None:
        """Load index from disk.

        Args:
            path: File path to load from.
        """
        ...
