"""Sentence-transformers embedding - basic placeholder implementation."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.config import settings


class STEmbedding:
    """Sentence-transformers embedding strategy.

    Basic placeholder wrapping sentence-transformers model.
    CPU-bound encoding uses ThreadPoolExecutor for non-blocking async.

    Note: This is a basic implementation. Specialized agents can optimize
    batch processing, caching, and GPU usage later.
    """

    _executor: ThreadPoolExecutor | None = None
    _model: Any = None  # Lazy loaded

    def __init__(
        self,
        model_name: str | None = None,
        dimension: int | None = None,
    ):
        """Initialize sentence-transformers embedding.

        Args:
            model_name: HuggingFace model name. Defaults to config value.
            dimension: Expected dimension. Defaults to config value.
        """
        self._model_name = model_name or settings.embedding_model_name
        self._dimension = dimension or settings.embedding_dimension

        if STEmbedding._executor is None:
            STEmbedding._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def _get_model(self) -> Any:
        """Lazy load the sentence-transformers model."""
        if STEmbedding._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                STEmbedding._model = SentenceTransformer(self._model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return STEmbedding._model

    def _encode_sync(self, text: str) -> NDArray[np.float32]:
        """Synchronous single text encoding."""
        model = self._get_model()
        vector = model.encode(text, convert_to_numpy=True)
        return vector.astype(np.float32)

    def _encode_batch_sync(self, texts: list[str]) -> NDArray[np.float32]:
        """Synchronous batch encoding."""
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)
        model = self._get_model()
        vectors = model.encode(texts, convert_to_numpy=True)
        return vectors.astype(np.float32)

    async def encode(self, text: str) -> NDArray[np.float32]:
        """Encode text to vector (non-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._encode_sync,
            text,
        )

    async def encode_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Encode multiple texts (non-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._encode_batch_sync,
            texts,
        )
