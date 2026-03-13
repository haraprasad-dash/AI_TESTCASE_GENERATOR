"""
LLM provider endpoints.
"""
import re
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel, Field
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


class EnhancePromptFileContext(BaseModel):
    filename: str
    content_type: str | None = None
    extracted_snippet: str | None = None


class EnhancePromptContext(BaseModel):
    jira_ids: List[str] = Field(default_factory=list)
    valueedge_ids: List[str] = Field(default_factory=list)
    files: List[EnhancePromptFileContext] = Field(default_factory=list)
    user_guide_url: str | None = None
    review_test_cases: bool | None = None
    review_user_guide: bool | None = None
    use_test_plan_template: bool | None = None
    use_test_case_template: bool | None = None
    constraints: List[str] = Field(default_factory=list)


class EnhancePromptRequest(BaseModel):
    prompt: str
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    prompt_type: Literal["test_plan", "test_case", "review", "review_test_cases", "review_user_guide"] = "test_case"
    context: EnhancePromptContext | None = None


def _compact_text(value: str | None, limit: int = 180) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _extract_priority_constraints(text: str) -> List[str]:
    constraints: List[str] = []
    lowered = text.lower()

    if re.search(r"\bonly\b.*\bhigh\s*priority\b|\bhigh\s*priority\b.*\bonly\b", lowered):
        constraints.append("Only include high-priority tasks.")

    if re.search(r"\bonly\b.*\bcritical\b|\bcritical\b.*\bonly\b", lowered):
        constraints.append("Only include critical-priority tasks.")

    return constraints


def _build_context_digest(
    prompt_type: Literal["test_plan", "test_case", "review", "review_test_cases", "review_user_guide"],
    context: EnhancePromptContext | None,
) -> str:
    if not context:
        return ""

    lines: List[str] = []

    if context.jira_ids:
        lines.append(f"JIRA IDs: {', '.join(context.jira_ids[:8])}")

    if context.valueedge_ids:
        lines.append(f"ValueEdge IDs: {', '.join(context.valueedge_ids[:8])}")

    if context.files:
        file_lines: List[str] = []
        for file_entry in context.files[:8]:
            ct = f" ({file_entry.content_type})" if file_entry.content_type else ""
            snippet = _compact_text(file_entry.extracted_snippet, limit=120)
            if snippet:
                file_lines.append(f"- {file_entry.filename}{ct}: {snippet}")
            else:
                file_lines.append(f"- {file_entry.filename}{ct}")
        lines.append("Attachments:\n" + "\n".join(file_lines))

    if prompt_type in {"test_plan", "test_case"}:
        if context.use_test_plan_template is not None:
            lines.append(f"Use test plan template: {context.use_test_plan_template}")
        if context.use_test_case_template is not None:
            lines.append(f"Use test case template: {context.use_test_case_template}")

    if prompt_type in {"review", "review_test_cases", "review_user_guide"}:
        if context.review_test_cases is not None or context.review_user_guide is not None:
            lines.append(
                "Review modes: "
                f"test_cases={bool(context.review_test_cases)}, "
                f"user_guide={bool(context.review_user_guide)}"
            )
        if context.user_guide_url:
            lines.append(f"User guide URL: {context.user_guide_url}")

    if context.constraints:
        lines.append("Explicit constraints:\n" + "\n".join(f"- {c}" for c in context.constraints[:8]))

    return "\n".join(lines).strip()


def _build_enhance_system_prompt(prompt_type: Literal["test_plan", "test_case", "review", "review_test_cases", "review_user_guide"]) -> str:
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

    if prompt_type in {"review", "review_test_cases", "review_user_guide"}:
        subtype = (
            "test case review"
            if prompt_type == "review_test_cases"
            else "user guide review"
            if prompt_type == "review_user_guide"
            else "review"
        )
        return (
            f"{base_rules} "
            f"This enhancement is for {subtype.upper()} instructions. "
            "Focus on coverage gaps, quality checks, traceability, defects, and prioritized review actions."
        )

    return (
        f"{base_rules} "
        "This enhancement is for TEST CASE generation instructions. "
        "Add precise testcase-focused coverage guidance: positive, negative, edge, boundary, security, performance where relevant. "
        "Mention concrete testcase dimensions such as endpoints/fields/conditions/error codes when applicable."
    )


