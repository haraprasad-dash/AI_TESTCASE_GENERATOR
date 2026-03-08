# SOP 04: OpenText ValueEdge Integration

## Goal
Implement ValueEdge REST API client for fetching work item details.

## Layer
Layer 3: Tools (`backend/app/services/valueedge_client.py`)

## API Reference
- Base URL: `https://{instance}.com`
- Auth: OAuth 2.0 Client Credentials
- Token endpoint: `POST /authentication/sign_in`
- Docs: ValueEdge REST API documentation

## Implementation

### ValueEdge Client (`services/valueedge_client.py`)

```python
"""
OpenText ValueEdge API Client for fetching work items.
"""
import httpx
import time
from typing import Optional, Dict, Any, List
from app.models import ValueEdgeConfig


class ValueEdgeClientError(Exception):
    """Base exception for ValueEdge client errors."""
    pass


class ValueEdgeAuthError(ValueEdgeClientError):
    """Authentication failed."""
    pass


class ValueEdgeNotFoundError(ValueEdgeClientError):
    """Work item not found."""
    pass


class ValueEdgeClient:
    """Client for ValueEdge REST API."""
    
    def __init__(self, config: ValueEdgeConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/") if config.base_url else ""
        self._client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers={"Accept": "application/json"},
            timeout=30.0
        )
        # Get initial token
        await self._ensure_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token using client credentials."""
        token_url = f"{self.base_url}/authentication/sign_in"
        
        try:
            response = await self._client.post(
                token_url,
                headers={"Content-Type": "application/json"},
                json={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret
                }
            )
            
            if response.status_code == 401:
                raise ValueEdgeAuthError("Invalid client credentials")
            
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in - 60  # 1 min buffer
            
            return self._access_token
            
        except httpx.ConnectError as e:
            raise ValueEdgeClientError(f"Cannot connect to ValueEdge: {e}")
    
    async def _ensure_token(self):
        """Ensure we have a valid access token."""
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._get_access_token()
            self._client.headers["Authorization"] = f"Bearer {self._access_token}"
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test ValueEdge connection by fetching shared spaces."""
        await self._ensure_token()
        
        try:
            response = await self._client.get(
                f"{self.base_url}/api/shared_spaces"
            )
            
            if response.status_code == 401:
                # Token may have expired, try refreshing
                await self._get_access_token()
                self._client.headers["Authorization"] = f"Bearer {self._access_token}"
                response = await self._client.get(
                    f"{self.base_url}/api/shared_spaces"
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            raise ValueEdgeClientError(f"Cannot connect to ValueEdge: {e}")
    
    async def get_work_item(self, item_id: str, shared_space_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch work item details.
        
        Args:
            item_id: Work item ID
            shared_space_id: Shared space ID (defaults to config)
            
        Returns:
            Dict with work item data
        """
        await self._ensure_token()
        
        space_id = shared_space_id or self.config.shared_space_id
        if not space_id:
            raise ValueEdgeClientError("Shared space ID not configured")
        
        try:
            response = await self._client.get(
                f"{self.base_url}/api/shared_spaces/{space_id}/work_items/{item_id}"
            )
            
            if response.status_code == 404:
                raise ValueEdgeNotFoundError(f"Work item not found: {item_id}")
            
            if response.status_code == 401:
                raise ValueEdgeAuthError("Authentication failed")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError as e:
            raise ValueEdgeClientError(f"Cannot connect to ValueEdge: {e}")
    
    def extract_relevant_fields(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant fields from work item.
        
        Returns:
            Dict with: id, name, type, phase, description, author, 
                      creation_time, last_modified
        """
        return {
            "id": item_data.get("id"),
            "name": item_data.get("name"),
            "type": item_data.get("subtype") or item_data.get("type"),
            "phase": item_data.get("phase", {}).get("name") if item_data.get("phase") else None,
            "description": item_data.get("description"),
            "author": item_data.get("author", {}).get("name") if item_data.get("author") else None,
            "owner": item_data.get("owner", {}).get("name") if item_data.get("owner") else None,
            "creation_time": item_data.get("creation_time"),
            "last_modified": item_data.get("last_modified"),
            "story_points": item_data.get("story_points"),
            "priority": item_data.get("priority", {}).get("name") if item_data.get("priority") else None,
        }


async def fetch_valueedge_item(
    item_id: str,
    config: ValueEdgeConfig,
    shared_space_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to fetch and extract ValueEdge work item.
    
    Args:
        item_id: Work item ID
        config: ValueEdge configuration
        shared_space_id: Optional shared space ID
        
    Returns:
        Extracted work item fields
    """
    async with ValueEdgeClient(config) as client:
        item_data = await client.get_work_item(item_id, shared_space_id)
        return client.extract_relevant_fields(item_data)
```

### API Router (`routers/valueedge.py`)

```python
"""
ValueEdge API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from app.models import ValueEdgeConfig
from app.services.valueedge_client import (
    ValueEdgeClient, ValueEdgeAuthError, ValueEdgeNotFoundError, ValueEdgeClientError
)

router = APIRouter(prefix="/api/valueedge", tags=["valueedge"])


def get_valueedge_config() -> ValueEdgeConfig:
    """Get ValueEdge configuration from settings."""
    from app.config import get_settings
    settings = get_settings()
    return ValueEdgeConfig(
        base_url=settings.valueedge_base_url,
        client_id=settings.valueedge_client_id,
        client_secret=settings.valueedge_client_secret,
        shared_space_id=settings.valueedge_shared_space_id
    )


@router.post("/test-connection")
async def test_valueedge_connection(
    config: ValueEdgeConfig = Depends(get_valueedge_config)
) -> Dict[str, Any]:
    """Test ValueEdge connection."""
    if not all([config.base_url, config.client_id, config.client_secret]):
        raise HTTPException(400, "ValueEdge not configured")
    
    try:
        async with ValueEdgeClient(config) as client:
            spaces = await client.test_connection()
            space_list = spaces.get("data", [])
            return {
                "status": "success",
                "message": f"Connected! Found {len(space_list)} shared space(s)",
                "shared_spaces": [
                    {"id": s.get("id"), "name": s.get("name")}
                    for s in space_list
                ]
            }
    except ValueEdgeAuthError as e:
        raise HTTPException(401, str(e))
    except ValueEdgeClientError as e:
        raise HTTPException(500, str(e))


@router.get("/item/{item_id}")
async def get_valueedge_item(
    item_id: str,
    shared_space_id: Optional[int] = None,
    config: ValueEdgeConfig = Depends(get_valueedge_config)
) -> Dict[str, Any]:
    """Fetch ValueEdge work item details."""
    if not all([config.base_url, config.client_id, config.client_secret]):
        raise HTTPException(400, "ValueEdge not configured")
    
    try:
        async with ValueEdgeClient(config) as client:
            item_data = await client.get_work_item(item_id, shared_space_id)
            return client.extract_relevant_fields(item_data)
    except ValueEdgeNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueEdgeAuthError as e:
        raise HTTPException(401, str(e))
    except ValueEdgeClientError as e:
        raise HTTPException(500, str(e))
```

## Edge Cases
1. **Token expiration**: OAuth tokens expire ~1 hour - implement automatic refresh
2. **Shared space ID**: May be passed per-request or use default from config
3. **Pagination**: Large result sets may need pagination handling
4. **Nested fields**: Some fields are nested objects - extract safely
