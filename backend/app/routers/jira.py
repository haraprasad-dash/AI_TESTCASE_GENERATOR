"""
JIRA API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any
from app.models import JiraConfig
from app.services.jira_client import (
    JiraClient, JiraAuthError, JiraNotFoundError, JiraClientError
)

router = APIRouter(prefix="/api/jira", tags=["jira"])


def get_jira_config() -> JiraConfig:
    """Get JIRA configuration from settings."""
    from app.config import get_settings
    settings = get_settings()
    return JiraConfig(
        base_url=settings.jira_base_url,
        username=settings.jira_username,
        api_token=settings.jira_api_token,
        default_project=settings.jira_default_project
    )


@router.post("/test-connection")
async def test_jira_connection(
    override: Dict[str, Any] = Body(default_factory=dict),
    config: JiraConfig = Depends(get_jira_config),
) -> Dict[str, Any]:
    """Test JIRA connection."""
    merged = JiraConfig(
        base_url=override.get("base_url") or config.base_url,
        username=override.get("username") or config.username,
        api_token=override.get("api_token") or config.api_token,
        default_project=override.get("default_project") or config.default_project,
    )

    if not all([merged.base_url, merged.username, merged.api_token]):
        raise HTTPException(400, "JIRA not configured")
    
    try:
        async with JiraClient(merged) as client:
            user = await client.test_connection()
            return {
                "status": "success",
                "message": f"Connected as {user.get('displayName')}",
                "user": {
                    "accountId": user.get("accountId"),
                    "email": user.get("emailAddress"),
                    "displayName": user.get("displayName")
                }
            }
    except JiraAuthError as e:
        raise HTTPException(401, str(e))
    except JiraClientError as e:
        raise HTTPException(500, str(e))


@router.get("/issue/{issue_key}")
async def get_jira_issue(
    issue_key: str,
    config: JiraConfig = Depends(get_jira_config)
) -> Dict[str, Any]:
    """Fetch JIRA issue details."""
    if not all([config.base_url, config.username, config.api_token]):
        raise HTTPException(400, "JIRA not configured")
    
    try:
        async with JiraClient(config) as client:
            issue_data = await client.get_issue(issue_key)
            return client.extract_relevant_fields(issue_data)
    except JiraNotFoundError as e:
        raise HTTPException(404, str(e))
    except JiraAuthError as e:
        raise HTTPException(401, str(e))
    except JiraClientError as e:
        raise HTTPException(500, str(e))
