"""Main entry point for the Embedding Testing Suite."""

from typing import Any

from app.embeddings.base import EmbeddingStrategy
from app.testing.embedding_suite.data_loader import DataLoader
from app.testing.embedding_suite.metrics import (
    calculate_mrr,
    calculate_pollution_rate,
    check_deterministic_stability,
    cosine_similarity,
)


class EmbeddingRunner:
    """Orchestrates tests for embedding models."""

    def __init__(self, model: EmbeddingStrategy):
        """Initialize runner with a specific model implementation."""
        self.model = model
        self.results = {
            "config": {
                "model_class": model.__class__.__name__,
                "dimension": model.dimension,
            },
            "metrics": {},
            "failures": [],
        }

    async def run_suite(self, quotas: dict[str, int] | None = None) -> dict[str, Any]:
        """Run the full test suite."""
        quotas = quotas or {"Policy": 20, "Rule": 30}

        print(f"Loading data with quotas: {quotas}...")
        nodes = await DataLoader.fetch_stratified_nodes(quotas)
        print(f"Loaded {len(nodes)} nodes.")

        if not nodes:
            print("No nodes found! Aborting.")
            return self.results

        # 1. Baseline Generation (Embed all)
        # Note: We use the text as the canonical representation for baseline
        print("Generating baseline embeddings...")
        texts = [n.get("text", "") for n in nodes]

        # We assume encode_batch returns numpy array
        baseline_vectors = await self.model.encode_batch(texts)

        # 2. Stability Tests
        print("Running Deterministic Stability Tests...")
        await self._test_deterministic_stability(nodes, baseline_vectors)

        print("Running Semantic Stability Tests...")
        await self._test_semantic_stability(nodes, baseline_vectors)

        # 3. Recall Tests
        print("Running Recall Tests (Raw Text)...")
        await self._test_self_recall(nodes, baseline_vectors, context_mode=False)

        # Context Aware Mode (if summaries exist)
        # We'll skip for now if no summaries, or implement logic to check
        # print("Running Recall Tests (Context Aware)...")
        # await self._test_self_recall(nodes, baseline_vectors, context_mode=True)

        return self.results

    async def _test_deterministic_stability(
        self, nodes: list[dict], baseline_vectors: Any
    ) -> None:
        """Check if re-embedding produces identical vectors."""
        texts = [n.get("text", "") for n in nodes]
        new_vectors = await self.model.encode_batch(texts)

        failures = []
        stable_count = 0

        for i, text in enumerate(texts):
            vec_a = baseline_vectors[i]
            vec_b = new_vectors[i]

            is_stable, sim = check_deterministic_stability(vec_a, vec_b)

            if is_stable:
                stable_count += 1
            else:
                failures.append(
                    {
                        "test": "deterministic_stability",
                        "node_id": nodes[i].get("id"),
                        "text_snippet": text[:50],
                        "similarity": float(sim),
                    }
                )

        pass_rate = stable_count / len(nodes)
        self.results["metrics"]["deterministic_stability"] = pass_rate
        self.results["failures"].extend(failures)

    async def _test_semantic_stability(
        self, nodes: list[dict], baseline_vectors: Any
    ) -> None:
        """Check robustnes against finance-specific perturbations."""
        from app.testing.embedding_suite.perturbation import FinancePerturbator

        texts = [n.get("text", "") for n in nodes]
        perturbed_texts = [FinancePerturbator.perturb(t) for t in texts]

        new_vectors = await self.model.encode_batch(perturbed_texts)

        sims = []
        for i in range(len(nodes)):
            sim = cosine_similarity(baseline_vectors[i], new_vectors[i])
            sims.append(sim)

        avg_stability = sum(sims) / len(sims)
        self.results["metrics"]["semantic_stability_avg"] = avg_stability

    async def _test_self_recall(
        self, nodes: list[dict], baseline_vectors: Any, context_mode: bool = False
    ) -> None:
        """Check if nodes can retrieve themselves from the batch.

        Simulates retrieval by comparing query vector against ALL baseline vectors.
        """
        import numpy as np

        # Prepare Queries
        if context_mode:
            # Append summary if available
            queries = [
                f"{n.get('text', '')}\nContext: "
                f"{n.get('metadata', {}).get('summary', '')}"
                for n in nodes
            ]
        else:
            queries = [n.get("text", "") for n in nodes]

        query_vectors = await self.model.encode_batch(queries)

        hits_at_k = {1: 0, 5: 0, 10: 0}
        total_mrr = 0.0
        total_pollution = 0.0

        # Brute-force search simulation
        # Normalize baseline vectors for fast dot product
        norms = np.linalg.norm(baseline_vectors, axis=1)
        # Avoid div by zero
        norms[norms == 0] = 1e-10
        norm_baseline = baseline_vectors / norms[:, np.newaxis]

        for i, query_vec in enumerate(query_vectors):
            target_id = nodes[i].get("id")

            # Normalize query
            q_norm = np.linalg.norm(query_vec)
            if q_norm == 0:
                q_norm = 1e-10
            query_vec_n = query_vec / q_norm

            # Dot product (Cosine Sim)
            # scores shape: (N,)
            scores = np.dot(norm_baseline, query_vec_n)

            # Get Top-K indices
            # argsort is ascending, so take last K and reverse
            top_k_indices = np.argsort(scores)[-10:][::-1]

            # Construct results list for metrics
            retrieved_results = []
            for idx in top_k_indices:
                retrieved_results.append(nodes[idx])

            # Calculate Metrics
            mrr = calculate_mrr(retrieved_results, target_id, top_k=10)
            total_mrr += mrr

            pollution = calculate_pollution_rate(retrieved_results, nodes[i], top_k=5)
            total_pollution += pollution

            # Hits@K
            found_ranks = [
                j
                for j, res in enumerate(retrieved_results)
                if res.get("id") == target_id
            ]
            if found_ranks:
                rank = found_ranks[0] + 1  # 0-indexed to 1-indexed
                if rank <= 1:
                    hits_at_k[1] += 1
                if rank <= 5:
                    hits_at_k[5] += 1
                if rank <= 10:
                    hits_at_k[10] += 1
            else:
                # Log Failure (Not found in Top 10)
                self.results["failures"].append(
                    {
                        "test": f"recall_context_{context_mode}",
                        "query_node_id": target_id,
                        "top_match_id": retrieved_results[0].get("id"),
                        "top_match_score": float(scores[top_k_indices[0]]),
                        "query_snippet": queries[i][:50],
                    }
                )

        N = len(nodes)
        prefix = "ctx_" if context_mode else "raw_"
        self.results["metrics"][f"{prefix}recall@1"] = hits_at_k[1] / N
        self.results["metrics"][f"{prefix}recall@5"] = hits_at_k[5] / N
        self.results["metrics"][f"{prefix}recall@10"] = hits_at_k[10] / N
        self.results["metrics"][f"{prefix}mrr"] = total_mrr / N
        self.results["metrics"][f"{prefix}pollution_rate"] = total_pollution / N
