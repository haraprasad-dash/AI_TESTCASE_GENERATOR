"""
Input validation utilities.
"""
import re
from typing import Optional


def validate_jira_id(issue_key: str) -> bool:
    """
    Validate JIRA issue key format.
    Format: PROJECT-123
    """
    if not issue_key:
        return False
    pattern = r'^[A-Z][A-Z0-9]*-\d+$'
    return bool(re.match(pattern, issue_key))


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal.
    """
    # Remove any path components
    filename = filename.replace('..', '')
    filename = filename.replace('/', '')
    filename = filename.replace('\\', '')
    
    # Keep only safe characters
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    
    return filename


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def validate_temperature(temperature: float) -> float:
    """
    Validate and clamp temperature value.
    Temperature should be between 0.0 and 1.0.
    """
    return max(0.0, min(1.0, temperature))


def validate_max_tokens(max_tokens: int) -> int:
    """
    Validate and clamp max tokens value.
    """
    return max(1, min(8192, max_tokens))
