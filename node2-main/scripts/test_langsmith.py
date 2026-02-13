"""Quick smoke test: verify LangSmith tracing captures Node1ChatModel calls.

Usage:
    cd node2-main
    .\venv\Scripts\activate
    python scripts/test_langsmith.py
"""

import asyncio
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

# Set LangSmith env vars from .env
os.environ.setdefault("LANGSMITH_TRACING", os.getenv("LANGSMITH_TRACING", "false"))
os.environ.setdefault("LANGSMITH_ENDPOINT", os.getenv("LANGSMITH_ENDPOINT", ""))
os.environ.setdefault("LANGSMITH_API_KEY", os.getenv("LANGSMITH_API_KEY", ""))
os.environ.setdefault("LANGSMITH_PROJECT", os.getenv("LANGSMITH_PROJECT", "graphrag"))

print(f"LANGSMITH_TRACING = {os.environ.get('LANGSMITH_TRACING')}")
print(f"LANGSMITH_PROJECT = {os.environ.get('LANGSMITH_PROJECT')}")
print(
    f"LANGSMITH_API_KEY = {'***' + os.environ.get('LANGSMITH_API_KEY', '')[-6:] if os.environ.get('LANGSMITH_API_KEY') else 'NOT SET'}"
)
print()


async def main():
    from langchain_core.messages import HumanMessage

    from app.inference.llm_adapter import Node1ChatModel

    # Use 240s timeout to match the production setting
    llm = Node1ChatModel(timeout=240)
    print(f"Node1ChatModel -> {llm.base_url}")
    print("Sending test prompt to Node 1 (timeout: 240s)...")
    print("-" * 50)

    try:
        # Async call (primary path used in the pipeline)
        result = await llm.ainvoke(
            [HumanMessage(content="Say hello in exactly 5 words.")]
        )
        print(f"Response: {result.content[:300]}")
        print("-" * 50)
        print()
        print("✅ LLM call completed successfully!")
        print("   Check LangSmith dashboard for the trace:")
        print(f"   https://smith.langchain.com")
        print(f"   Project: {os.environ.get('LANGSMITH_PROJECT', 'graphrag')}")
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        print()
        print("Even on failure, LangSmith should have captured the trace.")
        print("Check: https://smith.langchain.com")


if __name__ == "__main__":
    asyncio.run(main())
