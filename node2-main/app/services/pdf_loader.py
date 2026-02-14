"""Service for loading and chunking local PDF files."""

import logging
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class LocalPDFLoader:
    """Handles loading and chunking of local PDF files."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the loader with chunking parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def load_and_split(self, file_path: str | Path) -> list[Document]:
        """Load a PDF file and split it into chunks.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of Document objects representing the chunks.

        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"PDF file not found: {path}")
            raise FileNotFoundError(f"PDF file not found: {path}")

        try:
            logger.info(f"Loading PDF: {path}")
            loader = PyMuPDFLoader(str(path))
            # PyMuPDFLoader returns one Document per page by default
            pages = loader.load()
            logger.debug(f"Loaded {len(pages)} pages from {path.name}")

            # Add file metadata
            for page in pages:
                # Ensure source is absolute path string for traceability
                page.metadata["source"] = str(path.absolute())
                page.metadata["filename"] = path.name

            # Split pages into chunks
            chunks = self.text_splitter.split_documents(pages)
            logger.info(f"Split {path.name} into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.exception(f"Failed to load PDF {path}")
            raise RuntimeError(f"Failed to load PDF {path}: {str(e)}") from e
