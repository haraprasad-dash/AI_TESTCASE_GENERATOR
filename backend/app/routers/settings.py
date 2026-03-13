"""
Settings endpoints.
"""
import os
import re
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pathlib import Path
from dotenv import dotenv_values
from app.config import get_settings as get_runtime_settings
from app.models import AppConfig

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _is_masked_secret(value: str | None) -> bool:
    if value is None:
        return False
    stripped = value.strip()
    return bool(stripped) and all(ch == "*" for ch in stripped)


def _normalize_secret_value(new_value: str | None, current_value: str | None) -> str:
    """
    Normalize secret input values.

    Rules:
    - Trim whitespace for real user-entered secrets.
    - If incoming value is masked placeholder (e.g. '***'), preserve only a real current secret.
    - Never persist masked placeholders as actual secrets.
    """
    incoming = (new_value or "").strip()
    current = (current_value or "").strip()

    if _is_masked_secret(incoming):
        if current and not _is_masked_secret(current):
            return current
        return ""

    # Accept accidental Authorization-style input and keep only the token.
    incoming = re.sub(r"^bearer\s+", "", incoming, flags=re.IGNORECASE).strip()
    return incoming


def _load_env_map(env_path: Path) -> Dict[str, str]:
    raw = dotenv_values(env_path)
    return {k: str(v) for k, v in raw.items() if v is not None}


def _write_env_map(env_path: Path, env_map: Dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in sorted(env_map.items())]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("")
async def get_app_settings() -> Dict[str, Any]:
    """Get all application settings (sensitive values masked)."""
    settings = get_runtime_settings()
    
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
    """Update application settings and persist them to backend/.env."""
    try:
        current = get_runtime_settings()
        env_path = Path(".env")
        env_map = _load_env_map(env_path) if env_path.exists() else {}

        # Preserve existing secret if client sends masked value (e.g. "***").
        jira_token = _normalize_secret_value(config.jira.api_token, current.jira_api_token)
        ve_secret = _normalize_secret_value(config.valueedge.client_secret, current.valueedge_client_secret)
        groq_key = _normalize_secret_value(config.llm.groq.api_key, current.groq_api_key)

        updates: Dict[str, str] = {
            "JIRA_BASE_URL": (config.jira.base_url or "").strip(),
            "JIRA_USERNAME": (config.jira.username or "").strip(),
            "JIRA_API_TOKEN": jira_token or "",
            "JIRA_DEFAULT_PROJECT": (config.jira.default_project or "").strip(),
            "VALUEEDGE_BASE_URL": (config.valueedge.base_url or "").strip(),
            "VALUEEDGE_CLIENT_ID": (config.valueedge.client_id or "").strip(),
            "VALUEEDGE_CLIENT_SECRET": ve_secret or "",
            "VALUEEDGE_SHARED_SPACE_ID": str(config.valueedge.shared_space_id) if config.valueedge.shared_space_id is not None else "",
            "GROQ_API_KEY": groq_key or "",
            "GROQ_DEFAULT_MODEL": (config.llm.groq.default_model or "llama-3.3-70b-versatile").strip(),
            "GROQ_DEFAULT_TEMPERATURE": str(config.llm.groq.default_temperature),
            "OLLAMA_BASE_URL": (config.llm.ollama.base_url or "http://localhost:11434").strip(),
            "OLLAMA_DEFAULT_MODEL": (config.llm.ollama.default_model or "llama3.1").strip(),
        }

        for key, value in updates.items():
            if value == "":
                env_map.pop(key, None)
                os.environ.pop(key, None)
            else:
                env_map[key] = value
                os.environ[key] = value

        _write_env_map(env_path, env_map)

        # Reset cached settings so next dependency reads latest values.
        get_runtime_settings.cache_clear()

        refreshed = get_runtime_settings()
        return {
            "status": "success",
            "message": "Settings saved",
            "active": {
                "jira_enabled": bool(refreshed.jira_base_url and refreshed.jira_username and refreshed.jira_api_token),
                "valueedge_enabled": bool(refreshed.valueedge_base_url and refreshed.valueedge_client_id and refreshed.valueedge_client_secret),
                "groq_enabled": bool(refreshed.groq_api_key),
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to save settings: {str(e)}")


@router.get("/templates")
async def get_templates() -> Dict[str, str]:
    """Get current template content."""
    from pathlib import Path
    
    templates = {}
    
    test_plan_path = Path("./templates/test_plan_generation.md")
    if test_plan_path.exists():
        templates["test_plan"] = test_plan_path.read_text(encoding="utf-8", errors="replace")
    
    test_case_path = Path("./templates/test_case_generation.md")
    if test_case_path.exists():
        templates["test_case"] = test_case_path.read_text(encoding="utf-8", errors="replace")
    
    return templates


@router.put("/templates")
async def update_templates(templates: Dict[str, str]) -> Dict[str, Any]:
    """Update template content."""
    from pathlib import Path
    
    try:
        if "test_plan" in templates:
            test_plan_path = Path("./templates/test_plan_generation.md")
            test_plan_path.parent.mkdir(parents=True, exist_ok=True)
            test_plan_path.write_text(templates["test_plan"], encoding="utf-8")
        
        if "test_case" in templates:
            test_case_path = Path("./templates/test_case_generation.md")
            test_case_path.parent.mkdir(parents=True, exist_ok=True)
            test_case_path.write_text(templates["test_case"], encoding="utf-8")
        
        return {"status": "success", "message": "Templates updated"}
        
    except Exception as e:
        raise HTTPException(500, f"Failed to update templates: {str(e)}")
