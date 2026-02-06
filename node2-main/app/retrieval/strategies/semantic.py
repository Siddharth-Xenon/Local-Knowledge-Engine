"""Semantic retriever using embedding similarity search."""

from app.config import settings
from app.embeddings.base import EmbeddingStrategy
from app.graph.connection import get_session
from app.index.base import VectorIndex
from app.retrieval.models import EvidenceSet, NodeResult


class SemanticRetriever:
    """Retrieves evidence by semantic similarity.

    Embeds the query, searches the vector index, then fetches
    full node content from Neo4j.
    """

    def __init__(
        self,
        embedding: EmbeddingStrategy,
        index: VectorIndex,
        top_k: int | None = None,
    ):
        """Initialize semantic retriever.

        Args:
            embedding: Embedding strategy for query encoding.
            index: Vector index for similarity search.
            top_k: Number of results to retrieve. Defaults to config value.
        """
        self._embedding = embedding
        self._index = index
        self._top_k = top_k or settings.semantic_top_k

    async def retrieve(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int | None = None,
        **kwargs,
    ) -> EvidenceSet:
        """Retrieve evidence by semantic similarity.

        Ignores entity_ids - uses pure semantic search.
        """
        k = max_nodes or self._top_k

        # Encode query
        query_vector = await self._embedding.encode(query)

        # Search index
        results = await self._index.search(query_vector, k=k)

        if not results:
            return EvidenceSet(
                nodes=[],
                query=query,
                graph_count=0,
                semantic_count=0,
            )

        # Fetch node content from Neo4j
        node_ids = [node_id for node_id, _ in results]
        score_map = {node_id: score for node_id, score in results}

        nodes: list[NodeResult] = []
        async with get_session() as session:
            # Batch fetch node content
            cypher = """
            UNWIND $ids AS id
            MATCH (n {id: id})
            RETURN n.id AS node_id,
                   COALESCE(n.content, n.name) AS content,
                   head(labels(n)) AS node_type
            """
            result = await session.run(cypher, ids=node_ids)
            records = await result.data()

            for record in records:
                node_id = record["node_id"]
                nodes.append(
                    NodeResult(
                        node_id=node_id,
                        content=str(record.get("content", "")),
                        node_type=record.get("node_type", "Unknown"),
                        score=score_map.get(node_id, 0.0),
                        source="semantic",
                    )
                )

        # Sort by score descending
        nodes.sort(key=lambda x: x.score, reverse=True)

        return EvidenceSet(
            nodes=nodes,
            query=query,
            graph_count=0,
            semantic_count=len(nodes),
        )
