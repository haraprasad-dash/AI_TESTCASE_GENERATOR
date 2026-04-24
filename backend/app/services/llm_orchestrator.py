"""
LLM Orchestrator - Unified interface for Groq and Ollama providers.
"""
import os
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import groq
from groq import Groq


class ProviderType(str, Enum):
    GROQ = "groq"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    provider: ProviderType
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class LLMConfig:
    """Configuration for LLM generation."""
    provider: ProviderType
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096
    top_p: Optional[float] = 0.9
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    # Provider-specific settings
    api_key: Optional[str] = None  # For Groq
    base_url: Optional[str] = None  # For Ollama


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Generate text as a stream."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test provider connectivity."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass


class GroqProvider(LLMProvider):
    """Groq cloud provider implementation."""
    
    # Minimal fallback only when live API lookup is unavailable.
    GROQ_MODELS = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    ]

    # Known retired/decommissioned Groq model ids that should never be shown.
    DECOMMISSIONED_MODELS = {
        "deepseek-r1-distill-qwen-32b",
        "deepseek-r1-distill-llama-70b",
        "mixtral-8x7b-32768",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: Optional[float] = 0.9,
        frequency_penalty: Optional[float] = 0.0,
        presence_penalty: Optional[float] = 0.0,
    ) -> LLMResponse:
        """Generate using Groq API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider=ProviderType.GROQ,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
            
        except groq.AuthenticationError as e:
            raise LLMError(f"Groq authentication failed: {e}")
        except groq.RateLimitError as e:
            raise LLMError(f"Groq rate limit exceeded: {e}")
        except Exception as e:
            raise LLMError(f"Groq generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: Optional[float] = 0.9,
        frequency_penalty: Optional[float] = 0.0,
        presence_penalty: Optional[float] = 0.0,
    ) -> AsyncIterator[str]:
        """Generate streaming response from Groq."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise LLMError(f"Groq stream failed: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Groq connection."""
        try:
            # Run SDK call in a thread and enforce a hard timeout so UI never hangs.
            models = await asyncio.wait_for(
                asyncio.to_thread(self.client.models.list),
                timeout=10.0,
            )
            return {
                "status": "connected",
                "provider": "groq",
                "available_models": len(models.data)
            }
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "provider": "groq",
                "error": "Groq connection timed out. Check network/firewall and try again."
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "groq",
                "error": str(e)
            }
    
    async def list_models(self) -> List[str]:
        """List available Groq models."""
        try:
            models = await asyncio.wait_for(
                asyncio.to_thread(self.client.models.list),
                timeout=10.0,
            )
            api_models = sorted(
                {
                    m.id.strip()
                    for m in models.data
                    if getattr(m, "id", None) and isinstance(m.id, str) and m.id.strip()
                }
            )
            filtered = [m for m in api_models if m not in self.DECOMMISSIONED_MODELS]
            return filtered or self.GROQ_MODELS
        except Exception:
            return self.GROQ_MODELS


class OllamaProvider(LLMProvider):
    """Ollama local provider implementation."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: Optional[float] = 0.9,
        frequency_penalty: Optional[float] = 0.0,
        presence_penalty: Optional[float] = 0.0,
    ) -> LLMResponse:
        """Generate using Ollama API."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        if not model:
            raise LLMError("No Ollama model configured. Select a model in AI Configuration or set OLLAMA_DEFAULT_MODEL.")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "top_p": top_p,
                            # Ollama has no direct OpenAI-style frequency/presence penalties.
                            # Keep API compatibility by passing a bounded repeat penalty.
                            "repeat_penalty": max(1.0, 1.0 + float((frequency_penalty or 0.0) * 0.1)),
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return LLMResponse(
                    content=data.get("response", ""),
                    model=model,
                    provider=ProviderType.OLLAMA,
                    prompt_tokens=data.get("prompt_eval_count"),
                    completion_tokens=data.get("eval_count"),
                    total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0))
                )
                
        except httpx.ConnectError:
            raise LLMError(f"Cannot connect to Ollama at {self.base_url}. Is it running?")
        except Exception as e:
            raise LLMError(f"Ollama generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: Optional[float] = 0.9,
        frequency_penalty: Optional[float] = 0.0,
        presence_penalty: Optional[float] = 0.0,
    ) -> AsyncIterator[str]:
        """Generate streaming response from Ollama."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        if not model:
            raise LLMError("No Ollama model configured. Select a model in AI Configuration or set OLLAMA_DEFAULT_MODEL.")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "top_p": top_p,
                            "repeat_penalty": max(1.0, 1.0 + float((frequency_penalty or 0.0) * 0.1)),
                        }
                    }
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            import json
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError:
                                pass
                                
        except Exception as e:
            raise LLMError(f"Ollama stream failed: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = data.get("models", [])
                
                return {
                    "status": "connected",
                    "provider": "ollama",
                    "available_models": len(models),
                    "models": [m.get("name") for m in models]
                }
                
        except httpx.ConnectError:
            return {
                "status": "error",
                "provider": "ollama",
                "error": f"Cannot connect to Ollama at {self.base_url}"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "ollama",
                "error": str(e)
            }
    
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m.get("name") for m in data.get("models", [])]
                
        except Exception as e:
            raise LLMError(f"Failed to list Ollama models: {e}")


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMOrchestrator:
    """Orchestrator for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._provider: Optional[LLMProvider] = None
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the appropriate provider."""
        if self.config.provider == ProviderType.GROQ:
            api_key = self.config.api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise LLMError("Groq API key not provided")
            self._provider = GroqProvider(api_key)
            
        elif self.config.provider == ProviderType.OLLAMA:
            base_url = self.config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self._provider = OllamaProvider(base_url)
            
        else:
            raise LLMError(f"Unknown provider: {self.config.provider}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate text using configured provider."""
        return await self._provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
        )
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Generate text stream using configured provider."""
        async for chunk in self._provider.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
        ):
            yield chunk
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test provider connection."""
        return await self._provider.test_connection()
    
    async def list_models(self) -> List[str]:
        """List available models."""
        return await self._provider.list_models()


def create_orchestrator(
    provider: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    top_p: Optional[float] = 0.9,
    frequency_penalty: Optional[float] = 0.0,
    presence_penalty: Optional[float] = 0.0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> LLMOrchestrator:
    """Factory function to create orchestrator from settings."""
    provider_type = ProviderType(provider)
    from app.config import get_settings

    settings = get_settings()
    default_model = settings.groq_default_model if provider_type == ProviderType.GROQ else settings.ollama_default_model
    resolved_model = (model or default_model or "").strip()
    if not resolved_model:
        raise LLMError(f"No model configured for provider '{provider_type.value}'.")
    
    config = LLMConfig(
        provider=provider_type,
        model=resolved_model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        api_key=api_key,
        base_url=base_url
    )
    
    return LLMOrchestrator(config)
