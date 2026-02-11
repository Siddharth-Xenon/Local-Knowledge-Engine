"""Verify semantic search works via Neo4j vector indexes."""

import asyncio

from app.config import settings
from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import connect, disconnect
from app.retrieval.strategies.semantic import SemanticRetriever


async def main():
    await connect()

    embedding = EmbeddingFactory.create()
    _ = await embedding.encode("warmup")

    retriever = SemanticRetriever(embedding=embedding, top_k=5)

    queries = [
        # "high value cash deposits",
        # "anti money laundering policy",
        # "customer due diligence",
        "Which rules limit the use of cash?",
        "Above what amount of transaction there is a possbility of rule violation?",
    ]

    for q in queries:
        result = await retriever.retrieve(q)
        print(f"\nQuery: '{q}'")
        print(f"  Found {result.semantic_count} results:")
        for node in result.nodes[:3]:
            print(
                f"  [{node.node_type}] {node.node_id}: "
                f"{node.content[:80]}... (score: {node.score:.4f})"
            )

    await disconnect()


asyncio.run(main())
