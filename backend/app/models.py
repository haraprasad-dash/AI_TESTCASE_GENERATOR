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
    file_id: Optional[str] = None
    filename: str
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    extracted_text: Optional[str] = None
    content_type: Optional[str] = None
    page_count: Optional[int] = None


class GenerationInputs(BaseModel):
    jira_id: Optional[str] = Field(None, pattern=r"^[A-Z][A-Z0-9]*-\d+$")
    jira_ids: List[str] = []
    valueedge_id: Optional[str] = None
    valueedge_ids: List[str] = []
    files: List[FileInput] = []
    custom_prompt: Optional[str] = None
    test_plan_prompt: Optional[str] = None
    test_case_prompt: Optional[str] = None
    use_test_plan_template: bool = True
    use_test_case_template: bool = True


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
    clarification_required: bool = False
    clarification_questions: List[str] = []


class GenerationResponse(BaseModel):
    request_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    timestamp: datetime
    outputs: GenerationOutputs
    metadata: GenerationMetadata
    error: Optional[str] = None


# ============================================
# Review Request/Response Models
# ============================================

class ClarificationEntry(BaseModel):
    questions: List[str] = []
    answer: str


class ReviewInputs(BaseModel):
    jira_id: Optional[str] = Field(None, pattern=r"^[A-Z][A-Z0-9]*-\d+$")
    jira_ids: List[str] = []
    valueedge_id: Optional[str] = None
    valueedge_ids: List[str] = []
    files: List[FileInput] = []
    custom_instructions: Optional[str] = None
    test_case_review_instructions: Optional[str] = None
    user_guide_review_instructions: Optional[str] = None
    review_test_cases: bool = True
    review_user_guide: bool = True
    clarification_history: List[ClarificationEntry] = []


class ReviewConfiguration(BaseModel):
    provider: Literal["groq", "ollama"] = "groq"
    model: Optional[str] = None
    temperature: float = 0.2


class ReviewRequest(BaseModel):
    request_id: Optional[str] = None
    timestamp: datetime
    inputs: ReviewInputs
    configuration: ReviewConfiguration


class ReviewMetadata(BaseModel):
    review_type: Literal["test-cases", "user-guide", "both"]
    clarification_required: bool = False
    clarification_questions: List[str] = []
    clarification_round: int = 0
    max_clarification_rounds: int = 3
    assumptions_applied: bool = False
    sources: List[str] = []


class ReviewResponse(BaseModel):
    review_id: str
    status: Literal["completed", "clarification_required", "failed"]
    timestamp: datetime
    report_markdown: str
    report_json: Dict[str, Any]
    partial_results: Optional[Dict[str, Any]] = None
    metadata: ReviewMetadata
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
