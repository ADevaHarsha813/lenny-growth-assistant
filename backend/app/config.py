from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal
import os


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: Literal["anthropic", "ollama"] = "ollama"
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"

    # Database
    database_url: str = ""

    # Vector Store
    chroma_persist_dir: str = "./chroma_data"

    # App
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"
    log_level: str = "INFO"

    # Security
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
