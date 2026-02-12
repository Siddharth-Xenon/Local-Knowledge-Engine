"""Tests for EmbeddingFactory with neo4j-graphrag embedders."""

import pytest
from unittest.mock import patch

from app.embeddings.factory import EmbeddingFactory


class TestEmbeddingFactory:
    @patch("app.embeddings.factory.SentenceTransformerEmbeddings")
    def test_create_default(self, mock_st):
        """Factory creates embedder with default model from config."""
        mock_st.return_value = "mock_embedder"
        result = EmbeddingFactory.create()

        mock_st.assert_called_once()
        assert result == "mock_embedder"

    @patch("app.embeddings.factory.SentenceTransformerEmbeddings")
    def test_create_custom_model(self, mock_st):
        """Factory creates embedder with custom model name."""
        mock_st.return_value = "custom_embedder"
        result = EmbeddingFactory.create(model_name="all-MiniLM-L6-v2")

        mock_st.assert_called_once_with(model="all-MiniLM-L6-v2")
        assert result == "custom_embedder"
