from __future__ import annotations

import logging
import time
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
        """Verify a single claim (convenience wrapper for batch)."""
        results = await self.verify_batch([claim])
        return results[0]

    async def verify_batch(self, claims: list[Claim]) -> list[VerificationResult]:
        """Verify multiple claims in a single batch query.

        Drastically reduces round-trips compared to verifying one by one.
        """
        if not claims:
            return []

        start = time.monotonic()
        try:
            results = await self._check_edges_batch(claims)
            duration = time.monotonic() - start
            logger.info(
                "Graph verification batch for %d claims took %.3fs",
                len(claims),
                duration,
            )
            return results
        except Exception as e:
            logger.warning("Batch verification failed: %s", e)
            # Fallback to unsupported for all if batch fails
            return [
                VerificationResult(
                    claim=c,
                    outcome=VerificationOutcome.UNSUPPORTED,
                    confidence=0.0,
                    reason=f"Batch verification error: {e}",
                )
                for c in claims
            ]

    async def _check_edges_batch(self, claims: list[Claim]) -> list[VerificationResult]:
        """Run a single Cypher query for all claims and process results."""
        batch_params = [
            {"id": c.claim_id, "subject": c.subject, "object": c.object_}
            for c in claims
        ]

        # UNWIND batch to check all S-O pairs at once
        # Matches in both directions: (s)-[r]-(o)
        query = """
        UNWIND $batch AS item
        MATCH (s) WHERE s.name = item.subject OR s.id = item.subject
        MATCH (o) WHERE o.name = item.object OR o.id = item.object
        MATCH (s)-[r]-(o)
        RETURN item.id AS claim_id,
                type(r) AS rel_type,
                startNode(r) = s AS is_forward
        """

        query_start = time.monotonic()
        results = self._run_query(query, {"batch": batch_params})
        query_duration = time.monotonic() - query_start
        logger.debug(
            "Graph Cypher query took %.3fs for %d items", query_duration, len(claims)
        )

        # Group edges by claim_id
        from collections import defaultdict

        edges_by_claim = defaultdict(list)
        for row in results:
            edges_by_claim[row["claim_id"]].append(row)

        # Determine outcome for each claim
        return [
            self._determine_outcome(claim, edges_by_claim[claim.claim_id])
            for claim in claims
        ]

    def _determine_outcome(self, claim: Claim, edges: list[dict]) -> VerificationResult:
        """Evaluate edges to determine outcome.

        Possibilities: SUPPORTED, CONTRADICTED, AMBIGUOUS, or UNSUPPORTED.
        """
        # 1. Forward edges (s -> o)
        forward_edges = [e for e in edges if e["is_forward"]]
        matches = [
            e
            for e in forward_edges
            if self._predicate_matches(claim.predicate, e["rel_type"])
        ]

        if matches:
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.SUPPORTED,
                confidence=0.95,
                evidence_used=[f"edge:{e['rel_type']}" for e in matches],
                reason=f"Graph edge confirms: {matches[0]['rel_type']}",
            )

        if forward_edges:
            # Edges exist in correct direction but types don't match
            # This is AMBIGUOUS unless we want to be strict
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.AMBIGUOUS,
                confidence=0.4,
                evidence_used=[f"edge:{e['rel_type']}" for e in forward_edges],
                reason=(
                    f"Edge exists but type mismatch: "
                    f"found {[e['rel_type'] for e in forward_edges]}, "
                    f"expected {claim.predicate}"
                ),
            )

        # 2. Reverse edges (o -> s)
        reverse_edges = [e for e in edges if not e["is_forward"]]
        reverse_matches = [
            e
            for e in reverse_edges
            if self._predicate_matches(claim.predicate, e["rel_type"])
        ]

        if reverse_matches:
            return VerificationResult(
                claim=claim,
                outcome=VerificationOutcome.CONTRADICTED,
                confidence=0.7,
                evidence_used=[
                    f"edge:{e['rel_type']}(reversed)" for e in reverse_matches
                ],
                reason="Relationship exists but in opposite direction",
            )

        # 3. No relevant edges found
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
