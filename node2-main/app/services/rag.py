"""GraphRAG service — orchestrates retrieval + LLM generation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from neo4j_graphrag.generation import GraphRAG

from app.inference.llm_adapter import Node1LLM

if TYPE_CHECKING:
    from neo4j_graphrag.generation.types import RagResultModel
    from neo4j_graphrag.retrievers import (
        HybridCypherRetriever,
        Text2CypherRetriever,
        VectorCypherRetriever,
    )

logger = logging.getLogger(__name__)

# Type alias for all supported retrievers
LibraryRetriever = (
    "VectorCypherRetriever | Text2CypherRetriever | HybridCypherRetriever"
)


class RAGService:
    """GraphRAG service using neo4j-graphrag built-in components.

    Wraps GraphRAG pipeline: retriever → LLM → answer.
    """

    def __init__(
        self,
        retriever: VectorCypherRetriever | Text2CypherRetriever | HybridCypherRetriever,
        llm: Node1LLM | None = None,
    ) -> None:
        self._llm = llm or Node1LLM()
        self._rag = GraphRAG(retriever=retriever, llm=self._llm)

    def search(
        self,
        query: str,
        return_context: bool = True,
    ) -> RagResultModel:
        """Synchronous RAG search."""
        return self._rag.search(query_text=query, return_context=return_context)

    async def asearch(
        self,
        query: str,
        return_context: bool = True,
    ) -> RagResultModel:
        """Async RAG search."""
        return await self._rag.asearch(query_text=query, return_context=return_context)
