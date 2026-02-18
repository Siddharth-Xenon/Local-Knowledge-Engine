# Local-First Enterprise Knowledge Engine

** (GraphRAG + Verification) **
*Internal Development Guide*

> [!NOTE]
> **Current Status (Feb 2026):** Phase 1-5 Complete. The system is a functional dual-node knowledge engine with a LangGraph-based verification pipeline and a web-based frontend.

---


## 0. Purpose of This Document

This document is a **developer reference** for building a **local-first, hallucination-resistant enterprise knowledge engine**.

It is **not**:

* marketing material
* a product pitch
* a vision statement

It **is**:

* a system design guide
* a decision log
* a benchmark reference
* a build checklist

Primary goals:

* determinism
* privacy
* auditability
* bounded intelligence

---

## 1. Problem Definition (Engineering View)

### 1.1 Core Problem

Enterprises in regulated domains need AI systems that:

* operate **entirely on-prem / local**
* **do not hallucinate**
* can **justify every claim**
* can **refuse to answer safely**
* are usable on **modest infrastructure**

LLMs alone cannot satisfy these constraints.

---

### 1.2 Key Constraints

| Constraint         | Implication                             |
| ------------------ | --------------------------------------- |
| Data privacy       | No cloud APIs                           |
| Legal liability    | Hallucinations unacceptable             |
| Cost sensitivity   | No large GPU clusters                   |
| Audit requirements | Every answer must be traceable          |
| Latency tolerance  | Seconds are acceptable, minutes are not |

---

### 1.3 Design Philosophy

> **Trust the system, not the model**

The LLM is treated as:

* a probabilistic reasoning engine
* **never** a source of truth

Truth comes from:

* structured knowledge (GraphDB)
* retrieval boundaries
* verification passes

---

## 2. Enterprise Success Metrics

These metrics define whether the system is **usable in real enterprises**.

They are **not ML benchmarks**.

---

### 2.1 Hallucination Metrics (Primary)

#### 2.1.1 Claim-Level Hallucination Rate (CHR)

**Definition:**
Percentage of generated factual claims that are **not supported** by retrieved knowledge.

```
CHR = unsupported_claims / total_claims
```

Target:

* **< 1%** (hard requirement)

Notes:

* Claims are atomic (one fact per claim)
* Measured *after verification*, not raw generation

---

#### 2.1.2 Unsupported Answer Rate (UAR)

**Definition:**
Percentage of answers that contain **any unsupported claim**.

Target:

* **< 5%** (initial)
* **< 1%** (mature system)

This is stricter than CHR and more meaningful for legal use.

---

### 2.2 Abstention Quality Metrics

Enterprises prefer **safe refusal** over confident nonsense.

#### 2.2.1 Correct Abstention Rate (CAR)

**Definition:**
When required knowledge is missing, the system should **explicitly refuse or defer**.

Target:

* > **95%**

Failure case:

* model guesses instead of abstaining

---

#### 2.2.2 False Abstention Rate (FAR)

**Definition:**
System abstains even though sufficient knowledge exists.

Target:

* < **5%**

This is a usability metric.

---

### 2.3 Retrieval Metrics (GraphRAG-Specific)

#### 2.3.1 Evidence Coverage

**Definition:**
Percentage of claims that have at least **one supporting graph node or document chunk**.

Target:

* > **99%**

---

#### 2.3.2 Evidence Precision

**Definition:**
How often retrieved evidence is actually relevant to the claim.

Target:

* > **90%**

Low precision increases:

* latency
* verification cost
* confusion in audits

---

### 2.4 Latency Metrics (Enterprise-Tolerant)

Latency is important, but **not dominant**.

#### Chat Queries

* TTFT: **≤ 4s**
* End-to-end: **≤ 6s**

#### Knowledge / GraphRAG Queries

* TTFT: **≤ 8s**
* End-to-end: **≤ 12s**

These are acceptable in legal / finance workflows.

---

### 2.5 Auditability Metrics

#### 2.5.1 Trace Completeness

Every answer must have:

* retrieved nodes
* graph paths
* verification outcome
* regeneration decisions

Target:

* **100%**

If an answer cannot be traced, it must not be served.

---

