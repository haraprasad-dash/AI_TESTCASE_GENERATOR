"""
Generation Service - Orchestrates test plan and test case generation.
"""
import uuid
import time
import re
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncIterator
from pathlib import Path

from app.models import (
    GenerationRequest, GenerationResponse, GenerationInputs,
    GenerationConfiguration, GenerationOutputs, GenerationMetadata,
    GenerationOutput, TestCasesOutput
)
from app.services.llm_orchestrator import (
    LLMOrchestrator, create_orchestrator, LLMError, LLMResponse
)


class GenerationError(Exception):
    """Base exception for generation errors."""
    pass


class ContextAssemblyError(GenerationError):
    """Failed to assemble context from inputs."""
    pass


class GenerationService:
    """Service for generating test plans and test cases."""
    
    async def generate(
        self,
        inputs: GenerationInputs,
        config: GenerationConfiguration,
        websocket_callback: Optional[callable] = None
    ) -> GenerationResponse:
        """
        Generate test plan and test cases.
        
        Args:
            inputs: JIRA ID, ValueEdge ID, files, custom prompt
            config: LLM provider, model, temperature settings
            websocket_callback: Optional callback for progress updates
            
        Returns:
            GenerationResponse with test plan and test cases
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            plan_prompt = self._resolve_section_prompt(inputs.test_plan_prompt, inputs.custom_prompt)
            case_prompt = self._resolve_section_prompt(inputs.test_case_prompt, inputs.custom_prompt)

            # Step 1: Assemble context
            if websocket_callback:
                await websocket_callback({"step": "assembling", "percent": 10})
            
            context = await self._assemble_context(inputs)
            sources = self._identify_sources(inputs)

            # Keep prompts within provider limits (especially Groq TPM limits).
            if context.strip():
                context = self._apply_context_budget(context, config.provider, config.model or "")
            
            has_custom_instructions = bool(plan_prompt or case_prompt)
            if not context.strip() and not has_custom_instructions:
                raise ContextAssemblyError("No content found in inputs")
            
            # Step 2: Initialize LLM orchestrator
            if websocket_callback:
                await websocket_callback({"step": "initializing", "percent": 20})

            from app.config import get_settings
            settings = get_settings()
            selected_model = config.model
            if config.provider == "groq":
                selected_model = self._resolve_supported_groq_model(config.model)

            orchestrator = create_orchestrator(
                provider=config.provider,
                model=selected_model,
                temperature=config.temperature,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                api_key=settings.groq_api_key if config.provider == "groq" else None,
                base_url=settings.ollama_base_url if config.provider == "ollama" else None
            )
            orchestrator.config.max_tokens = self._safe_max_tokens(
                config.max_tokens,
                config.provider,
                orchestrator.config.model,
            )
            
            # Step 3: Generate test plan
            if websocket_callback:
                await websocket_callback({"step": "generating_plan", "percent": 30})
            
            test_plan = await self._generate_test_plan(
                orchestrator,
                context,
                plan_prompt,
                inputs.use_test_plan_template,
            )
            
            # Step 4: Generate test cases
            if websocket_callback:
                await websocket_callback({"step": "generating_cases", "percent": 60})
            
            test_cases = await self._generate_test_cases(
                orchestrator,
                context,
                case_prompt,
                inputs.use_test_case_template,
            )

            combined_output = f"{test_plan.content}\n\n{test_cases.content}"
            clarification_questions = self._extract_clarification_questions(combined_output)
            clarification_prompt = self._merge_prompts(plan_prompt, case_prompt, inputs.custom_prompt)
            clarification_required = self._should_require_clarification(
                clarification_prompt,
                test_plan.content,
                test_cases.content,
                clarification_questions,
            )
            if clarification_required and not clarification_questions:
                clarification_questions = self._default_clarification_questions(clarification_prompt)
            
            # Step 5: Build response
            if websocket_callback:
                await websocket_callback({"step": "finalizing", "percent": 90})
            
            total_time = int((time.time() - start_time) * 1000)
            
            return GenerationResponse(
                request_id=request_id,
                status="completed",
                timestamp=datetime.utcnow(),
                outputs=GenerationOutputs(
                    test_plan=GenerationOutput(
                        content=test_plan.content,
                        format="markdown",
                        token_usage=test_plan.total_tokens,
                        generation_time_ms=total_time // 2
                    ),
                    test_cases=TestCasesOutput(
                        content="" if clarification_required else test_cases.content,
                        format="markdown",
                        count=0 if clarification_required else self._count_test_cases(test_cases.content),
                        token_usage=test_cases.total_tokens,
                        generation_time_ms=total_time // 2
                    )
                ),
                metadata=GenerationMetadata(
                    model_used=orchestrator.config.model,
                    temperature=config.temperature,
                    total_tokens=(test_plan.total_tokens or 0) + (test_cases.total_tokens or 0),
                    sources=sources,
                    clarification_required=clarification_required,
                    clarification_questions=clarification_questions
                )
            )
            
        except LLMError as e:
            # Ollama resilience: local models may timeout or fail (e.g., endpoint/model issues).
            # Return deterministic artifacts instead of an empty/failed result.
            if config.provider == "ollama":
                try:
                    plan_prompt = self._resolve_section_prompt(inputs.test_plan_prompt, inputs.custom_prompt)
                    case_prompt = self._resolve_section_prompt(inputs.test_case_prompt, inputs.custom_prompt)
                    bdd_mode = self._is_bdd_requested(case_prompt)
                    fallback_plan = self._build_fallback_test_plan(context, plan_prompt)
                    if bdd_mode:
                        fallback_cases = self._ensure_gherkin_fence(
                            self._build_fallback_bdd_test_cases(context, case_prompt)
                        )
                    else:
                        fallback_cases = self._build_fallback_table_test_cases(context, case_prompt)

                    clarification_prompt = self._merge_prompts(plan_prompt, case_prompt, inputs.custom_prompt)
                    clarification_required = self._explicitly_requests_clarification_first(clarification_prompt)
                    clarification_questions = self._default_clarification_questions(clarification_prompt) if clarification_required else []

                    total_time = int((time.time() - start_time) * 1000)
                    return GenerationResponse(
                        request_id=request_id,
                        status="completed",
                        timestamp=datetime.utcnow(),
                        outputs=GenerationOutputs(
                            test_plan=GenerationOutput(
                                content=fallback_plan,
                                format="markdown",
                                token_usage=0,
                                generation_time_ms=total_time // 2,
                            ),
                            test_cases=TestCasesOutput(
                                content="" if clarification_required else fallback_cases,
                                format="markdown",
                                count=0 if clarification_required else self._count_test_cases(fallback_cases),
                                token_usage=0,
                                generation_time_ms=total_time // 2,
                            ),
                        ),
                        metadata=GenerationMetadata(
                            model_used=f"ollama-fallback/{config.model or 'default'}",
                            temperature=config.temperature,
                            total_tokens=0,
                            sources=sources,
                            clarification_required=clarification_required,
                            clarification_questions=clarification_questions,
                        ),
                    )
                except Exception:
                    pass

            # Fallback: if Groq model hits rate limits, retry with adaptive token budget
            # and then alternate models/providers before failing.
            if config.provider == "groq" and (self._is_rate_limit_error(str(e)) or self._is_decommissioned_model_error(str(e))):
                try:
                    from app.config import get_settings
                    settings = get_settings()
                    retry_specs = self._build_groq_retry_specs(
                        error_message=str(e),
                        requested_model=config.model,
                        ollama_default_model=settings.ollama_default_model,
                    )

                    # Quality-preserving behavior: if immediate retry is not possible,
                    # wait and retry once on the same selected model (no model switch).
                    if not retry_specs and self._is_rate_limit_error(str(e)):
                        wait_seconds = self._rate_limit_backoff_seconds(str(e))
                        await asyncio.sleep(wait_seconds)
                        retry_specs = [{
                            "provider": "groq",
                            "model": config.model or "llama-3.3-70b-versatile",
                            "max_tokens": 256,
                        }]

                    if not retry_specs:
                        return GenerationResponse(
                            request_id=request_id,
                            status="failed",
                            timestamp=datetime.utcnow(),
                            outputs=GenerationOutputs(),
                            metadata=GenerationMetadata(
                                model_used=config.model or "unknown",
                                temperature=config.temperature,
                                sources=self._identify_sources(inputs)
                            ),
                            error=self._friendly_generation_error(str(e), config.provider, config.model or "")
                        )

                    for spec in retry_specs:
                        try:
                            fallback_orchestrator = create_orchestrator(
                                provider=spec["provider"],
                                model=spec["model"],
                                temperature=config.temperature,
                                top_p=config.top_p,
                                frequency_penalty=config.frequency_penalty,
                                presence_penalty=config.presence_penalty,
                                api_key=settings.groq_api_key if spec["provider"] == "groq" else None,
                                base_url=settings.ollama_base_url if spec["provider"] == "ollama" else None,
                            )
                            fallback_orchestrator.config.max_tokens = spec["max_tokens"]

                            plan_prompt = self._resolve_section_prompt(inputs.test_plan_prompt, inputs.custom_prompt)
                            case_prompt = self._resolve_section_prompt(inputs.test_case_prompt, inputs.custom_prompt)
                            test_plan = await self._generate_test_plan(
                                fallback_orchestrator,
                                context,
                                plan_prompt,
                                inputs.use_test_plan_template,
                            )
                            test_cases = await self._generate_test_cases(
                                fallback_orchestrator,
                                context,
                                case_prompt,
                                inputs.use_test_case_template,
                            )

                            combined_output = f"{test_plan.content}\n\n{test_cases.content}"
                            clarification_questions = self._extract_clarification_questions(combined_output)
                            clarification_required = self._should_require_clarification(
                                inputs.custom_prompt,
                                test_plan.content,
                                test_cases.content,
                                clarification_questions,
                            )
                            if clarification_required and not clarification_questions:
                                clarification_questions = self._default_clarification_questions(inputs.custom_prompt)
                            total_time = int((time.time() - start_time) * 1000)

                            return GenerationResponse(
                                request_id=request_id,
                                status="completed",
                                timestamp=datetime.utcnow(),
                                outputs=GenerationOutputs(
                                    test_plan=GenerationOutput(
                                        content=test_plan.content,
                                        format="markdown",
                                        token_usage=test_plan.total_tokens,
                                        generation_time_ms=total_time // 2,
                                    ),
                                    test_cases=TestCasesOutput(
                                        content="" if clarification_required else test_cases.content,
                                        format="markdown",
                                        count=0 if clarification_required else self._count_test_cases(test_cases.content),
                                        token_usage=test_cases.total_tokens,
                                        generation_time_ms=total_time // 2,
                                    ),
                                ),
                                metadata=GenerationMetadata(
                                    model_used=f"{spec['provider']}/{spec['model']}",
                                    temperature=config.temperature,
                                    total_tokens=(test_plan.total_tokens or 0) + (test_cases.total_tokens or 0),
                                    sources=sources,
                                    clarification_required=clarification_required,
                                    clarification_questions=clarification_questions,
                                ),
                            )
                        except Exception:
                            continue
                except Exception:
                    pass

            # Fallback: if Ollama hits timeout/model-not-found/connection issues,
            # retry with lower token budget and a stable local fallback model.
            if config.provider == "ollama":
                try:
                    from app.config import get_settings
                    settings = get_settings()
                    retry_specs = self._build_ollama_retry_specs(
                        error_message=str(e),
                        requested_model=config.model,
                        ollama_default_model=settings.ollama_default_model,
                    )

                    for spec in retry_specs:
                        try:
                            fallback_orchestrator = create_orchestrator(
                                provider="ollama",
                                model=spec["model"],
                                temperature=config.temperature,
                                top_p=config.top_p,
                                frequency_penalty=config.frequency_penalty,
                                presence_penalty=config.presence_penalty,
                                base_url=settings.ollama_base_url,
                            )
                            fallback_orchestrator.config.max_tokens = spec["max_tokens"]

                            plan_prompt = self._resolve_section_prompt(inputs.test_plan_prompt, inputs.custom_prompt)
                            case_prompt = self._resolve_section_prompt(inputs.test_case_prompt, inputs.custom_prompt)
                            test_plan = await self._generate_test_plan(
                                fallback_orchestrator,
                                context,
                                plan_prompt,
                                inputs.use_test_plan_template,
                            )
                            test_cases = await self._generate_test_cases(
                                fallback_orchestrator,
                                context,
                                case_prompt,
                                inputs.use_test_case_template,
                            )

                            combined_output = f"{test_plan.content}\n\n{test_cases.content}"
                            clarification_questions = self._extract_clarification_questions(combined_output)
                            clarification_required = self._should_require_clarification(
                                inputs.custom_prompt,
                                test_plan.content,
                                test_cases.content,
                                clarification_questions,
                            )
                            if clarification_required and not clarification_questions:
                                clarification_questions = self._default_clarification_questions(inputs.custom_prompt)
                            total_time = int((time.time() - start_time) * 1000)

                            return GenerationResponse(
                                request_id=request_id,
                                status="completed",
                                timestamp=datetime.utcnow(),
                                outputs=GenerationOutputs(
                                    test_plan=GenerationOutput(
                                        content=test_plan.content,
                                        format="markdown",
                                        token_usage=test_plan.total_tokens,
                                        generation_time_ms=total_time // 2,
                                    ),
                                    test_cases=TestCasesOutput(
                                        content="" if clarification_required else test_cases.content,
                                        format="markdown",
                                        count=0 if clarification_required else self._count_test_cases(test_cases.content),
                                        token_usage=test_cases.total_tokens,
                                        generation_time_ms=total_time // 2,
                                    ),
                                ),
                                metadata=GenerationMetadata(
                                    model_used=f"ollama/{spec['model']}",
                                    temperature=config.temperature,
                                    total_tokens=(test_plan.total_tokens or 0) + (test_cases.total_tokens or 0),
                                    sources=sources,
                                    clarification_required=clarification_required,
                                    clarification_questions=clarification_questions,
                                ),
                            )
                        except Exception:
                            continue
                except Exception:
                    pass

            return GenerationResponse(
                request_id=request_id,
                status="failed",
                timestamp=datetime.utcnow(),
                outputs=GenerationOutputs(),
                metadata=GenerationMetadata(
                    model_used=config.model or "unknown",
                    temperature=config.temperature,
                    sources=self._identify_sources(inputs)
                ),
                error=self._friendly_generation_error(str(e), config.provider, config.model or "")
            )

        except Exception as e:
            return GenerationResponse(
                request_id=request_id,
                status="failed",
                timestamp=datetime.utcnow(),
                outputs=GenerationOutputs(),
                metadata=GenerationMetadata(
                    model_used=config.model or "unknown",
                    temperature=config.temperature,
                    sources=self._identify_sources(inputs)
                ),
                error=str(e)
            )
    
    async def _assemble_context(self, inputs: GenerationInputs) -> str:
        """Assemble context from all input sources."""
        from app.services.jira_client import fetch_jira_issue, JiraClientError
        from app.services.valueedge_client import fetch_valueedge_item, ValueEdgeClientError
        from app.config import get_settings
        
        context_parts = []
        settings = get_settings()
        jira_ids = self._collect_ticket_ids(inputs.jira_id, getattr(inputs, "jira_ids", []))
        valueedge_ids = self._collect_ticket_ids(inputs.valueedge_id, getattr(inputs, "valueedge_ids", []))
        
        # Fetch JIRA content
        if jira_ids and settings.jira_base_url:
            jira_config = type('Config', (), {
                'base_url': settings.jira_base_url,
                'username': settings.jira_username,
                'api_token': settings.jira_api_token
            })()
            for jira_id in jira_ids:
                try:
                    issue_data = await fetch_jira_issue(jira_id, jira_config)
                    context_parts.append(self._format_jira_context(issue_data))
                except JiraClientError as e:
                    context_parts.append(f"<!-- JIRA fetch failed for {jira_id}: {e} -->")
        
        # Fetch ValueEdge content
        if valueedge_ids and settings.valueedge_base_url:
            ve_config = type('Config', (), {
                'base_url': settings.valueedge_base_url,
                'client_id': settings.valueedge_client_id,
                'client_secret': settings.valueedge_client_secret,
                'shared_space_id': settings.valueedge_shared_space_id
            })()
            for valueedge_id in valueedge_ids:
                try:
                    item_data = await fetch_valueedge_item(valueedge_id, ve_config)
                    context_parts.append(self._format_valueedge_context(item_data))
                except ValueEdgeClientError as e:
                    context_parts.append(f"<!-- ValueEdge fetch failed for {valueedge_id}: {e} -->")
        
        # Add file content
        for file in inputs.files:
            if file.extracted_text:
                context_parts.append(self._format_file_context(file))
        
        return "\n\n---\n\n".join(context_parts)
    
    def _identify_sources(self, inputs: GenerationInputs) -> List[str]:
        """Identify which sources were used."""
        sources = []
        if self._collect_ticket_ids(inputs.jira_id, getattr(inputs, "jira_ids", [])):
            sources.append("jira")
        if self._collect_ticket_ids(inputs.valueedge_id, getattr(inputs, "valueedge_ids", [])):
            sources.append("valueedge")
        if inputs.files:
            sources.append("files")
        has_custom = any([
            bool(inputs.custom_prompt and inputs.custom_prompt.strip()),
            bool(inputs.test_plan_prompt and inputs.test_plan_prompt.strip()),
            bool(inputs.test_case_prompt and inputs.test_case_prompt.strip()),
        ])
        if has_custom:
            sources.append("custom_instructions")
        return sources

    def _collect_ticket_ids(self, primary_id: Optional[str], additional_ids: Optional[List[str]]) -> List[str]:
        """Collect ticket IDs from legacy single field + new list field, preserving order and uniqueness."""
        collected: List[str] = []
        if primary_id and primary_id.strip():
            collected.append(primary_id.strip())

        for ticket_id in additional_ids or []:
            if ticket_id and str(ticket_id).strip():
                normalized = str(ticket_id).strip()
                if normalized not in collected:
                    collected.append(normalized)

        return collected
    
    def _format_jira_context(self, issue_data: Dict[str, Any]) -> str:
        """Format JIRA issue data as context."""
        parts = [f"## JIRA Issue: {issue_data.get('key')}"]
        parts.append(f"**Summary:** {issue_data.get('summary', 'N/A')}")
        parts.append(f"**Type:** {issue_data.get('issue_type', 'N/A')}")
        parts.append(f"**Priority:** {issue_data.get('priority', 'N/A')}")
        parts.append(f"**Status:** {issue_data.get('status', 'N/A')}")
        
        if issue_data.get('description'):
            parts.append(f"\n**Description:**\n{issue_data['description']}")
        
        if issue_data.get('labels'):
            parts.append(f"\n**Labels:** {', '.join(issue_data['labels'])}")
        
        return "\n".join(parts)
    
    def _format_valueedge_context(self, item_data: Dict[str, Any]) -> str:
        """Format ValueEdge item data as context."""
        parts = [f"## ValueEdge Item: {item_data.get('id')}"]
        parts.append(f"**Name:** {item_data.get('name', 'N/A')}")
        parts.append(f"**Type:** {item_data.get('type', 'N/A')}")
        parts.append(f"**Phase:** {item_data.get('phase', 'N/A')}")
        
        if item_data.get('description'):
            parts.append(f"\n**Description:**\n{item_data['description']}")
        
        return "\n".join(parts)
    
    def _format_file_context(self, file_input) -> str:
        """Format file content as context."""
        parts = [f"## Uploaded Document: {file_input.filename}"]
        parts.append(file_input.extracted_text)
        return "\n".join(parts)

    def _safe_max_tokens(self, requested: int, provider: str, model: str) -> int:
        """Clamp completion tokens to provider-safe defaults.

        Groq-hosted llama-3.3-70b-versatile supports 32 768 context tokens.
        Previous 1 200-token cap caused truncated / thin outputs.  Now we
        allow up to 4 096 completion tokens for standard models while still
        keeping a conservative cap for GPT-OSS models with tighter TPM.
        """
        requested = max(256, requested or 4096)

        if provider == "groq":
            if "gpt-oss" in (model or ""):
                return min(requested, 450)
            # Standard Groq models (llama-3.x, mixtral): allow full user budget.
            return min(requested, 4096)

        # Ollama local models can become very slow on large completions.
        return min(requested, 4096)

    def _is_rate_limit_error(self, message: str) -> bool:
        lower = (message or "").lower()
        markers = ["rate limit", "rate_limit_exceeded", "429", "tpm", "tpd"]
        return any(marker in lower for marker in markers)

    def _is_decommissioned_model_error(self, message: str) -> bool:
        lower = (message or "").lower()
        markers = ["decommissioned", "model_decommissioned", "no longer supported", "invalid_request_error"]
        return any(marker in lower for marker in markers)

    def _is_timeout_error(self, message: str) -> bool:
        lower = (message or "").lower()
        markers = ["timeout", "timed out", "read timeout", "request timed out", "context deadline"]
        return any(marker in lower for marker in markers)

    def _resolve_supported_groq_model(self, requested_model: Optional[str]) -> str:
        """Map known retired Groq models to a stable supported default."""
        fallback = "llama-3.3-70b-versatile"
        if not requested_model:
            return fallback

        retired_prefixes = [
            "deepseek-r1-distill-qwen-32b",
            "deepseek-r1-distill-llama-70b",
            "mixtral-8x7b-32768",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        normalized = requested_model.strip().lower()
        if any(normalized == p for p in retired_prefixes):
            return fallback
        return requested_model

    def _extract_remaining_groq_tokens(self, message: str) -> Optional[int]:
        """Parse Groq error text like 'Limit 200000, Used 198760, Requested 1925'."""
        if not message:
            return None
        match = re.search(r'Limit\s+(\d+)\s*,\s*Used\s+(\d+)\s*,\s*Requested\s+(\d+)', message, re.IGNORECASE)
        if not match:
            return None
        limit = int(match.group(1))
        used = int(match.group(2))
        remaining = limit - used
        return max(0, remaining)

    def _extract_requested_groq_tokens(self, message: str) -> Optional[int]:
        """Parse requested token count from Groq rate-limit error message."""
        if not message:
            return None
        match = re.search(r'Requested\s+(\d+)', message, re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))

    def _rate_limit_backoff_seconds(self, message: str) -> int:
        """Compute bounded backoff for same-model retry on Groq rate-limit.

        This does not change model or quality constraints; it only waits and retries once.
        """
        remaining = self._extract_remaining_groq_tokens(message)
        requested = self._extract_requested_groq_tokens(message)

        if remaining is None:
            return 20

        if remaining <= 0:
            return 60

        if requested is None:
            return 20

        deficit = requested - remaining
        if deficit <= 0:
            return 10

        # Conservative bounded wait window.
        return max(15, min(60, int(deficit / 40)))

    def _build_groq_retry_specs(
        self,
        error_message: str,
        requested_model: Optional[str],
        ollama_default_model: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Build Groq retry strategy.

        Policy:
        - Rate-limit errors: preserve explicit user-selected Groq model; retry only same model
          with reduced max_tokens. Do not silently switch to another model.
        - Decommissioned model errors: allow fallback to supported Groq models, then Ollama.
        """
        model = requested_model or "llama-3.3-70b-versatile"
        specs: List[Dict[str, Any]] = []

        if self._is_rate_limit_error(error_message):
            remaining = self._extract_remaining_groq_tokens(error_message)
            if remaining and remaining >= 280:
                specs.append({
                    "provider": "groq",
                    "model": model,
                    "max_tokens": max(256, min(remaining - 120, 900)),
                })
            return specs

        if self._is_decommissioned_model_error(error_message):
            for fallback_model in [
                "llama-3.3-70b-versatile",
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "openai/gpt-oss-120b",
            ]:
                if fallback_model != model:
                    specs.append({
                        "provider": "groq",
                        "model": fallback_model,
                        "max_tokens": 700,
                    })

            configured_ollama = (ollama_default_model or "").strip()
            if configured_ollama:
                specs.append({
                    "provider": "ollama",
                    "model": configured_ollama,
                    "max_tokens": 700,
                })

        return specs

    def _build_ollama_retry_specs(
        self,
        error_message: str,
        requested_model: Optional[str],
        ollama_default_model: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Build Ollama retry strategy.

        Policy:
        - Timeout or heavy-load errors: retry same model with reduced max_tokens once.
        - Missing model errors: retry with configured default model (if present).
        - Connection errors: no retry specs; return actionable error to user.
        """
        model = requested_model or ollama_default_model or ""
        lower = (error_message or "").lower()
        specs: List[Dict[str, Any]] = []

        if "cannot connect to ollama" in lower or "connection refused" in lower:
            return specs

        if self._is_timeout_error(error_message):
            if not model:
                return specs
            specs.append({
                "model": model,
                "max_tokens": 1200,
            })
            return specs

        if "model" in lower and ("not found" in lower or "does not exist" in lower):
            configured = (ollama_default_model or "").strip()
            if configured and configured != model:
                specs.append({
                    "model": configured,
                    "max_tokens": 1200,
                })

        return specs

    def _friendly_generation_error(self, raw_error: str, provider: str, model: str) -> str:
        """Return user-friendly actionable error text while preserving root cause context."""
        if provider == "groq" and self._is_rate_limit_error(raw_error):
            remaining = self._extract_remaining_groq_tokens(raw_error)
            if remaining is not None:
                return (
                    f"Groq token limit reached for model '{model}'. "
                    f"Remaining daily tokens are too low ({remaining}). "
                    "Please switch to another Groq model, use Ollama local provider, or retry later after quota reset."
                )
            return (
                f"Groq rate limit reached for model '{model}'. "
                "Please switch model/provider (recommended: Ollama local) or retry later."
            )
        if provider == "ollama":
            lower = (raw_error or "").lower()
            if "cannot connect to ollama" in lower or "connection refused" in lower:
                return (
                    "Cannot connect to Ollama. Please ensure Ollama is running and reachable at OLLAMA_BASE_URL "
                    "(default http://localhost:11434), then retry."
                )
            if "model" in lower and ("not found" in lower or "does not exist" in lower):
                return (
                    f"Ollama model '{model}' is not installed. Run: ollama pull {model} "
                    "or switch to an installed model from AI Configuration."
                )
            if self._is_timeout_error(raw_error):
                return (
                    f"Ollama request timed out for model '{model}'. "
                    "Try again with lower max tokens or use a lighter model."
                )
        return raw_error

    def _apply_context_budget(self, context: str, provider: str, model: str = "") -> str:
        """Trim oversized context so prompt + completion stays inside provider limits."""
        if not context:
            return context

        # Rough estimate: ~4 chars per token for English-heavy text.
        def est_tokens(text: str) -> int:
            return max(1, len(text) // 4)

        # Groq llama-3.3-70b has 32k context; allow generous input budget.
        # GPT-OSS models still have tight TPM — keep them conservative.
        if provider == "groq" and "gpt-oss" in (model or ""):
            max_context_tokens = 900
        elif provider == "groq":
            max_context_tokens = 6000
        else:
            max_context_tokens = 6000
        if est_tokens(context) <= max_context_tokens:
            return context

        target_chars = max_context_tokens * 4
        head_chars = int(target_chars * 0.7)
        tail_chars = target_chars - head_chars

        # Keep beginning and ending sections, where requirements/summaries often live.
        trimmed = (
            context[:head_chars]
            + "\n\n--- CONTEXT TRIMMED FOR TOKEN LIMIT ---\n\n"
            + context[-tail_chars:]
        )
        return trimmed
    
    async def _generate_test_plan(
        self,
        orchestrator: LLMOrchestrator,
        context: str,
        custom_prompt: Optional[str],
        include_template: bool,
    ) -> LLMResponse:
        """Generate test plan using LLM."""
        prompt = self._build_test_plan_prompt(context, custom_prompt, include_template)

        response = await orchestrator.generate(
            prompt=prompt,
            system_prompt=self._get_test_plan_system_prompt()
        )

        # Quality gate: retry once if the plan is too thin/non-structured.
        if self._is_weak_test_plan(response.content):
            retry_prompt = (
                f"{prompt}\n\n"
                "# QUALITY REQUIREMENTS\n"
                "Regenerate a complete, production-grade test plan.\n"
                "Must include these sections at minimum:\n"
                "1. Introduction\n"
                "2. Scope\n"
                "3. Test Objectives\n"
                "4. Test Strategy/Approach\n"
                "5. Test Scenarios Coverage Matrix\n"
                "6. Entry/Exit Criteria\n"
                "7. Risks and Mitigations\n"
                "8. Assumptions and Dependencies\n"
                "9. Deliverables\n"
                "Do not return only a preface or prompt restatement."
            )
            response = await orchestrator.generate(
                prompt=retry_prompt,
                system_prompt=self._get_test_plan_system_prompt()
            )

        response.content = self._sanitize_generated_content(response.content)
        if self._is_weak_test_plan(response.content):
            response.content = self._build_fallback_test_plan(context, custom_prompt)

        response.content = self._ensure_test_plan_source_reference(response.content, context)

        return response

    def _ensure_test_plan_source_reference(self, content: str, context: str) -> str:
        """Ensure Jira-grounded plans include an explicit Source Reference line."""
        jira_key = self._extract_jira_issue_key(context)
        jira_summary = self._extract_jira_summary(context)

        if not jira_key and not jira_summary:
            return content

        lower_content = (content or "").lower()
        if "source reference" in lower_content and (not jira_key or jira_key.lower() in lower_content):
            return content

        reference_bits = []
        if jira_key:
            reference_bits.append(f"JIRA: {jira_key}")
        if jira_summary:
            reference_bits.append(f"Summary: {jira_summary}")
        reference_line = f"**Source Reference:** {' | '.join(reference_bits)}"

        lines = (content or "").splitlines()
        if not lines:
            return reference_line

        insert_at = 1
        for idx, line in enumerate(lines):
            stripped = line.strip().lower()
            if stripped.startswith("## 1. introduction") or stripped.startswith("## introduction"):
                insert_at = idx + 1
                break

        lines.insert(insert_at, reference_line)
        return "\n".join(lines)

    def _extract_jira_issue_key(self, context: str) -> Optional[str]:
        """Extract Jira issue key from assembled context text."""
        match = re.search(r"##\s*JIRA\s*Issue:\s*([A-Z][A-Z0-9]+-\d+)", context or "")
        return match.group(1) if match else None

    def _extract_jira_summary(self, context: str) -> Optional[str]:
        """Extract Jira summary line from assembled context text."""
        match = re.search(r"\*\*Summary:\*\*\s*(.+)", context or "")
        if not match:
            return None
        summary = (match.group(1) or "").strip()
        return summary[:200] if summary else None
    
    async def _generate_test_cases(
        self,
        orchestrator: LLMOrchestrator,
        context: str,
        custom_prompt: Optional[str],
        include_template: bool,
    ) -> LLMResponse:
        """Generate test cases using LLM."""
        template_hint = self._resolve_test_case_template(include_template)
        bdd_mode = self._is_bdd_requested(custom_prompt, template_hint)
        prompt = self._build_test_case_prompt(context, custom_prompt, include_template)

        response = await orchestrator.generate(
            prompt=prompt,
            system_prompt=self._get_test_case_system_prompt(bdd_mode)
        )

        # Groq quality optimization: for thin or incomplete outputs, switch to
        # sectioned generation by coverage group and merge results.
        if self._is_weak_test_cases(response.content, bdd_mode):
            sectioned = await self._generate_test_cases_sectioned(
                orchestrator=orchestrator,
                context=context,
                custom_prompt=custom_prompt,
                include_template=include_template,
                bdd_mode=bdd_mode,
            )
            if not self._is_weak_test_cases(sectioned.content, bdd_mode):
                response = sectioned

        # If user already clarified missing artifacts are unavailable,
        # do one forced best-effort retry instead of asking same questions again.
        if (
            self._has_user_clarification_response(custom_prompt)
            and self._user_declined_missing_artifacts(custom_prompt)
            and self._looks_like_clarification_only(response.content)
        ):
            forced_prompt = (
                f"{prompt}\n\n"
                "# FINAL DIRECTIVE\n"
                "User has already answered clarifications and confirmed some artifacts are unavailable. "
                "Do NOT ask clarification questions again. "
                "Generate best-effort BDD test cases using available inputs and clearly state assumptions."
            )
            response = await orchestrator.generate(
                prompt=forced_prompt,
                system_prompt=self._get_test_case_system_prompt(bdd_mode)
            )

        # Quality gate: retry once if output is shallow for either BDD or table mode.
        if self._is_weak_test_cases(response.content, bdd_mode):
            quality_requirements = (
                "# QUALITY REQUIREMENTS\n"
                "Regenerate with comprehensive, production-grade coverage.\n"
                "Minimum required:\n"
                "- Cover functional, negative, boundary, edge, permission, and data integrity scenarios\n"
                "- Do not ask clarification questions again; proceed with explicit assumptions when details are missing\n"
            )
            if bdd_mode:
                quality_requirements += (
                    "- 1 Feature with Background\n"
                    "- At least 12 scenarios\n"
                    "- Include tags: @Functional, @Negative, @EdgeCase, @Acceptance, @E2E, @Exploratory\n"
                    "- Include at least 3 Scenario Outline cases with Examples\n"
                    "- Include role/permission and data-integrity coverage\n"
                )
            else:
                quality_requirements += (
                    "- Use markdown tables\n"
                    "- At least 15 test cases total\n"
                    "- Include sections: Functional, Negative, Boundary\n"
                    "- Every row must include Test ID, Description, Preconditions, Steps, Expected Result, Priority\n"
                )

            quality_prompt = f"{prompt}\n\n{quality_requirements}"
            response = await orchestrator.generate(
                prompt=quality_prompt,
                system_prompt=self._get_test_case_system_prompt(bdd_mode)
            )

        # Normalize generated content so the UI doesn't show literal HTML tags.
        response.content = self._sanitize_generated_content(response.content)
        if bdd_mode:
            response.content = self._normalize_bdd_content(response.content)
            response.content = self._repair_truncated_bdd_tail(response.content)
            if self._is_weak_test_cases(response.content, True):
                response.content = self._build_fallback_bdd_test_cases(context, custom_prompt)
                response.content = self._repair_truncated_bdd_tail(response.content)
            response.content = self._ensure_gherkin_fence(response.content)
        else:
            if self._is_weak_test_cases(response.content, False):
                response.content = self._build_fallback_table_test_cases(context, custom_prompt)
        return response

    async def _generate_test_cases_sectioned(
        self,
        orchestrator: LLMOrchestrator,
        context: str,
        custom_prompt: Optional[str],
        include_template: bool,
        bdd_mode: bool,
    ) -> LLMResponse:
        """Generate cases in focused category calls and merge into one output."""
        base_prompt = self._build_test_case_prompt(context, custom_prompt, include_template)
        system_prompt = self._get_test_case_system_prompt(bdd_mode)

        section_instructions = [
            (
                "positive_negative",
                "Generate ONLY Positive and Negative categories. Minimum 8 total scenarios/cases."
            ),
            (
                "edge_boundary",
                "Generate ONLY Edge Case and Boundary categories. Minimum 6 total scenarios/cases, including at least 2 boundary-focused data-driven cases."
            ),
            (
                "security_performance",
                "Generate ONLY Security and Performance categories. Minimum 6 total scenarios/cases. Include authz, XSS/injection, response time, and large dataset behavior."
            ),
        ]

        merged_parts: List[str] = []
        sum_prompt_tokens = 0
        sum_completion_tokens = 0
        sum_total_tokens = 0
        model_name = orchestrator.config.model

        for section_name, section_rule in section_instructions:
            section_prompt = (
                f"{base_prompt}\n\n"
                "# SECTIONED GENERATION MODE\n"
                f"Section: {section_name}\n"
                f"{section_rule}\n"
                "Do not ask clarifying questions. Proceed with explicit assumptions where needed."
            )
            section_resp = await orchestrator.generate(
                prompt=section_prompt,
                system_prompt=system_prompt,
            )
            model_name = section_resp.model or model_name
            sum_prompt_tokens += section_resp.prompt_tokens or 0
            sum_completion_tokens += section_resp.completion_tokens or 0
            sum_total_tokens += section_resp.total_tokens or 0

            content = self._sanitize_generated_content(section_resp.content or "")
            if bdd_mode:
                content = self._repair_truncated_bdd_tail(self._normalize_bdd_content(content))
                content = self._strip_markdown_fence(content)
            merged_parts.append(content)

        merged_content = "\n\n".join([part for part in merged_parts if part.strip()])
        if bdd_mode:
            merged_content = self._ensure_gherkin_fence(merged_content)

        return LLMResponse(
            content=merged_content,
            model=model_name,
            provider=orchestrator.config.provider,
            prompt_tokens=sum_prompt_tokens or None,
            completion_tokens=sum_completion_tokens or None,
            total_tokens=sum_total_tokens or None,
        )

    def _strip_markdown_fence(self, content: str) -> str:
        """Remove surrounding markdown code fences from generated sections."""
        text = (content or "").strip()
        text = re.sub(r'^```[a-zA-Z0-9_-]*\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        return text.strip()
    
    def _build_test_plan_prompt(self, context: str, custom_prompt: Optional[str], include_template: bool = True) -> str:
        """Build test plan generation prompt."""
        template = ""
        if include_template:
            template_path = Path("./templates/test_plan_generation.md")
            template = self._load_valid_template(
                template_path=template_path,
                fallback_template=self._default_test_plan_template(),
                required_markers=["# test plan", "## 1. introduction", "## 2. test objectives"],
            )

        custom_instructions = custom_prompt.strip() if custom_prompt and custom_prompt.strip() else None

        instruction_priority = [
            "# INSTRUCTION PRIORITY (HIGHEST TO LOWEST)",
            "1. CUSTOM INSTRUCTIONS (must be followed exactly when provided)",
            "2. REQUIREMENT CONTEXT (facts and constraints)",
            "3. OUTPUT TEMPLATE (reference only; adapt as needed)",
            "",
            "If any conflict exists, follow CUSTOM INSTRUCTIONS.",
        ]

        source_traceability = [
            "# SOURCE TRACEABILITY (MANDATORY)",
            "- In section 1 (Introduction), include a short 'Source Reference' line.",
            "- If context contains a JIRA issue key, include that key exactly (e.g., SCRUM-5).",
            "- If context contains a summary/title, include it in the Source Reference.",
            "- Do not invent source identifiers not present in context.",
        ]
        
        prompt_parts = [
            "\n".join(instruction_priority),
            "",
            "# MINIMUM OUTPUT QUALITY",
            "- Return a complete, production-grade test plan (not prompt template text).",
            "- Include ALL standard sections: Introduction, Scope, Objectives, Test Items, Test Approach, Environment, Entry/Exit Criteria, Risks, Schedule, Deliverables.",
            "- Test Approach must include a Test Types Matrix covering: Functional Positive, Functional Negative, Boundary, Edge Case, Security, Performance.",
            "- Risk Assessment must include at least 3 specific risks with mitigations.",
            "- Entry/Exit criteria must be measurable and specific.",
            "- If details are missing, state explicit assumptions and proceed.",
            "",
            "\n".join(source_traceability),
            "",
            "# CUSTOM INSTRUCTIONS",
            custom_instructions or "Generate a comprehensive test plan based on the above requirements.",
            "",
            "# REQUIREMENT CONTEXT",
            context,
            "",
            "# OUTPUT TEMPLATE (REFERENCE, NOT MANDATORY)",
            template if include_template else "Template disabled by user selection. Use custom instructions and context only.",
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_test_case_prompt(self, context: str, custom_prompt: Optional[str], include_template: bool = True) -> str:
        """Build test case generation prompt."""
        template = self._resolve_test_case_template(include_template)

        custom_instructions = custom_prompt.strip() if custom_prompt and custom_prompt.strip() else None
        bdd_mode = self._is_bdd_requested(custom_instructions, template)

        instruction_priority = [
            "# INSTRUCTION PRIORITY (HIGHEST TO LOWEST)",
            "1. CUSTOM INSTRUCTIONS (must be followed exactly when provided)",
            "2. REQUIREMENT CONTEXT (facts and constraints)",
            "3. OUTPUT TEMPLATE (reference only; adapt as needed)",
            "",
            "If any conflict exists, follow CUSTOM INSTRUCTIONS.",
        ]
        
        bdd_guidance = [
            "# BDD MODE",
            "Generate Gherkin BDD scenarios only.",
            "Do NOT output markdown tables.",
            "Do NOT use HTML tags such as <br>.",
            "Use plain text with Feature/Scenario/Given/When/Then.",
        ] if bdd_mode else []

        prompt_parts = [
            "\n".join(instruction_priority),
            "",
            "# MINIMUM OUTPUT QUALITY",
            "- Return finished, executable test cases (not prompt template text).",
            "- Cover ALL 6 mandatory categories: Positive, Negative, Edge Case, Boundary Value, Security, Performance.",
            "- Minimum 20 test cases/scenarios total.",
            "- Each test case must have concrete steps and specific expected results.",
            "- If details are missing, state explicit assumptions and proceed.",
            "",
            "# CUSTOM INSTRUCTIONS",
            custom_instructions or "Generate detailed test cases based on the above requirements.",
            "",
            "\n".join(bdd_guidance) if bdd_guidance else "",
            "",
            "# REQUIREMENT CONTEXT",
            context,
            "",
            "# OUTPUT TEMPLATE (REFERENCE, NOT MANDATORY)",
            template if include_template else "Template disabled by user selection. Use custom instructions and context only.",
        ]
        
        return "\n\n".join([part for part in prompt_parts if part.strip()])

    def _resolve_section_prompt(self, section_prompt: Optional[str], legacy_prompt: Optional[str]) -> Optional[str]:
        """Prefer section-specific prompt and fallback to legacy custom prompt."""
        if section_prompt and section_prompt.strip():
            return section_prompt
        if legacy_prompt and legacy_prompt.strip():
            return legacy_prompt
        return None

    def _merge_prompts(self, *prompts: Optional[str]) -> Optional[str]:
        merged = [p.strip() for p in prompts if p and p.strip()]
        if not merged:
            return None
        return "\n\n".join(merged)
    
    def _get_test_plan_system_prompt(self) -> str:
        """Get system prompt for test plan generation."""
        return """You are a Principal Test Architect with 15+ years of experience writing IEEE 829-compliant test plans for enterprise software releases.

INSTRUCTION PRECEDENCE:
- User CUSTOM INSTRUCTIONS are highest priority.
- Follow context facts next.
- Treat any template as guidance, not strict requirements.

MANDATORY OUTPUT STRUCTURE — produce ALL of these sections:
1. Introduction (with Source Reference, Scope In/Out)
2. Test Objectives (primary, secondary, quality goals)
3. Test Items (table: Item ID, Feature, Priority, Description)
4. Test Approach (test levels table + test types matrix covering Functional, Negative, Boundary, Edge, Security, Performance)
5. Test Environment (table: component, details)
6. Entry and Exit Criteria (checklist format with specific, measurable criteria)
7. Risk Assessment (table: Risk ID, Description, Impact, Probability, Mitigation)
8. Test Schedule (table: Phase, Start, End, Owner)
9. Assumptions and Dependencies
10. Deliverables

QUALITY RULES:
- Every section must contain substantive content, not just headers.
- Include at least 3 risks with specific mitigations.
- Entry/exit criteria must be measurable (not vague).
- Test types matrix must cover at minimum: Functional Positive, Functional Negative, Boundary, Edge Case, Security, Performance.
- Use Markdown tables for structured data.
- Be specific to the actual feature described in the requirements — do not produce generic filler.
- If details are missing from the requirements, state explicit assumptions and proceed.

Output in professional Markdown format. Do NOT return prompt templates or placeholder text."""
    
    def _get_test_case_system_prompt(self, bdd_mode: bool = False) -> str:
        """Get system prompt for test case generation."""
        if bdd_mode:
            return """You are a Principal SDET specializing in BDD test automation. Generate comprehensive, automation-ready Gherkin test scenarios.

INSTRUCTION PRECEDENCE:
- User CUSTOM INSTRUCTIONS are highest priority.
- Follow context facts next.
- Treat any template as guidance, not strict requirements.

MANDATORY COVERAGE — generate scenarios for ALL of these categories:
1. POSITIVE / HAPPY PATH (at least 4 scenarios): Standard expected user flows
2. NEGATIVE / ERROR HANDLING (at least 4 scenarios): Invalid inputs, unauthorized access, missing data
3. EDGE CASES (at least 3 scenarios): Empty states, max/min limits, special characters, concurrent access
4. BOUNDARY VALUES (at least 2 scenarios): At limits, just below/above limits (use Scenario Outline with Examples table)
5. SECURITY (at least 2 scenarios): XSS, injection, authorization, session handling
6. PERFORMANCE (at least 2 scenarios): Response time, load behavior, large dataset handling

OUTPUT FORMAT RULES:
- Output Gherkin ONLY: Feature, Background, Scenario, Scenario Outline, Given/When/Then/And
- Use tags: @Positive, @Negative, @EdgeCase, @Boundary, @Security, @Performance, @P0/@P1/@P2
- Include at least 1 Background block with common preconditions
- Include at least 3 Scenario Outline blocks with Examples tables for data-driven coverage
- Keep steps concrete and executable — no vague steps like "verify it works"
- Do NOT output markdown tables
- Do NOT use HTML tags such as <br>
- Target: 20-30 total scenarios minimum

Output in clean plain text Gherkin format."""

        return """You are a Principal SDET with deep expertise in systematic test case design. Generate comprehensive, executable test cases.

INSTRUCTION PRECEDENCE:
- User CUSTOM INSTRUCTIONS are highest priority.
- Follow context facts next.
- Treat any template as guidance, not strict requirements.

MANDATORY COVERAGE — generate test cases for ALL of these categories:
1. FUNCTIONAL POSITIVE (at least 5 cases): Happy path, standard user workflows
2. FUNCTIONAL NEGATIVE (at least 5 cases): Invalid inputs, error handling, unauthorized actions
3. BOUNDARY VALUE (at least 3 cases): Min/max limits, just below/above thresholds
4. EDGE CASES (at least 3 cases): Empty states, special characters, concurrent operations
5. SECURITY (at least 3 cases): XSS, injection, authorization checks, session handling
6. PERFORMANCE (at least 2 cases): Response time, rendering under load, large dataset behavior

OUTPUT FORMAT — use Markdown tables with these columns:
| Test ID | Category | Description | Preconditions | Steps | Expected Result | Priority |

QUALITY RULES:
- Every test case must have concrete, executable steps (not vague descriptions)
- Expected results must be specific and verifiable
- Preconditions must be stated explicitly
- Assign priority: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- Group test cases under category headers (## Functional Positive, ## Negative, etc.)
- Target: 25-35 total test cases minimum
- Do NOT output HTML tags like <br>

Output in professional Markdown format with tables."""

    def _resolve_test_case_template(self, include_template: bool) -> str:
        """Resolve test case template content with safe fallback."""
        if not include_template:
            return ""

        template_path = Path("./templates/test_case_generation.md")
        return self._load_valid_template(
            template_path=template_path,
            fallback_template=self._default_test_case_template(),
            required_markers=["# test cases", "| test id |", "## functional test cases"],
        )

    def _template_indicates_bdd(self, template_text: Optional[str]) -> bool:
        """Detect whether template content strongly indicates BDD/Gherkin output."""
        if not template_text:
            return False
        normalized = template_text.lower()
        bdd_markers = ["bdd", "gherkin", "feature:", "scenario:", "given", "when", "then"]
        return sum(1 for marker in bdd_markers if marker in normalized) >= 3

    def _is_bdd_requested(self, custom_prompt: Optional[str], template_hint: Optional[str] = None) -> bool:
        """Detect whether BDD/Gherkin output should be used.

        Priority:
        1) Explicit user opt-out (non-BDD) wins.
        2) Explicit user BDD request wins.
        3) Otherwise infer from template when template clearly indicates BDD.
        4) Default to BDD-first output for deterministic Gherkin generation.
        """
        normalized = (custom_prompt or "").lower()
        # Respect explicit opt-out phrases first (e.g., "non-BDD", "without gherkin").
        non_bdd_markers = [
            "non-bdd",
            "non bdd",
            "without bdd",
            "not bdd",
            "no bdd",
            "without gherkin",
            "not gherkin",
            "no gherkin",
        ]
        if any(marker in normalized for marker in non_bdd_markers):
            return False

        if any(keyword in normalized for keyword in ["bdd", "gherkin", "given-when-then", "given when then"]):
            return True

        if self._template_indicates_bdd(template_hint):
            return True

        return True

    def _sanitize_generated_content(self, content: str) -> str:
        """Clean common HTML artifacts returned by models in markdown/plain outputs."""
        # Convert HTML break tags to real newlines.
        sanitized = re.sub(r"<\s*br\s*/?\s*>", "\n", content, flags=re.IGNORECASE)
        # Collapse excessive blank lines introduced by normalization.
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
        return sanitized.strip()

    def _extract_clarification_questions(self, content: str) -> List[str]:
        """Detect and extract clarification questions when the model asks for missing info."""
        if not content or len(content.strip()) == 0:
            return []

        lower = content.lower()
        clarification_signals = [
            "before i generate",
            "need a few clarifications",
            "need clarification",
            "please clarify",
            "questions before",
            "missing information",
        ]

        signal_detected = any(signal in lower for signal in clarification_signals)
        if not signal_detected:
            return []

        questions: List[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Remove common list markers.
            line = re.sub(r"^[-*]\s+", "", line)
            line = re.sub(r"^\d+[.)]\s+", "", line)

            if "?" in line:
                q = line
                if not q.endswith("?"):
                    q = q[: q.rfind("?") + 1]
                questions.append(q)

            # Fallback: capture bullet lines in clarification sections even without '?'.
            if not questions and re.match(r"^[-*]\s+", raw_line.strip()):
                candidate = re.sub(r"^[-*]\s+", "", raw_line.strip())
                if len(candidate) > 15:
                    questions.append(candidate)

        # Deduplicate while preserving order.
        unique_questions: List[str] = []
        seen = set()
        for q in questions:
            key = q.lower()
            if key not in seen:
                seen.add(key)
                unique_questions.append(q)

        if unique_questions:
            return unique_questions

        # Last-resort clarification marker if model explicitly asks for clarifications
        # but did not format lines as explicit questions.
        scenario_count = len(re.findall(r'^\s*Scenario:', content, re.MULTILINE | re.IGNORECASE))
        if signal_detected and scenario_count == 0:
            return ["Please provide the missing business/UI details requested by the AI response and regenerate."]

        return []

    def _has_user_clarification_response(self, custom_prompt: Optional[str]) -> bool:
        if not custom_prompt:
            return False
        return "user clarification responses:" in custom_prompt.lower() or "clarification conversation history:" in custom_prompt.lower()

    def _user_declined_missing_artifacts(self, custom_prompt: Optional[str]) -> bool:
        if not custom_prompt:
            return False
        normalized = custom_prompt.lower()
        patterns = [
            "no snapshot",
            "don't have snapshot",
            "do not have snapshot",
            "no ui snapshot",
            "not available",
            "go ahead",
            "proceed directly",
            "generate testcases",
        ]
        return any(p in normalized for p in patterns)

    def _looks_like_clarification_only(self, content: str) -> bool:
        if not content or not content.strip():
            return True
        lower = content.lower()
        signal_phrases = [
            "clarification required",
            "need clarification",
            "please clarify",
            "before i generate",
            "missing information",
        ]
        scenario_count = len(re.findall(r'^\s*Scenario:', content, re.MULTILINE | re.IGNORECASE))
        return any(s in lower for s in signal_phrases) and scenario_count == 0

    def _should_require_clarification(
        self,
        custom_prompt: Optional[str],
        test_plan_content: str,
        test_cases_content: str,
        clarification_questions: List[str],
    ) -> bool:
        """Decide if we should switch UI into clarification flow instead of showing incomplete cases."""
        # Zero-shot mode should return best-effort outputs directly instead of
        # repeatedly blocking on clarification requests.
        if not (custom_prompt and custom_prompt.strip()):
            return False

        if self._has_user_clarification_response(custom_prompt) and self._user_declined_missing_artifacts(custom_prompt):
            if test_cases_content.strip():
                return False

        # Deterministic trigger: if user explicitly asks for clarifying questions
        # before generation, open clarification flow even when model over-eagerly
        # returns full output.
        if self._explicitly_requests_clarification_first(custom_prompt) and not self._has_user_clarification_response(custom_prompt):
            return True

        if clarification_questions:
            return True

        combined = f"{test_plan_content}\n\n{test_cases_content}".lower()
        explicit_signals = [
            "clarification required",
            "need clarification",
            "please clarify",
            "missing information",
            "before i generate",
            "i need",
        ]
        if any(signal in combined for signal in explicit_signals):
            return True

        # If user asked for BDD, at least one scenario should exist.
        bdd_requested = self._is_bdd_requested(custom_prompt)
        scenario_count = len(re.findall(r'^\s*Scenario:', test_cases_content, re.MULTILINE | re.IGNORECASE))
        if bdd_requested and scenario_count == 0:
            return True

        # Guardrail for empty or placeholder testcase output.
        normalized = test_cases_content.strip().lower()
        if normalized in {"", "```", "```gherkin\n```", "```gherkin\n\n```"}:
            return True

        return False

    def _explicitly_requests_clarification_first(self, custom_prompt: Optional[str]) -> bool:
        if not custom_prompt:
            return False
        lower = custom_prompt.lower()
        markers = [
            "ask me those questions",
            "ask questions",
            "before generating",
            "before generate",
            "need feedback",
            "clarification",
        ]
        return ("ask" in lower and "question" in lower and ("before" in lower or "clarification" in lower)) or all(m in lower for m in ["ask", "question", "before generating"]) or any(m in lower for m in markers)
    
    def _default_test_plan_template(self) -> str:
        """Default test plan template."""
        return """# Test Plan

