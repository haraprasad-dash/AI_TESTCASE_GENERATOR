"""
Generation Service - Orchestrates test plan and test case generation.
"""
import uuid
import time
import re
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
            # Step 1: Assemble context
            if websocket_callback:
                await websocket_callback({"step": "assembling", "percent": 10})
            
            context = await self._assemble_context(inputs)
            sources = self._identify_sources(inputs)

            # Keep prompts within provider limits (especially Groq TPM limits).
            context = self._apply_context_budget(context, config.provider, config.model or "")
            
            if not context.strip():
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
            
            test_plan = await self._generate_test_plan(orchestrator, context, inputs.custom_prompt)
            
            # Step 4: Generate test cases
            if websocket_callback:
                await websocket_callback({"step": "generating_cases", "percent": 60})
            
            test_cases = await self._generate_test_cases(orchestrator, context, inputs.custom_prompt)

            combined_output = f"{test_plan.content}\n\n{test_cases.content}"
            clarification_questions = self._extract_clarification_questions(combined_output)
            clarification_required = self._should_require_clarification(
                inputs.custom_prompt,
                test_plan.content,
                test_cases.content,
                clarification_questions,
            )
            if clarification_required and not clarification_questions:
                clarification_questions = [
                    "What exact purge rule fields are mandatory on the configuration screen?",
                    "What are valid ranges/formats for retention and schedule inputs?",
                    "What are role/permission rules for create/edit/execute purge actions?",
                    "What confirmations, warnings, or audit/logging behaviors are expected?",
                    "Which negative and boundary behaviors from the snapshots must be prioritized?",
                ]
            
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
                    bdd_mode = self._is_bdd_requested(inputs.custom_prompt)
                    fallback_plan = self._build_fallback_test_plan(context, inputs.custom_prompt)
                    if bdd_mode:
                        fallback_cases = self._ensure_gherkin_fence(
                            self._build_fallback_bdd_test_cases(context, inputs.custom_prompt)
                        )
                    else:
                        fallback_cases = self._build_fallback_table_test_cases(context, inputs.custom_prompt)

                    clarification_required = self._explicitly_requests_clarification_first(inputs.custom_prompt)
                    clarification_questions = [
                        "What exact purge rule fields are mandatory on the configuration screen?",
                        "What are valid ranges/formats for retention and schedule inputs?",
                        "What are role/permission rules for create/edit/execute purge actions?",
                        "What confirmations, warnings, or audit/logging behaviors are expected?",
                        "Which negative and boundary behaviors from the snapshots must be prioritized?",
                    ] if clarification_required else []

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
                    retry_specs: List[Dict[str, Any]] = []

                    # 1) Retry same model with smaller completion budget if remaining quota is low.
                    remaining = self._extract_remaining_groq_tokens(str(e))
                    if remaining and remaining >= 280:
                        retry_specs.append({
                            "provider": "groq",
                            "model": config.model or "llama-3.3-70b-versatile",
                            "max_tokens": max(256, min(remaining - 120, 900)),
                        })

                    # 2) Retry alternate Groq models that may have different limits/availability.
                    for fallback_model in [
                        "llama-3.3-70b-versatile",
                        "llama-3.1-70b-versatile",
                        "mixtral-8x7b-32768",
                    ]:
                        if fallback_model != (config.model or ""):
                            retry_specs.append({
                                "provider": "groq",
                                "model": fallback_model,
                                "max_tokens": 700,
                            })

                    # 3) Last resort: local Ollama fallback if available.
                    retry_specs.append({
                        "provider": "ollama",
                        "model": settings.ollama_default_model,
                        "max_tokens": 700,
                    })

                    for spec in retry_specs:
                        try:
                            fallback_orchestrator = create_orchestrator(
                                provider=spec["provider"],
                                model=spec["model"],
                                temperature=config.temperature,
                                api_key=settings.groq_api_key if spec["provider"] == "groq" else None,
                                base_url=settings.ollama_base_url if spec["provider"] == "ollama" else None,
                            )
                            fallback_orchestrator.config.max_tokens = spec["max_tokens"]

                            test_plan = await self._generate_test_plan(fallback_orchestrator, context, inputs.custom_prompt)
                            test_cases = await self._generate_test_cases(fallback_orchestrator, context, inputs.custom_prompt)

                            combined_output = f"{test_plan.content}\n\n{test_cases.content}"
                            clarification_questions = self._extract_clarification_questions(combined_output)
                            clarification_required = self._should_require_clarification(
                                inputs.custom_prompt,
                                test_plan.content,
                                test_cases.content,
                                clarification_questions,
                            )
                            if clarification_required and not clarification_questions:
                                clarification_questions = [
                                    "What exact purge rule fields are mandatory on the configuration screen?",
                                    "What are valid ranges/formats for retention and schedule inputs?",
                                    "What are role/permission rules for create/edit/execute purge actions?",
                                    "What confirmations, warnings, or audit/logging behaviors are expected?",
                                    "Which negative and boundary behaviors from the snapshots must be prioritized?",
                                ]
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
        
        # Fetch JIRA content
        if inputs.jira_id and settings.jira_base_url:
            try:
                jira_config = type('Config', (), {
                    'base_url': settings.jira_base_url,
                    'username': settings.jira_username,
                    'api_token': settings.jira_api_token
                })()
                issue_data = await fetch_jira_issue(inputs.jira_id, jira_config)
                context_parts.append(self._format_jira_context(issue_data))
            except JiraClientError as e:
                context_parts.append(f"<!-- JIRA fetch failed: {e} -->")
        
        # Fetch ValueEdge content
        if inputs.valueedge_id and settings.valueedge_base_url:
            try:
                ve_config = type('Config', (), {
                    'base_url': settings.valueedge_base_url,
                    'client_id': settings.valueedge_client_id,
                    'client_secret': settings.valueedge_client_secret,
                    'shared_space_id': settings.valueedge_shared_space_id
                })()
                item_data = await fetch_valueedge_item(inputs.valueedge_id, ve_config)
                context_parts.append(self._format_valueedge_context(item_data))
            except ValueEdgeClientError as e:
                context_parts.append(f"<!-- ValueEdge fetch failed: {e} -->")
        
        # Add file content
        for file in inputs.files:
            if file.extracted_text:
                context_parts.append(self._format_file_context(file))
        
        return "\n\n---\n\n".join(context_parts)
    
    def _identify_sources(self, inputs: GenerationInputs) -> List[str]:
        """Identify which sources were used."""
        sources = []
        if inputs.jira_id:
            sources.append("jira")
        if inputs.valueedge_id:
            sources.append("valueedge")
        if inputs.files:
            sources.append("files")
        return sources
    
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
        """Clamp completion tokens to provider-safe defaults."""
        requested = max(256, requested or 1024)

        if provider == "groq":
            # Keep completion budget conservative to avoid 413 TPM failures.
            # Model-specific override for GPT-OSS models shown to have tight TPM in this app.
            if "gpt-oss" in (model or ""):
                return min(requested, 450)
            return min(requested, 1200)

        # Ollama local models can become very slow on large completions.
        return min(requested, 1400)

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
        return raw_error

    def _apply_context_budget(self, context: str, provider: str, model: str = "") -> str:
        """Trim oversized context so prompt + completion stays inside provider limits."""
        if not context:
            return context

        # Rough estimate: ~4 chars per token for English-heavy text.
        def est_tokens(text: str) -> int:
            return max(1, len(text) // 4)

        # Groq TPM errors observed around 8k; reserve room for template/system/output.
        if provider == "groq" and "gpt-oss" in (model or ""):
            max_context_tokens = 900
        else:
            max_context_tokens = 2200 if provider == "groq" else 3000
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
        custom_prompt: Optional[str]
    ) -> LLMResponse:
        """Generate test plan using LLM."""
        prompt = self._build_test_plan_prompt(context, custom_prompt)

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

        return response
    
    async def _generate_test_cases(
        self,
        orchestrator: LLMOrchestrator,
        context: str,
        custom_prompt: Optional[str]
    ) -> LLMResponse:
        """Generate test cases using LLM."""
        bdd_mode = self._is_bdd_requested(custom_prompt)
        prompt = self._build_test_case_prompt(context, custom_prompt)

        response = await orchestrator.generate(
            prompt=prompt,
            system_prompt=self._get_test_case_system_prompt(bdd_mode)
        )

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
    
    def _build_test_plan_prompt(self, context: str, custom_prompt: Optional[str]) -> str:
        """Build test plan generation prompt."""
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
        
        prompt_parts = [
            "\n".join(instruction_priority),
            "",
            "# MINIMUM OUTPUT QUALITY",
            "- Return a complete test plan (not prompt template text).",
            "- Include clear sections, risks, entry/exit criteria, and coverage matrix.",
            "- If details are missing, proceed with explicit assumptions.",
            "",
            "# CUSTOM INSTRUCTIONS",
            custom_instructions or "Generate a comprehensive test plan based on the above requirements.",
            "",
            "# REQUIREMENT CONTEXT",
            context,
            "",
            "# OUTPUT TEMPLATE (REFERENCE, NOT MANDATORY)",
            template,
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_test_case_prompt(self, context: str, custom_prompt: Optional[str]) -> str:
        """Build test case generation prompt."""
        template_path = Path("./templates/test_case_generation.md")
        template = self._load_valid_template(
            template_path=template_path,
            fallback_template=self._default_test_case_template(),
            required_markers=["# test cases", "| test id |", "## functional test cases"],
        )

        custom_instructions = custom_prompt.strip() if custom_prompt and custom_prompt.strip() else None
        bdd_mode = self._is_bdd_requested(custom_instructions)

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
            "- Return finished test cases (not prompt template text).",
            "- Cover functional, negative, boundary, and edge scenarios.",
            "- If details are missing, proceed with explicit assumptions.",
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
            template,
        ]
        
        return "\n\n".join([part for part in prompt_parts if part.strip()])
    
    def _get_test_plan_system_prompt(self) -> str:
        """Get system prompt for test plan generation."""
        return """You are an expert Test Architect. Create a comprehensive Test Plan based on the provided requirements.

Instruction precedence:
- User CUSTOM INSTRUCTIONS are highest priority.
- Follow context facts next.
- Treat any template as guidance, not strict requirements.

Follow these principles:
1. Analyze requirements thoroughly before writing
2. Use IEEE 829 standard structure
3. Define clear test objectives and scope
4. Include risk assessment and mitigation
5. Specify entry and exit criteria
6. Define test environment requirements

Output in professional Markdown format."""
    
    def _get_test_case_system_prompt(self, bdd_mode: bool = False) -> str:
        """Get system prompt for test case generation."""
        if bdd_mode:
            return """You are an expert Test Engineer. Create detailed BDD test cases based on the provided requirements.

Instruction precedence:
- User CUSTOM INSTRUCTIONS are highest priority.
- Follow context facts next.
- Treat any template as guidance, not strict requirements.

Follow these principles:
1. Output Gherkin only: Feature, Scenario, Given, When, Then (And optional)
2. Include positive, negative, boundary, and edge scenarios where relevant
3. Keep steps concrete and executable
4. Do not output markdown tables
5. Do not output HTML tags like <br>

Output in clean plain text Gherkin format."""

        return """You are an expert Test Engineer. Create detailed Test Cases based on the provided requirements.

Instruction precedence:
- User CUSTOM INSTRUCTIONS are highest priority.
- Follow context facts next.
- Treat any template as guidance, not strict requirements.

Follow these principles:
1. Include positive (happy path) test cases
2. Include negative (error handling) test cases
3. Add boundary value analysis cases
4. Include edge cases and corner cases
5. Use Given-When-Then format where applicable
6. Define clear preconditions and expected results
7. Assign priority (High/Medium/Low) to each case
8. Do not output HTML tags like <br>

Output in professional Markdown format with tables."""

    def _is_bdd_requested(self, custom_prompt: Optional[str]) -> bool:
        """Detect whether the user explicitly requested BDD/Gherkin output."""
        if not custom_prompt:
            return False
        normalized = custom_prompt.lower()
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

        return any(keyword in normalized for keyword in ["bdd", "gherkin", "given-when-then", "given when then"])

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
        if not content or len(content.strip()) < 800:
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
        if found < 5:
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
            return self._scenario_count(content) < 8

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

        raw = template_path.read_text()
        lower = raw.lower()

        # Reject prompt-library/article content accidentally used as generation template.
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
        if any(marker in lower for marker in invalid_markers):
            return fallback_template

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

    def _build_fallback_bdd_test_cases(self, context: str, custom_prompt: Optional[str]) -> str:
        """Produce a deterministic baseline BDD suite when model output is empty."""
        feature_name = "Purge Rule Management in Agent Portal"
        domain_hint = "records are purged according to configured retention rules"

        if "purge" not in (context or "").lower() and "purge" not in (custom_prompt or "").lower():
            feature_name = "Configuration Workflow in Agent Portal"
            domain_hint = "configuration changes are validated and applied safely"

        return f"""@Functional
Feature: {feature_name}
    As a configuration administrator
    I want to create, edit, and execute configuration safely
    So that {domain_hint}

    Background:
        Given I am authenticated in the agent portal
        And I have permission to manage purge configurations

    @Functional @Acceptance
    Scenario: Create soft purge rule with valid values
        Given I am on the purge rule configuration page
        When I create a soft purge rule with valid retention inputs
        Then the rule is saved successfully
        And the rule is listed as active

    @Functional @Acceptance
    Scenario: Create hard purge rule with valid values
        Given I am on the purge rule configuration page
        When I create a hard purge rule with valid retention inputs
        Then the rule is saved successfully
        And the rule is listed as active

    @Negative
    Scenario: Reject rule creation with missing mandatory fields
        Given I am on the purge rule configuration page
        When I submit a rule with required fields missing
        Then I see validation errors for each missing field
        And the rule is not created

    @Negative
    Scenario: Reject negative retention values
        Given I am creating a purge rule
        When I enter negative retention values
        Then the system blocks save
        And shows a validation message

    @EdgeCase
    Scenario Outline: Validate retention boundary values
        Given I am creating a purge rule
        When I enter retention value <value>
        Then the system returns <result>

        Examples:
            | value | result            |
            | 0     | validation error  |
            | 1     | accepted          |
            | 9999  | accepted or capped|

    @E2E
    Scenario: Execute scheduled soft purge run
        Given an active soft purge rule exists
        When the scheduled time is reached
        Then eligible records are soft purged
        And a run entry is recorded in audit logs

    @E2E
    Scenario: Execute scheduled hard purge run
        Given an active hard purge rule exists
        When the scheduled time is reached
        Then eligible records are hard purged
        And a run entry is recorded in audit logs

    @Functional
    Scenario: Edit existing purge rule
        Given an active purge rule exists
        When I update retention configuration and save
        Then the updated rule is persisted
        And future runs use updated values

    @Functional
    Scenario: Disable purge rule
        Given an active purge rule exists
        When I disable the rule
        Then the rule status becomes disabled
        And scheduled runs do not execute for that rule

    @Exploratory
    Scenario: Verify behavior with concurrent rule updates
        Given two admins open the same purge rule
        When both attempt updates concurrently
        Then conflict handling prevents silent overwrite
        And the user sees clear resolution guidance

    @Negative
    Scenario: Unauthorized user attempts purge rule changes
        Given a user without required permission is logged in
        When the user tries to create or edit purge rules
        Then access is denied
        And the action is logged as unauthorized

    @Functional
    Scenario: View purge execution history and status
        Given purge runs have executed
        When I open purge history
        Then I see run status, timestamp, and impacted record counts
"""

    def _build_fallback_table_test_cases(self, context: str, custom_prompt: Optional[str]) -> str:
        """Produce deterministic markdown testcases for non-BDD mode."""
        return """# Test Cases

## Functional Test Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
| TC-F-001 | Create soft purge rule with valid data | User has config access | Open purge config, enter valid soft purge values, save | Rule is created and shown active | High |
| TC-F-002 | Create hard purge rule with valid data | User has config access | Open purge config, enter valid hard purge values, save | Rule is created and shown active | High |
| TC-F-003 | Edit existing purge rule | Existing purge rule present | Open rule, update retention values, save | Updated values are persisted | High |
| TC-F-004 | Disable purge rule | Existing active rule present | Open rule, disable, save | Rule status changes to disabled | Medium |
| TC-F-005 | View purge rule details | Existing rule present | Open rule details page | All configured values are displayed correctly | Medium |

## Negative Test Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
| TC-N-001 | Submit rule with missing mandatory fields | User has config access | Leave required fields empty and save | Validation errors are shown; save blocked | High |
| TC-N-002 | Submit negative retention values | User has config access | Enter negative value and save | Validation error shown; save blocked | High |
| TC-N-003 | Unauthorized user modifies purge rule | User lacks required role | Attempt create/edit action | Access denied and action not persisted | High |
| TC-N-004 | Invalid schedule format | User has config access | Enter invalid schedule/time format and save | Validation error shown | Medium |

## Boundary and Edge Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
| TC-B-001 | Retention minimum boundary | User has config access | Enter minimum allowed retention value and save | Rule saved successfully | Medium |
| TC-B-002 | Retention maximum boundary | User has config access | Enter maximum allowed retention value and save | Rule saved successfully | Medium |
| TC-B-003 | Retention below minimum | User has config access | Enter value below minimum and save | Validation error shown | High |
| TC-B-004 | Retention above maximum | User has config access | Enter value above maximum and save | Validation error shown | High |
| TC-E-001 | Concurrent edits to same rule | Two users editing same rule | Save conflicting updates from both users | Conflict handled; no silent overwrite | Medium |
| TC-E-002 | Scheduled purge run with no eligible records | Active rule exists | Trigger scheduled run with no matching records | Run completes safely with zero affected count | Medium |
"""

    def _build_fallback_test_plan(self, context: str, custom_prompt: Optional[str]) -> str:
        """Produce deterministic complete test plan when model output is weak."""
        return """# Test Plan

## 1. Introduction
This test plan covers validation of the target feature using available requirement context and explicit assumptions where details are missing.

## 2. Scope
- In scope: functional behavior, validation rules, negative scenarios, boundary handling, and execution outcomes.
- Out of scope: undocumented features and external systems not present in provided inputs.

## 3. Test Objectives
- Verify correctness of core feature behavior.
- Verify error handling and validation controls.
- Verify data integrity and permission constraints.

## 4. Test Strategy and Approach
- Functional testing for expected workflows.
- Negative testing for invalid inputs and unauthorized actions.
- Boundary and edge testing for limits and concurrency.
- Regression checks on key flows after updates.

## 5. Coverage Matrix
| Area | Coverage Type |
|------|---------------|
| Core workflow | Functional, E2E |
| Validation | Negative, Boundary |
| Authorization | Negative, Security |
| Data consistency | Edge, Regression |

## 6. Entry and Exit Criteria
### Entry Criteria
- Requirements context available.
- Test environment reachable.

### Exit Criteria
- Critical defects resolved or accepted with mitigation.
- Core, negative, and boundary tests executed.

## 7. Risks and Mitigations
| Risk | Mitigation |
|------|------------|
| Missing detailed UI specs | Proceed with assumptions and mark unclear areas |
| Incomplete validation rules | Add exploratory and boundary tests |
| Authorization ambiguity | Add permission-focused negative tests |

## 8. Assumptions and Dependencies
- Missing UI specifics are interpreted using standard configuration patterns.
- Unspecified ranges are validated with conservative boundaries.

## 9. Deliverables
- Test plan document
- Detailed test cases
- Execution summary and defect report
"""
