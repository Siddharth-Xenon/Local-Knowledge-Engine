"""
Script to verify Prompt Manager integration on Node 1.
Checks:
1. Raw prompt generation (legacy support)
2. Managed prompt generation (template rendering)
3. Error handling for missing templates
"""

import asyncio
import sys
import httpx

# Configuration
NODE1_URL = "http://localhost:8001"
MODEL = "deepseek-r1:8b-llama-distill-q4_K_M"

async def verify_prompt_manager() -> None:
    print(f"[SEARCHING] Verifying Prompt Manager at {NODE1_URL}...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Test Raw Prompt (Backward Compatibility)
        print("\n[TEST 1] Raw Prompt (Legacy Mode)")
        try:
            resp = await client.post(
                f"{NODE1_URL}/generate",
                json={
                    "prompt": "Say hello!",
                    "model": MODEL
                }
            )
            if resp.status_code == 200:
                print("[PASS] Raw prompt worked")
            else:
                print(f"[FAIL] Raw prompt failed: {resp.text}")
        except Exception as e:
            print(f"[FAIL] Raw prompt error: {e}")

        # 2. Test Managed Prompt (RAG v1.0.0)
        print("\n[TEST 2] Managed Prompt (RAG v1.0.0)")
        variables = {
            "query": "What is the capital of France?",
            "context": {
                "evidence": [
                    {"id": "1", "text": "Paris is the capital of France."}
                ]
            }
        }
        
        try:
            resp = await client.post(
                f"{NODE1_URL}/generate",
                json={
                    "prompt_key": "rag",
                    "version": "1.0.0",
                    "variables": variables,
                    "model": MODEL
                }
            )
            if resp.status_code == 200:
                print("[PASS] Managed prompt worked")
                print(f"   Response: {resp.json().get('response', '')[:50]}...")
            else:
                print(f"[FAIL] Managed prompt failed: {resp.text}")
        except Exception as e:
            print(f"[FAIL] Managed prompt error: {e}")

        # 3. Test Missing Template
        print("\n[TEST 3] Missing Template Error")
        try:
            resp = await client.post(
                f"{NODE1_URL}/generate",
                json={
                    "prompt_key": "rag",
                    "version": "9.9.9",  # Non-existent
                    "variables": {}
                }
            )
            if resp.status_code == 400 and "render failed" in resp.text:
                print("[PASS] Correctly caught missing template")
            else:
                print(f"[FAIL] Unexpected behavior: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[FAIL] Error: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_prompt_manager())
