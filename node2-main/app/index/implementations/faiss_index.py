"""FAISS vector index for production use."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from app.config import settings


class FaissIndex:
    """FAISS-based vector index for production.

    Uses FAISS IndexFlatIP (inner product) with normalized vectors
    for cosine similarity. Non-blocking via ThreadPoolExecutor.
    """

    _executor: ThreadPoolExecutor | None = None

    def __init__(self, dimension: int | None = None):
        """Initialize FAISS index.

        Args:
            dimension: Vector dimension. Defaults to config value.
        """
        self._dimension = dimension or settings.embedding_dimension
        self._id_to_idx: dict[str, int] = {}  # node_id -> faiss index
        self._idx_to_id: dict[int, str] = {}  # faiss index -> node_id
        self._index = None  # Lazy loaded

        if FaissIndex._executor is None:
            FaissIndex._executor = ThreadPoolExecutor(max_workers=2)

    def _get_index(self):
        """Lazy load FAISS index."""
        if self._index is None:
            try:
                import faiss

                # IndexFlatIP for inner product (cosine sim with normalized vectors)
                self._index = faiss.IndexFlatIP(self._dimension)
            except ImportError:
                raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
        return self._index

    @property
    def size(self) -> int:
        """Return the number of vectors in the index."""
        return len(self._id_to_idx)

    async def add(self, node_id: str, vector: NDArray[np.float32]) -> None:
        """Add a single vector (normalizes for cosine similarity)."""
        loop = asyncio.get_running_loop()

        def _add() -> None:
            index = self._get_index()
            # Normalize vector
            norm = np.linalg.norm(vector)
            normalized = vector / norm if norm > 0 else vector

            # Add to index
            idx = index.ntotal
            index.add(normalized.reshape(1, -1))

            # Update mappings
            self._id_to_idx[node_id] = idx
            self._idx_to_id[idx] = node_id

        await loop.run_in_executor(self._executor, _add)

    async def add_batch(
        self,
        node_ids: list[str],
        vectors: NDArray[np.float32],
    ) -> None:
        """Add multiple vectors."""
        loop = asyncio.get_running_loop()

        def _add_batch() -> None:
            if len(node_ids) == 0:
                return
            index = self._get_index()

            # Normalize vectors
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            normalized = vectors / norms

            # Record starting index
            start_idx = index.ntotal

            # Add to index
            index.add(normalized)

            # Update mappings
            for i, node_id in enumerate(node_ids):
                idx = start_idx + i
                self._id_to_idx[node_id] = idx
                self._idx_to_id[idx] = node_id

        await loop.run_in_executor(self._executor, _add_batch)

    async def search(
        self,
        query_vector: NDArray[np.float32],
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search for k nearest neighbors (non-blocking)."""
        loop = asyncio.get_running_loop()

        def _search() -> list[tuple[str, float]]:
            index = self._get_index()
            if index.ntotal == 0:
                return []

            # Normalize query
            norm = np.linalg.norm(query_vector)
            normalized = query_vector / norm if norm > 0 else query_vector

            # Search (limit k to available vectors)
            actual_k = min(k, index.ntotal)
            scores, indices = index.search(normalized.reshape(1, -1), actual_k)

            # Convert to (node_id, score) tuples
            results = []
            for i in range(actual_k):
                idx = int(indices[0][i])
                if idx in self._idx_to_id:
                    results.append((self._idx_to_id[idx], float(scores[0][i])))
            return results

        return await loop.run_in_executor(self._executor, _search)

    async def save(self, path: str) -> None:
        """Save index and mappings to disk."""
        loop = asyncio.get_running_loop()

        def _save() -> None:
            import json

            import faiss

            Path(path).parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self._get_index(), path)

            # Save ID mappings
            mappings_path = path + ".mappings.json"
            with open(mappings_path, "w") as f:
                json.dump(
                    {
                        "id_to_idx": self._id_to_idx,
                        "dimension": self._dimension,
                    },
                    f,
                )

        await loop.run_in_executor(self._executor, _save)

    async def load(self, path: str) -> None:
        """Load index and mappings from disk."""
        loop = asyncio.get_running_loop()

        def _load() -> None:
            import json

            import faiss

            if not Path(path).exists():
                return

            # Load FAISS index
            self._index = faiss.read_index(path)

            # Load ID mappings
            mappings_path = path + ".mappings.json"
            if Path(mappings_path).exists():
                with open(mappings_path) as f:
                    data = json.load(f)
                self._id_to_idx = {
                    k: int(v) for k, v in data.get("id_to_idx", {}).items()
                }
                self._idx_to_id = {v: k for k, v in self._id_to_idx.items()}

        await loop.run_in_executor(self._executor, _load)
