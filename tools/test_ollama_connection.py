#!/usr/bin/env python3
"""
Ollama API Connection Test Tool
Phase 2: Link - Connectivity Verification

Usage:
    python tools/test_ollama_connection.py
    python tools/test_ollama_connection.py --url http://localhost:11434
"""

import os
import sys
import argparse
import httpx
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_ollama_connection(base_url: str = "http://localhost:11434") -> dict:
    """
    Test connection to Ollama API.
    
    Args:
        base_url: Ollama base URL (defaults to OLLAMA_BASE_URL env var or localhost)
        
    Returns:
        dict with status, message, and details
    """
    result = {
        "status": "unknown",
        "message": "",
        "details": {},
        "timestamp": None
    }
    
    # Check base URL
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    base_url = base_url.rstrip("/")
    
    print(f"🔗 Testing connection to: {base_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test basic connectivity
            print("⏳ Checking Ollama server...")
            response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = data.get("models", [])
            
            if not models:
                result["status"] = "warning"
                result["message"] = "Ollama is running but no models are installed"
                result["details"]["models"] = []
            else:
                model_names = [m.get("name") for m in models]
                result["status"] = "success"
                result["message"] = f"Connected! {len(models)} model(s) available"
                result["details"]["models"] = model_names
                
                # Test generation with first available model
                test_model = model_names[0]
                print(f"🧪 Testing generation with model: {test_model}")
                
                try:
                    gen_response = await client.post(
                        f"{base_url}/api/generate",
                        json={
                            "model": test_model,
                            "prompt": "Say 'Ollama connection successful' and nothing else.",
                            "stream": False,
                            "options": {"temperature": 0.0}
                        },
                        timeout=30.0
                    )
                    gen_response.raise_for_status()
                    gen_data = gen_response.json()
                    
                    result["details"]["test_response"] = gen_data.get("response", "").strip()
                    result["details"]["test_model"] = test_model
                    
                except Exception as gen_err:
                    result["details"]["test_error"] = str(gen_err)
                    
    except httpx.ConnectError as e:
        result["status"] = "error"
        result["message"] = f"Cannot connect to Ollama at {base_url}"
        result["details"]["error"] = "Connection refused - Is Ollama running?"
        result["details"]["hint"] = "Start Ollama with: ollama serve"
        
    except httpx.TimeoutException:
        result["status"] = "error"
        result["message"] = "Connection timed out"
        result["details"]["error"] = "Request took too long"
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Unexpected error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result


async def pull_model(base_url: str, model: str) -> dict:
    """Pull a model from Ollama registry."""
    result = {"status": "unknown", "message": ""}
    base_url = base_url.rstrip("/")
    
    print(f"⬇️ Pulling model: {model}")
    print("⏳ This may take several minutes...")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{base_url}/api/pull",
                json={"name": model, "stream": False}
            )
            response.raise_for_status()
            
            result["status"] = "success"
            result["message"] = f"Successfully pulled model: {model}"
            
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Failed to pull model: {str(e)}"
    
    return result


async def main_async():
    parser = argparse.ArgumentParser(description="Test Ollama API Connection")
    parser.add_argument("--url", help="Ollama base URL (or set OLLAMA_BASE_URL env var)")
    parser.add_argument("--pull", help="Pull a model (e.g., llama3.1)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔗 OLLAMA API CONNECTION TEST")
    print("=" * 60)
    print()
    
    base_url = args.url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    if args.pull:
        result = await pull_model(base_url, args.pull)
        print()
        print("-" * 60)
        if result["status"] == "success":
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
        print("-" * 60)
        return
    
    result = await test_ollama_connection(base_url)
    
    print()
    print("-" * 60)
    if result["status"] == "success":
        print(f"✅ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        print(f"📦 Models: {', '.join(result['details']['models'])}")
        if result["details"].get("test_response"):
            print(f"🧪 Test Response: {result['details']['test_response']}")
    elif result["status"] == "warning":
        print(f"⚠️ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        print("💡 Tip: Run 'ollama pull llama3.1' to install a model")
    else:
        print(f"❌ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        if result["details"].get("hint"):
            print(f"💡 Hint: {result['details']['hint']}")
        if result["details"].get("error"):
            print(f"🔍 Error: {result['details']['error']}")
    print("-" * 60)
    
    # Exit code
    sys.exit(0 if result["status"] in ["success", "warning"] else 1)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
