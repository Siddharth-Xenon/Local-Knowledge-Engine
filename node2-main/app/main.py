"""Node 2 Main Application - Knowledge Engine Core."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import neo4j
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j_graphrag.llm.openai_llm import OpenAILLM

from fastapi.staticfiles import StaticFiles

from app.api.routes import entities, health, query
from app.config import settings
from app.core import KnowledgeEngineError
from app.embeddings.factory import EmbeddingFactory
from app.graph.connection import connect, disconnect
from app.inference.llm_adapter import Node1ChatModel
from app.pipeline.graph import build_pipeline
from app.pipeline.nodes import PipelineNodes
from app.retrieval.context_packager import ContextPackager
from app.retrieval.factory import RetrieverFactory
from app.services.query_service import QueryService
from app.services.retrieval_service import RetrievalService
from app.verification.claim_extractor import ClaimExtractor
from app.verification.graph_verifier import GraphVerifier
from app.verification.semantic_verifier import SemanticVerifier
from app.verification.verifier import Verifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # === STARTUP ===

    # 0. Enable LangSmith tracing if configured
    if settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        logger.info(
            "LangSmith tracing enabled (project: %s)",
            settings.langsmith_project,
        )

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
    retriver_llm = OpenAILLM(
        model_name=settings.llm_config["retriever_llm"], api_key=settings.openai_api_key
    )
    claim_extractor_llm = OpenAILLM(
        model_name=settings.llm_config["claim_extractor_llm"],
        api_key=settings.openai_api_key,
    )
    llm = OpenAILLM(
        model_name=settings.llm_config["query_llm"], api_key=settings.openai_api_key
    )

    retriever = RetrieverFactory.create(
        driver=driver,
        embedder=embedder,
        retriever_type=settings.retriever_type,
        llm=retriver_llm,
    )
    logger.info(f"Retriever: {settings.retriever_type}")

    # 5. Create retrieval service
    packager = ContextPackager()
    retrieval_service = RetrievalService(retriever=retriever, packager=packager)

    # 6. Create verification pipeline
    # llm = Node1ChatModel()
    claim_extractor = ClaimExtractor(llm=claim_extractor_llm)
    graph_verifier = GraphVerifier(driver=driver, database=settings.query_database)
    semantic_verifier = SemanticVerifier(embedder=embedder)
    verifier = Verifier(
        graph_verifier=graph_verifier,
        semantic_verifier=semantic_verifier,
    )

    nodes = PipelineNodes(
        retrieval_service=retrieval_service,
        llm=llm,
        claim_extractor=claim_extractor,
        verifier=verifier,
    )
    pipeline = build_pipeline(nodes)
    query_service = QueryService(pipeline)

    # 7. Store in app state for dependency injection
    app.state.driver = driver
    app.state.embedder = embedder
    app.state.retrieval_service = retrieval_service
    app.state.query_service = query_service

    logger.info("Verification pipeline initialized")

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


# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/ui")
async def ui():
    """Serve the Single-Page Application."""
    from fastapi.responses import FileResponse

    return FileResponse("app/static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
