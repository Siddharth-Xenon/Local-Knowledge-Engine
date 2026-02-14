# PLAN-local-pdf-ingestion

> **Goal:** Implement a lightweight, synchronous pipeline to ingest local PDF documents into Neo4j vector store.

## 1. Overview
We need a simple, reliable way to ingest local PDF files into our Knowledge Graph (Neo4j). This pipeline will read PDFs from a local directory, extract text using `PyMuPDF`, chunk the text, and store both the text chunks and their embeddings in Neo4j. Unlike the complex `llm-graph-builder`, this will be a focused, single-source implementation (Local File -> Neo4j).

## 2. Project Type
**BACKEND**

## 3. Success Criteria
1.  **Parsing:** Successfully extract text from PDF files using `PyMuPDF`.
2.  **Chunking:** Split text into semantic chunks with metadata (page number, source file).
3.  **Storage:** Store chunks in Neo4j with `Element` label and vector embeddings.
4.  **Retrieval:** confirm that existing retrieval pipeline can find these chunks.
5.  **Simplicity:** Single CLI command to run ingestion.

## 4. Tech Stack
| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Loader** | `langchain_community.document_loaders.PyMuPDFLoader` | Fast, accurate text extraction with metadata. |
| **Splitter** | `RecursiveCharacterTextSplitter` | Standard LangChain splitter for preserving context. |
| **Vector Store** | `Neo4jVector` / Custom Cypher | Direct integration with our existing Neo4j instance. |
| **Embeddings** | `SentenceTransformer` (via Node 1 or Local) | Consistent with existing `rule_embedding` index. |
| **Language** | Python 3.11 | Existing backend language. |

## 5. File Structure
```
node2-main/
├── app/
│   ├── services/
│   │   ├── ingestion.py       # [NEW] Core ingestion service logic
│   │   └── pdf_loader.py      # [NEW] Wrapper for PDF loading/chunking
├── scripts/
│   └── ingest_pdfs.py         # [NEW] CLI entry point for ingestion
```

## 6. Task Breakdown

### Phase 1: Foundation
| Task ID | Name | Agent | Skill | Priority | Input/Output/Verify |
|---------|------|-------|-------|----------|---------------------|
| **1.1** | Add Dependencies | `backend-specialist` | `python-patterns` | P0 | **In:** `pyproject.toml` or `requirements.txt`<br>**Out:** Installed `pymupdf` <br>**Verify:** `import fitz` succeeds. |
| **1.2** | Create PDF Loader | `backend-specialist` | `clean-code` | P1 | **In:** `app/services/pdf_loader.py`<br>**Out:** Class `LocalPDFLoader` that returns list of Chunks.<br>**Verify:** Unit test parsing a dummy PDF. |

### Phase 2: Ingestion Logic
| Task ID | Name | Agent | Skill | Priority | Input/Output/Verify |
|---------|------|-------|-------|----------|---------------------|
| **2.1** | Create Ingestion Service | `backend-specialist` | `database-platform` | P1 | **In:** `app/services/ingestion.py`<br>**Out:** `IngestionService.ingest_file(path)`<br>**Verify:** Service connects to Neo4j and processes chunks. |
| **2.2** | Implement Neo4j Write | `backend-specialist` | `database-platform` | P1 | **In:** `app/services/ingestion.py`<br>**Out:** Cypher queries to create `(:Element)` nodes.<br>**Verify:** Check Neo4j Browser for new nodes. |

### Phase 3: CLI & Integration
| Task ID | Name | Agent | Skill | Priority | Input/Output/Verify |
|---------|------|-------|-------|----------|---------------------|
| **3.1** | Create Ingestion Script | `backend-specialist` | `bash-linux` | P2 | **In:** `scripts/ingest_pdfs.py`<br>**Out:** CLI tool accepting folder path.<br>**Verify:** Run `python scripts/ingest_pdfs.py ./data` and see success logs. |

## 7. Phase X: Verification Checklist
### Automated Checks
- [ ] **Linting:** `flake8 app/services/ingestion.py scripts/ingest_pdfs.py`
- [ ] **Type Check:** `mypy app/services/ingestion.py`

### Manual Verification
- [ ] **Functionality:** Place `test.pdf` in `data/`, run script.
- [ ] **Database:** Query `MATCH (n:Element) RETURN n LIMIT 5` in Neo4j.
- [ ] **Retrieval:** Use Node 2 API to ask a question answered by the PDF.