## 3. Hallucination Benchmark Design

This section defines **how we test hallucination**, not how we avoid it.

---

### 3.1 Benchmark Philosophy

Do **not** benchmark:

* model knowledge
* trivia recall
* general intelligence

Benchmark:

* grounding
* refusal behavior
* consistency
* traceability

---

### 3.2 Claim-Centric Evaluation (Core)

All benchmarks operate at **claim level**, not answer level.

#### Step 1: Generate Answer

#### Step 2: Extract Claims

#### Step 3: Verify Each Claim

#### Step 4: Score Outcome

---

### 3.3 Claim Categories

Each claim is labeled into one category:

| Category     | Description                   |
| ------------ | ----------------------------- |
| Supported    | Evidence exists in graph/docs |
| Contradicted | Evidence disproves claim      |
| Unsupported  | No evidence found             |
| Ambiguous    | Evidence incomplete / unclear |

Only **Supported** claims are allowed to pass without regeneration.

---

### 3.4 Benchmark Types

#### 3.4.1 In-Domain Grounded Queries

* Questions fully answerable from knowledge base
* Tests retrieval + verification correctness

Expected:

* Near-zero hallucination
* No abstention

---

#### 3.4.2 Out-of-Scope Queries

* Questions **not answerable** from knowledge base
* Tests refusal behavior

Expected:

* Explicit abstention
* No fabricated answers

---

#### 3.4.3 Adversarial Queries

* Questions that *sound* answerable
* Subtle missing facts

Example:

> “What clause allows early termination in Contract X?”

When no such clause exists.

Expected:

* Abstention or clarification request

---

#### 3.4.4 Partial-Knowledge Queries

* Some facts exist, others don’t

Expected:

* Partial answer + explicit uncertainty
* No guessing

---

### 3.5 Regression Hallucination Tests

Every change to:

* prompt
* retrieval logic
* verification logic

must be run against:

* a fixed hallucination benchmark set

Any increase in:

* CHR
* UAR

is a **hard failure**.

---

## 4. Non-Goals (Important)

This system explicitly does **not** aim to:

* be creative
* answer open-ended speculative questions
* replace human judgment
* operate without knowledge boundaries

It is a **bounded reasoning system**.

---

# 5. System Architecture

## 5.1 High-Level Architecture

The system is designed as a **multi-stage, local-first reasoning pipeline**.

Key principle:

> **LLMs never access raw enterprise data directly. They operate only on retrieved, bounded context.**

### Logical Components

```
┌────────────┐
│   Client   │ (Browser)
└─────┬──────┘
      │
      │ LangGraph Pipeline
      ▼ ═════════════════
      │
      ├─────────────► Retrieval (neo4j-graphrag)
      │                     │ (Node 2)
      │                     ▼
      │              Evidence Set
      │
      ▼
┌────────────────────┐
│  Generator (LLM)   │ (Node 1)
└─────┬──────────────┘
      │
      ▼
┌────────────────────┐
│ Claim Extraction   │ (LangChain)
└─────┬──────────────┘
      │
      ▼
┌────────────────────┐
│ Verification Layer │ (Node 2)
└─────┬──────────────┘
      │
      ▼
┌────────────────────┐
│ Response Controller│ (LangGraph Nodes)
└─────┬──────────────┘
      │
      ▼
┌────────────┐
│   Output   │ (Alpine UI)
└────────────┘

```

---

## 5.2 Node-Level Deployment

### Node 1 — **Inference Node (RTX 2060)**

Responsibilities:

* LLM generation
* Prompt construction
* Partial regeneration
* Final answer assembly

Hard rule:

* **No graph traversal**
* **No embedding computation**
* **No verification**

This node is latency-sensitive.

---

### Node 2 — **Knowledge + Verification Node (GTX 1660)**

Responsibilities:

* GraphDB queries
* Embedding search
* Reranking
* Claim verification
* Evidence scoring

This node is correctness-sensitive, not latency-sensitive.

---

## 6. Request Lifecycle (End-to-End Flow)

This is the **canonical execution path**.
All optimizations must preserve this structure.

---

### Step 1: Query Intake

**Component:** Query Orchestrator (Node 1)

Responsibilities:

