"""Domain models for retrieval system."""

from pydantic import BaseModel, Field


class NodeResult(BaseModel):
    """A single retrieved node from the knowledge graph."""

    node_id: str = Field(description="Graph node ID")
    content: str = Field(description="Text content of the node")
    node_type: str = Field(description="Type: Entity, Document, Clause, etc.")
    score: float = Field(default=0.0, description="Relevance score (0-1)")
    source: str = Field(
        default="unknown", description="Retrieval source: 'graph' or 'semantic'"
    )


class EvidenceSet(BaseModel):
    """Collection of retrieved evidence nodes."""

    nodes: list[NodeResult] = Field(default_factory=list, description="Retrieved nodes")
    query: str = Field(description="Original query")
    graph_count: int = Field(default=0, description="Nodes from graph retrieval")
    semantic_count: int = Field(default=0, description="Nodes from semantic retrieval")
    metadata: dict = Field(default={}, description="Metadata of the node")


class StructuredContext(BaseModel):
    """LLM-ready formatted evidence with source tracking."""

    formatted: str = Field(description="Formatted evidence: E1: [type] content...")
    evidence_ids: list = Field(
        default=[], description="Evidence IDs: ['E1', 'E2', ...]"
    )
    token_count: int = Field(default=0, description="Approximate token count")
    sources: list = Field(default=[], description="Original node IDs for audit trail")
    metadata: dict = Field(default={}, description="Metadata of the node")
