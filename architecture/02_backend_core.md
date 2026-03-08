# SOP 02: Backend Core (Config, Models, Database)

## Goal
Establish the core backend infrastructure: configuration management, data models, and database layer.

## Layer
Layer 3: Tools (`backend/app/`)

## Files
- `backend/app/config.py` - Settings management
- `backend/app/models.py` - Pydantic schemas
- `backend/app/database.py` - Database connection

## Implementation

### 1. Configuration (`config.py`)

```python
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
```

### 2. Models (`models.py`)

```python
"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ============================================
# Configuration Models
# ============================================

class JiraConfig(BaseModel):
    enabled: bool = True
    base_url: Optional[str] = None
    username: Optional[str] = None
    api_token: Optional[str] = None
    default_project: Optional[str] = None


class ValueEdgeConfig(BaseModel):
    enabled: bool = False
    base_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    shared_space_id: Optional[int] = None


class GroqConfig(BaseModel):
    api_key: Optional[str] = None
    default_model: str = "llama-3.3-70b-versatile"
    default_temperature: float = 0.2


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1"


class LLMConfig(BaseModel):
    default_provider: Literal["groq", "ollama"] = "groq"
    groq: GroqConfig = GroqConfig()
    ollama: OllamaConfig = OllamaConfig()


class TemplateConfig(BaseModel):
    test_plan_path: str = "./templates/test_plan_generation.md"
    test_case_path: str = "./templates/test_case_generation.md"


class ExportConfig(BaseModel):
    default_format: Literal["markdown", "pdf", "excel", "json", "gherkin"] = "markdown"
    auto_save: bool = True
    output_directory: str = "./outputs"


class AppConfig(BaseModel):
    jira: JiraConfig = JiraConfig()
    valueedge: ValueEdgeConfig = ValueEdgeConfig()
    llm: LLMConfig = LLMConfig()
    templates: TemplateConfig = TemplateConfig()
    export: ExportConfig = ExportConfig()


# ============================================
# Generation Request/Response Models
# ============================================

class FileInput(BaseModel):
    filename: str
    path: str
    extracted_text: Optional[str] = None
    content_type: Optional[str] = None


class GenerationInputs(BaseModel):
    jira_id: Optional[str] = Field(None, pattern=r"^[A-Z][A-Z0-9]*-\d+$")
    valueedge_id: Optional[str] = None
    files: List[FileInput] = []
    custom_prompt: Optional[str] = None


class GenerationConfiguration(BaseModel):
    provider: Literal["groq", "ollama"] = "groq"
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 4096


class GenerationRequest(BaseModel):
    request_id: str
    timestamp: datetime
    inputs: GenerationInputs
    configuration: GenerationConfiguration


class GenerationOutput(BaseModel):
    content: str
    format: str = "markdown"
    token_usage: Optional[int] = None
    generation_time_ms: Optional[int] = None


class TestCasesOutput(GenerationOutput):
    count: Optional[int] = None


class GenerationOutputs(BaseModel):
    test_plan: Optional[GenerationOutput] = None
    test_cases: Optional[TestCasesOutput] = None


class GenerationMetadata(BaseModel):
    model_used: str
    temperature: float
    total_tokens: Optional[int] = None
    sources: List[str] = []


class GenerationResponse(BaseModel):
    request_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    timestamp: datetime
    outputs: GenerationOutputs
    metadata: GenerationMetadata
    error: Optional[str] = None


# ============================================
# Export Models
# ============================================

class ExportRequest(BaseModel):
    request_id: str
    format: Literal["markdown", "pdf", "excel", "json", "gherkin"]
    include_test_plan: bool = True
    include_test_cases: bool = True


class ExportResponse(BaseModel):
    file_path: str
    format: str
    size_bytes: int


# ============================================
# WebSocket Message Models
# ============================================

class WSMessageType(str, Enum):
    STARTED = "generation.started"
    PROGRESS = "generation.progress"
    CHUNK = "generation.chunk"
    COMPLETED = "generation.completed"
    ERROR = "generation.error"


class WSMessage(BaseModel):
    type: WSMessageType
    request_id: str
    data: Dict[str, Any] = {}
```

### 3. Database (`database.py`)

```python
"""
SQLite database for persistent storage of settings and generation history.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, Text, Integer
from datetime import datetime
import json

DATABASE_URL = "sqlite+aiosqlite:///./data/settings.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class SettingsRecord(Base):
    """Store encrypted application settings."""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    encrypted_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationHistory(Base):
    """Track generation requests and outputs."""
    __tablename__ = "generation_history"
    
    id = Column(String, primary_key=True)
    request_data = Column(Text)  # JSON
    response_data = Column(Text)  # JSON
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Edge Cases
1. **Missing env vars**: Pydantic will use defaults or raise validation errors
2. **Database not initialized**: `init_db()` should be called on startup
3. **Invalid JIRA ID format**: Pydantic regex validation will reject
4. **Large file uploads**: Enforced by `max_upload_size` setting