* Normalize input
* Detect query type:

  * chat
  * factual lookup
  * analytical / multi-hop
* Assign execution policy

Output:

```json
{
  "query": "...",
  "query_type": "graph_rag",
  "confidence_requirement": "high"
}
```

---

### Step 2: Retrieval (GraphRAG)

**Component:** Retrieval Layer (Node 2)

Retrieval is **two-stage**:

1. **Graph Traversal**

   * Explicit edges
   * Relationship constraints
2. **Semantic Augmentation**

   * Embedding similarity
   * Limited top-k

Hard limits:

* Max nodes: 50–100
* Max tokens injected: 512–1024

Output:

```json
{
  "evidence_nodes": [...],
  "documents": [...],
  "graph_paths": [...]
}
```

---

### Step 3: Context Packaging

**Component:** Context Packager (Node 1)

Responsibilities:

* Deduplicate evidence
* Rank by relevance
* Convert to **structured context**

Context format:

* Bullet facts
* Tables
* Explicit source IDs

LLMs should **never receive raw documents**.

---

### Step 4: Answer Generation

**Component:** Generator LLM (Node 1)

Model:

* DeepSeek-R1-Distill-Llama-8B (Q4)

Prompt rules:

* Must cite evidence IDs
* Must not speculate
* Must state uncertainty explicitly

Output includes:

* Answer text
* Inline evidence references

---

### Step 5: Claim Extraction

**Component:** Claim Extractor (Node 1, CPU)

Purpose:

* Convert free-form text into **atomic claims**

Example:

```
"The contract allows early termination after 90 days."
```

Becomes:

```json
{
  "subject": "contract",
  "predicate": "allows termination",
  "object": "after 90 days"
}
```

This step is deterministic and rule-based where possible.

---

### Step 6: Claim Verification

**Component:** Verification Engine (Node 2)

Each claim is checked against:

* Graph edges
* Document snippets
* Prior verified claims

Outcomes:

* supported
* contradicted
* unsupported
* ambiguous

---

### Step 7: Response Control

**Component:** Response Controller (Node 1)

Decision logic:

| Verification Result | Action                              |
| ------------------- | ----------------------------------- |
| All supported       | Return answer                       |
| Minor unsupported   | Regenerate section                  |
| Contradiction       | Block + regenerate                  |
| Ambiguous           | Add uncertainty / ask clarification |

This is **policy-driven**, not model-driven.

---

## 7. Architecture Guarantees

The system guarantees:

* No claim without evidence
* No silent guessing
* No unverifiable output
* Deterministic regeneration decisions

If a guarantee cannot be met:

* the system must abstain

---

## 8. Python-Centric Technology Stack

This section lists **preferred tools**, not rigid requirements.

---

### 8.1 Core Language

* **Python 3.10+**

Reasons:

* ecosystem maturity
* LLM tooling
* graph libraries
* rapid iteration

---

### 8.2 LLM Inference
Here’s an **updated version of section 8.2**, rewritten to reflect the decision to use **Ollama**, while keeping the document *engineering-focused* and future-proof.

You can drop this directly into your markdown.

---

### 8.2 LLM Inference

LLM inference is treated as a **replaceable runtime dependency**, not a core logic component.
All safety, verification, and orchestration logic exists **outside** the inference engine.

---

**Primary**

* **Ollama**

  * Local LLM runtime and model manager
  * Serves GGUF-based models via HTTP API
  * GPU-accelerated inference (CUDA)
  * Simple deployment and lifecycle management
  * Used as a **stateless inference backend**

* **Models**

  * DeepSeek-R1-Distill-Llama-8B (Q4) — primary generator
  * Small instruction / NLI model (3B–7B Q4) — verifier
  * All models run fully on a single GPU (no layer splitting)

---

**Integration Pattern**

* Ollama is accessed only through internal Python services
* Clients never interact with Ollama directly
* All responses are:

  * schema-validated
  * post-processed
  * verified before exposure

---

### 8.3 Graph Layer

Options (pick one initially):

* Neo4j (Cypher, strong tooling)
* RedisGraph (lighter, faster)
* NetworkX (for prototypes)

Graph must support:

* path queries
* relationship types
* metadata on nodes/edges

---

