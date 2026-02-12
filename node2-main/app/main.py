"""Node 2 Main Application - Knowledge Engine Core."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import neo4j
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import entities, health, query
from app.config import settings
from app.core import KnowledgeEngineError
from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import connect, disconnect
from app.retrieval.context_packager import ContextPackager
from app.retrieval.factory import RetrieverFactory
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # === STARTUP ===

    # 1. Connect to Neo4j (async driver for existing graph operations)
    await connect()
    logger.info("Connected to Neo4j (async)")

    # 2. Create sync Neo4j driver for library retrievers
    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    driver.verify_connectivity()
    logger.info("Connected to Neo4j (sync driver for retrievers)")

    # 3. Create embedder (neo4j-graphrag SentenceTransformerEmbeddings)
    embedder = EmbeddingFactory.create()
    logger.info(f"Embedder: {settings.embedding_model_name}")

    # 4. Create retriever from config
    retriever = RetrieverFactory.create(
        driver=driver,
        embedder=embedder,
        retriever_type=settings.retriever_type,
    )
    logger.info(f"Retriever: {settings.retriever_type}")

    # 5. Create service
    packager = ContextPackager()
    service = RetrievalService(retriever=retriever, packager=packager)

    # 6. Store in app state for dependency injection
    app.state.driver = driver
    app.state.embedder = embedder
    app.state.retrieval_service = service

    logger.info("Retrieval system initialized")

    yield

    # === SHUTDOWN ===
    driver.close()
    logger.info("Closed sync Neo4j driver")
    await disconnect()
    logger.info("Disconnected from Neo4j (async)")


app = FastAPI(
    title="Node 2 - Knowledge Engine",
    description="Main application for Local Knowledge Engine (GTX 1660)",
    version="0.3.0",
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
        "version": "0.3.0",
    }


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host=settings.host, port=settings.port)
