#!/usr/bin/env python3
"""
JIRA API Connection Test Tool
Phase 2: Link - Connectivity Verification

Usage:
    python tools/test_jira_connection.py
    python tools/test_jira_connection.py --issue PROJ-123
"""

import os
import sys
import base64
import argparse
import asyncio
import httpx
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_jira_connection(
    base_url: str = None,
    username: str = None,
    api_token: str = None
) -> dict:
    """
    Test connection to JIRA API.
    
    Args:
        base_url: JIRA base URL
        username: JIRA email/username
        api_token: JIRA API token
        
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
    base_url = base_url or os.getenv("JIRA_BASE_URL")
    username = username or os.getenv("JIRA_USERNAME")
    api_token = api_token or os.getenv("JIRA_API_TOKEN")
    
    # Validate inputs
    missing = []
    if not base_url:
        missing.append("JIRA_BASE_URL")
    if not username:
        missing.append("JIRA_USERNAME")
    if not api_token:
        missing.append("JIRA_API_TOKEN")
    
    if missing:
        result["status"] = "error"
        result["message"] = f"Missing configuration: {', '.join(missing)}"
        result["details"]["hint"] = "Set environment variables or use command line arguments"
        return result
    
    # Normalize base URL
    base_url = base_url.rstrip("/")
    
    print(f"🔗 Testing connection to: {base_url}")
    print(f"👤 Username: {username}")
    masked_token = api_token[:4] + "..." + api_token[-4:] if len(api_token) > 8 else "***"
    print(f"🔑 API Token: {masked_token}")
    
    try:
        # Create Basic Auth header
        credentials = base64.b64encode(
            f"{username}:{api_token}".encode()
        ).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test mypermissions endpoint
            print("⏳ Testing JIRA API connection...")
            
            response = await client.get(
                f"{base_url}/rest/api/3/myself",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result["status"] = "success"
                result["message"] = f"Connected as {data.get('displayName', username)}"
                result["details"] = {
                    "account_id": data.get("accountId"),
                    "email": data.get("emailAddress"),
                    "display_name": data.get("displayName"),
                    "active": data.get("active", False)
                }
                
            elif response.status_code == 401:
                result["status"] = "error"
                result["message"] = "Authentication failed - Invalid credentials"
                result["details"]["hint"] = "Check your API token at https://id.atlassian.com/manage-profile/security/api-tokens"
                
            elif response.status_code == 403:
                result["status"] = "error"
                result["message"] = "Forbidden - Insufficient permissions"
                
            else:
                result["status"] = "error"
                result["message"] = f"HTTP Error {response.status_code}"
                result["details"]["response"] = response.text[:200]
                
    except httpx.ConnectError as e:
        result["status"] = "error"
        result["message"] = f"Cannot connect to {base_url}"
        result["details"]["error"] = str(e)
        result["details"]["hint"] = "Check your JIRA URL and network connection"
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Unexpected error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result


async def fetch_issue(
    issue_key: str,
    base_url: str = None,
    username: str = None,
    api_token: str = None
) -> dict:
    """Fetch a specific JIRA issue."""
    result = {"status": "unknown", "message": "", "details": {}}
    
    base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
    username = username or os.getenv("JIRA_USERNAME")
    api_token = api_token or os.getenv("JIRA_API_TOKEN")
    
    if not all([base_url, username, api_token]):
        result["status"] = "error"
        result["message"] = "Missing JIRA credentials"
        return result
    
    try:
        credentials = base64.b64encode(
            f"{username}:{api_token}".encode()
        ).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"⏳ Fetching issue: {issue_key}")
            
            response = await client.get(
                f"{base_url}/rest/api/3/issue/{issue_key}",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", {})
                
                result["status"] = "success"
                result["message"] = f"Issue found: {issue_key}"
                result["details"] = {
                    "key": data.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "issue_type": fields.get("issuetype", {}).get("name"),
                    "priority": fields.get("priority", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
                }
                
            elif response.status_code == 404:
                result["status"] = "error"
                result["message"] = f"Issue not found: {issue_key}"
                
            else:
                result["status"] = "error"
                result["message"] = f"HTTP Error {response.status_code}"
                
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error: {str(e)}"
    
    return result


async def main_async():
    parser = argparse.ArgumentParser(description="Test JIRA API Connection")
    parser.add_argument("--url", help="JIRA base URL")
    parser.add_argument("--username", help="JIRA username/email")
    parser.add_argument("--api-token", help="JIRA API token")
    parser.add_argument("--issue", help="Fetch a specific issue (e.g., PROJ-123)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔗 JIRA API CONNECTION TEST")
    print("=" * 60)
    print()
    
    if args.issue:
        result = await fetch_issue(
            args.issue,
            args.url,
            args.username,
            args.api_token
        )
    else:
        result = await test_jira_connection(
            args.url,
            args.username,
            args.api_token
        )
    
    print()
    print("-" * 60)
    if result["status"] == "success":
        print(f"✅ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        for key, value in result["details"].items():
            print(f"   {key}: {value}")
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
