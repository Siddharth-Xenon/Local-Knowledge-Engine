# Local PDF Ingestion Pipeline

## Overview
The Local PDF Ingestion Pipeline is a lightweight mechanism to ingest local PDF documents into the `graphrag` Neo4j database. It is designed to be a simple, single-source alternative to complex graph builders, focusing on processing local files for Retrieval Augmented Generation (RAG).

## Architecture
The pipeline consists of three main components:

1.  **Loader (`app/services/pdf_loader.py`)**:
    *   Uses `PyMuPDF` (via `langchain_community`) to extract text from PDFs.
    *   Splits text into chunks using `RecursiveCharacterTextSplitter`.
    *   Preserves metadata such as page numbers and source filenames.

2.  **Ingestion Service (`app/services/ingestion.py`)**:
    *   Orchestrates the loading and embedding process.
    *   Uses the project's standard `EmbeddingFactory` (SentenceTransformers) to generate vector embeddings.
    *   Stores chunks in Neo4j with the `foundational` schema:
        *   `(:Document {filename, source})`
        *   `(:Element {text, embedding, page, source})`
        *   `(:Document)-[:HAS_CHUNK]->(:Element)`
    *   **Database Targeting**: Explicitly writes to the `graphrag` database, keeping it separate from the main application's transactional data.

3.  **CLI Tool (`scripts/ingest_pdfs.py`)**:
    *   User-facing script to trigger ingestion.
    *   Supports processing a single file or recursively scanning a directory.

## Usage

### Prerequisites
Ensure dependencies are installed:
```bash
pip install langchain-community pymupdf neo4j-graphrag
```

### Running Ingestion
To ingest a single PDF or a folder of PDFs into the `graphrag` database:

```bash
# Ingest single file
python scripts/ingest_pdfs.py "path/to/document.pdf"

# Ingest entire folder
python scripts/ingest_pdfs.py "path/to/documents_folder"
```

### Database Configuration
*   **Ingestion**: Writes to `database="graphrag"`.
*   **Main App**: Defaults to the standard Neo4j database (e.g. `neo4j` or `test`), ensuring financial data and ingested knowledge remain logically separated.

## dependency
*   `langchain-community`
*   `pymupdf`
*   `neo4j-graphrag`
*   `langchain`
