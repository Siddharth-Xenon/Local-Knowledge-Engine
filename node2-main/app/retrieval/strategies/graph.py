"""Graph-based retriever using Neo4j traversal."""

from app.config import settings
from app.graph.connection import get_session
from app.retrieval.models import EvidenceSet, NodeResult


class GraphRetriever:
    """Retrieves evidence by traversing the knowledge graph.

    Uses Neo4j to find related nodes starting from entity IDs.
    Leverages existing async Neo4j driver for non-blocking I/O.
    """

    def __init__(
        self,
        max_depth: int | None = None,
        max_nodes: int | None = None,
    ):
        """Initialize graph retriever.

        Args:
            max_depth: Traversal depth. Defaults to config value.
            max_nodes: Max nodes to return. Defaults to config value.
        """
        self._max_depth = max_depth or settings.graph_traversal_depth
        self._max_nodes = max_nodes or settings.retrieval_max_nodes

    async def retrieve(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        max_nodes: int | None = None,
        **kwargs,
    ) -> EvidenceSet:
        """Retrieve evidence by graph traversal.

        If entity_ids provided, traverses from those nodes.
        Otherwise, searches for nodes containing query text.
        """
        limit = max_nodes or self._max_nodes
        nodes: list[NodeResult] = []

        async with get_session() as session:
            if entity_ids:
                # Traverse from provided entity IDs
                cypher = """
                MATCH (start {id: $start_id})
                OPTIONAL MATCH path = (start)-[*1..$depth]-(related)
                WITH start, related
                WHERE related IS NOT NULL OR start IS NOT NULL
                WITH COALESCE(related, start) AS node,
                     labels(COALESCE(related, start)) AS lbls
                RETURN DISTINCT node.id AS node_id, 
                       node.content AS content,
                       node.name AS name,
                       head(lbls) AS node_type
                LIMIT $limit
                """
                for entity_id in entity_ids[:5]:  # Limit starting points
                    result = await session.run(
                        cypher,
                        start_id=entity_id,
                        depth=self._max_depth,
                        limit=limit,
                    )
                    records = await result.data()
                    for record in records:
                        content = record.get("content") or record.get("name") or ""
                        if content:
                            nodes.append(
                                NodeResult(
                                    node_id=record["node_id"],
                                    content=str(content),
                                    node_type=record.get("node_type", "Unknown"),
                                    score=1.0,  # Graph results are equally relevant
                                    source="graph",
                                )
                            )
                        if len(nodes) >= limit:
                            break
                    if len(nodes) >= limit:
                        break
            else:
                # Text search fallback - search by content/name
                cypher = """
                MATCH (n)
                WHERE n.content CONTAINS $query OR n.name CONTAINS $query
                RETURN n.id AS node_id,
                       COALESCE(n.content, n.name) AS content,
                       head(labels(n)) AS node_type
                LIMIT $limit
                """
                result = await session.run(cypher, query=query, limit=limit)
                records = await result.data()
                for record in records:
                    nodes.append(
                        NodeResult(
                            node_id=record["node_id"],
                            content=str(record.get("content", "")),
                            node_type=record.get("node_type", "Unknown"),
                            score=0.8,  # Lower score for text search
                            source="graph",
                        )
                    )

        # Deduplicate by node_id
        seen = set()
        unique_nodes = []
        for node in nodes:
            if node.node_id not in seen:
                seen.add(node.node_id)
                unique_nodes.append(node)

        return EvidenceSet(
            nodes=unique_nodes[:limit],
            query=query,
            graph_count=len(unique_nodes),
            semantic_count=0,
        )
