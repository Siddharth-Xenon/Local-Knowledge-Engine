"""
Synthetic Financial Data Generator

Generates synthetic banking/finance knowledge graph data using Google Gemini API.
Outputs JSON files for nodes/edges and Cypher statements for Neo4j import.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Constants
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3-flash-preview"

# Default output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "synthetic"

# Generation defaults
DEFAULTS = {
    "banks": 2,
    "customers_per_bank": 10,
    "transactions_per_customer": 5,
    "seed": 42,
}

# Gemini client (initialized lazily)
_client: genai.Client | None = None


def get_client() -> genai.Client | None:
    """Get or create Gemini client."""
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            print("ERROR: GEMINI_API_KEY not set in environment")
            return None
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def call_gemini_api(prompt: str, temperature: float = 0.7) -> str | None:
    """
    Call Google Gemini API with the given prompt.
    Uses streaming to collect full response.

    Returns the response text or None on error.
    """
    client = get_client()
    if client is None:
        return None

    try:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
        )

        # Collect streamed response
        full_response = ""
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                full_response += chunk.text

        return full_response if full_response else None

    except Exception as e:
        print(f"ERROR: Gemini API request failed: {e}")
        return None


def parse_json_from_response(content: str) -> list[dict] | dict | None:
    """
    Parse JSON from LLM response.
    Handles markdown code blocks if present.
    """
    # Strip markdown code blocks if present
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        print(f"Content preview: {content[:200]}...")
        return None


def load_prompt(name: str) -> str | None:
    """Load a prompt template from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
    if not prompt_path.exists():
        print(f"ERROR: Prompt file not found: {prompt_path}")
        return None
    return prompt_path.read_text(encoding="utf-8")


def add_provenance(data: dict | list[dict]) -> dict | list[dict]:
    """Add provenance metadata to node(s)."""
    now = datetime.utcnow().isoformat() + "Z"
    provenance = {
        "source": "synthetic",
        "created_at": now,
        "last_verified": now,
        "confidence": 1.0,
    }

    if isinstance(data, list):
        for item in data:
            item.update(provenance)
    else:
        data.update(provenance)

    return data


def ensure_output_dirs(output_dir: Path) -> None:
    """Create output directory structure."""
    (output_dir / "nodes").mkdir(parents=True, exist_ok=True)
    (output_dir / "edges").mkdir(parents=True, exist_ok=True)
    (output_dir / "cypher").mkdir(parents=True, exist_ok=True)


def save_json(data: Any, output_dir: Path, subdir: str, filename: str) -> None:
    """Save data as JSON file."""
    path = output_dir / subdir / f"{filename}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {path}")


def test_api_connection() -> bool:
    """Test Gemini API connection with a simple prompt."""
    print("Testing Gemini API connection...")

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not set in environment")
        return False

    # Simple test prompt
    content = call_gemini_api("Reply with exactly: OK", temperature=0)

    if content is None:
        print("❌ API request failed")
        return False

    print("✅ API connection successful")
    print(f"   Response: {content.strip()}")
    return True


# =============================================================================
# Node Generation Functions
# =============================================================================


def generate_banks(count: int = 2) -> list[dict]:
    """Generate synthetic bank nodes."""
    print(f"Generating {count} banks...")

    prompt_template = load_prompt("bank")
    if not prompt_template:
        return []

    prompt = prompt_template.replace("{count}", str(count))
    content = call_gemini_api(prompt)

    if content is None:
        return []

    banks = parse_json_from_response(content)
    if banks is None or not isinstance(banks, list):
        print("ERROR: Expected list of banks")
        return []

    banks = add_provenance(banks)
    print(f"  ✅ Generated {len(banks)} banks")
    return banks


