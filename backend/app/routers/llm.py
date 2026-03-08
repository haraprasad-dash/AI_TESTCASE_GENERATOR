"""
LLM provider endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from app.services.llm_orchestrator import (
    create_orchestrator, LLMError, ProviderType
)
from app.config import get_settings

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post("/test-connection")
async def test_llm_connection(
    provider: str = Query(..., enum=["groq", "ollama"])
) -> Dict[str, Any]:
    """Test LLM provider connection."""
    settings = get_settings()
    
    try:
        if provider == "groq":
            orchestrator = create_orchestrator(
                provider="groq",
                api_key=settings.groq_api_key
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
    provider: str = Query(..., enum=["groq", "ollama"])
) -> List[str]:
    """List available models for provider."""
    settings = get_settings()
    
    try:
        if provider == "groq":
            # If no API key is set, return the static list of models
            if not settings.groq_api_key:
                from app.services.llm_orchestrator import GroqProvider
                return GroqProvider.GROQ_MODELS
            
            orchestrator = create_orchestrator(
                provider="groq",
                api_key=settings.groq_api_key
            )
        else:
            orchestrator = create_orchestrator(
                provider="ollama",
                base_url=settings.ollama_base_url
            )
        
        return await orchestrator.list_models()
        
    except LLMError as e:
        # Fallback to static model list for Groq if orchestrator fails
        if provider == "groq":
            from app.services.llm_orchestrator import GroqProvider
            return GroqProvider.GROQ_MODELS
        raise HTTPException(503, str(e))
    except Exception:
        # Final fallback - return static model list for Groq
        if provider == "groq":
            from app.services.llm_orchestrator import GroqProvider
            return GroqProvider.GROQ_MODELS
        raise HTTPException(503, f"Failed to load {provider} models")
