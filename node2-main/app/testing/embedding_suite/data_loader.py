"""Data loading module for retrieving test samples from Neo4j."""

import asyncio
from typing import Any

from app.graph.repository import GraphRepository


class DataLoader:
    """Fetches nodes from Neo4j for testing purposes."""

    @staticmethod
    async def fetch_stratified_nodes(quotas: dict[str, int]) -> list[dict[str, Any]]:
        """Fetch nodes stratified by label.

        Args:
            quotas: Dictionary where key is the Neo4j Label and value is the count.
                    Example: {"Policy": 30, "Rule": 40}

        Returns:
            List of node dictionaries.
        """
        tasks = []
        for label, count in quotas.items():
            tasks.append(GraphRepository.query_nodes(label=label, limit=count))

        # Run all queries in parallel
        results = await asyncio.gather(*tasks)

        all_nodes = []
        for batch in results:
            all_nodes.extend(batch)

        return all_nodes