def generate_policies(banks: list[dict]) -> tuple[list, list, list, list]:
    """Generate policies, rules, thresholds, and conditions for banks."""
    print(f"Generating policies for {len(banks)} banks...")

    prompt_template = load_prompt("policy")
    if not prompt_template:
        return [], [], [], []

    all_policies = []
    all_rules = []
    all_thresholds = []
    all_conditions = []

    for bank in banks:
        bank_id = bank["bank_id"]
        bank_name = bank["name"]

        prompt = prompt_template.replace("{bank_id}", bank_id).replace(
            "{bank_name}", bank_name
        )
        content = call_gemini_api(prompt)

        if content is None:
            continue

        data = parse_json_from_response(content)
        if data is None or not isinstance(data, dict):
            print(f"  ⚠️  Skipping policies for {bank_id} - invalid response")
            continue

        policies = data.get("policies", [])
        rules = data.get("rules", [])
        thresholds = data.get("thresholds", [])
        conditions = data.get("conditions", [])

        # Add bank reference to policies
        for policy in policies:
            policy["bank_id"] = bank_id

        all_policies.extend(add_provenance(policies))
        all_rules.extend(add_provenance(rules))
        all_thresholds.extend(add_provenance(thresholds))
        all_conditions.extend(add_provenance(conditions))

    print(f"  ✅ Generated {len(all_policies)} policies, {len(all_rules)} rules")
    print(f"     {len(all_thresholds)} thresholds, {len(all_conditions)} conditions")
    return all_policies, all_rules, all_thresholds, all_conditions


def generate_customers(
    banks: list[dict], count_per_bank: int = 10
) -> tuple[list, list]:
    """Generate customers and accounts for banks."""
    print(f"Generating {count_per_bank} customers per bank...")

    prompt_template = load_prompt("customer")
    if not prompt_template:
        return [], []

    all_customers = []
    all_accounts = []

    for bank in banks:
        bank_id = bank["bank_id"]
        bank_name = bank["name"]

        prompt = (
            prompt_template.replace("{count}", str(count_per_bank))
            .replace("{bank_id}", bank_id)
            .replace("{bank_name}", bank_name)
        )
        content = call_gemini_api(prompt)

        if content is None:
            continue

        data = parse_json_from_response(content)
        if data is None or not isinstance(data, dict):
            print(f"  ⚠️  Skipping customers for {bank_id} - invalid response")
            continue

        customers = data.get("customers", [])
        accounts = data.get("accounts", [])

        all_customers.extend(add_provenance(customers))
        all_accounts.extend(add_provenance(accounts))

    print(
        f"  ✅ Generated {len(all_customers)} customers, {len(all_accounts)} accounts"
    )
    return all_customers, all_accounts


def generate_transactions(
    accounts: list[dict],
    customers: list[dict],
    policies: list[dict],
    count_per_customer: int = 5,
) -> tuple[list, list, list]:
    """Generate transactions, risk flags, and decisions."""
    print(f"Generating up to {count_per_customer} transactions per customer...")

    prompt_template = load_prompt("transaction")
    if not prompt_template:
        return [], [], []

    all_transactions = []
    all_risk_flags = []
    all_decisions = []

    # Build lookup for customer -> accounts
    customer_accounts = {}
    for acc in accounts:
        cust_id = acc.get("customer_id")
        if cust_id not in customer_accounts:
            customer_accounts[cust_id] = []
        customer_accounts[cust_id].append(acc)

    # Build lookup for bank -> policies
    bank_policies = {}
    for pol in policies:
        bank_id = pol.get("bank_id")
        if bank_id not in bank_policies:
            bank_policies[bank_id] = []
        bank_policies[bank_id].append(pol["policy_id"])

    # Generate transactions per customer
    for customer in customers:
        cust_id = customer["customer_id"]
        bank_id = customer.get("bank_id")
        cust_accounts = customer_accounts.get(cust_id, [])

        if not cust_accounts:
            continue

        # Use first account
        account = cust_accounts[0]
        acc_id = account["account_id"]
        policy_ids = bank_policies.get(bank_id, [])

        prompt = (
            prompt_template.replace("{count}", str(count_per_customer))
            .replace("{account_id}", acc_id)
            .replace("{customer_id}", cust_id)
            .replace("{bank_id}", bank_id or "UNKNOWN")
            .replace("{policy_ids}", ", ".join(policy_ids) if policy_ids else "None")
        )

        content = call_gemini_api(prompt)

        if content is None:
            continue

        data = parse_json_from_response(content)
        if data is None or not isinstance(data, dict):
            continue

        transactions = data.get("transactions", [])
        risk_flags = data.get("risk_flags", [])
        decisions = data.get("decisions", [])

        all_transactions.extend(add_provenance(transactions))
        all_risk_flags.extend(add_provenance(risk_flags))
        all_decisions.extend(add_provenance(decisions))

    print(f"  ✅ Generated {len(all_transactions)} transactions")
    print(f"     {len(all_risk_flags)} risk flags, {len(all_decisions)} decisions")
    return all_transactions, all_risk_flags, all_decisions


