"""Context packager - transforms EvidenceSet to LLM-ready StructuredContext."""

from app.retrieval.models import EvidenceSet, StructuredContext


class ContextPackager:
    """Packages evidence into LLM-consumable format.

    Assigns evidence IDs (E1, E2, ...), formats content with types,
    and tracks sources for audit trail.
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
    ):
        """Initialize context packager.

        Args:
            max_tokens: Maximum tokens in formatted output.
            chars_per_token: Estimate for token counting.
        """
        self._max_tokens = max_tokens
        self._chars_per_token = chars_per_token

    def package(self, evidence: EvidenceSet) -> StructuredContext:
        """Package evidence into structured context.

        Args:
            evidence: EvidenceSet from retriever.

        Returns:
            StructuredContext ready for LLM consumption.
        """
        max_chars = int(self._max_tokens * self._chars_per_token)

        lines: list[str] = []
        evidence_ids: list[str] = []
        sources: list[str] = []
        current_chars = 0

        for i, node in enumerate(evidence.nodes):
            evidence_id = f"E{i + 1}"

            # Format: E1: [Document] Content here...
            formatted_line = f"{evidence_id}: [{node.node_type}] {node.content}"
            line_chars = len(formatted_line)

            # Check token limit
            if current_chars + line_chars > max_chars:
                # Add truncation notice
                lines.append("[TRUNCATED - more evidence available]")
                break

            lines.append(formatted_line)
            evidence_ids.append(evidence_id)
            sources.append(node.node_id)
            current_chars += line_chars + 1  # +1 for newline

        formatted = "\n".join(lines)
        token_count = int(len(formatted) / self._chars_per_token)

        return StructuredContext(
            formatted=formatted,
            evidence_ids=evidence_ids,
            token_count=token_count,
            sources=sources,
        )