### 8.4 Vector / Embeddings

* `sentence-transformers`
* `faiss` (CPU index)
* Optional GPU FAISS on Node 2

Embedding storage:

* in-memory preferred
* disk only for cold data

---

### 8.5 Verification Models

* Small instruction-tuned LLM (3B–7B Q4)
* Or NLI model (entailment-based)

Verification runs:

* batched
* non-streaming
* timeout-safe

---

### 8.6 Orchestration & APIs

* `FastAPI` (inter-node APIs)
* `LangGraph` (Workflow orchestration)
* `LangChain` (LLM abstraction & Structured Output)
* JSON over HTTP
* Stateless calls

### 8.8 Logging & Observability

* `structlog` for structured JSON logging
* `LangSmith` for pipeline tracing
* `Prometheus` (planned)

No message queues initially.

---

### 8.7 Observability

Mandatory:

* Structured logs (JSON)
* Per-claim verification logs
* Latency breakdowns

Optional:

* Prometheus metrics
* Simple dashboards

---

## 9. What We Still Haven’t Defined (On Purpose)

These will be addressed later:

* Exact prompts
* Schema for claims
* Regeneration thresholds
* Policy DSL
* Human-in-the-loop workflows

They depend on:

* domain
* data shape
* enterprise tolerance

---

# 10. Prompt Design (Generator + Verifier)

Prompting is treated as **system logic**, not text generation.

All prompts must be:

* versioned
* testable
* regression-checked

---

## 10.1 Generator Prompt (Primary LLM)

### Design Goals

* Force grounding
* Penalize speculation
* Encourage explicit uncertainty
* Produce machine-parseable structure

---

### 10.1.1 Generator System Prompt (Conceptual)

Core constraints embedded in the system prompt:

* You may only use the provided context.
* Every factual statement must reference evidence IDs.
* If evidence is missing, state uncertainty.
* Do not infer beyond retrieved facts.

**The model is explicitly discouraged from “being helpful.”**

---

### 10.1.2 Generator Output Contract

The generator must return **structured output**, not free text.

Recommended format (JSON-first):

```json
{
  "answer": [
    {
      "statement": "...",
      "evidence_ids": ["E12", "E19"]
    }
  ],
  "uncertainties": [
    {
      "statement": "...",
      "reason": "insufficient evidence"
    }
  ]
}
```

Free-form text is rendered **only after verification**.

---

### 10.1.3 Anti-Patterns to Avoid

❌ “Based on my knowledge…”
❌ “It is likely that…”
❌ “Typically, such systems…”

These phrases correlate strongly with hallucinations.

---

## 10.2 Claim Extraction Design

Claim extraction must be:

* deterministic
* explainable
* minimally model-dependent

---

### 10.2.1 Claim Definition

A **claim** is an atomic factual assertion that can be verified independently.

Structure:

```json
{
  "claim_id": "C123",
  "subject": "...",
  "predicate": "...",
  "object": "...",
  "qualifiers": {
    "time": "...",
    "conditions": "..."
  },
  "evidence_refs": ["E12"]
}
```

---

### 10.2.2 Extraction Strategy

Preferred order:

1. Rule-based parsing (regex, patterns)
2. Lightweight LLM extraction (only if needed)
3. Manual fallbacks

Claims should be **minimal**, even if it increases count.

---

### 10.2.3 Claim Granularity Rule

> If a claim cannot be disproved independently, it is too large.

---

## 11. Verification Engine Design

Verification is **the core safety mechanism**.

---

## 11.1 Verification Inputs

Each verification request includes:

* Claim
* Supporting evidence nodes
* Graph paths
* Source metadata

---

## 11.2 Verification Outcomes

Each claim must resolve to **one** of:

| Outcome      | Meaning                    |
| ------------ | -------------------------- |
| supported    | Evidence clearly supports  |
| contradicted | Evidence disproves         |
| unsupported  | No evidence                |
| ambiguous    | Evidence unclear / partial |

Only `supported` is allowed to pass silently.

---

## 11.3 Verification Methods

Verification is multi-layered.

### Layer 1: Graph Consistency

* Edge existence
* Direction correctness
* Relationship type match

### Layer 2: Textual Support