## 1. Introduction
### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions

## 2. Test Objectives

## 3. Test Approach
### 3.1 Test Levels
### 3.2 Test Types

## 4. Test Environment

## 5. Entry and Exit Criteria

## 6. Risk Assessment

## 7. Test Schedule

## 8. Resources

## 9. Deliverables
"""
    
    def _default_test_case_template(self) -> str:
        """Default test case template."""
        return """# Test Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|

## Functional Test Cases

## Negative Test Cases

## Boundary Value Cases
"""
    
    def _count_test_cases(self, content: str) -> int:
        """Count number of test cases in generated content."""
        # BDD/Gherkin heuristic
        scenario_count = self._scenario_count(content)
        if scenario_count > 0:
            return scenario_count

        # Simple heuristic: count rows in markdown tables
        table_rows = re.findall(r'^\|.*\|$', content, re.MULTILINE)
        # Subtract header and separator rows
        return max(0, len(table_rows) - 2)

    def _scenario_count(self, content: str) -> int:
        """Count BDD scenarios including Scenario Outline."""
        return len(
            re.findall(
                r'^\s*(Scenario:|Scenario Outline:)',
                content,
                re.MULTILINE | re.IGNORECASE,
            )
        )

    def _is_weak_test_plan(self, content: str) -> bool:
        """Detect weak/non-actionable test plan output."""
        if not content or len(content.strip()) < 450:
            return True

        lower = content.lower()
        required_markers = [
            'introduction',
            'scope',
            'test objective',
            'entry',
            'exit',
            'risk',
            'deliverable',
        ]
        found = sum(1 for marker in required_markers if marker in lower)
        section_count = len(re.findall(r'^\s*##\s+', content, re.MULTILINE))
        if found < 4 and section_count < 6:
            return True

        if 'original prompt' in lower and 'test strategy' not in lower:
            return True

        return False

    def _is_effectively_empty(self, content: str) -> bool:
        """Detect empty or placeholder-only model output."""
        if not content:
            return True
        normalized = content.strip().lower()
        return normalized in {"", "```", "```markdown\n```", "```gherkin\n```", "```gherkin\n\n```"}

    def _is_weak_test_cases(self, content: str, bdd_mode: bool) -> bool:
        """Detect shallow testcase outputs for both BDD and table modes."""
        if self._is_effectively_empty(content):
            return True

        if bdd_mode:
            if self._has_truncated_bdd_tail(content):
                return True
            return self._scenario_count(content) < 12

        # Table mode: require reasonable row coverage.
        table_rows = re.findall(r'^\|.*\|$', content, re.MULTILINE)
        data_rows = max(0, len(table_rows) - 2)
        if data_rows < 8:
            return True

        lower = content.lower()
        if "test suite" in lower and "|" not in content:
            return True

        return False

    def _load_valid_template(self, template_path: Path, fallback_template: str, required_markers: List[str]) -> str:
        """Load template if it looks like an output template; otherwise return fallback."""
        if not template_path.exists():
            return fallback_template

        try:
            raw = template_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Windows environments may default to cp1252 and fail on mixed/legacy files.
            # Fallback to a permissive decode so generation does not crash on template read.
            raw = template_path.read_text(encoding="latin-1", errors="replace")
        lower = raw.lower()

        # Reject prompt-library/article content accidentally used as generation template.
        # Exception: test_case template may intentionally be a BDD prompt library.
        template_name = template_path.name.lower()
        allow_bdd_prompt_library = template_name == "test_case_generation.md" and self._template_indicates_bdd(raw)
        invalid_markers = [
            "author:",
            "website:",
            "linkedin:",
            "chapter:",
            "template 1:",
            "purpose:",
            "role:",
            "[paste requirements",
            "rice pot",
        ]
        if not allow_bdd_prompt_library and any(marker in lower for marker in invalid_markers):
            return fallback_template

        if allow_bdd_prompt_library:
            return raw

        if not all(marker in lower for marker in required_markers):
            return fallback_template

        return raw

    def _normalize_bdd_content(self, content: str) -> str:
        """Normalize loose BDD text into consistently readable Gherkin blocks."""
        text = content

        # Convert custom tags seen in model outputs into standard Gherkin headings.
        text = re.sub(r'@\s*(Functional|Negative|Edge\s*Case)\s*Scenario\s*:\s*', 'Scenario: ', text, flags=re.IGNORECASE)

        # Ensure each BDD keyword starts on its own line for readability.
        text = re.sub(r'\s+(Feature:)\s*', '\n\n\\1 ', text)
        text = re.sub(r'\s+(Scenario:)\s*', '\n\n\\1 ', text)
        text = re.sub(r'\s+(Given|When|Then|And|But)\s+', '\n  \\1 ', text)

        # Clean duplicated whitespace/newlines caused by normalization.
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)

        return text.strip()

    def _has_truncated_bdd_tail(self, content: str) -> bool:
        """Detect obviously truncated trailing BDD steps like 'Given I'."""
        text = re.sub(r'^```(?:gherkin)?\s*\n?', '', content.strip(), flags=re.IGNORECASE)
        text = re.sub(r'\n```\s*$', '', text)
        lines = text.splitlines()
        non_empty = [ln.strip() for ln in lines if ln.strip()]
        if not non_empty:
            return True

        last = non_empty[-1]
        if re.match(r'^(Given|When|Then|And|But)\s*$', last, re.IGNORECASE):
            return True

        if re.match(
            r'^(Given|When|Then|And|But)\s+(i|the|a|an|to|with|on|in|at|my|our|user|admin)\s*$',
            last,
            re.IGNORECASE,
        ):
            return True

        return False

    def _repair_truncated_bdd_tail(self, content: str) -> str:
        """Drop the trailing broken scenario block if model output was cut mid-step."""
        text = re.sub(r'^```(?:gherkin)?\s*\n?', '', content.strip(), flags=re.IGNORECASE)
        text = re.sub(r'\n```\s*$', '', text)
        lines = text.splitlines()
        if not lines:
            return content.strip()

        scenario_indices = [
            idx for idx, line in enumerate(lines)
            if re.match(r'^\s*Scenario(?: Outline)?:', line, re.IGNORECASE)
        ]
        if not scenario_indices:
            return text.strip()

        # Work only on the last scenario block.
        last_scenario_idx = scenario_indices[-1]
        block = [ln for ln in lines[last_scenario_idx:] if ln.strip()]
        if not block:
            return text.strip()

        step_lines = [
            ln for ln in block
            if re.match(r'^\s*(Given|When|Then|And|But)\b', ln, re.IGNORECASE)
        ]
        has_then = any(re.match(r'^\s*Then\b', ln, re.IGNORECASE) for ln in step_lines)
        last_non_empty = block[-1].strip()

        broken_tail = self._has_truncated_bdd_tail("\n".join(block))
        insufficient_steps = len(step_lines) < 3 or not has_then

        if broken_tail or insufficient_steps or re.match(r'^Scenario(?: Outline)?:\s*$', last_non_empty, re.IGNORECASE):
            repaired = "\n".join(lines[:last_scenario_idx]).rstrip()
            return repaired

        return text.strip()

    def _ensure_gherkin_fence(self, content: str) -> str:
        """Wrap BDD content in a fenced code block so markdown preserves line breaks."""
        stripped = content.strip()
        if stripped.startswith("```"):
            return stripped
        return f"```gherkin\n{stripped}\n```"

    def _feature_focus(self, custom_prompt: Optional[str], context: str) -> str:
        """Infer a neutral feature focus phrase from prompt/context."""
        candidate = (custom_prompt or "").strip()
        if not candidate:
            candidate = (context or "").strip()
        if not candidate:
            return "Target Feature"

        # Collapse multiline prompt and keep a readable short title.
        candidate = re.sub(r"\s+", " ", candidate)
        return candidate[:80].strip(" .:-") or "Target Feature"

    def _default_clarification_questions(self, prompt_hint: Optional[str]) -> List[str]:
        """Return neutral clarification questions (no stale domain hardcoding)."""
        focus = self._feature_focus(prompt_hint, "")
        return [
            f"For '{focus}', what are the mandatory input fields and validation rules?",
            "What are the expected success outcomes and key error conditions?",
            "Are there role/permission constraints that should be validated?",
            "Which boundary and negative scenarios are highest priority?",
            "Do you have any API/UI constraints or examples to anchor expected results?",
        ]

    def _build_fallback_bdd_test_cases(self, context: str, custom_prompt: Optional[str]) -> str:
        """Produce a deterministic baseline BDD suite when model output is empty."""
        feature_name = self._feature_focus(custom_prompt, context)
        domain_hint = "the requested behavior works correctly with functional, negative, and edge validations"

        return f"""@Functional