# =============================================================================
# Edge Generation Functions
# =============================================================================


def generate_edges(nodes: dict[str, list]) -> dict[str, list]:
    """
    Generate all edge types based on node relationships.
    Edges are derived deterministically from node data.
    """
    print("Generating edges...")

    edges = {
        "OWNS_ACCOUNT": [],
        "OPERATES": [],
        "EXECUTED_ON": [],
        "INITIATED_BY": [],
        "HAS_POLICY": [],
        "CONTAINS_RULE": [],
        "USES_THRESHOLD": [],
        "USES_CONDITION": [],
        "EVALUATED_UNDER": [],
        "VIOLATES": [],
        "TRIGGERS": [],
        "RESULTS_IN": [],
    }

    # Customer → Account (OWNS_ACCOUNT)
    for account in nodes.get("accounts", []):
        edges["OWNS_ACCOUNT"].append(
            {
                "from": account.get("customer_id"),
                "to": account.get("account_id"),
                "type": "OWNS_ACCOUNT",
            }
        )

    # Bank → Account (OPERATES)
    for account in nodes.get("accounts", []):
        edges["OPERATES"].append(
            {
                "from": account.get("bank_id"),
                "to": account.get("account_id"),
                "type": "OPERATES",
            }
        )

    # Transaction → Account (EXECUTED_ON)
    for txn in nodes.get("transactions", []):
        edges["EXECUTED_ON"].append(
            {
                "from": txn.get("transaction_id"),
                "to": txn.get("account_id"),
                "type": "EXECUTED_ON",
            }
        )

    # Transaction → Customer (INITIATED_BY)
    for txn in nodes.get("transactions", []):
        edges["INITIATED_BY"].append(
            {
                "from": txn.get("transaction_id"),
                "to": txn.get("customer_id"),
                "type": "INITIATED_BY",
            }
        )

    # Bank → Policy (HAS_POLICY)
    for policy in nodes.get("policies", []):
        edges["HAS_POLICY"].append(
            {
                "from": policy.get("bank_id"),
                "to": policy.get("policy_id"),
                "type": "HAS_POLICY",
            }
        )

    # Policy → Rule (CONTAINS_RULE)
    for rule in nodes.get("rules", []):
        edges["CONTAINS_RULE"].append(
            {
                "from": rule.get("policy_id"),
                "to": rule.get("rule_id"),
                "type": "CONTAINS_RULE",
            }
        )

    # Rule → Threshold (USES_THRESHOLD)
    for threshold in nodes.get("thresholds", []):
        edges["USES_THRESHOLD"].append(
            {
                "from": threshold.get("rule_id"),
                "to": threshold.get("threshold_id"),
                "type": "USES_THRESHOLD",
            }
        )

    # Rule → Condition (USES_CONDITION)
    for condition in nodes.get("conditions", []):
        edges["USES_CONDITION"].append(
            {
                "from": condition.get("rule_id"),
                "to": condition.get("condition_id"),
                "type": "USES_CONDITION",
            }
        )

    # RiskFlag → Rule (TRIGGERS - reverse direction)
    for flag in nodes.get("risk_flags", []):
        edges["TRIGGERS"].append(
            {
                "from": flag.get("rule_id"),
                "to": flag.get("risk_flag_id"),
                "type": "TRIGGERS",
            }
        )

    # Transaction → Decision (RESULTS_IN)
    for decision in nodes.get("decisions", []):
        edges["RESULTS_IN"].append(
            {
                "from": decision.get("transaction_id"),
                "to": decision.get("decision_id"),
                "type": "RESULTS_IN",
            }
        )

    # Count edges
    total = sum(len(e) for e in edges.values())
    edge_types_used = sum(1 for e in edges.values() if e)
    print(f"  ✅ Generated {total} edges across {edge_types_used} types")

    return edges


