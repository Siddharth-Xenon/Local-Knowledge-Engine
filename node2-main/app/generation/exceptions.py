"""Exceptions for the Generation Module."""

from typing import Any
from app.core import KnowledgeEngineError


class PromptError(KnowledgeEngineError):
    """Base error for prompt operations."""


class PromptNotFoundError(PromptError):
    """Prompt template not found."""


class PromptRenderError(PromptError):
    """Failed to render prompt."""
