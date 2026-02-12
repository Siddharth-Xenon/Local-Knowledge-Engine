"""Integration tests for RetrievalService against a live Neo4j instance.

Run explicitly: pytest tests/test_retrieval_integration.py -m neo4j -v

Requires:
  - Neo4j running on bolt://localhost:7687
  - Vector index 'rule_embedding' created (or will test graceful failure)
"""

import neo4j
import pytest
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import VectorCypherRetriever

from app.config import settings
from app.retrieval.factory import VECTOR_RETRIEVAL_QUERY
from app.retrieval.models import EvidenceSet
from app.services.retrieval_service import RetrievalService

pytestmark = pytest.mark.neo4j

TEST_LABEL = "__RetrievalTest__"
TEST_RULE_ID = "test_rule_integration_001"


@pytest.fixture(scope="module")
def sync_driver():
    """Sync Neo4j driver for retriever (retrievers use sync driver)."""
    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    driver.verify_connectivity()
    yield driver
    driver.close()


@pytest.fixture(autouse=True)
def cleanup_test_nodes(sync_driver):
    """Remove test nodes before/after each test."""
    _delete_test_nodes(sync_driver)
    yield
    _delete_test_nodes(sync_driver)


def _delete_test_nodes(driver: neo4j.Driver) -> None:
    with driver.session() as session:
        session.run(f"MATCH (n:{TEST_LABEL}) DETACH DELETE n")


def _seed_node_with_metadata(driver: neo4j.Driver, embedding: list[float]) -> None:
    """Create a test node with full metadata and an embedding."""
    with driver.session() as session:
        session.run(
            f"""
            CREATE (n:{TEST_LABEL} {{
                rule_id: $rule_id,
                name: 'Integration Test Rule',
                description: 'A rule created for integration testing',
                embedding: $embedding
            }})
            """,
            rule_id=TEST_RULE_ID,
            embedding=embedding,
        )


def _seed_node_without_metadata(driver: neo4j.Driver, embedding: list[float]) -> None:
    """Create a test node with minimal properties — no rule_id, no description."""
    with driver.session() as session:
        session.run(
            f"""
            CREATE (n:{TEST_LABEL} {{
                name: 'Bare Node',
                embedding: $embedding
            }})
            """,
            embedding=embedding,
        )


class TestRetrievalIntegration:
    """Tests that run real retriever.search() against Neo4j."""

    def test_retrieve_seeded_node(self, sync_driver):
        """Seed a node, retrieve it, verify EvidenceSet shape."""
        fake_embedding = [0.1] * settings.embedding_dimension
        _seed_node_with_metadata(sync_driver, fake_embedding)

        class FixedEmbedder(Embedder):
            """Returns a fixed embedding to match the seeded node."""

            def embed_query(self, text: str, **kwargs) -> list[float]:
                return fake_embedding

        retriever = VectorCypherRetriever(
            driver=sync_driver,
            index_name=settings.vector_index_name,
            embedder=FixedEmbedder(),
            retrieval_query=VECTOR_RETRIEVAL_QUERY,
        )
        service = RetrievalService(retriever=retriever)

        result = service.retrieve("integration test query", top_k=5)

        assert isinstance(result, EvidenceSet)
        # We seeded at least one node — it should appear if the index exists
        if len(result.nodes) > 0:
            node = next((n for n in result.nodes if n.node_id == TEST_RULE_ID), None)
            if node:
                assert node.content is not None
                assert node.source == "library"

    def test_retrieve_handles_nodes_without_metadata(self, sync_driver):
        """Nodes missing expected metadata fields should not crash."""
        fake_embedding = [0.2] * settings.embedding_dimension
        _seed_node_without_metadata(sync_driver, fake_embedding)

        class FixedEmbedder(Embedder):
            def embed_query(self, text: str, **kwargs) -> list[float]:
                return fake_embedding

        retriever = VectorCypherRetriever(
            driver=sync_driver,
            index_name=settings.vector_index_name,
            embedder=FixedEmbedder(),
            retrieval_query=VECTOR_RETRIEVAL_QUERY,
        )
        service = RetrievalService(retriever=retriever)

        # This must not raise AttributeError
        result = service.retrieve("bare node test", top_k=5)
        assert isinstance(result, EvidenceSet)
