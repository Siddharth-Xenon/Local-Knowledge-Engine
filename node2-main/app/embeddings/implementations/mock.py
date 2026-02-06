"""Mock embedding for testing - deterministic vector from text hash."""

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from numpy.typing import NDArray

from app.config import settings


class MockEmbedding:
    """Deterministic embedding strategy for testing.

    Generates consistent vectors by hashing text content.
    Non-blocking via ThreadPoolExecutor.
    """

    _executor: ThreadPoolExecutor | None = None

    def __init__(self, dimension: int | None = None):
        """Initialize mock embedding.

        Args:
            dimension: Vector dimension. Defaults to config value.
        """
        self._dimension = dimension or settings.embedding_dimension
        if MockEmbedding._executor is None:
            MockEmbedding._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def _hash_to_vector(self, text: str) -> NDArray[np.float32]:
        """Convert text to deterministic vector via hashing.

        Uses SHA-256 hash extended to fill the dimension.
        """
        # Create deterministic seed from text
        hash_bytes = hashlib.sha256(text.encode()).digest()
        seed = int.from_bytes(hash_bytes[:4], "big")

        # Generate deterministic random vector
        rng = np.random.default_rng(seed)
        vector = rng.random(self._dimension).astype(np.float32)

        # Normalize to unit vector for cosine similarity
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode text to vector (non-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._hash_to_vector,
            text,
        )

    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts (non-blocking)."""
        loop = asyncio.get_running_loop()

        def _batch_encode() -> NDArray[np.float32]:
            vectors = [self._hash_to_vector(t) for t in texts]
            return (
                np.stack(vectors)
                if vectors
                else np.empty((0, self._dimension), dtype=np.float32)
            )

        return await loop.run_in_executor(self._executor, _batch_encode)
