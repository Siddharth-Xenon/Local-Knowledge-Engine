"""Reporting module for test results."""

import json
import os
from datetime import datetime
from typing import Any


class Reporter:
    """Handles report generation and saving."""

    @staticmethod
    def save_report(results: dict[str, Any], output_dir: str = "reports") -> str:
        """Save results to a JSON file."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"embedding_test_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Add metadata
        results["meta"] = {"timestamp": timestamp, "version": "1.0.0"}

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        return filepath

    @staticmethod
    def print_summary(results: dict[str, Any]) -> None:
        """Print a human-readable summary to stdout."""
        metrics = results.get("metrics", {})
        config = results.get("config", {})
        failures = results.get("failures", [])

        print("\n" + "=" * 50)
        print(f"EMBEDDING SUITE REPORT ({config.get('model_class')})")
        print("=" * 50)

        print("\n[Metrics]")
        for k, v in metrics.items():
            print(f"  {k:<25}: {v:.4f}")

        print(f"\n[Failures]: {len(failures)}")

        # Group failures by test
        fail_counts = {}
        for f in failures:
            test = f.get("test", "unknown")
            fail_counts[test] = fail_counts.get(test, 0) + 1

        for test, count in fail_counts.items():
            print(f"  {test}: {count}")

        print("\n" + "=" * 50)
