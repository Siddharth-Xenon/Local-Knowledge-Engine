"""Node 1 Inference Server - Minimal Ollama Wrapper."""

import asyncio
import logging
import subprocess
import time
import shutil
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.generate import router as generate_router
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ensure_ollama_service() -> subprocess.Popen | None:
    """
    Ensure the Ollama service is running.
    Returns the subprocess object if we started it, else None.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{settings.ollama_url}")
            logger.info("✅ Ollama service is reachable.")
            return None
    except httpx.RequestError:
        pass  # Not running, proceed to start it

    logger.info("⚠️ Ollama service not found. Starting subprocess...")
    try:
        # Resolve executable path
        if settings.ollama_path == "ollama":
            ollama_exe = shutil.which("ollama")
            if not ollama_exe:
                raise FileNotFoundError("Could not find 'ollama' in PATH")
        else:
            ollama_exe = settings.ollama_path

        # Start process
        process = subprocess.Popen(
            [ollama_exe, "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            encoding="utf-8",
            errors="replace",
        )
        logger.info(f"🚀 Started Ollama service (PID: {process.pid})")

        # Wait for startup
        start_time = time.time()
        while time.time() - start_time < settings.ollama_start_timeout:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{settings.ollama_url}")
                    if resp.status_code == 200:
                        logger.info("✅ Ollama service is ready.")
                        return process
            except httpx.RequestError:
                await asyncio.sleep(1)

        logger.warning("❌ Ollama startup timed out, but proceeding.")
        return process

    except Exception as e:
        logger.error(f"❌ Failed to start Ollama: {e}")
        return None


async def ensure_model_ready(model_name: str) -> None:
    """
    Ensure the specified model is pulled and loaded.
    1. Check if installed.
    2. Pull if missing.
    3. Preload into memory.
    """
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 1. Check availability
            resp = await client.get(f"{settings.ollama_url}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                # Check for exact match or :latest
                if model_name not in models and f"{model_name}:latest" not in models:
                    logger.info(
                        f"📥 Model '{model_name}' not found locally. Pulling... "
                        "(this may take a while)"
                    )
                    # 2. Pull Model
                    pull_resp = await client.post(
                        f"{settings.ollama_url}/api/pull",
                        json={"model": model_name, "stream": False},
                        timeout=None,  # Blocking call for download
                    )
                    pull_resp.raise_for_status()
                    logger.info(f"✅ Model '{model_name}' pulled successfully.")
                else:
                    logger.info(
                        f"📦 Model '{model_name}' found locally. Skipping download."
                    )

            # 3. Preload via CLI (to ensure visibility in 'ollama ps')
            logger.info(f"🔥 Preloading model '{model_name}' via CLI...")
            # Using ollama run with empty input sends one request and exits,
            # but Ollama keeps the model in memory for 5 mins.
            subprocess.run(
                [settings.ollama_path, "run", model_name, ""],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            logger.info(f"✅ Model '{model_name}' signaled to load.")

    except httpx.ReadTimeout:
        logger.warning(f"⚠️ Preloading '{model_name}' timed out, but likely started.")
    except Exception as e:
        logger.warning(f"❌ Failed to ensure model availability: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan.
    """
    # 1. Start Service
    ollama_process = await ensure_ollama_service()

    # 2. Prepare Model
    await ensure_model_ready(settings.default_model)

    yield

    # 3. Cleanup
    if ollama_process:
        logger.info("🛑 Stopping Ollama subprocess...")
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ollama_process.kill()
        logger.info("Ollama stopped.")


app = FastAPI(
    title="Node 1 - Inference Server",
    description="Dedicated inference server wrapping Ollama (RTX 2060)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Node 1 Inference Server", "status": "running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
