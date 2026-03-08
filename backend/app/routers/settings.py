"""
Settings endpoints.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.config import get_settings
from app.models import AppConfig

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings() -> Dict[str, Any]:
    """Get all application settings (sensitive values masked)."""
    settings = get_settings()
    
    return {
        "jira": {
            "enabled": bool(settings.jira_base_url),
            "base_url": settings.jira_base_url,
            "username": settings.jira_username,
            "api_token": "***" if settings.jira_api_token else None,
            "default_project": settings.jira_default_project
        },
        "valueedge": {
            "enabled": bool(settings.valueedge_base_url),
            "base_url": settings.valueedge_base_url,
            "client_id": settings.valueedge_client_id,
            "client_secret": "***" if settings.valueedge_client_secret else None,
            "shared_space_id": settings.valueedge_shared_space_id
        },
        "llm": {
            "default_provider": "groq" if settings.groq_api_key else "ollama",
            "groq": {
                "api_key": "***" if settings.groq_api_key else None,
                "default_model": settings.groq_default_model,
                "default_temperature": settings.groq_default_temperature
            },
            "ollama": {
                "base_url": settings.ollama_base_url,
                "default_model": settings.ollama_default_model
            }
        }
    }


@router.put("")
async def update_settings(config: AppConfig) -> Dict[str, Any]:
    """
    Update application settings.
    
    Note: In production, this would save to database.
    For now, settings are read from environment variables.
    """
    # This is a placeholder - in a real implementation,
    # we would save to encrypted database storage
    return {
        "status": "success",
        "message": "Settings would be saved to encrypted storage",
        "note": "Currently settings are loaded from environment variables"
    }


@router.get("/templates")
async def get_templates() -> Dict[str, str]:
    """Get current template content."""
    from pathlib import Path
    
    templates = {}
    
    test_plan_path = Path("./templates/test_plan_generation.md")
    if test_plan_path.exists():
        templates["test_plan"] = test_plan_path.read_text()
    
    test_case_path = Path("./templates/test_case_generation.md")
    if test_case_path.exists():
        templates["test_case"] = test_case_path.read_text()
    
    return templates


@router.put("/templates")
async def update_templates(templates: Dict[str, str]) -> Dict[str, Any]:
    """Update template content."""
    from pathlib import Path
    
    try:
        if "test_plan" in templates:
            test_plan_path = Path("./templates/test_plan_generation.md")
            test_plan_path.parent.mkdir(parents=True, exist_ok=True)
            test_plan_path.write_text(templates["test_plan"])
        
        if "test_case" in templates:
            test_case_path = Path("./templates/test_case_generation.md")
            test_case_path.parent.mkdir(parents=True, exist_ok=True)
            test_case_path.write_text(templates["test_case"])
        
        return {"status": "success", "message": "Templates updated"}
        
    except Exception as e:
        raise HTTPException(500, f"Failed to update templates: {str(e)}")
