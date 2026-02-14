"""Graph verifier — verifies claims against Neo4j knowledge graph edges.

Layer 1 verification (GOAL.md §11.3): edge existence, direction, type match.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.verification.models import Claim, VerificationOutcome, VerificationResult

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)

# Cypher query to check if a relationship exists between subject and object
_EDGE_CHECK_QUERY = """
MATCH (s)-[r]->(o)
WHERE (s.name = $subject OR s.id = $subject)
  AND (o.name = $object OR o.id = $object)
RETURN type(r) AS rel_type, s.name AS source, o.name AS target
LIMIT 5
"""

# Reverse direction check — does the edge exist in the opposite direction?
_REVERSE_EDGE_QUERY = """
MATCH (o)-[r]->(s)
WHERE (s.name = $subject OR s.id = $subject)
  AND (o.name = $object OR o.id = $object)
RETURN type(r) AS rel_type, o.name AS source, s.name AS target
LIMIT 5
"""


class GraphVerifier:
    """Verifies claims against the Neo4j knowledge graph.

    Checks edge existence, relationship direction, and type match.
    """

    def __init__(self, driver: Driver, database: str = "neo4j") -> None:
        self._driver = driver
        self._database = database

    async def verify(self, claim: Claim) -> VerificationResult:
        """Verify a single claim against the graph.

        Runs Cypher queries to check edge existence between
        the claim's subject and object.
        """
        try:
            return await self._check_edge(claim)
        except Exception as e:
            logger.warning("Graph verification failed for %s: %s", claim.claim_id, e)
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.UNSUPPORTED,
                confidence=0.0,
                reason=f"Graph verification error: {e}",
            )

    async def _check_edge(self, claim: Claim) -> VerificationResult:
        """Check if a graph edge supports the claim."""
        params = {"subject": claim.subject, "object": claim.object_}

        # Forward direction check
        forward_results = self._run_query(_EDGE_CHECK_QUERY, params)

        if forward_results:
            # Check if any relationship type matches the predicate
            matching = [
                r
                for r in forward_results
                if self._predicate_matches(claim.predicate, r["rel_type"])
            ]

            if matching:
                return VerificationResult(
                    claim=claim,
                    outcome=VerificationOutcome.SUPPORTED,
                    confidence=0.95,
                    evidence_used=[f"edge:{r['rel_type']}" for r in matching],
                    reason=f"Graph edge confirms: {matching[0]['rel_type']}",
                )

            # Edge exists but different type — might contradict
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.AMBIGUOUS,
                confidence=0.4,
                evidence_used=[f"edge:{r['rel_type']}" for r in forward_results],
                reason=(
                    f"Edge exists but type mismatch: "
                    f"found {forward_results[0]['rel_type']}, "
                    f"expected {claim.predicate}"
                ),
            )

        # Check reverse direction — could indicate contradiction
        reverse_results = self._run_query(_REVERSE_EDGE_QUERY, params)
        if reverse_results:
            matching_reverse = [
                r
                for r in reverse_results
                if self._predicate_matches(claim.predicate, r["rel_type"])
            ]
            if matching_reverse:
                return VerificationResult(
                    claim=claim,
                    outcome=VerificationOutcome.CONTRADICTED,
                    confidence=0.7,
                    evidence_used=[
                        f"edge:{r['rel_type']}(reversed)" for r in matching_reverse
                    ],
                    reason="Relationship exists but in opposite direction",
                )

        # No edges found at all
        return VerificationResult(
            claim=claim,
            outcome=VerificationOutcome.UNSUPPORTED,
            confidence=0.0,
            reason="No graph edge found between subject and object",
        )

    def _run_query(self, query: str, params: dict) -> list[dict]:
        """Execute a Cypher query and return results as dicts."""
        with self._driver.session(database=self._database) as session:
            result = session.run(query, params)
            return [dict(record) for record in result]

    @staticmethod
    def _predicate_matches(predicate: str, rel_type: str) -> bool:
        """Fuzzy match between a claim predicate and a graph relationship type.

        Normalizes both to lowercase and checks containment in either direction.
        """
        pred = predicate.lower().replace(" ", "_")
        rel = rel_type.lower()
        return pred in rel or rel in pred
