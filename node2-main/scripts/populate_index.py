"""Populate Neo4j vector indexes from existing graph nodes.

Usage:
    cd node2-main
    venv\\Scripts\\activate
    python -m scripts.populate_index
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path for app imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import connect, disconnect
from app.services.embedding_service import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("populate_index")


async def main() -> None:
    """Connect to Neo4j, embed nodes, store vectors in graph."""
    logger.info("Starting Neo4j vector index population...")

    # 1. Connect to Neo4j
    await connect()
    logger.info(f"Connected to Neo4j at {settings.neo4j_uri}")

    try:
        # 2. Create embedding model
        embedding = EmbeddingFactory.create()
        logger.info(
            f"Embedding: {settings.embedding_type} "
            f"({settings.embedding_model_name}, dim={settings.embedding_dimension})"
        )

        # 3. Warm up model
        _ = await embedding.encode("warmup")
        logger.info("Embedding model warmed up")

        # 4. Create vector indexes
        service = EmbeddingService(embedding=embedding)
        await service.create_vector_indexes()

        # 5. Populate embeddings
        count = await service.populate()

        if count == 0:
            logger.warning("No nodes were embedded. Is the graph seeded?")
            return

        logger.info(f"Done. {count} nodes embedded into Neo4j.")

    finally:
        await disconnect()
        logger.info("Disconnected from Neo4j")


if __name__ == "__main__":
    asyncio.run(main())
