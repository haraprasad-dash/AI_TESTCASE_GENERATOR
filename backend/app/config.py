"""
Configuration management using Pydantic Settings.
Supports environment variables and .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_port: int = 8000
    app_host: str = "127.0.0.1"
    log_level: str = "INFO"
    max_upload_size: int = 20  # MB
    session_timeout: int = 60  # minutes
    
    # JIRA
    jira_base_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_default_project: Optional[str] = None
    
    # ValueEdge
    valueedge_base_url: Optional[str] = None
    valueedge_client_id: Optional[str] = None
    valueedge_client_secret: Optional[str] = None
    valueedge_shared_space_id: Optional[int] = None
    
    # LLM - Groq
    groq_api_key: Optional[str] = None
    groq_default_model: str = "llama-3.3-70b-versatile"
    groq_default_temperature: float = 0.2
    
    # LLM - Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
