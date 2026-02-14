import asyncio
import logging
import uuid
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.connection import connect, disconnect, get_session
from app.services.graph_builder import (
    GraphBuilderService,
    GraphExtraction,
    Entity,
    Relationship,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_cypher")


async def main():
    logger.info("Connecting to Neo4j...")
    await connect()

    service = GraphBuilderService(database="graphrag")

    # Test Data
    chunk_id = str(uuid.uuid4())
    source_doc = "test_verification.pdf"

    extraction = GraphExtraction(
        entities=[
            Entity(name="TestPerson", label="Person", description="A test entity"),
            Entity(name="TestOrg", label="Organization"),
            Entity(name="NewEntity", label="Concept"),  # Entity not in Source/Target
        ],
        relationships=[
            Relationship(
                source="TestPerson",
                target="TestOrg",
                type="WORKS_FOR",
                description="Test relationship",
            ),
            Relationship(
                source="TestPerson",
                target="NonExistentEntity",  # Test implicit creation
                type="KNOWS",
            ),
        ],
    )

    try:
        # 1. Create a Dummy Chunk
        logger.info(f"Creating dummy chunk {chunk_id}...")
        async with get_session(database="graphrag") as session:
            await session.run(
                "CREATE (c:Element {id: $id, text: 'Test content', source: $source})",
                id=chunk_id,
                source=source_doc,
            )

        # 2. Run _save_graph
        logger.info("Executing _save_graph...")
        await service._save_graph(extraction, chunk_id, source_doc)

        # 3. Verify Results
        logger.info("Verifying data in Neo4j...")
        async with get_session(database="graphrag") as session:
            # Check Entities
            result = await session.run(
                "MATCH (e:Entity {source: $source}) RETURN e.name, e.label",
                source=source_doc,
            )
            entities = [record.data() async for record in result]
            logger.info(f"Entities found: {entities}")

            # Check Relationships
            result = await session.run(
                """
                MATCH (s:Entity)-[r]->(t:Entity) 
                WHERE s.source = $source OR t.source = $source
                RETURN s.name, type(r), t.name
                """,
                source=source_doc,
            )
            rels = [record.data() async for record in result]
            logger.info(f"Relationships found: {rels}")

            # Check MENTIONS
            result = await session.run(
                "MATCH (c:Element {id: $id})-[:MENTIONS]->(e:Entity) RETURN e.name",
                id=chunk_id,
            )
            mentions = [record.data() async for record in result]
            logger.info(f"Mentions found: {len(mentions)} (Expected 3)")

    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        raise e
    finally:
        # Cleanup
        logger.info("Cleaning up test data...")
        async with get_session(database="graphrag") as session:
            await session.run(
                """
                MATCH (n) 
                WHERE n.source = $source OR n.id = $id
                DETACH DELETE n
                """,
                source=source_doc,
                id=chunk_id,
            )
        await disconnect()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
