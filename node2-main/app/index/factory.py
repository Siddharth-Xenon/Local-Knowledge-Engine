"""Factory for creating vector index from configuration."""

from app.config import settings
from app.index.base import VectorIndex
from app.index.implementations.faiss_index import FaissIndex
from app.index.implementations.memory_index import MemoryIndex


class IndexFactory:
    """Factory for creating vector index implementations.

    Reads index_type from config and returns appropriate implementation.
    """

    @staticmethod
    def create(index_type: str | None = None) -> VectorIndex:
        """Create a vector index from config.

        Args:
            index_type: Override config value. Options: "memory", "faiss"

        Returns:
            VectorIndex implementation.

        Raises:
            ValueError: If index type is unknown.
        """
        type_name = index_type or settings.index_type

        if type_name == "memory":
            return MemoryIndex()
        elif type_name == "faiss":
            return FaissIndex()
        else:
            raise ValueError(
                f"Unknown index type: {type_name}. Options: 'memory', 'faiss'"
            )
