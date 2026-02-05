"""Node 1 Inference Server - Minimal Ollama Wrapper."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.generate import router as generate_router
from app.config import settings

app = FastAPI(
    title="Node 1 - Inference Server",
    description="Dedicated inference server wrapping Ollama (RTX 2060)",
    version="0.1.0",
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
