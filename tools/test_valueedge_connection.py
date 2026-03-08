#!/usr/bin/env python3
"""
OpenText ValueEdge API Connection Test Tool
Phase 2: Link - Connectivity Verification

Usage:
    python tools/test_valueedge_connection.py
    python tools/test_valueedge_connection.py --item 1234
"""

import os
import sys
import argparse
import asyncio
import httpx
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def get_access_token(
    base_url: str,
    client_id: str,
    client_secret: str
) -> dict:
    """Get OAuth 2.0 access token using client credentials flow."""
    token_url = f"{base_url}/authentication/sign_in"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            token_url,
            headers={"Content-Type": "application/json"},
            json={
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "access_token": data.get("access_token"),
                "token_type": data.get("token_type", "Bearer"),
                "expires_in": data.get("expires_in", 3600)
            }
        else:
            return {
                "status": "error",
                "message": f"Token request failed: HTTP {response.status_code}",
                "response": response.text[:200]
            }


async def test_valueedge_connection(
    base_url: str = None,
    client_id: str = None,
    client_secret: str = None
) -> dict:
    """
    Test connection to ValueEdge API.
    
    Args:
        base_url: ValueEdge base URL
        client_id: OAuth client ID
        client_secret: OAuth client secret
        
    Returns:
        dict with status, message, and details
    """
    result = {
        "status": "unknown",
        "message": "",
        "details": {},
        "timestamp": None
    }
    
    # Get credentials from args or environment
    base_url = (base_url or os.getenv("VALUEEDGE_BASE_URL", "")).rstrip("/")
    client_id = client_id or os.getenv("VALUEEDGE_CLIENT_ID")
    client_secret = client_secret or os.getenv("VALUEEDGE_CLIENT_SECRET")
    
    # Validate inputs
    missing = []
    if not base_url:
        missing.append("VALUEEDGE_BASE_URL")
    if not client_id:
        missing.append("VALUEEDGE_CLIENT_ID")
    if not client_secret:
        missing.append("VALUEEDGE_CLIENT_SECRET")
    
    if missing:
        result["status"] = "error"
        result["message"] = f"Missing configuration: {', '.join(missing)}"
        result["details"]["hint"] = "Set environment variables or use command line arguments"
        return result
    
    print(f"🔗 Testing connection to: {base_url}")
    print(f"👤 Client ID: {client_id[:8]}..." if len(client_id) > 8 else f"👤 Client ID: {client_id}")
    masked_secret = client_secret[:4] + "..." + client_secret[-4:] if len(client_secret) > 8 else "***"
    print(f"🔑 Client Secret: {masked_secret}")
    
    try:
        # Get access token
        print("⏳ Requesting OAuth token...")
        token_result = await get_access_token(base_url, client_id, client_secret)
        
        if token_result["status"] == "error":
            result["status"] = "error"
            result["message"] = token_result["message"]
            if "response" in token_result:
                result["details"]["response"] = token_result["response"]
            return result
        
        access_token = token_result["access_token"]
        print("✅ OAuth token obtained successfully")
        
        # Test connection by fetching shared spaces
        print("⏳ Testing API access...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/api/shared_spaces",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                spaces = data.get("data", [])
                
                result["status"] = "success"
                result["message"] = f"Connected! Found {len(spaces)} shared space(s)"
                result["details"] = {
                    "shared_spaces": [
                        {"id": s.get("id"), "name": s.get("name")} 
                        for s in spaces
                    ],
                    "token_expires_in": token_result.get("expires_in")
                }
                
            elif response.status_code == 401:
                result["status"] = "error"
                result["message"] = "Token valid but API access denied"
                
            else:
                result["status"] = "error"
                result["message"] = f"API Error: HTTP {response.status_code}"
                
    except httpx.ConnectError as e:
        result["status"] = "error"
        result["message"] = f"Cannot connect to {base_url}"
        result["details"]["error"] = str(e)
        result["details"]["hint"] = "Check your ValueEdge URL and network connection"
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Unexpected error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result


async def fetch_work_item(
    item_id: str,
    shared_space_id: str = None,
    base_url: str = None,
    client_id: str = None,
    client_secret: str = None
) -> dict:
    """Fetch a specific work item."""
    result = {"status": "unknown", "message": "", "details": {}}
    
    base_url = (base_url or os.getenv("VALUEEDGE_BASE_URL", "")).rstrip("/")
    client_id = client_id or os.getenv("VALUEEDGE_CLIENT_ID")
    client_secret = client_secret or os.getenv("VALUEEDGE_CLIENT_SECRET")
    shared_space_id = shared_space_id or os.getenv("VALUEEDGE_SHARED_SPACE_ID")
    
    if not all([base_url, client_id, client_secret]):
        result["status"] = "error"
        result["message"] = "Missing ValueEdge credentials"
        return result
    
    if not shared_space_id:
        result["status"] = "error"
        result["message"] = "Missing shared_space_id (set VALUEEDGE_SHARED_SPACE_ID)"
        return result
    
    try:
        # Get token
        token_result = await get_access_token(base_url, client_id, client_secret)
        if token_result["status"] == "error":
            result["status"] = "error"
            result["message"] = token_result["message"]
            return result
        
        access_token = token_result["access_token"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"⏳ Fetching work item: {item_id}")
            
            response = await client.get(
                f"{base_url}/api/shared_spaces/{shared_space_id}/work_items/{item_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result["status"] = "success"
                result["message"] = f"Work item found: {item_id}"
                result["details"] = {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "type": data.get("subtype", data.get("type")),
                    "phase": data.get("phase", {}).get("name") if data.get("phase") else None
                }
                
            elif response.status_code == 404:
                result["status"] = "error"
                result["message"] = f"Work item not found: {item_id}"
                
            else:
                result["status"] = "error"
                result["message"] = f"HTTP Error {response.status_code}"
                
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error: {str(e)}"
    
    return result


async def main_async():
    parser = argparse.ArgumentParser(description="Test ValueEdge API Connection")
    parser.add_argument("--url", help="ValueEdge base URL")
    parser.add_argument("--client-id", help="OAuth client ID")
    parser.add_argument("--client-secret", help="OAuth client secret")
    parser.add_argument("--item", help="Fetch a specific work item")
    parser.add_argument("--shared-space", help="Shared space ID (for --item)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔗 VALUEDGE API CONNECTION TEST")
    print("=" * 60)
    print()
    
    if args.item:
        result = await fetch_work_item(
            args.item,
            args.shared_space,
            args.url,
            args.client_id,
            args.client_secret
        )
    else:
        result = await test_valueedge_connection(
            args.url,
            args.client_id,
            args.client_secret
        )
    
    print()
    print("-" * 60)
    if result["status"] == "success":
        print(f"✅ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        for key, value in result["details"].items():
            if key != "shared_spaces":
                print(f"   {key}: {value}")
        if result["details"].get("shared_spaces"):
            print("   Shared Spaces:")
            for space in result["details"]["shared_spaces"]:
                print(f"     - {space.get('id')}: {space.get('name')}")
    else:
        print(f"❌ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        if result["details"].get("hint"):
            print(f"💡 Hint: {result['details']['hint']}")
        if result["details"].get("error"):
            print(f"🔍 Error: {result['details']['error']}")
    print("-" * 60)
    
    sys.exit(0 if result["status"] == "success" else 1)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
