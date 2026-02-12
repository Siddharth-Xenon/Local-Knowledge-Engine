"""Factory for creating neo4j-graphrag compatible embedders."""

from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

from app.config import settings


class EmbeddingFactory:
    """Factory for creating embedders compatible with neo4j-graphrag retrievers."""

    @staticmethod
    def create(
        model_name: str | None = None,
    ) -> SentenceTransformerEmbeddings:
        """Create a SentenceTransformer embedder.

        Args:
            model_name: Override config value.

        Returns:
            SentenceTransformerEmbeddings instance compatible with neo4j-graphrag.
        """
        return SentenceTransformerEmbeddings(
            model=model_name or settings.embedding_model_name,
        )