Feature: {feature_name}
    As a product user
    I want the requested behavior to work reliably
    So that {domain_hint}

    Background:
        Given the system is available
        And the user has required access rights

    @Functional @Acceptance
    Scenario: Complete primary workflow with valid input
        Given valid data is prepared
        When the user performs the primary action
        Then the operation succeeds
        And the expected output is visible

    @Functional @Acceptance
    Scenario: Complete secondary workflow with valid input
        Given valid data is prepared
        When the user performs a related action
        Then the system processes it successfully
        And data remains consistent

    @Negative
    Scenario: Reject request with missing required fields
        Given a required field is not provided
        When the user submits the request
        Then the system blocks submission
        And shows a clear validation error

    @Negative
    Scenario: Reject malformed or invalid input
        Given input violates validation rules
        When the user submits the action
        Then the system rejects the request
        And returns a meaningful error response

    @EdgeCase
    Scenario Outline: Validate boundary values
        Given the user is entering boundary data
        When value <value> is submitted
        Then the system returns <result>

        Examples:
            | value | result            |
            | 0     | validation error  |
            | 1     | accepted          |
            | 9999  | accepted or capped |

    @E2E
    Scenario: End-to-end flow succeeds
        Given prerequisites are completed
        When the user executes the full flow
        Then all expected stages complete successfully
        And results are recorded for auditability

    @E2E
    Scenario: End-to-end flow handles failure safely
        Given a recoverable failure condition occurs
        When the flow is executed
        Then the system reports failure clearly
        And preserves data integrity

    @Functional
    Scenario: Update existing entity successfully
        Given an existing entity is present
        When the user edits and saves changes
        Then updates are persisted
        And subsequent reads return updated data

    @Functional
    Scenario: Disable feature-specific entity
        Given an active entity exists
        When the user disables it
        Then status changes to disabled
        And dependent actions no longer execute

    @Exploratory
    Scenario: Verify behavior with concurrent updates
        Given two users open the same entity
        When both attempt updates concurrently
        Then conflict handling prevents silent overwrite
        And the user sees clear resolution guidance

    @Negative
    Scenario: Unauthorized user attempts restricted action
        Given a user without required permission is logged in
        When the user tries a restricted operation
        Then access is denied
        And the action is logged as unauthorized

    @Functional
    Scenario: View operation history and status
        Given actions have been executed previously
        When the user opens history
        Then status, timestamps, and key metrics are visible
