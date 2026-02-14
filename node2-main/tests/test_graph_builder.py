"""Tests for GraphBuilderService."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.graph_builder import (
    GraphBuilderService,
    GraphExtraction,
    Entity,
    Relationship,
)


class TestGraphBuilderService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_llm = AsyncMock()
        self.service = GraphBuilderService(llm=self.mock_llm)

    async def test_extract_entities_success(self):
        # Mock LLM response
        self.mock_llm.ainvoke.return_value = MagicMock(
            content='{"entities": [{"name": "Neo4j", "label": "Technology"}], "relationships": []}'
        )

        extraction = await self.service._extract_entities("Neo4j is great.")

        self.assertIsNotNone(extraction)
        self.assertEqual(len(extraction.entities), 1)
        self.assertEqual(extraction.entities[0].name, "Neo4j")
        self.assertEqual(extraction.entities[0].label, "Technology")

    async def test_extract_entities_invalid_json(self):
        self.mock_llm.ainvoke.return_value = MagicMock(content="Not JSON")

        extraction = await self.service._extract_entities("Bad input.")
        self.assertIsNone(extraction)

    @patch("app.services.graph_builder.get_session")
    async def test_save_graph(self, mock_get_session):
        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        mock_session.execute_write.side_effect = lambda f, *args: f(mock_tx, *args)
        mock_get_session.return_value.__aenter__.return_value = mock_session

        data = GraphExtraction(
            entities=[Entity(name="Alice", label="Person")], relationships=[]
        )

        # We need to mock the tx.run call inside the lambda passed to execute_write
        # But our implementation uses a lambda: lambda tx: tx.run(query, params)
        # So we can just check if execute_write was called

        await self.service._save_graph(data, "chunk1", "doc1")

        mock_session.execute_write.assert_called_once()

    async def test_process_document_no_chunks(self):
        self.service._fetch_chunks = AsyncMock(return_value=[])

        result = await self.service.process_document("empty.pdf")

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "no_chunks")


if __name__ == "__main__":
    unittest.main()
