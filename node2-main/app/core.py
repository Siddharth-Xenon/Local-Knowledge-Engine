"""Core utilities: exceptions and timeouts."""

from typing import Any


class KnowledgeEngineError(Exception):
    """Base exception for Knowledge Engine."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class GraphConnectionError(KnowledgeEngineError):
    """Failed to connect to Neo4j."""


class InferenceTimeoutError(KnowledgeEngineError):
    """Inference request timed out."""


class InferenceUnavailableError(KnowledgeEngineError):
    """Node 1 inference server is unavailable."""


# Timeout constants (seconds)
GRAPH_OPERATION_TIMEOUT = 5
INFERENCE_TIMEOUT = 60
HEALTH_CHECK_TIMEOUT = 5
