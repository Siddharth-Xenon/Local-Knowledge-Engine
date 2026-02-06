"""Entity API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    """Request to create an entity."""

    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    properties: dict[str, Any] = Field(default_factory=dict)


class EntityResponse(BaseModel):
    """Entity response with metadata."""

    id: str
    name: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class EntityList(BaseModel):
    """List of entities."""

    entities: list[EntityResponse]
    count: int