"""

    def _build_fallback_table_test_cases(self, context: str, custom_prompt: Optional[str]) -> str:
        """Produce deterministic markdown testcases for non-BDD mode."""
        focus = self._feature_focus(custom_prompt, context)
        return f"""# Test Cases - {focus}

## Functional Test Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
| TC-F-001 | Execute primary workflow with valid data | User has required access | Enter valid input and submit primary action | Operation succeeds and output is shown | High |
| TC-F-002 | Execute secondary workflow with valid data | User has required access | Trigger related action with valid input | Operation succeeds with correct state update | High |
| TC-F-003 | Update existing entity | Existing entity present | Open entity, edit fields, save | Changes persist and are visible on reload | High |
| TC-F-004 | Disable active entity | Existing active entity present | Disable entity and save | Status becomes disabled and behavior reflects disabled state | Medium |
| TC-F-005 | View entity details | Existing entity present | Open details page/view | Configured values are displayed accurately | Medium |

## Negative Test Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
| TC-N-001 | Submit with missing mandatory fields | User has required access | Leave required fields empty and submit | Validation errors are shown and action is blocked | High |
| TC-N-002 | Submit invalid value format | User has required access | Enter malformed value and submit | Validation error shown; action blocked | High |
| TC-N-003 | Unauthorized user attempts modification | User lacks required role | Attempt create/edit action | Access denied and action not persisted | High |
| TC-N-004 | Backend returns processing error | Service endpoint available | Trigger known invalid request | User sees clear error and no partial save | Medium |