# =============================================================================
# Cypher Export
# =============================================================================


def node_to_cypher(label: str, node: dict) -> str:
    """Convert a node dict to a Cypher CREATE statement."""
    # Filter out None values and format properties
    props = {k: v for k, v in node.items() if v is not None}
    props_str = ", ".join(f"{k}: {json.dumps(v)}" for k, v in props.items())

    return f"CREATE (:{label} {{{props_str}}});"


def edge_to_cypher(edge: dict, from_label: str, to_label: str) -> str:
    """Convert an edge dict to Cypher MATCH + CREATE statement."""
    from_id = edge["from"]
    to_id = edge["to"]
    rel_type = edge["type"]

    # Determine ID fields based on labels
    from_id_field = f"{from_label.lower()}_id"
    to_id_field = f"{to_label.lower()}_id"

    return (
        f"MATCH (a:{from_label} {{{from_id_field}: {json.dumps(from_id)}}}), "
        f"(b:{to_label} {{{to_id_field}: {json.dumps(to_id)}}}) "
        f"CREATE (a)-[:{rel_type}]->(b);"
    )


# Mapping of edge type to (from_label, to_label)
EDGE_LABEL_MAP = {
    "OWNS_ACCOUNT": ("Customer", "Account"),
    "OPERATES": ("Bank", "Account"),
    "EXECUTED_ON": ("Transaction", "Account"),
    "INITIATED_BY": ("Transaction", "Customer"),
    "HAS_POLICY": ("Bank", "Policy"),
    "CONTAINS_RULE": ("Policy", "Rule"),
    "USES_THRESHOLD": ("Rule", "Threshold"),
    "USES_CONDITION": ("Rule", "Condition"),
    "EVALUATED_UNDER": ("Transaction", "Policy"),
    "VIOLATES": ("Transaction", "Rule"),
    "TRIGGERS": ("Rule", "RiskFlag"),
    "RESULTS_IN": ("Transaction", "Decision"),
}

# Mapping of node type to label
NODE_LABEL_MAP = {
    "banks": "Bank",
    "customers": "Customer",
    "accounts": "Account",
    "transactions": "Transaction",
    "policies": "Policy",
    "rules": "Rule",
    "thresholds": "Threshold",
    "conditions": "Condition",
    "risk_flags": "RiskFlag",
    "decisions": "Decision",
}


