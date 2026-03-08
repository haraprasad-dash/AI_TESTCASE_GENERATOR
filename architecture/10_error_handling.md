# SOP 10: Error Handling

## Goal
Implement comprehensive error handling with retry logic and user-friendly messages.

## Layer
Layer 3: Tools (distributed across all modules)

## Error Categories

| Code | Category | Example | User Message |
|------|----------|---------|--------------|
| AUTH_001 | Authentication | Invalid JIRA token | "JIRA authentication failed. Please check your API token in settings." |
| CONN_001 | Connection | JIRA server unreachable | "Cannot connect to JIRA. Please check your network and JIRA URL." |
| FILE_001 | File Upload | File too large | "File exceeds 20MB limit. Please compress or split the file." |
| FILE_002 | File Processing | OCR failed | "Could not extract text from image. Please check image quality." |
| LLM_001 | LLM Error | Groq rate limit | "Rate limit exceeded. Please wait a moment and try again." |
| LLM_002 | LLM Error | Ollama not running | "Ollama is not running. Please start Ollama or switch to Groq." |
| GEN_001 | Generation | Empty context | "No requirements found. Please provide JIRA ID, ValueEdge ID, or upload files." |

## Implementation

### Custom Exceptions (`utils/exceptions.py`)

```python
"""
Custom exceptions for the application.
"""


class AppError(Exception):
    """Base application error."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


# Authentication Errors
class AuthenticationError(AppError):
    """Base authentication error."""
    pass


class JiraAuthError(AuthenticationError):
    """JIRA authentication failed."""
    
    def __init__(self, message: str = "JIRA authentication failed", details: dict = None):
        super().__init__(
            message=message,
            code="AUTH_001",
            details=details
        )


class ValueEdgeAuthError(AuthenticationError):
    """ValueEdge authentication failed."""
    
    def __init__(self, message: str = "ValueEdge authentication failed", details: dict = None):
        super().__init__(
            message=message,
            code="AUTH_002",
            details=details
        )


# Connection Errors
class ConnectionError(AppError):
    """Base connection error."""
    pass


class JiraConnectionError(ConnectionError):
    """Cannot connect to JIRA."""
    
    def __init__(self, message: str = "Cannot connect to JIRA", details: dict = None):
        super().__init__(
            message=message,
            code="CONN_001",
            details=details
        )


class ValueEdgeConnectionError(ConnectionError):
    """Cannot connect to ValueEdge."""
    
    def __init__(self, message: str = "Cannot connect to ValueEdge", details: dict = None):
        super().__init__(
            message=message,
            code="CONN_002",
            details=details
        )


# File Errors
class FileError(AppError):
    """Base file error."""
    pass


class FileTooLargeError(FileError):
    """File exceeds size limit."""
    
    def __init__(self, size_mb: float, max_mb: float = 20):
        super().__init__(
            message=f"File too large: {size_mb:.1f}MB (max {max_mb}MB)",
            code="FILE_001",
            details={"size_mb": size_mb, "max_mb": max_mb}
        )


class FileProcessingError(FileError):
    """Failed to process file."""
    
    def __init__(self, message: str, filename: str = None):
        super().__init__(
            message=message,
            code="FILE_002",
            details={"filename": filename}
        )


# LLM Errors
class LLMError(AppError):
    """Base LLM error."""
    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(
            message=message,
            code="LLM_001",
            details={"retry_after": retry_after}
        )


class LLMUnavailableError(LLMError):
    """LLM service unavailable."""
    
    def __init__(self, provider: str, message: str = None):
        super().__init__(
            message=message or f"{provider} is not available",
            code="LLM_002",
            details={"provider": provider}
        )


# Generation Errors
class GenerationError(AppError):
    """Base generation error."""
    pass


class EmptyContextError(GenerationError):
    """No input sources provided."""
    
    def __init__(self):
        super().__init__(
            message="No requirements found. Please provide JIRA ID, ValueEdge ID, or upload files.",
            code="GEN_001",
            details={}
        )
```

