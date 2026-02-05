"""Node 2 Main Application Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the main application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "knowledge-engine-dev"

    # Node 1 Inference Server (RTX 2060 machine)
    # Easy to update: just change this when network changes
    node1_url: str = "http://192.168.0.103:8001"
    inference_timeout: int = 60

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
