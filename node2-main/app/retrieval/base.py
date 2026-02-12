"""Retriever type aliases for internal usage.

The actual retriever implementations come from neo4j-graphrag library.
This module provides type aliases and the protocol for internal code.
"""

from __future__ import annotations

from neo4j_graphrag.retrievers import (
    HybridCypherRetriever,
    Text2CypherRetriever,
    VectorCypherRetriever,
)

# Type alias for any library retriever
Retriever = VectorCypherRetriever | Text2CypherRetriever | HybridCypherRetriever
