#!/usr/bin/env python3
"""
GROQ API Connection Test Tool
Phase 2: Link - Connectivity Verification

Usage:
    python tools/test_groq_connection.py
    python tools/test_groq_connection.py --model llama-3.3-70b-versatile
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from groq import Groq
    from groq import AuthenticationError, APIError
except ImportError:
    print("❌ ERROR: groq package not installed")
    print("   Run: pip install groq")
    sys.exit(1)


def test_groq_connection(api_key: str = None, model: str = "llama-3.3-70b-versatile") -> dict:
    """
    Test connection to Groq API.
    
    Args:
        api_key: Groq API key (defaults to GROQ_API_KEY env var)
        model: Model to test with
        
    Returns:
        dict with status, message, and details
    """
    result = {
        "status": "unknown",
        "message": "",
        "details": {},
        "timestamp": None
    }
    
    # Check API key
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        result["status"] = "error"
        result["message"] = "GROQ_API_KEY not provided or set in environment"
        return result
    
    # Mask key for display
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"🔑 Using API Key: {masked_key}")
    
    try:
        # Initialize client
        client = Groq(api_key=api_key)
        
        # Test with a simple completion
        print(f"🧪 Testing with model: {model}")
        print("⏳ Sending test request...")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Groq connection successful' and nothing else."}
            ],
            max_tokens=10,
            temperature=0.0
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        usage = response.usage
        
        result["status"] = "success"
        result["message"] = f"Connection successful: {content}"
        result["details"] = {
            "model": model,
            "response": content,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }
        
    except AuthenticationError as e:
        result["status"] = "error"
        result["message"] = f"Authentication failed: Invalid API key"
        result["details"]["error"] = str(e)
        
    except APIError as e:
        result["status"] = "error"
        result["message"] = f"API Error: {e.message}"
        result["details"]["error"] = str(e)
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Unexpected error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result


def list_available_models(api_key: str = None) -> list:
    """List available models from Groq."""
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ GROQ_API_KEY not set")
        return []
    
    try:
        client = Groq(api_key=api_key)
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Test Groq API Connection")
    parser.add_argument("--api-key", help="Groq API key (or set GROQ_API_KEY env var)")
    parser.add_argument("--model", default="llama-3.3-70b-versatile", help="Model to test")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔗 GROQ API CONNECTION TEST")
    print("=" * 60)
    
    if args.list_models:
        print("\n📋 Available Models:")
        models = list_available_models(args.api_key)
        for model in models:
            print(f"   - {model}")
        return
    
    print()
    result = test_groq_connection(args.api_key, args.model)
    
    print()
    print("-" * 60)
    if result["status"] == "success":
        print(f"✅ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        print(f"📊 Tokens Used: {result['details']['total_tokens']}")
    else:
        print(f"❌ STATUS: {result['status'].upper()}")
        print(f"📝 Message: {result['message']}")
        if result["details"].get("error"):
            print(f"🔍 Error Details: {result['details']['error']}")
    print("-" * 60)
    
    # Exit code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