## Boundary and Edge Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
| TC-B-001 | Minimum boundary accepted | User has required access | Submit minimum allowed value | Request accepted and saved | Medium |
| TC-B-002 | Maximum boundary accepted | User has required access | Submit maximum allowed value | Request accepted and saved | Medium |
| TC-B-003 | Below-minimum boundary rejected | User has required access | Submit value below minimum | Validation error shown | High |
| TC-B-004 | Above-maximum boundary rejected | User has required access | Submit value above maximum | Validation error shown | High |
| TC-E-001 | Concurrent updates conflict handling | Two users editing same entity | Save conflicting updates from both users | Conflict handled; no silent overwrite | Medium |
| TC-E-002 | Empty-result execution path | Valid setup with no matching data | Execute operation with no matching records | Operation completes safely with no data corruption | Medium |
"""

    def _build_fallback_test_plan(self, context: str, custom_prompt: Optional[str]) -> str:
        """Produce deterministic complete test plan when model output is weak."""
        focus = self._feature_focus(custom_prompt, context)
        source = f"{custom_prompt or ''}\n{context or ''}".lower()

        scope_items = [
            "Functional behavior and core workflow validation",
            "Negative scenarios and failure-path handling",
            "Boundary and edge behavior under abnormal inputs",
        ]
        objective_items = [
            "Verify expected workflow execution and outcomes",
            "Verify robust error handling with meaningful failure signals",
            "Verify data integrity and operational reliability",
        ]
        risk_rows = [
            ("Missing explicit business rules", "Use conservative assumptions and flag clarifications"),
            ("Incomplete validation details", "Add exploratory and boundary-oriented test design"),
        ]

        if "jenkins" in source:
            scope_items.append("Jenkins pipeline stage orchestration and node/pod provisioning behavior")
            objective_items.append("Confirm Jenkins pipeline failure path captures actionable diagnostics")
            risk_rows.append(("Jenkins agent/environment drift", "Pin agent image/tool versions and verify startup checks"))
        if "gitlab" in source:
            scope_items.append("GitLab repository access, checkout, and credential usage flows")
            objective_items.append("Validate secure GitLab token handling and repository fetch behavior")
            risk_rows.append(("GitLab credential/token issues", "Add auth-failure and token-rotation regression tests"))
        if "stringindexoutofboundsexception" in source or "stringindexoutofbounds" in source:
            scope_items.append("Runtime exception handling for string parsing and empty-value edge cases")
            objective_items.append("Prevent StringIndexOutOfBoundsException via defensive input validation")
            risk_rows.append(("Unhandled string parsing exceptions", "Add null/empty/malformed input checks before substring operations"))

        scope_text = "\n".join(f"- {item}" for item in scope_items)
        objective_text = "\n".join(f"- {item}" for item in objective_items)
        risk_text = "\n".join(f"| {risk} | {mitigation} |" for risk, mitigation in risk_rows)

        return f"""# Test Plan - {focus}

