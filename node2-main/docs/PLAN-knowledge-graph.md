# PLAN-knowledge-graph

## Overview
Implement a "Level 2/3" Knowledge Graph Construction pipeline for the Local Knowledge Engine. 
**Strategy**: "Async Refiner" (Option B).
1.  **Ingestion**: Standard PDF chunking (fast).
2.  **Refinement**: Background job extracts entities and relationships using Node 1 LLM.
This decouples resource-intensive extraction from the user upload flow, ensuring responsiveness on local hardware.

## Project Type
**BACKEND**

## Success Criteria
1.  **Async Execution**: `GraphBuilderService` runs without blocking the main thread or HTTP response.
2.  **Entity Extraction**: `Person`, `Organization`, `Location`, `Concept` entities are extracted from PDF chunks.
3.  **Graph Connectivity**: Entities are linked to their source Chunks via `MENTIONS` relationships.
4.  **Resilience**: Failure in graph building does not corrupt the `Document` or `Element` nodes.

## Tech Stack
-   **LangChain**: For text splitting and potential extraction chains.
-   **Neo4j**: Graph database.
-   **Pydantic**: Data validation for extraction schema.
-   **Node 1 LLM**: `deepseek-r1:8b-llama-distill-q4_K_M` (Local Inference).

## File Structure
```
node2-main/
├── app/
│   ├── services/
│   │   ├── graph_builder.py       # [NEW] Service for graph extraction
│   │   └── ingestion.py           # [MODIFY] Trigger graph build (async)
│
└── scripts/
    └── build_graph.py             # [NEW] CLI to trigger refinement manually
```

## Task Breakdown

### Phase 1: Core Service Implementation

#### Task 1.1: Create Extraction Schema & Prompt
-   **Agent**: `backend-specialist`
-   **Skill**: `api-patterns` (Pydantic), `prompt-engineering`
-   **Input**: `app/services/graph_builder.py`
-   **Action**: Define Pydantic models for `Entity` and `Relationship`. Create the system prompt for Node 1.
-   **Output**: `GraphBuilderService` class with `_extract_entities` method (mocked LLM for now).
-   **Verify**: Unit test `test_extraction_schema` passes with valid JSON sample.

#### Task 1.2: Implement Graph Writability
-   **Agent**: `backend-specialist`
-   **Skill**: `database-design`
-   **Input**: `app/services/graph_builder.py`
-   **Action**: Implement `_save_graph` method using Cypher `UNWIND` / `MERGE`.
-   **Output**: Functional `build_graph_for_document` that takes mock entities and writes to Neo4j.
-   **Verify**: Run service against a test document ID; verify nodes appear in Neo4j.

#### Task 1.3: Integrate Node 1 LLM
-   **Agent**: `backend-specialist`
-   **Input**: `app/services/graph_builder.py`
-   **Action**: Connect `Node1LLM` (from `app.inference.llm_adapter`) to the extraction method. Use `asyncio` to handle LLM latency.
-   **Output**: Full end-to-end `process_document` method.
-   **Verify**: Rate-limit check (ensure we don't DDOS Node 1).

### Phase 2: Integration & CLI

#### Task 2.1: Create CLI Trigger
-   **Agent**: `backend-specialist`
-   **Input**: `scripts/build_graph.py`
-   **Action**: Create a CLI script to run `GraphBuilderService` for a specific file or all files.
-   **Output**: `python scripts/build_graph.py --file "foo.pdf"` works.
-   **Verify**: Manual execution on sample PDF.

#### Task 2.2: Async Hook in Ingestion
-   **Agent**: `backend-specialist`
-   **Input**: `app/services/ingestion.py`
-   **Action**: Add `background_tasks.add_task(graph_builder.process, doc_id)` (or simple fire-and-forget for now) to `ingest_file`.
-   **Output**: Uploading a file automatically triggers graph building in background.
-   **Verify**: Logs show "Ingestion complete" followed by "Graph building started".

## Phase X: Verification

### Checklist
- [ ] **Lint & Type Check**: `ruff check .`
- [ ] **Unit Tests**: `pytest` passes for new service.
- [ ] **Manual Verification**:
    1.  Ingest `sample.pdf`.
    2.  Wait for logs "Graph build complete".
    3.  Neo4j Query: `MATCH (c:Element)-[:MENTIONS]->(e:Entity) RETURN c, e LIMIT 10`.
    4.  Verify entities look reasonable (not garbage).

### Final Sign-off
- Date: [Pending]
- Status: [Pending]
