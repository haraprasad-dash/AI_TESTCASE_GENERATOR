# SOP 03: JIRA Integration

## Goal
Implement JIRA REST API client for fetching issue details.

## Layer
Layer 3: Tools (`backend/app/services/jira_client.py`)

## API Reference
- Base URL: `https://{instance}.atlassian.net/rest/api/3`
- Auth: Basic Auth (email + API Token)
- Docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

## Implementation

### JIRA Client (`services/jira_client.py`)

```python
"""
JIRA API Client for fetching issue details.
"""
import base64
import httpx
from typing import Optional, Dict, Any, List
from app.models import JiraConfig


class JiraClientError(Exception):
    """Base exception for JIRA client errors."""
    pass


class JiraAuthError(JiraClientError):
    """Authentication failed."""
    pass


class JiraNotFoundError(JiraClientError):
    """Issue not found."""
    pass


class JiraClient:
    """Client for JIRA REST API v3."""
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/") if config.base_url else ""
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_auth_header(self) -> str:
        """Generate Basic Auth header."""
        credentials = base64.b64encode(
            f"{self.config.username}:{self.config.api_token}".encode()
        ).decode()
        return f"Basic {credentials}"
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": self._get_auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test JIRA connection by fetching current user."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            response = await self._client.get(
                f"{self.base_url}/rest/api/3/myself"
            )
            
            if response.status_code == 401:
                raise JiraAuthError("Invalid credentials")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            raise JiraClientError(f"Cannot connect to JIRA: {e}")
    
    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Fetch issue details by key.
        
        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")
            
        Returns:
            Dict with issue data
            
        Raises:
            JiraNotFoundError: If issue doesn't exist
            JiraAuthError: If authentication fails
            JiraClientError: For other errors
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            response = await self._client.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}"
            )
            
            if response.status_code == 404:
                raise JiraNotFoundError(f"Issue not found: {issue_key}")
            
            if response.status_code == 401:
                raise JiraAuthError("Invalid credentials")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            raise JiraClientError(f"Cannot connect to JIRA: {e}")
    
    def extract_relevant_fields(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant fields from JIRA issue.
        
        Returns:
            Dict with: key, summary, description, issue_type, priority,
                      labels, components, status, assignee, reporter
        """
        fields = issue_data.get("fields", {})
        
        return {
            "key": issue_data.get("key"),
            "summary": fields.get("summary"),
            "description": self._extract_description(fields.get("description")),
            "issue_type": fields.get("issuetype", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "labels": fields.get("labels", []),
            "components": [c.get("name") for c in fields.get("components", [])],
            "status": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
            "created": fields.get("created"),
            "updated": fields.get("updated"),
        }
    
    def _extract_description(self, description: Any) -> str:
        """Extract text from Atlassian Document Format."""
        if not description:
            return ""
        
        if isinstance(description, str):
            return description
        
        # Handle Atlassian Document Format
        if isinstance(description, dict):
            return self._extract_text_from_adf(description)
        
        return str(description)
    
    def _extract_text_from_adf(self, node: Dict[str, Any]) -> str:
        """Recursively extract text from ADF nodes."""
        texts = []
        
        if node.get("type") == "text":
            return node.get("text", "")
        
        if "content" in node:
            for child in node["content"]:
                texts.append(self._extract_text_from_adf(child))
        
        return " ".join(texts)


async def fetch_jira_issue(issue_key: str, config: JiraConfig) -> Dict[str, Any]:
    """
    Convenience function to fetch and extract JIRA issue.
    
    Args:
        issue_key: JIRA issue key
        config: JIRA configuration
        
    Returns:
        Extracted issue fields
    """
    async with JiraClient(config) as client:
        issue_data = await client.get_issue(issue_key)
        return client.extract_relevant_fields(issue_data)
```

### API Router (`routers/jira.py`)

```python
"""
JIRA API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
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
async def test_jira_connection(config: JiraConfig = Depends(get_jira_config)) -> Dict[str, Any]:
    """Test JIRA connection."""
    if not all([config.base_url, config.username, config.api_token]):
        raise HTTPException(400, "JIRA not configured")
    
    try:
        async with JiraClient(config) as client:
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
```

## Edge Cases
1. **ADF Description**: JIRA uses Atlassian Document Format for descriptions - must extract text recursively
2. **Missing fields**: Some fields may be null (assignee, priority) - handle gracefully
3. **Rate limiting**: JIRA has API rate limits - implement exponential backoff if needed
4. **Large descriptions**: Very long descriptions may need truncation
