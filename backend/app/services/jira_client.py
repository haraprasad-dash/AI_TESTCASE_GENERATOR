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
