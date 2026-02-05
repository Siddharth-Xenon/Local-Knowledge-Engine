"""Node 2 Main Application - Knowledge Engine Core."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core import KnowledgeEngineError
from app.graph.connection import connect, disconnect
from app.api.routes import health, entities


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup: Connect to Neo4j
    await connect()
    yield
    # Shutdown: Disconnect from Neo4j
    await disconnect()


app = FastAPI(
    title="Node 2 - Knowledge Engine",
    description="Main application for Local Knowledge Engine (GTX 1660)",
    version="0.1.0",
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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Node 2 Knowledge Engine",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
