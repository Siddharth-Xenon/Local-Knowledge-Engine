"""Node 1 Inference Server Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the inference server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    default_model: str = "deepseek-r1:8b-llama-distill-q4_K_M"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001


settings = Settings()
