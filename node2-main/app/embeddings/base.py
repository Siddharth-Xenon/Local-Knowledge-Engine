"""Embedding strategies protocol and base classes."""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class EmbeddingStrategy(Protocol):
    """Protocol for embedding strategies.

    All implementations must be async and non-blocking.
    CPU-bound operations should use asyncio.run_in_executor().
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    @abstractmethod
    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode a single text into a vector.

        Args:
            text: Input text to encode.

        Returns:
            Float32 numpy array of shape (dimension,).
        """
        ...

    @abstractmethod
    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts into vectors.

        Args:
            texts: List of input texts to encode.

        Returns:
            Float32 numpy array of shape (len(texts), dimension).
        """
        ...