## 1. Introduction
This test plan validates the requested behavior for **{focus}** using provided context and explicit assumptions where details are missing.

## 2. Scope
### In Scope
{scope_text}

### Out of Scope
- Undocumented features and external systems not referenced in provided inputs.

## 3. Test Objectives
{objective_text}

## 4. Test Strategy and Approach
- Functional testing for expected flows
- Negative testing for failure modes and invalid inputs
- Boundary and edge testing for limits and malformed values
- Regression testing for previously failed areas

## 5. Coverage Matrix
| Area | Coverage Type |
|------|---------------|
| Core workflow | Functional, E2E |
| Error handling | Negative, Failure-mode |
| Input robustness | Boundary, Edge |
| Reliability | Regression |

## 6. Entry and Exit Criteria
### Entry Criteria
- Requirements context is available.
- Test environment and required integrations are reachable.

### Exit Criteria
- Critical defects are resolved or explicitly accepted.
- Core, negative, and boundary scenarios are executed.

## 7. Risks and Mitigations
| Risk | Mitigation |
|------|------------|
{risk_text}

## 8. Assumptions and Dependencies
- Missing implementation details are interpreted conservatively and flagged for clarification.
- Integration endpoints and credentials are available in test environment.

## 9. Deliverables
- Test plan document
- Detailed test cases (functional, negative, boundary, edge)
- Execution summary with defects and recommendations
"""
