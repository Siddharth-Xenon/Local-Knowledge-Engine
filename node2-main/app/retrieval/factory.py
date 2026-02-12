"""Factory for creating neo4j-graphrag retrievers from configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neo4j_graphrag.retrievers import (
    HybridCypherRetriever,
    Text2CypherRetriever,
    VectorCypherRetriever,
)

from app.config import settings

if TYPE_CHECKING:
    import neo4j
    from neo4j_graphrag.embeddings.base import Embedder
    from neo4j_graphrag.llm.base import LLMInterface


# Default retrieval query — returns node content for context packaging
VECTOR_RETRIEVAL_QUERY = """
RETURN node.rule_id AS node_id,
       COALESCE(node.description, node.name) AS text,
       head(labels(node)) AS node_type,
       score
"""

HYBRID_RETRIEVAL_QUERY = VECTOR_RETRIEVAL_QUERY


class RetrieverFactory:
    """Factory for creating neo4j-graphrag retriever implementations.

    Creates library retrievers backed by Neo4j vector and fulltext indexes.
    """

    @staticmethod
    def create_vector(
        driver: neo4j.Driver,
        embedder: Embedder,
        index_name: str | None = None,
        retrieval_query: str | None = None,
    ) -> VectorCypherRetriever:
        """Create a vector similarity retriever."""
        return VectorCypherRetriever(
            driver=driver,
            index_name=index_name or settings.vector_index_name,
            embedder=embedder,
            retrieval_query=retrieval_query or VECTOR_RETRIEVAL_QUERY,
        )

    @staticmethod
    def create_text2cypher(
        driver: neo4j.Driver,
        llm: LLMInterface,
        examples: list[str] | None = None,
    ) -> Text2CypherRetriever:
        """Create a text-to-Cypher retriever."""
        return Text2CypherRetriever(
            driver=driver,
            llm=llm,
            examples=examples or [],
        )

    @staticmethod
    def create_hybrid(
        driver: neo4j.Driver,
        embedder: Embedder,
        vector_index_name: str | None = None,
        fulltext_index_name: str | None = None,
        retrieval_query: str | None = None,
    ) -> HybridCypherRetriever:
        """Create a hybrid (vector + fulltext) retriever."""
        return HybridCypherRetriever(
            driver=driver,
            vector_index_name=vector_index_name or settings.vector_index_name,
            fulltext_index_name=fulltext_index_name or settings.fulltext_index_name,
            embedder=embedder,
            retrieval_query=retrieval_query or HYBRID_RETRIEVAL_QUERY,
        )

    @staticmethod
    def create(
        driver: neo4j.Driver,
        embedder: Embedder | None = None,
        llm: LLMInterface | None = None,
        retriever_type: str | None = None,
    ) -> VectorCypherRetriever | Text2CypherRetriever | HybridCypherRetriever:
        """Create a retriever from config.

        Args:
            driver: Neo4j driver instance.
            embedder: Required for vector/hybrid retrievers.
            llm: Required for text2cypher retriever.
            retriever_type: Override config. Options: "vector", "text2cypher", "hybrid"

        Returns:
            Library retriever instance.
        """
        type_name = retriever_type or settings.retriever_type

        if type_name == "vector":
            if embedder is None:
                raise ValueError("Vector retriever requires embedder.")
            return RetrieverFactory.create_vector(driver, embedder)

        elif type_name == "text2cypher":
            if llm is None:
                raise ValueError("Text2Cypher retriever requires llm.")
            return RetrieverFactory.create_text2cypher(driver, llm)

        elif type_name == "hybrid":
            if embedder is None:
                raise ValueError("Hybrid retriever requires embedder.")
            return RetrieverFactory.create_hybrid(driver, embedder)

        else:
            raise ValueError(
                f"Unknown retriever type: {type_name}. "
                f"Options: 'vector', 'text2cypher', 'hybrid'"
            )
