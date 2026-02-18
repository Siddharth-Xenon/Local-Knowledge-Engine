from enum import Enum


class ThinkingLevel(str, Enum):
    """Enum for Gemini thinking levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MINIMAL = "MINIMAL"
