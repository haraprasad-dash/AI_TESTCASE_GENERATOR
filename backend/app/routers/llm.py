"""
LLM provider endpoints.
"""
import re
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from typing import Dict, Any, List, Literal
from app.services.llm_orchestrator import (
    create_orchestrator, LLMError, ProviderType
)
from app.config import get_settings

router = APIRouter(prefix="/api/llm", tags=["llm"])


def _normalize_groq_key(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"^bearer\s+", "", value.strip(), flags=re.IGNORECASE).strip()


@router.post("/test-connection")
async def test_llm_connection(
    provider: str = Query(..., enum=["groq", "ollama"]),
    x_groq_api_key: str | None = Header(default=None)
) -> Dict[str, Any]:
    """Test LLM provider connection."""
    settings = get_settings()
    
    try:
        if provider == "groq":
            api_key = _normalize_groq_key(x_groq_api_key) or _normalize_groq_key(settings.groq_api_key)
            if not api_key:
                raise HTTPException(400, "Groq API key not configured")
            orchestrator = create_orchestrator(
                provider="groq",
                api_key=api_key
            )
        else:
            orchestrator = create_orchestrator(
                provider="ollama",
                base_url=settings.ollama_base_url
            )
        
        result = await orchestrator.test_connection()
        
        if result.get("status") == "error":
            raise HTTPException(503, result.get("error"))
        
        return result
        
    except LLMError as e:
        raise HTTPException(503, str(e))


@router.get("/models")
async def list_models(
    provider: str = Query(..., enum=["groq", "ollama"]),
    x_groq_api_key: str | None = Header(default=None)
) -> List[str]:
    """List available models for provider."""
    settings = get_settings()
    
    try:
        if provider == "groq":
            api_key = _normalize_groq_key(x_groq_api_key) or _normalize_groq_key(settings.groq_api_key)
            if not api_key:
                raise HTTPException(400, "Groq API key not configured")
            orchestrator = create_orchestrator(
                provider="groq",
                api_key=api_key,
            )
        else:
            orchestrator = create_orchestrator(
                provider="ollama",
                base_url=settings.ollama_base_url
            )
        
        return await orchestrator.list_models()
        
    except LLMError as e:
        raise HTTPException(503, str(e))
    except Exception:
        raise HTTPException(503, f"Failed to load {provider} models")


class EnhancePromptRequest(BaseModel):
    prompt: str
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    prompt_type: Literal["test_plan", "test_case", "review"] = "test_case"


def _build_enhance_system_prompt(prompt_type: Literal["test_plan", "test_case", "review"]) -> str:
    base_rules = (
        "You are an expert QA engineer and prompt specialist. "
        "Rewrite the user's instruction to be clearer and more actionable. "
        "Rules: (1) State requirements directly — no preamble/filler. "
        "(2) Preserve explicit user constraints exactly (for example: only high-priority tasks). "
        "(3) Remove vague wording and keep concise, concrete language. "
        "(4) Return ONLY the improved prompt text — no explanation."
    )

    if prompt_type == "test_plan":
        return (
            f"{base_rules} "
            "This enhancement is for TEST PLAN instructions only. "
            "Focus on plan-level content: scope, objectives, phases, risks, timelines, entry/exit criteria, dependencies, and priorities. "
            "Do NOT rewrite into testcase/API endpoint checklists unless user explicitly asks for testcase-level output. "
            "If priority filtering is requested, keep only that priority level in the enhanced instruction."
        )

    if prompt_type == "review":
        return (
            f"{base_rules} "
            "This enhancement is for REVIEW instructions. "
            "Focus on coverage gaps, quality checks, traceability, defects, and prioritized review actions."
        )

    return (
        f"{base_rules} "
        "This enhancement is for TEST CASE generation instructions. "
        "Add precise testcase-focused coverage guidance: positive, negative, edge, boundary, security, performance where relevant. "
        "Mention concrete testcase dimensions such as endpoints/fields/conditions/error codes when applicable."
    )


@router.post("/enhance-prompt")
async def enhance_prompt(request: EnhancePromptRequest) -> Dict[str, Any]:
    """Enhance a user prompt to be more specific and effective for test generation."""
    settings = get_settings()

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(400, "Prompt cannot be empty")

    system_prompt = _build_enhance_system_prompt(request.prompt_type)

    try:
        if request.provider == "groq":
            if not settings.groq_api_key:
                raise HTTPException(503, "Groq API key not configured. Add GROQ_API_KEY to your .env file.")
            orchestrator = create_orchestrator(
                provider="groq",
                api_key=settings.groq_api_key,
                model=request.model,
                temperature=0.3,
            )
        else:
            orchestrator = create_orchestrator(
                provider="ollama",
                base_url=settings.ollama_base_url,
                model=request.model,
                temperature=0.3,
            )

        # Override max_tokens via config after construction
        orchestrator.config.max_tokens = 512

        result = await orchestrator.generate(
            prompt=request.prompt,
            system_prompt=system_prompt,
        )
        return {"enhanced_prompt": result.content.strip()}

    except LLMError as e:
        raise HTTPException(503, str(e))
