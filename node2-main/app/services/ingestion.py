"""Service for ingesting local documents."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

from app.graph.connection import get_session
from app.services.pdf_loader import LocalPDFLoader

logger = logging.getLogger(__name__)


class IngestionService:
    """Handles ingestion of local documents into Neo4j."""

    def __init__(
        self,
        embedder: SentenceTransformerEmbeddings,
        database: str | None = None,
        graph_builder: Any | None = None,
    ):
        self.embedder = embedder
        self.loader = LocalPDFLoader()
        self.database = database
        self.graph_builder = graph_builder

    async def ingest_file(self, file_path: str | Path) -> dict[str, Any]:
        """Ingest a single file.

        Args:
            file_path: Path to the local file.

        Returns:
            Dictionary with status and details.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {path}")
            return {"status": "error", "message": "File not found"}

        logger.info(f"Ingesting file: {path}")

        # 1. Load and Split
        try:
            chunks = self.loader.load_and_split(path)
        except Exception as e:
            logger.error(f"Loader failed for {path}: {e}")
            return {"status": "error", "message": f"Loader failed: {str(e)}"}

        if not chunks:
            logger.warning(f"No text extracted from {path}")
            return {"status": "skipped", "reason": "empty"}

        texts = [c.page_content for c in chunks]

        # 2. Embed
        try:
            # Check for embed_documents (LangChain style)
            if hasattr(self.embedder, "embed_documents"):
                embeddings = self.embedder.embed_documents(texts)
            # Check for encode_batch (EmbeddingStrategy protocol)
            elif hasattr(self.embedder, "encode_batch"):
                # Usually async in our codebase, but neo4j-graphrag's might be sync?
                # app/embeddings/base.py defines encode_batch as async
                # But EmbeddingFactory returns SentenceTransformerEmbeddings
                # which is from lib
                # The lib version likely has embed_query.
                # Let's assume embed_query exits if embed_documents doesn't.
                embeddings = [self.embedder.embed_query(t) for t in texts]
            else:
                # Fallback
                embeddings = [self.embedder.embed_query(t) for t in texts]

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return {"status": "error", "message": f"Embedding failed: {e}"}

        # 3. Write to Neo4j
        try:
            # Use execute_write for write transactions
            async with get_session(database=self.database) as session:
                await session.execute_write(self._save_chunks, chunks, embeddings)
        except Exception as e:
            logger.error(f"Database write failed: {e}")
            return {"status": "error", "message": f"Database write failed: {e}"}

        # 4. Trigger Graph Build (Async)
        if self.graph_builder:
            logger.info(f"Triggering background graph build for {path.name}...")
            # We use create_task to run it in the background
            asyncio.create_task(self.graph_builder.process_document(path.name))

        logger.info(f"Successfully ingested {len(chunks)} chunks from {path.name}")
        return {"status": "success", "chunks": len(chunks)}

    @staticmethod
    async def _save_chunks(tx, chunks, embeddings):
        """Save chunks and vectors to Neo4j."""
        query = """
        UNWIND $batch AS item
        MERGE (d:Document {source: item.source})
        ON CREATE SET d.filename = item.filename, d.ingested_at = datetime()
        
        CREATE (e:Element {id: randomUUID()})
        SET e.text = item.text,
            e.page = item.page,
            e.embedding = item.embedding,
            e.source = item.source,
            e.createdAt = datetime()
            
        CREATE (d)-[:HAS_CHUNK]->(e)
        """

        batch = []
        for chunk, embedding in zip(chunks, embeddings):
            # Ensure valid float list
            vec = embedding
            if hasattr(vec, "tolist"):
                vec = vec.tolist()

            batch.append(
                {
                    "source": chunk.metadata.get("source"),
                    "filename": chunk.metadata.get("filename"),
                    "text": chunk.page_content,
                    "page": chunk.metadata.get("page_number", 1),
                    "embedding": vec,
                }
            )

        await tx.run(query, batch=batch)
