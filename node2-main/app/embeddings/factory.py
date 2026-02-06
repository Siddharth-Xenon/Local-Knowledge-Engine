"""Factory for creating embedding strategies from configuration."""

from app.config import settings
from app.embeddings.base import EmbeddingStrategy
from app.embeddings.implementations.mock import MockEmbedding
from app.embeddings.implementations.sentence_transformers import STEmbedding


class EmbeddingFactory:
    """Factory for creating embedding strategies.

    Reads embedding_type from config and returns appropriate implementation.
    """

    @staticmethod
    def create(embedding_type: str | None = None) -> EmbeddingStrategy:
        """Create an embedding strategy from config.

        Args:
            embedding_type: Override config value.
                Options: "mock", "sentence-transformers"

        Returns:
            EmbeddingStrategy implementation.

        Raises:
            ValueError: If embedding type is unknown.
        """
        type_name = embedding_type or settings.embedding_type

        if type_name == "mock":
            return MockEmbedding()
        elif type_name == "sentence-transformers":
            return STEmbedding()
        else:
            raise ValueError(
                f"Unknown embedding type: {type_name}. "
                f"Options: 'mock', 'sentence-transformers'"
            )
