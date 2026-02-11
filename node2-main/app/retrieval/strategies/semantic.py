"""Semantic retriever using Neo4j native vector index."""

from app.config import settings
from app.embeddings.base import EmbeddingStrategy
from app.graph.connection import get_session
from app.retrieval.models import EvidenceSet, NodeResult


class SemanticRetriever:
    """Retrieves evidence by semantic similarity via Neo4j vector indexes.

    Encodes the query, searches Neo4j vector indexes for Rule and Policy
    nodes, then returns full node content with similarity scores.
    """

    def __init__(
        self,
        embedding: EmbeddingStrategy,
        top_k: int | None = None,
    ):
        """Initialize semantic retriever.

        Args:
            embedding: Embedding strategy for query encoding.
            top_k: Number of results to retrieve. Defaults to config value.
        """
        self._embedding = embedding
        self._top_k = top_k or settings.semantic_top_k

    async def retrieve(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int | None = None,
        **kwargs,
    ) -> EvidenceSet:
        """Retrieve evidence by semantic similarity from Neo4j vector index."""
        k = max_nodes or self._top_k

        # Encode query
        query_vector = await self._embedding.encode(query)

        nodes: list[NodeResult] = []
        async with get_session() as session:
            # Search both Rule and Policy vector indexes
            for index_name in ["rule_embedding", "policy_embedding"]:
                cypher = (
                    "CALL db.index.vector.queryNodes("
                    f"'{index_name}', $k, $vec) "
                    "YIELD node, score "
                    "RETURN COALESCE(node.rule_id, "
                    "node.policy_id, node.id) AS node_id, "
                    "COALESCE(node.description, "
                    "node.name) AS content, "
                    "head(labels(node)) AS node_type, "
                    "score"
                )
                try:
                    result = await session.run(cypher, k=k, vec=query_vector.tolist())
                    records = await result.data()

                    for record in records:
                        nodes.append(
                            NodeResult(
                                node_id=record["node_id"],
                                content=str(record.get("content", "")),
                                node_type=record.get("node_type", "Unknown"),
                                score=record.get("score", 0.0),
                                source="semantic",
                            )
                        )
                except Exception:
                    # Index may not exist yet — skip silently
                    pass

        # Sort by score descending and limit
        nodes.sort(key=lambda x: x.score, reverse=True)
        nodes = nodes[:k]

        return EvidenceSet(
            nodes=nodes,
            query=query,
            graph_count=0,
            semantic_count=len(nodes),
        )
