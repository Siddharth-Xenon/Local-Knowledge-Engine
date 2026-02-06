"""End-to-end integration tests for retrieval system."""

import pytest
from app.api.routes.query import QueryRequest
from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import Neo4jConnection
from app.graph.repository import GraphRepository
from app.index.factory import IndexFactory
from app.main import app
from app.retrieval.factory import RetrieverFactory
from app.services.retrieval_service import RetrievalService
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def setup_neo4j():
    """Setup and teardown Neo4j connection."""
    await Neo4jConnection.connect()
    yield
    await Neo4jConnection.disconnect()


@pytest.mark.asyncio
async def test_graph_retrieval_e2e(setup_neo4j):
    """Test graph retrieval via service."""
    # 1. Create a test node in Neo4j
    node_id = await GraphRepository.create_node(
        "Policy", {"name": "Test Policy", "content": "This is a test policy content."}
    )

    try:
        # 2. Setup service (using mock embedding/memory index for speed)
        embedding = EmbeddingFactory.create("mock")
        index = IndexFactory.create("memory")
        retriever = RetrieverFactory.create(
            embedding=embedding,
            index=index,
            retriever_type="graph",
        )
        service = RetrievalService(retriever=retriever)

        # 3. Retrieve using entity ID
        result = await service.retrieve_and_package(
            query="irrelevant",  # Graph retrieval follows links irrespective of query
            entity_ids=[node_id],
        )

        # 4. Verify
        # Note: GraphRetriever currently traverses *neighbors*.
        # If we start at node_id, does it return the node itself?
        # The Cypher query in graph.py returns `COALESCE(related, start)`.
        # So it should return the start node if it meets criteria.

        assert len(result.evidence_ids) > 0
        assert node_id in result.sources
        assert "Test Policy" in result.formatted

    finally:
        # Cleanup could be added here if we had a delete method
        pass


@pytest.mark.asyncio
async def test_semantic_retrieval_e2e(setup_neo4j):
    """Test semantic retrieval via service."""
    # 1. Create a test node
    node_id = await GraphRepository.create_node(
        "Rule",
        {"name": "Test Rule", "content": "Special rule for high value transactions."},
    )

    try:
        # 2. Setup service and POPULATE index
        embedding = EmbeddingFactory.create("mock")
        index = IndexFactory.create("memory")

        # Add vector to index
        vector = await embedding.encode("Special rule for high value transactions.")
        await index.add(node_id, vector)

        retriever = RetrieverFactory.create(
            embedding=embedding,
            index=index,
            retriever_type="semantic",
        )
        service = RetrievalService(retriever=retriever)

        # 3. Retrieve using query matches content
        result = await service.retrieve_and_package(
            query="high value transactions",
        )

        # 4. Verify
        assert len(result.evidence_ids) > 0
        assert node_id in result.sources
        assert "Test Rule" in result.formatted

    finally:
        pass


@pytest.mark.asyncio
async def test_api_query_endpoint(client, setup_neo4j):
    """Test the /query API endpoint."""
    # Note: The API uses app.state which is initialized in lifespan.
    # TestClient with lifespan context manager handles this.

    with TestClient(app) as local_client:
        # 1. Create data (we need to populate the app's index)
        # Access the index from app state
        index = app.state.index
        embedding = app.state.embedding

        # Create node
        node_id = await GraphRepository.create_node(
            "Account",
            {"name": "Savings Account", "content": "Standard savings account details."},
        )

        # Add to index
        vec = await embedding.encode("Standard savings account details.")
        await index.add(node_id, vec)

        # 2. Call API
        response = local_client.post(
            "/query", json={"query": "savings account details"}
        )

        # 3. Verify
        assert response.status_code == 200
        data = response.json()
        context = data["context"]

        assert len(context["evidence_ids"]) > 0
        assert "Savings Account" in context["formatted"]
