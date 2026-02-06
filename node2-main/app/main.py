"""Node 2 Main Application - Knowledge Engine Core."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import entities, health, query
from app.config import settings
from app.core import KnowledgeEngineError
from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import connect, disconnect
from app.index.factory import IndexFactory
from app.retrieval.context_packager import ContextPackager
from app.retrieval.factory import RetrieverFactory
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # === STARTUP ===

    # 1. Connect to Neo4j
    await connect()
    logger.info("Connected to Neo4j")

    # 2. Initialize embedding model (lazy loaded on first use)
    embedding = EmbeddingFactory.create()
    logger.info(f"Embedding strategy: {settings.embedding_type}")

    # 3. Initialize vector index
    index = IndexFactory.create()

    # 4. Load index from disk if exists
    index_path = Path(settings.index_path)
    if index_path.exists():
        await index.load(str(index_path))
        logger.info(f"Loaded index from {index_path} ({index.size} vectors)")
    else:
        logger.info("No existing index found, starting fresh")

    # 5. Warm up embedding model (encode dummy text)
    try:
        _ = await embedding.encode("warmup")
        logger.info("Embedding model warmed up")
    except Exception as e:
        logger.warning(f"Embedding warmup failed: {e}")

    # 6. Create retriever and service
    retriever = RetrieverFactory.create(embedding=embedding, index=index)
    packager = ContextPackager()
    service = RetrievalService(retriever=retriever, packager=packager)

    # 7. Store in app state for dependency injection
    app.state.embedding = embedding
    app.state.index = index
    app.state.retrieval_service = service

    logger.info("Retrieval system initialized")

    yield

    # === SHUTDOWN ===

    # 1. Save index to disk
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        await app.state.index.save(str(index_path))
        logger.info(f"Saved index to {index_path}")
    except Exception as e:
        logger.error(f"Failed to save index: {e}")

    # 2. Disconnect from Neo4j
    await disconnect()
    logger.info("Disconnected from Neo4j")


app = FastAPI(
    title="Node 2 - Knowledge Engine",
    description="Main application for Local Knowledge Engine (GTX 1660)",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(KnowledgeEngineError)
async def knowledge_engine_error_handler(
    request: Request,
    exc: KnowledgeEngineError,
) -> JSONResponse:
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


# Include routers
app.include_router(health.router)
app.include_router(entities.router)
app.include_router(query.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Node 2 Knowledge Engine",
        "status": "running",
        "version": "0.2.0",
    }


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host=settings.host, port=settings.port)
