"""Core exceptions for Node 1."""

from typing import Any


class Node1Error(Exception):
    """Base exception for Node 1."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PromptNotFoundError(Node1Error):
    """Prompt template not found."""


class PromptRenderError(Node1Error):
    """Failed to render prompt."""
