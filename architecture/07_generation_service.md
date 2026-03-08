# SOP 07: Generation Service

## Goal
Orchestrate the generation of test plans and test cases from multiple input sources.

## Layer
Layer 3: Tools (`backend/app/services/generation_service.py`)

## Process Flow

```
1. Collect Inputs (JIRA, ValueEdge, Files)
         |
         v
2. Fetch/Extract Content from all sources
         |
         v
3. Assemble Context (consolidate all content)
         |
         v
4. Load Templates (test plan + test case)
         |
         v
5. Build Prompts (inject context into templates)
         |
         v
6. Send to LLM for Generation
         |
         v
7. Parse and Format Output
         |
         v
8. Return Response
```

## Implementation

### Generation Service (`services/generation_service.py`)

```python
"""
Generation Service - Orchestrates test plan and test case generation.
"""
import uuid
import time
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
from app.services.template_engine import TemplateEngine


class GenerationError(Exception):
    """Base exception for generation errors."""
    pass


class ContextAssemblyError(GenerationError):
    """Failed to assemble context from inputs."""
    pass


class GenerationService:
    """Service for generating test plans and test cases."""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
    
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
            
            if not context.strip():
                raise ContextAssemblyError("No content found in inputs")
            
            # Step 2: Initialize LLM orchestrator
            if websocket_callback:
                await websocket_callback({"step": "initializing", "percent": 20})
            
            orchestrator = create_orchestrator(
                provider=config.provider,
                model=config.model,
                temperature=config.temperature
            )
            
            # Step 3: Generate test plan
            if websocket_callback:
                await websocket_callback({"step": "generating_plan", "percent": 30})
            
            test_plan = await self._generate_test_plan(orchestrator, context, inputs.custom_prompt)
            
            # Step 4: Generate test cases
            if websocket_callback:
                await websocket_callback({"step": "generating_cases", "percent": 60})
            
            test_cases = await self._generate_test_cases(orchestrator, context, inputs.custom_prompt)
            
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
                        content=test_cases.content,
                        format="markdown",
                        count=self._count_test_cases(test_cases.content),
                        token_usage=test_cases.total_tokens,
                        generation_time_ms=total_time // 2
                    )
                ),
                metadata=GenerationMetadata(
                    model_used=config.model or orchestrator.config.model,
                    temperature=config.temperature,
                    total_tokens=(test_plan.total_tokens or 0) + (test_cases.total_tokens or 0),
                    sources=sources
                )
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
    
    async def generate_stream(
        self,
        inputs: GenerationInputs,
        config: GenerationConfiguration
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate with streaming output.
        
        Yields:
            Dict with type and data for each chunk
        """
        request_id = str(uuid.uuid4())
        
        yield {"type": "started", "request_id": request_id}
        
        try:
            # Assemble context
            yield {"type": "progress", "step": "assembling", "percent": 10}
            context = await self._assemble_context(inputs)
            
            if not context.strip():
                yield {"type": "error", "error": "No content found in inputs"}
                return
            
            # Initialize orchestrator
            yield {"type": "progress", "step": "initializing", "percent": 20}
            orchestrator = create_orchestrator(
                provider=config.provider,
                model=config.model,
                temperature=config.temperature
            )
            
            # Generate test plan (streaming)
            yield {"type": "progress", "step": "generating_plan", "percent": 30}
            plan_prompt = self._build_test_plan_prompt(context, inputs.custom_prompt)
            
            plan_chunks = []
            async for chunk in orchestrator.generate_stream(
                prompt=plan_prompt,
                system_prompt=self._get_test_plan_system_prompt()
            ):
                plan_chunks.append(chunk)
                yield {"type": "chunk", "section": "test_plan", "content": chunk}
            
            # Generate test cases (streaming)
            yield {"type": "progress", "step": "generating_cases", "percent": 60}
            cases_prompt = self._build_test_case_prompt(context, inputs.custom_prompt)
            
            cases_chunks = []
            async for chunk in orchestrator.generate_stream(
                prompt=cases_prompt,
                system_prompt=self._get_test_case_system_prompt()
            ):
                cases_chunks.append(chunk)
                yield {"type": "chunk", "section": "test_cases", "content": chunk}
            
            # Complete
            yield {
                "type": "completed",
                "request_id": request_id,
                "test_plan": "".join(plan_chunks),
                "test_cases": "".join(cases_chunks)
            }
            
        except Exception as e:
            yield {"type": "error", "error": str(e)}
    
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
    
    async def _generate_test_plan(
        self,
        orchestrator: LLMOrchestrator,
        context: str,
        custom_prompt: Optional[str]
    ) -> LLMResponse:
        """Generate test plan using LLM."""
        prompt = self._build_test_plan_prompt(context, custom_prompt)
        
        return await orchestrator.generate(
            prompt=prompt,
            system_prompt=self._get_test_plan_system_prompt()
        )
    
    async def _generate_test_cases(
        self,
        orchestrator: LLMOrchestrator,
        context: str,
        custom_prompt: Optional[str]
    ) -> LLMResponse:
        """Generate test cases using LLM."""
        prompt = self._build_test_case_prompt(context, custom_prompt)
        
        return await orchestrator.generate(
            prompt=prompt,
            system_prompt=self._get_test_case_system_prompt()
        )
    
    def _build_test_plan_prompt(self, context: str, custom_prompt: Optional[str]) -> str:
        """Build test plan generation prompt."""
        template_path = Path("./templates/test_plan_generation.md")
        if template_path.exists():
            template = template_path.read_text()
        else:
            template = self._default_test_plan_template()
        
        prompt_parts = [
            "# REQUIREMENT CONTEXT",
            context,
            "",
            "# CUSTOM INSTRUCTIONS",
            custom_prompt or "Generate a comprehensive test plan based on the above requirements.",
            "",
            "# OUTPUT TEMPLATE",
            template
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_test_case_prompt(self, context: str, custom_prompt: Optional[str]) -> str:
        """Build test case generation prompt."""
        template_path = Path("./templates/test_case_generation.md")
        if template_path.exists():
            template = template_path.read_text()
        else:
            template = self._default_test_case_template()
        
        prompt_parts = [
            "# REQUIREMENT CONTEXT",
            context,
            "",
            "# CUSTOM INSTRUCTIONS",
            custom_prompt or "Generate detailed test cases based on the above requirements.",
            "",
            "# OUTPUT TEMPLATE",
            template
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _get_test_plan_system_prompt(self) -> str:
        """Get system prompt for test plan generation."""
        return """You are an expert Test Architect. Create a comprehensive Test Plan based on the provided requirements.

Follow these principles:
1. Analyze requirements thoroughly before writing
2. Use IEEE 829 standard structure
3. Define clear test objectives and scope
4. Include risk assessment and mitigation
5. Specify entry and exit criteria
6. Define test environment requirements

Output in professional Markdown format."""
    
    def _get_test_case_system_prompt(self) -> str:
        """Get system prompt for test case generation."""
        return """You are an expert Test Engineer. Create detailed Test Cases based on the provided requirements.

Follow these principles:
1. Include positive (happy path) test cases
2. Include negative (error handling) test cases
3. Add boundary value analysis cases
4. Include edge cases and corner cases
5. Use Given-When-Then format where applicable
6. Define clear preconditions and expected results
7. Assign priority (High/Medium/Low) to each case

Output in professional Markdown format with tables."""
    
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
        # Simple heuristic: count rows in markdown tables
        import re
        table_rows = re.findall(r'^\|.*\|$', content, re.MULTILINE)
        # Subtract header and separator rows
        return max(0, len(table_rows) - 2)
```

## Edge Cases
1. **Empty context**: Return error if no content from any source
2. **JIRA/ValueEdge fetch fails**: Include error comment but continue
3. **Very long context**: May exceed LLM context window - needs truncation
4. **LLM errors**: Return partial results with error message
5. **Custom prompt injection**: Escape or sanitize user-provided custom prompts
