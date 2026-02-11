"""Embedding service — generates embeddings and stores them in Neo4j."""

import logging
import time
from typing import Any

from app.config import settings
from app.embeddings.base import EmbeddingStrategy
from app.graph.connection import get_session
from app.graph.repository import GraphRepository

logger = logging.getLogger(__name__)

EMBEDDABLE_LABELS = ["Rule", "Policy"]

# Seeded data uses label-specific ID fields
_ID_FIELDS = {
    "Rule": "rule_id",
    "Policy": "policy_id",
}


def _get_node_id(node: dict[str, Any]) -> str | None:
    """Extract node ID using label-specific field, fallback to generic 'id'."""
    labels = node.get("_labels", [])
    for label in labels:
        field = _ID_FIELDS.get(label)
        if field and node.get(field):
            return node[field]
    return node.get("id")


def _get_id_field(label: str) -> str:
    """Return the ID property name for a given label."""
    return _ID_FIELDS.get(label, "id")


def _build_text(node: dict[str, Any]) -> str:
    """Build composite text for a node based on its label.

    Rule: uses description field.
    Policy: constructs from policy_type + status + version.
    """
    labels = node.get("_labels", [])

    if "Rule" in labels:
        desc = node.get("description", "")
        rule_type = node.get("rule_type", "")
        severity = node.get("severity", "")
        return f"Rule: {desc}. Type: {rule_type}. Severity: {severity}"

    if "Policy" in labels:
        policy_type = node.get("policy_type", "")
        status = node.get("status", "")
        version = node.get("version", "")
        effective_from = node.get("effective_from", "")
        return (
            f"Policy: {policy_type} ({status}). "
            f"Version: {version}. Effective from: {effective_from}"
        )

    return node.get("description", node.get("name", ""))


class EmbeddingService:
    """Generates embeddings and writes them into Neo4j as node properties."""

    def __init__(self, embedding: EmbeddingStrategy):
        self._embedding = embedding

    async def create_vector_indexes(self) -> None:
        """Create Neo4j vector indexes for Rule and Policy nodes."""
        dim = settings.embedding_dimension
        async with get_session() as session:
            for label in EMBEDDABLE_LABELS:
                index_name = f"{label.lower()}_embedding"
                cypher = (
                    f"CREATE VECTOR INDEX {index_name} IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.embedding) "
                    f"OPTIONS {{indexConfig: {{"
                    f"`vector.dimensions`: {dim}, "
                    f"`vector.similarity_function`: 'cosine'"
                    f"}}}}"
                )
                await session.run(cypher)
                logger.info(f"Vector index '{index_name}' ensured for :{label}")

    async def populate(self) -> int:
        """Fetch Rule + Policy nodes, embed, and store vectors in Neo4j.

        Returns the number of nodes embedded.
        """
        start = time.perf_counter()

        nodes = await GraphRepository.get_embeddable_nodes(EMBEDDABLE_LABELS)
        if not nodes:
            logger.warning("No embeddable nodes found in graph")
            return 0

        # Group nodes by label for batch Cypher updates
        by_label: dict[str, list[tuple[str, list[float]]]] = {}
        texts_to_embed: list[str] = []
        node_meta: list[tuple[str, str]] = []  # (label, node_id)

        for node in nodes:
            node_id = _get_node_id(node)
            if not node_id:
                continue
            text = _build_text(node)
            if not text.strip():
                logger.warning(f"Empty text for node {node_id}, skipping")
                continue

            label = node["_labels"][0]
            texts_to_embed.append(text)
            node_meta.append((label, node_id))

        if not texts_to_embed:
            logger.warning("No texts to embed after filtering")
            return 0

        # Batch embed all texts
        vectors = await self._embedding.encode_batch(texts_to_embed)

        # Group by label
        for i, (label, node_id) in enumerate(node_meta):
            by_label.setdefault(label, []).append((node_id, vectors[i].tolist()))

        # Write embeddings to Neo4j per label
        async with get_session() as session:
            for label, entries in by_label.items():
                id_field = _get_id_field(label)
                params = [{"nid": nid, "vec": vec} for nid, vec in entries]
                cypher = (
                    f"UNWIND $batch AS item "
                    f"MATCH (n:{label} {{{id_field}: item.nid}}) "
                    f"SET n.embedding = item.vec"
                )
                await session.run(cypher, batch=params)
                logger.info(f"Wrote {len(entries)} embeddings to :{label}")

        elapsed = time.perf_counter() - start
        logger.info(f"Embedded {len(texts_to_embed)} nodes in {elapsed:.2f}s")
        return len(texts_to_embed)
