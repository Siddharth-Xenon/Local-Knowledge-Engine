"""
Script to verify Ollama setup on Node 1.
Checks:
1. Connectivity to Ollama
2. Availability of the specific model
3. Basic generation capability
"""

import asyncio
import sys
from typing import Any

import httpx

# Configuration matching app/config.py
OLLAMA_URL = "http://localhost:11434"
MODEL = "deepseek-r1:8b-llama-distill-q4_K_M"


async def verify_ollama() -> None:
    """Run verification checks."""
    print(f"🔍 Verifying Ollama at {OLLAMA_URL}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check Connectivity
        try:
            resp = await client.get(f"{OLLAMA_URL}/")
            if resp.status_code == 200:
                print("✅ Ollama is running and reachable.")
            else:
                print(f"⚠️  Ollama reachable but returned {resp.status_code}")
        except httpx.RequestError as e:
            print(f"❌ Could not connect to Ollama: {e}")
            print("   (Make sure 'ollama serve' is running)")
            sys.exit(1)

        # 2. Check Model Availability
        print(f"\n📦 Checking for model: {MODEL}...")
        try:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            found = False
            available_names = []
            
            for m in models:
                name = m.get("name")
                available_names.append(name)
                # Check for exact match or match including :latest
                if name == MODEL or name == f"{MODEL}:latest":
                    found = True
                    details = m.get("details", {})
                    size_gb = m.get("size", 0) / (1024**3)
                    print(f"✅ Model found!")
                    print(f"   - Family: {details.get('family', 'unknown')}")
                    print(f"   - Quantization: {details.get('quantization_level', 'unknown')}")
                    print(f"   - Size: {size_gb:.2f} GB")
                    break
            
            if not found:
                print(f"❌ Model '{MODEL}' not found.")
                print(f"   Available models: {', '.join(available_names)}")
                print(f"\n   Run this command to pull it:")
                print(f"   ollama pull {MODEL}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Failed to list models: {e}")
            sys.exit(1)

        # 3. Test Generation
        print(f"\n⚡ Testing generation (streaming off)...")
        prompt = "Explain why the sky is blue in one sentence."
        print(f"   Prompt: '{prompt}'")
        
        try:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120.0
            )
            resp.raise_for_status()
            result = resp.json()
            response_text = result.get("response", "").strip()
            
            print(f"✅ Generation successful!")
            print(f"   Response: \"{response_text}\"")
            print(f"   Duration: {result.get('total_duration', 0) / 1e9:.2f}s")
            
        except httpx.TimeoutException:
            print("❌ Generation timed out (model might be loading slowly).")
        except Exception as e:
            print(f"❌ Generation failed: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(verify_ollama())
    except KeyboardInterrupt:
        print("\nAborted.")
