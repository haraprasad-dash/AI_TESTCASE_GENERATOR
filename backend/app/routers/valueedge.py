"""
ValueEdge API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
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
    override: Dict[str, Any] = Body(default_factory=dict),
    config: ValueEdgeConfig = Depends(get_valueedge_config)
) -> Dict[str, Any]:
    """Test ValueEdge connection."""
    merged = ValueEdgeConfig(
        base_url=override.get("base_url") or config.base_url,
        client_id=override.get("client_id") or config.client_id,
        client_secret=override.get("client_secret") or config.client_secret,
        shared_space_id=override.get("shared_space_id") or config.shared_space_id,
    )

    if not all([merged.base_url, merged.client_id, merged.client_secret]):
        raise HTTPException(400, "ValueEdge not configured")
    
    try:
        async with ValueEdgeClient(merged) as client:
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
