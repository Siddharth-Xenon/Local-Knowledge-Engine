"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.repository import GraphRepository
from app.inference.client import inference_client

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health check response."""

    status: str
    neo4j: str | None = None
    node1: str | None = None


@router.get("", response_model=HealthStatus)
async def health() -> HealthStatus:
    """Basic health check."""
    return HealthStatus(status="ok")


@router.get("/db", response_model=HealthStatus)
async def health_db() -> HealthStatus:
    """Check Neo4j database connectivity."""
    is_healthy = await GraphRepository.health_check()
    return HealthStatus(
        status="ok" if is_healthy else "error",
        neo4j="connected" if is_healthy else "disconnected",
    )


@router.get("/inference", response_model=HealthStatus)
async def health_inference() -> HealthStatus:
    """Check Node 1 inference server reachability."""
    is_healthy = await inference_client.health_check()
    return HealthStatus(
        status="ok" if is_healthy else "error",
        node1="reachable" if is_healthy else "unreachable",
    )
