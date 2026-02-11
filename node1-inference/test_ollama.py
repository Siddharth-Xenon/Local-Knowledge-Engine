import httpx
import asyncio
import json


async def test_ollama():
    url = "http://localhost:11434"
    model = "deepseek-r1:8b-llama-distill-q4_K_M"

    print(f"Testing Ollama at {url}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Check if server is up
        try:
            resp = await client.get(url)
            print(f"Status check: {resp.status_code}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return

        # 2. List models
        try:
            resp = await client.get(f"{url}/api/tags")
            print(f"Models check: {resp.status_code}")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                found = False
                for m in models:
                    print(f" - Found model: {m['name']}")
                    if m["name"] == model:
                        found = True

                if not found:
                    print(f"WARNING: Model '{model}' not found in list!")
        except Exception as e:
            print(f"Failed to list models: {e}")

        # 3. Test Generate
        print(f"\nTesting generation with model '{model}'...")
        try:
            resp = await client.post(
                f"{url}/api/generate",
                json={"model": model, "prompt": "Hello", "stream": False},
            )
            print(f"Generate status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Error body: {resp.text}")
            else:
                print(f"Success! Response: {resp.json().get('response')[:50]}...")

        except Exception as e:
            print(f"Failed to generate: {repr(e)}")


if __name__ == "__main__":
    asyncio.run(test_ollama())