def _is_misaligned(
    prompt_type: Literal["test_plan", "test_case", "review", "review_test_cases", "review_user_guide"],
    text: str,
) -> bool:
    lowered = text.lower()
    mentions_test_plan = "test plan" in lowered
    mentions_test_case = bool(re.search(r"test case|test cases|scenario|gherkin|endpoint", lowered))
    mentions_user_guide = bool(re.search(r"user guide|documentation|manual", lowered))
    mentions_review = "review" in lowered

    testcase_checklist_patterns = [
        r"\bpositive tests?\b",
        r"\bnegative tests?\b",
        r"\bedge cases?\b",
        r"\bboundary value\b",
        r"\berror codes?\b",
        r"\bsql injection\b",
        r"\bcross[- ]site scripting\b",
        r"\bcsrf\b",
        r"\bendpoint coverage\b",
        r"\bexpected results?\b",
        r"\bpreconditions?\b",
        r"\btest data\b",
    ]

    testplan_patterns = [
        r"\bscope\b",
        r"\bobjectives?\b",
        r"\btimeline\b",
        r"\bmilestones?\b",
        r"\bentry criteria\b",
        r"\bexit criteria\b",
        r"\brisk register\b",
        r"\bdependencies\b",
        r"\bstakeholders?\b",
        r"\bphases?\b",
    ]

    user_guide_patterns = [
        r"\buser guide\b",
        r"\bdocumentation\b",
        r"\bmanual\b",
        r"\binstallation steps?\b",
        r"\bonboarding\b",
        r"\bnavigation\b",
        r"\bui walkthrough\b",
        r"\bscreenshots?\b",
    ]

    if prompt_type == "test_plan":
        if any(re.search(pattern, lowered) for pattern in testcase_checklist_patterns):
            return True
        return mentions_test_case and not mentions_test_plan
    if prompt_type == "test_case":
        if any(re.search(pattern, lowered) for pattern in testplan_patterns):
            return True
        return mentions_test_plan and not mentions_test_case
    if prompt_type == "review_test_cases":
        if any(re.search(pattern, lowered) for pattern in user_guide_patterns):
            return True
        return mentions_user_guide and not mentions_test_case
    if prompt_type == "review_user_guide":
        if any(re.search(pattern, lowered) for pattern in testcase_checklist_patterns):
            return True
        return mentions_test_case and not mentions_user_guide
    if prompt_type == "review":
        return not mentions_review and (mentions_test_plan or mentions_test_case)
    return False


def _build_alignment_fallback(
    prompt_type: Literal["test_plan", "test_case", "review", "review_test_cases", "review_user_guide"],
    original_prompt: str,
    context_digest: str,
    constraints: List[str],
) -> str:
    lines: List[str] = []

    if prompt_type == "test_plan":
        lines.append("Generate a TEST PLAN only (do NOT generate test case lists).")
    elif prompt_type == "test_case":
        lines.append("Generate TEST CASE instructions focused on executable testcase coverage.")
    elif prompt_type == "review_test_cases":
        lines.append("Enhance TEST CASE REVIEW instructions (coverage, gaps, duplicates, traceability).")
    elif prompt_type == "review_user_guide":
        lines.append("Enhance USER GUIDE REVIEW instructions (accuracy, completeness, consistency, usability).")
    else:
        lines.append("Enhance REVIEW instructions with practical, prioritized review outcomes.")

    lines.append(f"Primary user intent: {_compact_text(original_prompt, limit=700)}")

    if constraints:
        lines.append("Must-preserve constraints:\n" + "\n".join(f"- {c}" for c in constraints[:8]))

    if context_digest:
        lines.append("Use this context:\n" + context_digest)

    lines.append("If required context is missing, state explicit assumptions/questions inside the instruction.")
    return "\n\n".join(lines).strip()


def _enforce_constraints(enhanced_prompt: str, constraints: List[str]) -> str:
    if not constraints:
        return enhanced_prompt

    output = enhanced_prompt.strip()
    lower = output.lower()
    missing = []
    for constraint in constraints:
        if constraint.lower() not in lower:
            missing.append(constraint)

    if not missing:
        return output

    return output + "\n\nMust-preserve constraints:\n" + "\n".join(f"- {c}" for c in missing)


def _normalize_test_plan_output(enhanced_prompt: str) -> str:
    output = enhanced_prompt.strip()
    lower = output.lower()
    if "test plan" in lower:
        return output
    return "Create a TEST PLAN only (not testcase checklist).\n\n" + output


@router.post("/enhance-prompt")
async def enhance_prompt(request: EnhancePromptRequest) -> Dict[str, Any]:
    """Enhance a user prompt to be more specific and effective for test generation."""
    settings = get_settings()

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(400, "Prompt cannot be empty")

    context_digest = _build_context_digest(request.prompt_type, request.context)
    system_prompt = _build_enhance_system_prompt(request.prompt_type)
    prompt_constraints = _extract_priority_constraints(request.prompt)
    if request.context and request.context.constraints:
        prompt_constraints.extend(request.context.constraints)

    normalized_constraints: List[str] = []
    for constraint in prompt_constraints:
        if constraint not in normalized_constraints:
            normalized_constraints.append(constraint)

    prompt_payload = request.prompt.strip()
    if context_digest:
        prompt_payload = (
            "Context digest (use only if relevant):\n"
            f"{context_digest}\n\n"
            "User instruction to enhance:\n"
            f"{request.prompt.strip()}"
        )

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

        # Override max_tokens via config after construction (when provider exposes config)
        if getattr(orchestrator, "config", None) is not None:
            orchestrator.config.max_tokens = 512

        result = await orchestrator.generate(
            prompt=prompt_payload,
            system_prompt=system_prompt,
        )
        enhanced_prompt = result.content.strip()
        enhanced_prompt = _enforce_constraints(enhanced_prompt, normalized_constraints)

        if _is_misaligned(request.prompt_type, enhanced_prompt):
            enhanced_prompt = _build_alignment_fallback(
                request.prompt_type,
                request.prompt,
                context_digest,
                normalized_constraints,
            )

        if request.prompt_type == "test_plan":
            enhanced_prompt = _normalize_test_plan_output(enhanced_prompt)

        return {"enhanced_prompt": enhanced_prompt}

    except LLMError as e:
        raise HTTPException(503, str(e))
