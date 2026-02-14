"""CLI script to build knowledge graph from ingested documents."""

import argparse
import asyncio
import logging
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.connection import connect, disconnect
from app.services.graph_builder import GraphBuilderService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_graph")


async def main():
    parser = argparse.ArgumentParser(
        description="Build Knowledge Graph from Ingested Documents"
    )
    parser.add_argument(
        "--file", help="Specific filename to process (e.g., 'doc.pdf')", default=None
    )
    parser.add_argument(
        "--all", action="store_true", help="Process all documents in database"
    )

    args = parser.parse_args()

    if not args.file and not args.all:
        logger.error("Must specify --file or --all")
        return

    # Initialize Neo4j
    logger.info("Connecting to Neo4j...")
    try:
        await connect()
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return

    try:
        logger.info("Initializing Graph Builder...")
        service = GraphBuilderService(database="graphrag")

        if args.file:
            logger.info(f"Processing single file: {args.file}")
            result = await service.process_document(args.file)
            logger.info(f"Result: {result}")

        elif args.all:
            # TODO: Fetch all filenames from DB and process them
            logger.warning("--all not fully implemented yet, use --file")
            pass

    except Exception as e:
        logger.error(f"Graph build failed: {e}")
    finally:
        await disconnect()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
