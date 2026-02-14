import asyncio
import logging
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.graph.connection import connect, disconnect, get_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_indexes")


async def create_indexes(database: str):
    logger.info(f"Creating indexes in database: {database}")

    async with get_session(database=database) as session:
        # 1. Vector Index for Chunks (Element)
        # 1536 for OpenAI, 768 for E5/Jina, 384 for MiniLM
        # We use settings.embedding_dimension
        logger.info(
            f"Creating Vector Index '{settings.vector_index_name}' for Element(embedding)..."
        )

        # Check if index exists first to avoid error or just use IF NOT EXISTS
        # Note: Cypher syntax for vector index creation varies by version, assuming 5.x standard
        vector_query = f"""
        CREATE VECTOR INDEX {settings.vector_index_name} IF NOT EXISTS
        FOR (n:Element) ON (n.embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {settings.embedding_dimension},
            `vector.similarity_function`: 'cosine'
        }}}}
        """
        try:
            await session.run(vector_query)
            logger.info("Vector index created (or already exists).")
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")

        # 2. Fulltext Index for Entities (Entity)
        # Used for Hybrid Search / Keyword Search
        logger.info(
            f"Creating Fulltext Index '{settings.fulltext_index_name}' for Entity(name, description)..."
        )
        fulltext_query = f"""
        CREATE FULLTEXT INDEX {settings.fulltext_index_name} IF NOT EXISTS
        FOR (n:Entity) ON EACH [n.name, n.description, n.label]
        """
        try:
            await session.run(fulltext_query)
            logger.info("Fulltext index created (or already exists).")
        except Exception as e:
            logger.error(f"Failed to create fulltext index: {e}")

        # 3. Constraint on Entity Name (optional but good for graph build performance)
        logger.info("Creating constraint on Entity name...")
        constraint_query = """
        CREATE CONSTRAINT entity_name_unique IF NOT EXISTS
        FOR (e:Entity) REQUIRE e.name IS UNIQUE
        """
        try:
            await session.run(constraint_query)
            logger.info("Entity uniqueness constraint created.")
        except Exception as e:
            # Just a warning, not critical for partial matching
            logger.warning(
                f"Could not create unique constraint (might duplicate names): {e}"
            )


async def main():
    await connect()
    try:
        # By default use the query_database setting, but can be overridden
        # In this context, we definitely want to prepare the 'graphrag' database we just ingested into
        target_db = settings.query_database
        if target_db == "neo4j":
            # If user hasn't switched yet, but asked about 'graphrag' db readiness
            target_db = "graphrag"

        await create_indexes(database=target_db)
    finally:
        await disconnect()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
