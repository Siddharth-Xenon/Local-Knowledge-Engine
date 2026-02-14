"""Node 2 Main Application Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the main application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "knowledge-engine-dev"
    query_database: str = "graphrag"

    # Node 1 Inference Server (RTX 2060 machine)
    node1_url: str = "http://0.0.0.0:8001"
    inference_timeout: int = 240

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Embedding Configuration
    embedding_model_name: str = "intfloat/e5-base-v2"
    embedding_dimension: int = 768

    # Neo4j Index Configuration
    vector_index_name: str = "rule_embedding"
    fulltext_index_name: str = "entity_fulltext"

    # Retrieval Configuration
    retriever_type: str = "text2cypher"  # "vector" | "text2cypher" | "hybrid"
    retrieval_max_nodes: int = 50
    semantic_top_k: int = 10

    # LLM
    openai_api_key: str = ""

    # LangSmith Tracing (Optional)
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "local-knowledge-engine"

    # LLM model
    llm_config: dict[str, str] = {
        "retriever_llm": "gpt-5",
        "claim_extractor_llm": "gpt-5-mini",
        "verifier_llm": "gpt-5-nano",
        "query_llm": "gpt-5-nano",
    }


settings = Settings()