* Document snippets
* Clause matching
* Section references

### Layer 3: Semantic Entailment (Optional)

* NLI model
* Conservative thresholds

---

## 11.4 Verification Policy Rules

Hard rules:

* Unsupported ≠ false → requires regeneration
* Contradicted → block output
* Ambiguous → must surface uncertainty

Soft rules:

* Low confidence → optional clarification
* Repeated ambiguity → escalate

---

## 12. Regeneration Strategy

Regeneration must be:

* targeted
* bounded
* explainable

---

### 12.1 Regeneration Scope

Allowed:

* Single sentence
* Single paragraph
* Single claim

Disallowed:

* Full answer regeneration by default

---

### 12.2 Regeneration Loop Limits

* Max regeneration attempts per claim: **2**
* Max total regeneration passes: **3**

After limits:

* Abstain or escalate

---

### 12.3 Regeneration Prompt Additions

Regeneration prompts include:

* Failed claim
* Reason for failure
* Allowed evidence set

This prevents the model from “searching” for new facts.

---

## 13. Failure Modes & Safe Fallbacks

Failures are expected.
Silently failing is unacceptable.

---

### 13.1 Known Failure Modes

| Failure              | Handling                 |
| -------------------- | ------------------------ |
| Retrieval miss       | Abstain                  |
| Verification timeout | Partial answer + warning |
| Model inconsistency  | Regenerate               |
| Graph inconsistency  | Flag data issue          |
| Resource exhaustion  | Graceful degrade         |

---

### 13.2 Safe Output Contract

If confidence < threshold:

* Answer must include uncertainty
* Or explicitly refuse

Never:

* guess
* fabricate
* overgeneralize

---

## 14. Testing Strategy (Local-First)

---

### 14.1 Unit Tests

* Claim extraction
* Verification logic
* Policy decisions

No LLM calls here.

---

### 14.2 Integration Tests

* Fixed prompts
* Fixed retrieval sets
* Deterministic outputs

LLM randomness must be minimized.

---

### 14.3 Hallucination Regression Tests

Mandatory before merges.

Metrics checked:

* CHR
* UAR
* CAR

Any regression blocks deployment.

---

## 15. Development Guardrails

These rules are non-negotiable:

* No direct LLM-to-database access
* No unchecked generation
* No silent fallbacks
* No prompt changes without benchmarks

---

# 16. Knowledge Modeling (GraphRAG Core)

The **graph is the source of truth**.
LLMs are consumers of graph-derived context.

---

## 16.1 Knowledge Representation Principles

Hard rules:

* Every fact must be representable as:

  * a node
  * an edge
  * or a node property
* Every relationship must be **typed**
* Every node must have **provenance metadata**

If knowledge cannot be structured, it must not be treated as authoritative.

---

## 16.2 Core Graph Schema (Minimal)

### 16.2.1 Node Types

| Node Type | Purpose                          |
| --------- | -------------------------------- |
| Entity    | People, orgs, systems, contracts |
| Document  | Policies, contracts, reports     |
| Clause    | Atomic legal / policy units      |
| Event     | Time-bound actions               |
| Concept   | Abstract definitions             |
| Source    | Origin of information            |

---

### 16.2.2 Edge Types

| Edge         | Meaning            |
| ------------ | ------------------ |
| REFERENCES   | Document → Clause  |
| DEFINES      | Document → Concept |
| INVOLVES     | Event → Entity     |
| GOVERNS      | Policy → Entity    |
| DEPENDS_ON   | Concept → Concept  |
| DERIVED_FROM | Node → Source      |

Edges must be **directional** and **semantically strict**.

---

## 16.3 Metadata (Non-Negotiable)

Every node must include:

```json
{
  "source_id": "...",
  "created_at": "...",
  "last_verified": "...",
  "confidence": 0.0-1.0,
  "access_level": "public | restricted | confidential"
}
```

Verification logic relies on this metadata.

---

## 17. Knowledge Ingestion Pipeline

Ingestion is **offline-first** and **reviewable**.

---

## 17.1 Ingestion Stages

```
Raw Data
   ↓
Parsing & Chunking
   ↓
Entity & Relation Extraction
   ↓
Human / Rule Validation
   ↓
Graph Insert
   ↓
Embedding Generation
```

