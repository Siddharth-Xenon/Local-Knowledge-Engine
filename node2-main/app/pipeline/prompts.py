"""System prompts for the verification pipeline.

All prompts are versioned constants — changes must be regression-tested.
Per GOAL.md §10.1: prompts are system logic, not text generation.
"""

# ── Grounded Generation ──────────────────────────────────────────────────────

GROUNDED_GENERATION_PROMPT = """\
You are a factual knowledge assistant. You answer ONLY from the provided context.

## Rules
1. Use ONLY the evidence provided below. Do NOT use prior knowledge.
2. Every factual statement MUST cite evidence IDs in square brackets, e.g. [E1].
3. If the evidence does not contain the answer, say "I cannot answer this from \
the available evidence."
4. Do NOT speculate, infer, or generalize beyond the evidence.
5. If evidence is partial, state what is known and explicitly flag uncertainty.
6. Return your answer as JSON with this exact structure:

```json
{{
  "answer": [
    {{
      "statement": "The factual claim text [E1].",
      "evidence_ids": ["E1"]
    }}
  ],
  "uncertainties": [
    {{
      "statement": "What is uncertain",
      "reason": "Why it is uncertain"
    }}
  ]
}}
```

## Evidence
{context}

## Question
{query}
"""

# ── Claim Extraction ─────────────────────────────────────────────────────────

CLAIM_EXTRACTION_PROMPT = """\
Extract atomic factual claims from the answer below.

Each claim must be a single, independently verifiable fact with:
- subject: the entity or concept
- predicate: the relationship or action
- object: the target value, entity, or condition
- evidence_refs: list of evidence IDs cited (e.g. ["E1", "E3"])

Split compound statements into separate claims.
Preserve evidence references from the original text.

Return a JSON array of claims:
```json
{{
  "claims": [
    {{
      "subject": "...",
      "predicate": "...",
      "object": "...",
      "evidence_refs": ["E1"],
      "source_statement": "Original sentence"
    }}
  ]
}}
```

## Answer to extract claims from:
{answer_text}
"""

# ── Regeneration ─────────────────────────────────────────────────────────────

REGENERATION_PROMPT = """\
A previous answer contained claims that could not be verified.

## Failed Claims
{failed_claims}

## Failure Reasons
{failure_reasons}

## Available Evidence
{context}

## Instructions
1. Rewrite ONLY the parts addressing the failed claims.
2. Use ONLY the evidence provided — do not introduce new facts.
3. If the evidence does not support the claim, explicitly state that.
4. Cite evidence IDs in every factual statement.

## Question
{query}
"""

# ── Anti-Pattern Detection ───────────────────────────────────────────────────

ANTI_PATTERN_PHRASES: list[str] = [
    "based on my knowledge",
    "based on my training",
    "it is likely that",
    "it is probable that",
    "typically, such",
    "in general,",
    "as an ai",
    "as a language model",
    "i believe that",
    "it's worth noting that",
    "it's important to note",
    "generally speaking",
    "in most cases",
    "from what i know",
    "to the best of my knowledge",
]
