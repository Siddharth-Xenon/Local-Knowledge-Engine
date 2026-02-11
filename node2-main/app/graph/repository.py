"""Generic graph repository for CRUD operations."""

from typing import Any
from uuid import uuid4

from app.graph.connection import get_session


class GraphRepository:
    """Generic repository for Neo4j graph operations."""

    @staticmethod
    async def create_node(
        label: str,
        properties: dict[str, Any],
    ) -> str:
        """
        Create a node with the given label and properties.

        Returns the node ID.
        """
        node_id = str(uuid4())
        properties["id"] = node_id

        async with get_session() as session:
            query = f"""
            CREATE (n:{label} $props)
            RETURN n.id AS id
            """
            result = await session.run(query, props=properties)
            record = await result.single()
            return record["id"] if record else node_id

    @staticmethod
    async def get_node(node_id: str) -> dict[str, Any] | None:
        """Get a node by its ID."""
        async with get_session() as session:
            query = """
            MATCH (n {id: $id})
            RETURN n, labels(n) AS labels
            """
            result = await session.run(query, id=node_id)
            record = await result.single()
            if record:
                node_data = dict(record["n"])
                node_data["_labels"] = record["labels"]
                return node_data
            return None

    @staticmethod
    async def create_edge(
        from_id: str,
        to_id: str,
        edge_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create an edge between two nodes."""
        props = properties or {}

        async with get_session() as session:
            query = f"""
            MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
            CREATE (a)-[r:{edge_type} $props]->(b)
            RETURN r
            """
            result = await session.run(
                query,
                from_id=from_id,
                to_id=to_id,
                props=props,
            )
            record = await result.single()
            return record is not None

    @staticmethod
    async def query_nodes(
        label: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query nodes with optional label and property filters."""
        async with get_session() as session:
            where_clauses = []
            params: dict[str, Any] = {"limit": limit}

            if filters:
                for key, value in filters.items():
                    param_name = f"filter_{key}"
                    where_clauses.append(f"n.{key} = ${param_name}")
                    params[param_name] = value

            label_part = f":{label}" if label else ""
            where_part = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            query = f"""
            MATCH (n{label_part})
            {where_part}
            RETURN n, labels(n) AS labels
            LIMIT $limit
            """

            result = await session.run(query, **params)
            records = await result.data()
            return [{**dict(r["n"]), "_labels": r["labels"]} for r in records]

    @staticmethod
    async def get_embeddable_nodes(
        labels: list[str],
    ) -> list[dict[str, Any]]:
        """Fetch nodes by label for embedding.

        Returns node properties with _labels metadata.
        """
        if not labels:
            return []

        async with get_session() as session:
            label_filter = " OR ".join(f"n:{lbl}" for lbl in labels)
            query = f"""
            MATCH (n)
            WHERE {label_filter}
            RETURN n, labels(n) AS labels
            """
            result = await session.run(query)
            records = await result.data()
            return [{**dict(r["n"]), "_labels": r["labels"]} for r in records]

    @staticmethod
    async def health_check() -> bool:
        """Check if Neo4j is reachable."""
        try:
            async with get_session() as session:
                result = await session.run("RETURN 1 AS x")
                record = await result.single()
                return record is not None and record["x"] == 1
        except Exception:
            return False