LLMs may assist ingestion, but **never bypass validation**.

---

## 17.2 Parsing & Chunking

Rules:

* Chunks ≤ 300 tokens
* Semantic boundaries preserved
* Stable chunk IDs

Chunk ID stability is required for auditability.

---

## 17.3 Entity & Relation Extraction

Preferred methods:

1. Rules (regex, templates)
2. Deterministic parsers
3. LLM-assisted extraction (reviewed)

Extracted entities are **candidates**, not facts.

---

## 17.4 Human-in-the-Loop Validation

For regulated domains:

* Ingestion requires approval
* Changes are versioned
* Old facts are never deleted, only deprecated

---

## 18. Security & Access Boundaries

Security is enforced **before** inference.

---

## 18.1 Access Control Model

Every request has:

* user identity
* role
* clearance level

Graph traversal respects:

* node access_level
* edge access_level

LLMs never see data the user is not allowed to see.

---

## 18.2 Prompt-Level Data Filtering

Before context injection:

* remove restricted nodes
* redact sensitive fields
* re-rank allowed evidence only

This happens **outside** the LLM.

---

## 18.3 Audit Logging (Mandatory)

Log per request:

* user
* query
* retrieved node IDs
* claims generated
* verification outcomes
* final response hash

Logs must be immutable.

---

## 19. Deployment Modes

The system is designed to run in **multiple enterprise environments**.

---

## 19.1 Single-Node (Developer Mode)

* One machine
* CPU or single GPU
* Reduced datasets

Purpose:

* development
* testing
* debugging

---

## 19.2 Dual-Node (Production Lite)

Your current architecture:

* Node 1: Inference
* Node 2: Knowledge + Verification
* Private network (LAN / Wi-Fi)

Purpose:

* SMEs
* pilot deployments
* internal tools

---

## 19.3 Air-Gapped / On-Prem

Requirements:

* No outbound network
* Local package mirrors
* Offline model storage

All components must function without internet.

---

## 20. Operational Guardrails

---

## 20.1 Model Updates

* Models are versioned
* No hot-swapping without regression tests
* Old versions retained for audits

---

## 20.2 Knowledge Updates

* Graph updates are atomic
* Partial updates are rejected
* Verification confidence decays over time

---

## 20.3 Failure Handling Policy

If any critical component fails:

* System degrades safely
* No speculative output
* Explicit error or abstention

---

## 21. Development Roadmap (Internal)

This is a **suggested build order**, not a promise.

### Phase 1: Foundation (COMPLETE ✅)
* Dual-node setup (GTX 1660 + RTX 2060)
* Core Neo4j Repository
* Inference Proxy

### Phase 1.5: Library Migration (COMPLETE ✅)
* Migration to `neo4j-graphrag` retrievers
* LangChain `BaseChatModel` implementation

### Phase 2: Verification Pipeline (COMPLETE ✅)
* LangGraph state machine orchestration
* Pydantic-based claim models
* Graph + Semantic multi-layer verification

### Phase 3: Hardening & Observability (COMPLETE ✅)
* Structured logging with `structlog`
* LangSmith tracing integration
* Resilience patterns (Circuit Breakers)

### Phase 4: Domain & Real-World Ingestion (COMPLETE ✅)
* PDF/DocX parsing with metadata preservation
* Automated KG construction via `SimpleKGPipeline`
* Entity resolution and merge logic

### Phase 5: GUI & Manual Verification (COMPLETE ✅)
* Single-page Application (Alpine.js + Tailwind)
* Manual claim review interface
* Smart evidence highlighting

### Phase 6: Optimization & Benchmarking (IN PROGRESS 🏗️)
* Semantic threshold tuning
* Text2Cypher robustness improvements
* Systematic hallucination benchmarking


---

## 22. Final Non-Negotiable Principles

1. **Correctness > Fluency**
2. **Refusal > Guessing**
3. **Traceability > Cleverness**
4. **Systems > Models**
5. **Bounded Intelligence > General Intelligence**

---

## End of Core Development Guide (v0)

This document should evolve alongside:

* code
* benchmarks
* postmortems

Any architectural deviation must be documented here first.






