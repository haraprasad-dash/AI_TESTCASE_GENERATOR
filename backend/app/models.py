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
