"""CLI Entry point for Embedding Testing Suite.

Run with: python -m app.testing.embedding_suite
"""

import argparse
import asyncio
import sys

from app.embeddings.implementations.sentence_transformers import STEmbedding
from app.graph.connection import Neo4jConnection
from app.graph.repository import GraphRepository
from app.testing.embedding_suite.reporting import Reporter
from app.testing.embedding_suite.runner import EmbeddingRunner


async def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(description="Embedding Testing Suite")
    parser.add_argument(
        "--policies", type=int, default=20, help="Number of policies to sample"
    )
    parser.add_argument(
        "--rules", type=int, default=30, help="Number of rules to sample"
    )
    parser.add_argument(
        "--thresholds", type=int, default=10, help="Number of thresholds to sample"
    )
    args = parser.parse_args()

    print("[*] Starting Embedding Testing Suite...")

    # 0. Connect to Neo4j
    try:
        await Neo4jConnection.connect()
    except Exception as e:
        print(f"[!] Failed to connect to Neo4j: {e}")
        sys.exit(1)

    try:
        # 1. Check Infrastructure
        if not await GraphRepository.health_check():
            print("[!] Neo4j is not reachable! Aborting.")
            sys.exit(1)

        # 2. Initialize Model
        # Start with default SentenceTransformer as per plan
        print("[*] Initializing Embedding Model...")
        try:
            model = STEmbedding()
        except Exception as e:
            print(f"[!] Model initialization failed: {e}")
            sys.exit(1)

        # 3. Initialize Runner
        runner = EmbeddingRunner(model)

        # 4. Run Suite
        quotas = {
            "Policy": args.policies,
            "Rule": args.rules,
            "Threshold": args.thresholds,
        }

        try:
            results = await runner.run_suite(quotas=quotas)
        except Exception as e:
            print(f"[!] Test Suite Error: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # 5. Reporting
        Reporter.print_summary(results)
        path = Reporter.save_report(results)
        print(f"\n[+] Report saved to: {path}")

        # 6. Exit Code
        if results.get("failures"):
            print("[!] Failures detected.")
            sys.exit(1)
        else:
            print("[*] All tests passed (or no failures logged).")
            # sys.exit(0) # Don't exit yet, let finally run

    finally:
        await Neo4jConnection.disconnect()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
