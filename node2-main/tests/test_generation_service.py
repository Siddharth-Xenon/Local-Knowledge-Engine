import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.generation_service import GenerationService
from app.inference.client import InferenceClient


@pytest.mark.asyncio
async def test_generation_service_integration():
    """Test that GenerationService renders prompt and calls client."""

    # Mock Client
    mock_client = MagicMock(spec=InferenceClient)
    mock_client.generate = AsyncMock(return_value="Mocked response")

    # Instantiate Service (uses real local templates by default)
    service = GenerationService(client=mock_client)

    # Test Data
    variables = {
        "query": "What is AI?",
        "context": {
            "evidence": [{"id": "1", "text": "AI is artificial intelligence."}]
        },
    }

    # Execution
    response = await service.generate_from_template(
        prompt_key="rag", version="1.0.0", variables=variables
    )

    # Verification
    assert response == "Mocked response"

    # Verify Client Call
    mock_client.generate.assert_called_once()
    call_args = mock_client.generate.call_args
    prompt_sent = call_args.kwargs["prompt"]

    # Verify Prompt Content (Rendering works)
    assert "You are a precise Knowledge Engine assistant." in prompt_sent
    assert "AI is artificial intelligence." in prompt_sent
    assert "User Query: What is AI?" in prompt_sent
