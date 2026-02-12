"""Unit tests for Node1LLM and Node1ChatModel adapters."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from neo4j_graphrag.exceptions import LLMGenerationError
from neo4j_graphrag.llm.types import LLMResponse

from app.inference.llm_adapter import Node1LLM, Node1ChatModel, _flatten_messages
from app.core import InferenceTimeoutError, InferenceUnavailableError


@pytest.fixture
def llm():
    """Node1LLM with test defaults."""
    with patch("app.inference.llm_adapter.settings") as mock_settings:
        mock_settings.node1_url = "http://test-node1:8001"
        mock_settings.inference_timeout = 10
        yield Node1LLM(
            model_name="test-model",
            base_url="http://test-node1:8001",
            timeout=10,
        )


@pytest.fixture
def chat_model():
    """Node1ChatModel with test defaults."""
    with patch("app.inference.llm_adapter.settings") as mock_settings:
        mock_settings.node1_url = "http://test-node1:8001"
        mock_settings.inference_timeout = 10
        yield Node1ChatModel(
            model_name="test-model",
            base_url="http://test-node1:8001",
            timeout=10,
        )


# --- Prompt building ---


class TestBuildPrompt:
    def test_basic(self, llm):
        result = llm._build_prompt("What is AI?")
        assert result == "[User]\nWhat is AI?"

    def test_with_system_instruction(self, llm):
        result = llm._build_prompt(
            "Generate Cypher",
            system_instruction="You are a Cypher expert.",
        )
        assert result == "[System]\nYou are a Cypher expert.\n\n[User]\nGenerate Cypher"

    def test_with_message_history(self, llm):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        result = llm._build_prompt("Follow up", message_history=history)
        assert "[User]\nHi" in result
        assert "[Assistant]\nHello!" in result
        assert result.endswith("[User]\nFollow up")

    def test_full_prompt(self, llm):
        result = llm._build_prompt(
            "My question",
            message_history=[{"role": "user", "content": "context"}],
            system_instruction="Be precise.",
        )
        parts = result.split("\n\n")
        assert parts[0] == "[System]\nBe precise."
        assert parts[1] == "[User]\ncontext"
        assert parts[2] == "[User]\nMy question"


# --- Flatten messages (LangChain) ---


class TestFlattenMessages:
    def test_single_human(self):
        from langchain_core.messages import HumanMessage

        result = _flatten_messages([HumanMessage(content="Hello")])
        assert result == "[Human]\nHello"

    def test_mixed_messages(self):
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        msgs = [
            SystemMessage(content="Be brief."),
            HumanMessage(content="What is 1+1?"),
            AIMessage(content="2"),
        ]
        result = _flatten_messages(msgs)
        assert "[System]\nBe brief." in result
        assert "[Human]\nWhat is 1+1?" in result
        assert "[Ai]\n2" in result


# --- Sync invoke (Node1LLM) ---


class TestInvokeSync:
    def test_success(self, llm):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "42",
            "model": "test",
            "done": True,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.inference.llm_adapter.httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = MagicMock(return_value=MagicMock())
            MockClient.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = llm.invoke("What is the answer?")

        assert isinstance(result, LLMResponse)
        assert result.content == "42"

    def test_timeout_wraps_as_llm_error(self, llm):
        import httpx

        with patch("app.inference.llm_adapter.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.TimeoutException("timed out")
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(LLMGenerationError):
                llm.invoke("slow query")


# --- Async ainvoke (Node1LLM) ---


class TestAinvokeAsync:
    @pytest.mark.asyncio
    async def test_success(self, llm):
        llm._async_client = MagicMock()
        llm._async_client.generate = AsyncMock(return_value="async answer")

        result = await llm.ainvoke("async question")

        assert isinstance(result, LLMResponse)
        assert result.content == "async answer"

    @pytest.mark.asyncio
    async def test_timeout_wraps_as_llm_error(self, llm):
        llm._async_client = MagicMock()
        llm._async_client.generate = AsyncMock(
            side_effect=InferenceTimeoutError("timed out", {})
        )

        with pytest.raises(LLMGenerationError):
            await llm.ainvoke("slow query")

    @pytest.mark.asyncio
    async def test_unavailable_wraps_as_llm_error(self, llm):
        llm._async_client = MagicMock()
        llm._async_client.generate = AsyncMock(
            side_effect=InferenceUnavailableError("node down", {})
        )

        with pytest.raises(LLMGenerationError):
            await llm.ainvoke("any query")


# --- Node1ChatModel ---


class TestNode1ChatModel:
    def test_llm_type(self, chat_model):
        assert chat_model._llm_type == "node1-local"

    def test_generate_success(self, chat_model):
        from langchain_core.messages import HumanMessage
        from langchain_core.outputs import ChatResult

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "Hello from Node 1",
            "model": "test",
            "done": True,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.inference.llm_adapter.httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = MagicMock(return_value=MagicMock())
            MockClient.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = chat_model._generate([HumanMessage(content="Hi")])

        assert isinstance(result, ChatResult)
        assert len(result.generations) == 1
        assert result.generations[0].message.content == "Hello from Node 1"

    @pytest.mark.asyncio
    async def test_agenerate_success(self, chat_model):
        from langchain_core.messages import HumanMessage
        from langchain_core.outputs import ChatResult

        with patch("app.inference.llm_adapter.InferenceClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.generate = AsyncMock(return_value="Async hello")
            MockClient.return_value = mock_instance

            result = await chat_model._agenerate([HumanMessage(content="Hi")])

        assert isinstance(result, ChatResult)
        assert result.generations[0].message.content == "Async hello"


# --- Integration (real Node 1 connection) ---


@pytest.mark.integration
class TestNode1Integration:
    """Real connection tests — requires Node 1 running at settings.node1_url.

    Run with: pytest tests/test_llm_adapter.py -m integration -v
    """

    def _make_llm(self):
        return Node1LLM()

    def test_invoke_real(self):
        llm = self._make_llm()
        result = llm.invoke("Say hello in one word.")

        assert isinstance(result, LLMResponse)
        assert len(result.content) > 0
        print(f"\n[SYNC] Node 1 responded: {result.content[:100]}")

    @pytest.mark.asyncio
    async def test_ainvoke_real(self):
        llm = self._make_llm()
        result = await llm.ainvoke("Say hello in one word.")

        assert isinstance(result, LLMResponse)
        assert len(result.content) > 0
        print(f"\n[ASYNC] Node 1 responded: {result.content[:100]}")
