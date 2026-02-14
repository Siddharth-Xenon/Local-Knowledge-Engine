"""CLI script to ingest local PDFs."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import connect, disconnect
from app.services.ingestion import IngestionService
from app.services.graph_builder import GraphBuilderService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Silence verbose libraries
logging.getLogger("neo4j_graphrag").setLevel(logging.INFO)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

logger = logging.getLogger("ingest_pdfs")


async def main():
    parser = argparse.ArgumentParser(description="Ingest local PDFs into Neo4j")
    parser.add_argument("path", help="Path to file or folder containing PDFs")

    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        logger.error(f"Invalid path: {path}")
        return

    # Initialize components
    logger.info("Connecting to Neo4j...")
    try:
        await connect()
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return

    try:
        logger.info("Initializing services...")
        # Create embedding model (might download model on first run)
        embedder = EmbeddingFactory.create()

        # Initialize Graph Builder
        graph_builder = GraphBuilderService(database="graphrag")

        # Pass graph_builder to IngestionService
        service = IngestionService(
            embedder, database="graphrag", graph_builder=graph_builder
        )

        pdf_files = []
        if path.is_file():
            if path.suffix.lower() == ".pdf":
                pdf_files = [path]
            else:
                logger.error(f"File {path} is not a PDF")
                return
        else:  # path is a directory
            pdf_files = list(path.glob("**/*.pdf"))

        logger.info(f"Found {len(pdf_files)} PDF file(s)")

        results = {"success": 0, "skipped": 0, "error": 0}

        for pdf_file in pdf_files:
            try:
                print(f"Processing {pdf_file.name}...", end="", flush=True)
                result = await service.ingest_file(pdf_file)
                status = result.get("status", "error")
                results[status] = results.get(status, 0) + 1
                print(f" [{status.upper()}]")
            except Exception as e:
                print(f" [ERROR]")
                logger.error(f"Failed to ingest {pdf_file.name}: {e}")
                results["error"] += 1

        logger.info("Ingestion complete!")
        logger.info(f"Summary: {results}")

        # Wait for any background graph build tasks to complete
        # In a real app these run in background, but for CLI we must wait
        pending = asyncio.all_tasks() - {asyncio.current_task()}
        if pending:
            logger.info(
                f"Waiting for {len(pending)} background tasks (Graph Building)..."
            )
            await asyncio.gather(*pending)

    finally:
        await disconnect()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
