"""Embeddings module."""

from app.embeddings.base import EmbeddingStrategy
from app.embeddings.factory import EmbeddingFactory

__all__ = ["EmbeddingStrategy", "EmbeddingFactory"]
