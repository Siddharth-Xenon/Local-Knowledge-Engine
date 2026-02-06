"""Metrics for evaluating embedding model performance."""

import numpy as np
from numpy.typing import NDArray


def cosine_similarity(vec_a: NDArray[np.float32], vec_b: NDArray[np.float32]) -> float:
    """Calculate cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    dot_product = np.dot(vec_a, vec_b)
    return float(dot_product / (norm_a * norm_b))


def calculate_mrr(results: list[dict], correct_node_id: str, top_k: int = 10) -> float:
    """Calculate Mean Reciprocal Rank (MRR) for a single query.

    Args:
        results: List of result nodes/dicts with 'id' field.
        correct_node_id: The ID of the target node.
        top_k: Maximum rank to consider.

    Returns:
        1/rank if found (1-based index), 0.0 otherwise.
    """
    for i, result in enumerate(results[:top_k]):
        if result.get("id") == correct_node_id:
            return 1.0 / (i + 1)
    return 0.0


def calculate_pollution_rate(
    results: list[dict], query_node_metadata: dict, top_k: int = 5
) -> float:
    """Calculate Top-K Pollution Rate.

    Heuristic: Checks if top-K results share the same primary label
    as the query node.

    Args:
        results: List of retrieved result nodes.
        query_node_metadata: Metadata of the query node (must have '_labels').
        top_k: Number of results to check.

    Returns:
        Pollution rate as a float (0.0 to 1.0).
    """
    if not results:
        return 0.0

    query_labels = set(query_node_metadata.get("_labels", []))
    if not query_labels:
        # If query has no labels, we can't judge pollution easily.
        # Assume no pollution (conservative) or 100% pollution?
        # Conservative: 0.0
        return 0.0

    polluted_count = 0
    checked_count = 0

    for result in results[:top_k]:
        result_labels = set(result.get("_labels", []))
        # Basic check: Intersection should not be empty for critical types
        # Refine this heuristic based on real data later.
        if not query_labels.intersection(result_labels):
            polluted_count += 1
        checked_count += 1

    return polluted_count / checked_count if checked_count > 0 else 0.0


def check_deterministic_stability(
    vec_a: NDArray[np.float32], vec_b: NDArray[np.float32], epsilon: float = 0.0001
) -> tuple[bool, float]:
    """Check if two vectors are effectively identical.

    Returns:
        (is_stable, similarity_score)
    """
    sim = cosine_similarity(vec_a, vec_b)
    is_stable = sim >= (1.0 - epsilon)
    return is_stable, sim
