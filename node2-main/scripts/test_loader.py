import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.pdf_loader import LocalPDFLoader
import logging

logging.basicConfig(level=logging.INFO)


def main():
    file_path = Path("data/pdf/Apple stock during pandemic.pdf")
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    print(f"Testing loader with {file_path}...")
    try:
        loader = LocalPDFLoader()
        chunks = loader.load_and_split(file_path)
        print(f"Successfully loaded {len(chunks)} chunks.")
        if chunks:
            print(f"First chunk preview: {chunks[0].page_content[:100]}...")
            print(f"Metadata: {chunks[0].metadata}")
    except Exception as e:
        print(f"Loader failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
