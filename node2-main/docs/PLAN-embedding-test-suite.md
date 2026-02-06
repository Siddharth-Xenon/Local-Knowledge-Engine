# PLAN-embedding-test-suite

**Goal**: Create an automated testing suite in `node2` to evaluate embedding model performance, stability, and reliability using live Neo4j data.

## 1. Context & Requirements
- **Environment**: Node 2 (Backend/Graph/Retrieval).
- **Core Dependencies**: `app.embeddings`, `app.graph` (Neo4j Connection).
- **Data Source**: Live Neo4j database (no external golden dataset yet).
- **Models**: implementations in `app/embeddings/implementations/`.

## 2. Evaluation Metrics

| Metric | Definition | Implementation Strategy |
| :--- | :--- | :--- |
| **Recall@K** | % of queries where the *correct* node appears in the top K results. | **Self-Retrieval**: Use node text as query. Ground Truth = Node ID. |
| **MRR (Mean Reciprocal Rank)** | Average of 1/rank of the first correct answer. | Penalizes correct answers that appear low in the list (e.g., rank 10 vs rank 1). |
| **Top-K Pollution Rate** | % of top-K results logically incompatible with query. | **Heuristic**: Check if retrieved nodes match query node's broad type/currency/threshold units. |
| **Stability (Deterministic)** | `Embed(text) approx Embed(text)` | Run same embedding twice. Pass if `CosineSimilarity >= 0.9999`. Log variance. |
| **Stability (Semantic)** | `Sim(Embed(text), Embed(text + noise)) > Threshold` | Perturbations (typos, case, **numeric**, **boundary words**) shouldn't tank similarity. |
| **False Attraction** | High scores for irrelevant nodes. | Log "high confidence" matches that are *not* the target node during Self-Retrieval. |

## 3. Architecture

### Module Structure
Values pending implementation in `app/testing/`.

```
app/
└── testing/
    └── embedding_suite/
        ├── __init__.py
        ├── runner.py          # Main entry point: Orchestrates the test run
        ├── data_loader.py     # Fetches stratified nodes from Neo4j
        ├── perturbation.py    # Generates semantic var (finance-aware)
        ├── metrics.py         # Calculators for MRR, Recall, polluted results
        └── reporting.py       # JSON/Console output generation
```

## 4. Workflows

### A. Evaluation Loop (Step-by-Step)
1.  **Setup**: Initialize the specific `EmbeddingModel` implementation.
2.  **Data Loading (Stratified)**: Fetch samples stratified by labels (e.g., 30 Policies, 40 Rules, 15 Thresholds).
3.  **Baseline Generation**: Embed all sampled nodes.
4.  **Test 1: Deterministic Stability**:
    *   Re-embed the same nodes.
    *   Compare Vectors. Fail if Cosine Similarity < 0.9999.
5.  **Test 2: Self-Retrieval (Recall@K & MRR)**:
    *   **Mode A (Raw)**: `node.text` -> Query.
    *   **Mode B (Context-Aware)**: `node.text + node.metadata.summary` -> Query.
    *   **Check**: Is Node ID in Top-K? Calculate Reciprocal Rank.
    *   **Pollution Check**: Are Top-K results of a different, incompatible Type?
6.  **Test 3: Semantic Stability (Finance)**:
    *   Apply perturbations:
        *   Numeric: "1M" -> "one million"
        *   Boundary: "gt" -> "exceeds"
        *   Typos/Case
    *   Embed and measure cosine similarity against baseline.

## 5. Implementation Steps

### Phase 1: Foundation & Data Loading
- [ ] Create `app/testing/embedding_suite/` structure.
- [ ] Implement `DataLoader.fetch_stratified_nodes(quotas={...})`.
- [ ] Implement `MetricCalculator.cosine_similarity` and `MRR`.

### Phase 2: Core Metrics (Stability & Recall)
- [ ] Implement `Runner.test_deterministic_stability` (with epsilon tolerance).
- [ ] Implement `Runner.test_self_recall` (includes MRR & Top-K Pollution heuristic).
- [ ] Implement `Perturbator` with finance-specific rules (numbers, boundaries).

### Phase 3: Reporting & CLI
- [ ] Create CLI entry point.
- [ ] Implement JSON logging for failures (query, expected_id, top_results, pollution_rate).

## 6. Future Expansion
- **Golden Dataset**: Support loading external JSON `{query: str, expected_ids: list[str]}`.
- **Negative Sampling**: Explicit checks against "distractor" nodes.
