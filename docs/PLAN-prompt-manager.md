# Plan: Prompt Manager System (Node 1 Focus)

> **Context:**
> - **Node 1 (RTX 2060):** Responsible for *Prompt Construction* and LLM Generation.
> - **Principles:** SOLID Design, Simple Versioning (SemVer), Audit Logging.
> - **Scope:** No A/B testing infrastructure needed now.

---

## 1. Overview

Move **Prompt Construction** logic to **Node 1**.
Implement a **Prompt Manager** that treats prompts as versioned assets.
Apply **SOLID principles**:
- **SRP:** `PromptLoader` (loads files), `PromptRenderer` (binds data), `PromptRegistry` (config).
- **OCP:** Add new prompt types without changing core logic.
- **DIP:** Generator depends on `IPromptEngine` interface, not concrete templates.

## 2. Success Criteria

| Metric | Target |
|--------|--------|
| **Versioning** | Explicit SemVer folders/files (e.g., `prompts/rag/v1.0.0.j2`) |
| **Audit** | Every generation logs `prompt_name`, `version`, and `final_text` |
| **Simplicity** | Default prompt logic if no version specified (latest stable) |
| **Performance** | Template caching (load once, render many) |

## 3. Architecture

### File Structure (on Node 1)
```
node1-inference/
├── app/
│   ├── core/
│   │   └── interfaces.py      # IPromptEngine protocol
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── engine.py           # Concrete implementation (Jinja2)
│   │   ├── loader.py           # File system logic
│   │   └── templates/
│   │       ├── rag/
│   │       │   ├── v1.0.0.j2
│   │       │   └── v1.1.0.j2
│   │       └── chat/
│   │           └── v1.0.0.j2
│   ├── services/
│   │   └── generation.py       # Orchestrator
```

### Data Flow
1. **Node 2** calls `POST /generate`:
   ```json
   {
     "prompt_key": "rag",
     "version": "1.0.0",
     "variables": { "context": "...", "query": "..." }
   }
   ```
2. **Node 1** `GenerationService`:
   - Calls `PromptEngine.render("rag", "1.0.0", variables)`
   - Engine delegates to `Loader` -> gets template -> Jinja2 render
   - Returns final string
3. **Node 1** `GenerationService`:
   - Logs audit trail (INFO level): `[AUDIT] PROMPT: rag:1.0.0 | HASH: ...`
   - Sends string to Ollama

## 4. Task Breakdown

### Task 4.1: Template Structure & Loader (SRP)
- **Agent:** `backend-specialist`
- **Output:**
  - `app/prompts/templates/rag/v1.0.0.j2` (Initial template)
  - `Loader` class that finds files by `family/version` path.
- **Verify:** `loader.get_template("rag", "1.0.0")` returns content.

### Task 4.2: Prompt Engine (DIP/OCP)
- **Agent:** `backend-specialist`
- **Output:** 
  - `JinjaPromptEngine` implementing `IPromptEngine`.
  - Caching logic (lru_cache) for compiled templates.
- **Verify:** Render "Hello {{name}}" -> "Hello User".

### Task 4.3: API & Service Integration
- **Agent:** `api-patterns`
- **Output:**
  - Update `GenerateRequest` (add `prompt_key`, `variables`).
  - Update `generate` endpoint to use `PromptEngine`.
  - Add explicit error handling for missing versions.
- **Verify:** curl request with valid/invalid version.

## 5. Phase X: Verification
- [ ] **Unit:** `test_prompt_loading.py` (mock filesystem)
- [ ] **Unit:** `test_rendering.py` (check variable substitution)
- [ ] **Integration:** Full end-to-end `POST /generate` check
- [ ] **Audit:** Verify logs show prompt version used
