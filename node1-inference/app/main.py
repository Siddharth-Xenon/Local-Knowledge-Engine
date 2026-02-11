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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan.
    - Check if Ollama is running.
    - Start Ollama if not running.
    - Cleanup on shutdown.
    """
    ollama_process = None
    started_by_us = False

    # 1. Check if Ollama is already running
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{settings.ollama_url}")
            logger.info("Ollama is already running.")
    except httpx.RequestError:
        # 2. Start Ollama
        logger.info("Ollama not found. Starting subprocess...")
        try:
            # Resolve executable path to avoid shell=True
            if settings.ollama_path == "ollama":
                ollama_exe = shutil.which("ollama")
                if not ollama_exe:
                    raise FileNotFoundError("Could not find 'ollama' in PATH")
            else:
                ollama_exe = settings.ollama_path

            ollama_process = subprocess.Popen(
                [ollama_exe, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,  # Important for signal handling
            )
            started_by_us = True
            logger.info(f"Started Ollama (PID: {ollama_process.pid})")

            # 3. Wait for startup
            start_time = time.time()
            while time.time() - start_time < settings.ollama_start_timeout:
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(f"{settings.ollama_url}")
                        if resp.status_code == 200:
                            logger.info("Ollama is ready.")
                            break
                except httpx.RequestError:
                    await asyncio.sleep(1)
            else:
                logger.warning("Ollama startup timed out, but proceeding.")

        except FileNotFoundError:
            logger.error(
                f"Could not find '{settings.ollama_path}'. Please install Ollama or check PATH."
            )
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")

    yield

    # Shutdown logic
    if started_by_us and ollama_process:
        logger.info("Stopping Ollama subprocess...")
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
