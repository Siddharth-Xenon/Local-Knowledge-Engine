"""Entity CRUD endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.api.schemas.entity import EntityCreate, EntityList, EntityResponse
from app.graph.repository import GraphRepository

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(request: EntityCreate) -> EntityResponse:
    """Create a new entity node."""
    properties = {
        "name": request.name,
        "type": request.type,
        "created_at": datetime.now(UTC).isoformat(),
        **request.properties,
    }

    node_id = await GraphRepository.create_node("Entity", properties)

    return EntityResponse(
        id=node_id,
        name=request.name,
        type=request.type,
        properties=request.properties,
        created_at=datetime.now(UTC),
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str) -> EntityResponse:
    """Get an entity by ID."""
    node = await GraphRepository.get_node(entity_id)

    if not node:
        raise HTTPException(status_code=404, detail="Entity not found")

    return EntityResponse(
        id=node.get("id", entity_id),
        name=node.get("name", ""),
        type=node.get("type", ""),
        properties={
            k: v
            for k, v in node.items()
            if k not in ("id", "name", "type", "created_at", "_labels")
        },
        created_at=node.get("created_at"),
    )


@router.get("", response_model=EntityList)
async def list_entities(
    type: str | None = None,
    limit: int = 100,
) -> EntityList:
    """List entities with optional type filter."""
    filters = {}
    if type:
        filters["type"] = type

    nodes = await GraphRepository.query_nodes(
        label="Entity",
        filters=filters if filters else None,
        limit=limit,
    )

    entities = [
        EntityResponse(
            id=n.get("id", ""),
            name=n.get("name", ""),
            type=n.get("type", ""),
            properties={
                k: v
                for k, v in n.items()
                if k not in ("id", "name", "type", "created_at", "_labels")
            },
            created_at=n.get("created_at"),
        )
        for n in nodes
    ]

    return EntityList(entities=entities, count=len(entities))
