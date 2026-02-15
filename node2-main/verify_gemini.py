import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.inference.factory import LLMFactory
from app.config import settings


def test_sync_invoke():
    print("Testing Sync Invoke (via Factory)...")
    try:
        # Assuming settings.gemini_model is set to a gemini model
        llm = LLMFactory.create(model_name=settings.gemini_model)
        response = llm.invoke("Hello, say 'sync factory test passed'.")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Sync Invoke Failed: {e}")


async def test_async_invoke():
    print("\nTesting Async Invoke (via Factory)...")
    try:
        llm = LLMFactory.create(model_name=settings.gemini_model)
        response = await llm.ainvoke("Hello, say 'async factory test passed'.")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Async Invoke Failed: {e}")


if __name__ == "__main__":
    if not settings.google_api_key:
        print(
            "WARNING: google_api_key is not set in settings. Trying env var GOOGLE_API_KEY directly."
        )
        # Fallback for testing if .env isn't loaded by settings yet in this script context
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

    test_sync_invoke()
    asyncio.run(test_async_invoke())