### Retry Logic (`utils/retry.py`)

```python
"""
Retry logic with exponential backoff.
"""
import asyncio
import random
from functools import wraps
from typing import Callable, TypeVar, Tuple, Optional
from app.utils.exceptions import AppError

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Tuple[type, ...] = (Exception,),
        on_retry: Optional[Callable[[Exception, int], None]] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
        self.on_retry = on_retry


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and jitter."""
    # Exponential backoff
    delay = config.base_delay * (config.exponential_base ** attempt)
    
    # Add jitter (±25%)
    jitter = delay * 0.25
    delay = delay + random.uniform(-jitter, jitter)
    
    # Cap at max delay
    return min(delay, config.max_delay)


async def retry_async(
    func: Callable[..., T],
    config: RetryConfig,
    *args,
    **kwargs
) -> T:
    """Execute async function with retry logic."""
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            # Don't retry on the last attempt
            if attempt >= config.max_retries:
                break
            
            # Calculate delay
            delay = calculate_delay(attempt, config)
            
            # Call retry callback if provided
            if config.on_retry:
                config.on_retry(e, attempt + 1)
            
            # Wait before retry
            await asyncio.sleep(delay)
    
    # All retries exhausted
    raise last_exception


def with_retry(config: RetryConfig = None):
    """Decorator for adding retry logic to async functions."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)
        return wrapper
    return decorator


# Predefined retry configs
RETRY_CONFIGS = {
    "jira_api": RetryConfig(
        max_retries=3,
        base_delay=1.0,
        exponential_base=2.0,
        retryable_exceptions=(ConnectionError, TimeoutError)
    ),
    "valueedge_api": RetryConfig(
        max_retries=3,
        base_delay=1.0,
        exponential_base=2.0,
        retryable_exceptions=(ConnectionError, TimeoutError)
    ),
    "llm_generation": RetryConfig(
        max_retries=2,
        base_delay=2.0,
        exponential_base=1.5,  # Linear-ish backoff
        retryable_exceptions=(ConnectionError, TimeoutError)
    ),
    "file_upload": RetryConfig(
        max_retries=1,
        base_delay=0.5,
        retryable_exceptions=(IOError,)
    )
}
```

### Error Handler Middleware (`middleware/error_handler.py`)

```python
"""
Global error handler middleware for FastAPI.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.exceptions import AppError


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except AppError as e:
            # Handle custom application errors
            return JSONResponse(
                status_code=self._get_status_code(e),
                content={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details
                    }
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            # Log the full error internally
            # Return generic message to client
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                }
            )
    
    def _get_status_code(self, error: AppError) -> int:
        """Map error codes to HTTP status codes."""
        code_map = {
            "AUTH_001": 401,
            "AUTH_002": 401,
            "CONN_001": 503,
            "CONN_002": 503,
            "FILE_001": 413,
            "FILE_002": 422,
            "LLM_001": 429,
            "LLM_002": 503,
            "GEN_001": 422,
        }
        return code_map.get(error.code, 500)
```

## User-Friendly Error Messages

| Error Code | User Message | Action |
|------------|--------------|--------|
| AUTH_001 | "JIRA authentication failed. Please check your API token in settings." | Open Settings |
| CONN_001 | "Cannot connect to JIRA. Please check your network and JIRA URL." | Retry with delay |
| FILE_001 | "File exceeds 20MB limit. Please compress or split the file." | Suggest compression |
| LLM_001 | "Rate limit exceeded. Please wait a moment and try again." | Auto-retry with backoff |
| LLM_002 | "Ollama is not running. Please start Ollama or switch to Groq." | Suggest alternative |
| GEN_001 | "No requirements found. Please provide JIRA ID, ValueEdge ID, or upload files." | Highlight input area |

## Edge Cases
1. **Multiple errors**: Show first error, log all errors
2. **Retry exhaustion**: Show final error with suggestion
3. **Partial failures**: Continue with available data, warn user
4. **Network intermittency**: Retry with exponential backoff
5. **Rate limiting**: Respect Retry-After header
