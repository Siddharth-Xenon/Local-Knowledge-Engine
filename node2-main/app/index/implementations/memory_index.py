"""In-memory vector index using numpy for cosine similarity."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from app.config import settings


class MemoryIndex:
    """Simple in-memory vector index for MVP.

    Uses numpy for cosine similarity search.
    Non-blocking via ThreadPoolExecutor.
    """

    _executor: ThreadPoolExecutor | None = None

    def __init__(self, dimension: int | None = None):
        """Initialize memory index.

        Args:
            dimension: Vector dimension. Defaults to config value.
        """
        self._dimension = dimension or settings.embedding_dimension
        self._vectors: dict[str, NDArray[np.float32]] = {}

        if MemoryIndex._executor is None:
            MemoryIndex._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def size(self) -> int:
        """Return the number of vectors in the index."""
        return len(self._vectors)

    async def add(self, node_id: str, vector: NDArray[np.float32]) -> None:
        """Add a single vector (normalizes for cosine similarity)."""
        # Normalize vector for cosine similarity
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        self._vectors[node_id] = vector

    async def add_batch(
        self,
        node_ids: list[str],
        vectors: NDArray[np.float32],
    ) -> None:
        """Add multiple vectors."""
        for i, node_id in enumerate(node_ids):
            await self.add(node_id, vectors[i])

    def _search_sync(
        self,
        query_vector: NDArray[np.float32],
        k: int,
    ) -> list[tuple[str, float]]:
        """Synchronous search using cosine similarity."""
        if not self._vectors:
            return []

        # Normalize query
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        # Compute cosine similarities (dot product of normalized vectors)
        scores: list[tuple[str, float]] = []
        for node_id, vec in self._vectors.items():
            similarity = float(np.dot(query_vector, vec))
            scores.append((node_id, similarity))

        # Sort by score descending and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    async def search(
        self,
        query_vector: NDArray[np.float32],
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search for k nearest neighbors (non-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._search_sync,
            query_vector,
            k,
        )

    async def save(self, path: str) -> None:
        """Save index to disk as JSON."""
        loop = asyncio.get_running_loop()

        def _save() -> None:
            data = {
                "dimension": self._dimension,
                "vectors": {
                    node_id: vec.tolist() for node_id, vec in self._vectors.items()
                },
            }
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f)

        await loop.run_in_executor(self._executor, _save)

    async def load(self, path: str) -> None:
        """Load index from disk."""
        loop = asyncio.get_running_loop()

        def _load() -> dict[str, NDArray[np.float32]]:
            if not Path(path).exists():
                return {}
            with open(path) as f:
                data = json.load(f)
            return {
                node_id: np.array(vec, dtype=np.float32)
                for node_id, vec in data.get("vectors", {}).items()
            }

        self._vectors = await loop.run_in_executor(self._executor, _load)
