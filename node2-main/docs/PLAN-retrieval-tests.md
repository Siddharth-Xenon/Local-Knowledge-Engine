# Restructure Retrieval Service Tests

Replace hand-crafted mocks with real neo4j-graphrag types and add integration tests against live Neo4j.

## Problem

The current `test_retrieval_e2e.py` uses a `MockRetrieverResultItem` that converts `metadata=None` to `{}` in its constructor — hiding the exact edge case that crashed production. The tests gave false confidence.

## Proposed Changes

---

### Unit Tests — Use Real Types

#### [MODIFY] [test_retrieval_service.py](file:///D:/project/Local-Knowledge-Engine/node2-main/tests/test_retrieval_service.py)

Rename `test_retrieval_e2e.py` → `test_retrieval_service.py` (it's a unit test, not e2e).

- **Remove** `MockRetrieverResultItem` and `MockRetrieverResult` classes
- **Import** real `RetrieverResultItem` and `RetrieverResult` from `neo4j_graphrag.types`
- **Keep** `MagicMock` only for the retriever's `.search()` method (needs Neo4j driver)
- **Add** explicit `metadata=None` test case — the exact scenario that caused the production crash

Test cases:
1. `test_retrieve_with_full_metadata` — items with complete `node_id`, `node_type`, `score`
2. `test_retrieve_with_none_metadata` — **the missing test** — `RetrieverResultItem(content="x", metadata=None)`
3. `test_retrieve_with_missing_metadata` — `RetrieverResultItem(content="x")` (default `None`)
4. `test_retrieve_empty_results` — empty items list
5. `test_retrieve_and_package` — full pipeline through to `StructuredContext`
6. `test_aretrieve_async` — async path

---

### Integration Tests — Real Neo4j

#### [NEW] [test_retrieval_integration.py](file:///D:/project/Local-Knowledge-Engine/node2-main/tests/test_retrieval_integration.py)

True integration test that hits a running Neo4j instance.

- Mark with `@pytest.mark.integration` (already excluded from default `pytest` runs via `addopts = "-m 'not integration'"` in `pyproject.toml`)
- Use `Neo4jConnection` from `app.graph.connection` for setup/teardown
- Create a test node with a vector embedding, run `VectorCypherRetriever.search()`, and verify `_to_evidence_set` handles the real result shape

Test cases:
1. `test_retrieval_against_live_neo4j` — seed a node, retrieve, verify `EvidenceSet` shape
2. `test_retrieval_node_without_metadata_property` — seed a node **without** metadata fields, verify graceful fallback

---

### Pytest Config

#### [MODIFY] [pyproject.toml](file:///D:/project/Local-Knowledge-Engine/node2-main/pyproject.toml)

Add `neo4j` marker alongside existing `integration`:

```toml
markers = [
    "integration: tests requiring a live Node 1 server",
    "neo4j: tests requiring a live Neo4j instance",
]
addopts = "-m 'not integration and not neo4j'"
```

> [!NOTE]
> Run integration tests explicitly: `pytest -m neo4j`

---

### Cleanup

#### [DELETE] [test_retrieval_e2e.py](file:///D:/project/Local-Knowledge-Engine/node2-main/tests/test_retrieval_e2e.py)

Replaced by `test_retrieval_service.py`.

---

## Verification Plan

### Automated Tests

1. **Unit tests (no Neo4j needed):**
   ```powershell
   cd D:\project\Local-Knowledge-Engine\node2-main
   .\venv\Scripts\activate
   pytest tests/test_retrieval_service.py -v
   ```
   All 6 tests should pass, especially `test_retrieve_with_none_metadata`.

2. **Integration tests (requires Neo4j running on localhost):**
   ```powershell
   cd D:\project\Local-Knowledge-Engine\node2-main
   .\venv\Scripts\activate
   pytest tests/test_retrieval_integration.py -v -m neo4j
   ```
   Both tests should pass against the live database.

3. **Full suite (confirm nothing broke):**
   ```powershell
   pytest tests/ -v --ignore=tests/test_retrieval_integration.py
   ```
