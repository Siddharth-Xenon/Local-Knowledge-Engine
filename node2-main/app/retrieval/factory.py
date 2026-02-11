"""Factory for creating retriever from configuration."""

from app.config import settings
from app.embeddings.base import EmbeddingStrategy
from app.retrieval.base import Retriever
from app.retrieval.strategies.graph import GraphRetriever
from app.retrieval.strategies.hybrid import HybridRetriever
from app.retrieval.strategies.semantic import SemanticRetriever


class RetrieverFactory:
    """Factory for creating retriever implementations.

    Reads retriever_type from config and returns appropriate implementation.
    """

    @staticmethod
    def create(
        embedding: EmbeddingStrategy | None = None,
        retriever_type: str | None = None,
    ) -> Retriever:
        """Create a retriever from config.

        Args:
            embedding: Required for semantic/hybrid retrievers.
            retriever_type: Override config value.
                Options: "graph", "semantic", "hybrid"

        Returns:
            Retriever implementation.

        Raises:
            ValueError: If retriever type is unknown or missing dependencies.
        """
        type_name = retriever_type or settings.retriever_type

        if type_name == "graph":
            return GraphRetriever()

        elif type_name == "semantic":
            if embedding is None:
                raise ValueError(
                    "Semantic retriever requires embedding. "
                    "Pass embedding= to create()."
                )
            return SemanticRetriever(embedding=embedding)

        elif type_name == "hybrid":
            if embedding is None:
                raise ValueError(
                    "Hybrid retriever requires embedding. Pass embedding= to create()."
                )
            graph = GraphRetriever()
            semantic = SemanticRetriever(embedding=embedding)
            return HybridRetriever(graph_retriever=graph, semantic_retriever=semantic)

        else:
            raise ValueError(
                f"Unknown retriever type: {type_name}. "
                f"Options: 'graph', 'semantic', 'hybrid'"
            )
