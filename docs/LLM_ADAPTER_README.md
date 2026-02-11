# Node 1 LLM Adapter for Neo4j GraphRAG

This document details the implementation of the `Node1LLM` adapter, designed to enable `neo4j-graphrag` to utilize the local Node 1 inference engine.

## Overview

The `Node1LLM` adapter bridges the gap between the `neo4j-graphrag` library and our custom Node 1 HTTP inference API. It allows the GraphRAG pipeline to perform generation tasks (like Text2Cypher and Answer Generation) using our local LLM hosted on Node 1.

## Architecture

The adapter is implemented in `node2-main/app/inference/llm_adapter.py`.

### Class: `Node1LLM`

Inherits from: `neo4j_graphrag.llm.base.LLMInterface`

Key responsibilities:
1.  **Prompt Flattening**: Converts the list of messages (System, User, Assistant) into a single string prompt suitable for the local model, preserving role markers.
2.  **Synchronous Inference (`invoke`)**: Uses `httpx.Client` to make blocking HTTP POST requests to Node 1's `/generate` endpoint.
3.  **Asynchronous Inference (`ainvoke`)**: Leverages the existing `InferenceClient` (in `node2-main/app/inference/client.py`) to handle async requests with built-in retry logic and error handling.
4.  **Error Handling**: Wraps connection errors and timeouts into `LLMGenerationError` for consistent exception handling within the GraphRAG pipeline.

## Usage

### 1. Initialization

```python
from app.inference.llm_adapter import Node1LLM

# Uses default settings from app.config (Node 1 URL, timeout)
llm = Node1LLM()

# Or with custom overrides
llm = Node1LLM(
    model_name="deepseek-r1:8b-llama-distill-q4_K_M",
    base_url="http://localhost:8001",
    timeout=60
)
```

### 2. Integration with GraphRAG

The adapter can be passed directly to `GraphRAG` or `Text2CypherRetriever`.

Example from `node2-main/app/services/rag.py`:

```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from app.inference.llm_adapter import Node1LLM

# 1. Initialize LLM
llm = Node1LLM()

# 2. Use in Retriever (for Text -> Cypher)
retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,  # <--- Inject adapter here
    examples=examples,
)

# 3. Use in RAG Pipeline (for Answer Generation)
rag = GraphRAG(retriever=retriever, llm=llm)

# 4. Search
response = rag.search(query_text="What user gives the lowest ratings?")
print(response.answer)
```

## Testing

A comprehensive test suite is available in `node2-main/tests/test_llm_adapter.py`.

### Unit Tests
Run unit tests to verify prompt building and mocking of network calls:
```bash
pytest node2-main/tests/test_llm_adapter.py
```

### Integration Tests
To verify connectivity with a running Node 1 instance, use the `integration` marker:
```bash
pytest node2-main/tests/test_llm_adapter.py -m integration
```
*Note: Ensure Node 1 is running at the configured URL before running integration tests.*

## Modified Files

-   `node2-main/app/inference/llm_adapter.py` (New): The adapter implementation.
-   `node2-main/app/services/rag.py` (New): Example script demonstrating usage.
-   `node2-main/tests/test_llm_adapter.py` (New): Unit and integration tests.
-   `node1-inference/app/services/generation.py`: Updated to improve audit logging and error handling for inference requests.