def export_cypher(
    nodes: dict[str, list], edges: dict[str, list], output_dir: Path
) -> None:
    """Export nodes and edges as Cypher statements."""
    print("Exporting Cypher statements...")

    cypher_path = output_dir / "cypher" / "import.cypher"

    with open(cypher_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated Cypher import script\n")
        f.write(f"// Generated: {datetime.utcnow().isoformat()}Z\n\n")

        # Create nodes
        f.write("// ============ NODES ============\n\n")
        for node_type, node_list in nodes.items():
            label = NODE_LABEL_MAP.get(node_type, node_type.title())
            if node_list:
                f.write(f"// {label} nodes ({len(node_list)})\n")
                for node in node_list:
                    f.write(node_to_cypher(label, node) + "\n")
                f.write("\n")

        # Create relationships
        f.write("// ============ RELATIONSHIPS ============\n\n")
        for edge_type, edge_list in edges.items():
            if edge_list:
                labels = EDGE_LABEL_MAP.get(edge_type)
                if labels:
                    f.write(f"// {edge_type} ({len(edge_list)})\n")
                    for edge in edge_list:
                        f.write(edge_to_cypher(edge, labels[0], labels[1]) + "\n")
                    f.write("\n")

    print(f"  ✅ Saved: {cypher_path}")


# =============================================================================
# Main Orchestration
# =============================================================================


def run_generation(
    banks_count: int = 2,
    customers_count: int = 10,
    transactions_count: int = 5,
    seed: int = 42,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    """Run the full synthetic data generation pipeline."""
    print("=" * 60)
    print("Synthetic Financial Data Generator")
    print("=" * 60)
    print("Configuration:")
    print(f"  Banks: {banks_count}")
    print(f"  Customers per bank: {customers_count}")
    print(f"  Transactions per customer: {transactions_count}")
    print(f"  Seed: {seed}")
    print(f"  Output: {output_dir}")
    print()

    # Create output directories
    ensure_output_dirs(output_dir)

    # Step 1: Generate banks
    banks = generate_banks(banks_count)
    if not banks:
        print("❌ Failed to generate banks. Aborting.")
        return
    save_json(banks, output_dir, "nodes", "bank")

    # Step 2: Generate policies for each bank
    policies, rules, thresholds, conditions = generate_policies(banks)
    save_json(policies, output_dir, "nodes", "policy")
    save_json(rules, output_dir, "nodes", "rule")
    save_json(thresholds, output_dir, "nodes", "threshold")
    save_json(conditions, output_dir, "nodes", "condition")

    # Step 3: Generate customers and accounts
    customers, accounts = generate_customers(banks, customers_count)
    save_json(customers, output_dir, "nodes", "customer")
    save_json(accounts, output_dir, "nodes", "account")

    # Step 4: Generate transactions
    transactions, risk_flags, decisions = generate_transactions(
        accounts, customers, policies, transactions_count
    )
    save_json(transactions, output_dir, "nodes", "transaction")
    save_json(risk_flags, output_dir, "nodes", "risk_flag")
    save_json(decisions, output_dir, "nodes", "decision")

    # Collect all nodes
    all_nodes = {
        "banks": banks,
        "policies": policies,
        "rules": rules,
        "thresholds": thresholds,
        "conditions": conditions,
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "risk_flags": risk_flags,
        "decisions": decisions,
    }

    # Step 5: Generate edges
    edges = generate_edges(all_nodes)
    for edge_type, edge_list in edges.items():
        if edge_list:
            save_json(edge_list, output_dir, "edges", edge_type.lower())

    # Step 6: Export Cypher
    export_cypher(all_nodes, edges, output_dir)

    # Summary
    print()
    print("=" * 60)
    print("✅ Generation Complete!")
    print("=" * 60)
    total_nodes = sum(len(n) for n in all_nodes.values())
    total_edges = sum(len(e) for e in edges.values())
    print(f"  Total nodes: {total_nodes}")
    print(f"  Total edges: {total_edges}")
    print(f"  Output: {output_dir}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic banking/finance knowledge graph data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--test-api",
        action="store_true",
        help="Test Gemini API connection and exit",
    )
    parser.add_argument(
        "--banks",
        type=int,
        default=DEFAULTS["banks"],
        help=f"Number of banks to generate (default: {DEFAULTS['banks']})",
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=DEFAULTS["customers_per_bank"],
        help=f"Customers per bank (default: {DEFAULTS['customers_per_bank']})",
    )
    parser.add_argument(
        "--transactions",
        type=int,
        default=DEFAULTS["transactions_per_customer"],
        help=f"Transactions per customer (default: {DEFAULTS['transactions_per_customer']})",  # noqa: E501
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULTS["seed"],
        help=f"Random seed for reproducibility (default: {DEFAULTS['seed']})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )

    args = parser.parse_args()

    if args.test_api:
        success = test_api_connection()
        sys.exit(0 if success else 1)

    run_generation(
        banks_count=args.banks,
        customers_count=args.customers,
        transactions_count=args.transactions,
        seed=args.seed,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
