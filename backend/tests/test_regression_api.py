from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.models import GenerationResponse, GenerationOutputs, GenerationMetadata
from app.routers import documents as documents_router
from app.routers import generation as generation_router
from app.routers import llm as llm_router


client = TestClient(app)


def _completed_generation_response() -> GenerationResponse:
    return GenerationResponse(
        request_id="regression-request",
        status="completed",
        timestamp=datetime.utcnow(),
        outputs=GenerationOutputs(),
        metadata=GenerationMetadata(
            model_used="llama-3.3-70b-versatile",
            temperature=0.2,
            sources=["custom_instructions"],
        ),
        error=None,
    )


def test_generate_rejects_when_all_inputs_missing() -> None:
    response = client.post(
        "/api/generate",
        json={"inputs": {"files": []}, "configuration": {"provider": "groq"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "At least one input source required" in body["error"]


def test_generate_allows_custom_prompt_only(monkeypatch) -> None:
    async def fake_generate(self, inputs, config, websocket_callback=None):
        return _completed_generation_response()

    monkeypatch.setattr(generation_router.GenerationService, "generate", fake_generate)

    response = client.post(
        "/api/generate",
        json={
            "inputs": {
                "files": [],
                "test_plan_prompt": "Create test plan for login flow",
                "test_case_prompt": "Create negative login test cases",
            },
            "configuration": {"provider": "groq", "temperature": 0.2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["metadata"]["sources"] == ["custom_instructions"]


def test_generate_allows_legacy_custom_prompt_only(monkeypatch) -> None:
    async def fake_generate(self, inputs, config, websocket_callback=None):
        return _completed_generation_response()

    monkeypatch.setattr(generation_router.GenerationService, "generate", fake_generate)

    response = client.post(
        "/api/generate",
        json={
            "inputs": {
                "files": [],
                "custom_prompt": "Generate login regression test coverage",
            },
            "configuration": {"provider": "groq", "temperature": 0.2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"


def test_generate_rejects_whitespace_only_custom_inputs() -> None:
    response = client.post(
        "/api/generate",
        json={
            "inputs": {
                "files": [],
                "custom_prompt": "   ",
                "test_plan_prompt": "\n\t",
                "test_case_prompt": "\n",
            },
            "configuration": {"provider": "groq"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "At least one input source required" in body["error"]


def test_generate_friendly_error_for_groq_rate_limit(monkeypatch) -> None:
    async def fake_generate(self, inputs, config, websocket_callback=None):
        return GenerationResponse(
            request_id="regression-request",
            status="failed",
            timestamp=datetime.utcnow(),
            outputs=GenerationOutputs(),
            metadata=GenerationMetadata(
                model_used="llama-3.3-70b-versatile",
                temperature=0.2,
                sources=[],
            ),
            error="Error code: 429 rate_limit_exceeded",
        )

    monkeypatch.setattr(generation_router.GenerationService, "generate", fake_generate)

    response = client.post(
        "/api/generate",
        json={
            "inputs": {"files": [], "custom_prompt": "Generate tests"},
            "configuration": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "Groq token/day limit reached" in body["error"]


def test_llm_test_connection_normalizes_bearer_header(monkeypatch) -> None:
    captured = {}

    class DummyOrchestrator:
        async def test_connection(self):
            return {"status": "connected", "provider": "groq", "available_models": 1}

    def fake_create_orchestrator(**kwargs):
        captured.update(kwargs)
        return DummyOrchestrator()

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key=None, ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", fake_create_orchestrator)

    response = client.post(
        "/api/llm/test-connection?provider=groq",
        headers={"x-groq-api-key": "Bearer gsk_test_123"},
    )

    assert response.status_code == 200
    assert captured["api_key"] == "gsk_test_123"
    assert response.json()["status"] == "connected"


def test_llm_test_connection_uses_saved_key_when_header_missing(monkeypatch) -> None:
    captured = {}

    class DummyOrchestrator:
        async def test_connection(self):
            return {"status": "connected", "provider": "groq", "available_models": 1}

    def fake_create_orchestrator(**kwargs):
        captured.update(kwargs)
        return DummyOrchestrator()

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_saved_key", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", fake_create_orchestrator)

    response = client.post("/api/llm/test-connection?provider=groq")

    assert response.status_code == 200
    assert captured["api_key"] == "gsk_saved_key"


def test_llm_models_normalizes_bearer_header(monkeypatch) -> None:
    captured = {}

    class DummyOrchestrator:
        async def list_models(self):
            return ["llama-3.3-70b-versatile"]

    def fake_create_orchestrator(**kwargs):
        captured.update(kwargs)
        return DummyOrchestrator()

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key=None, ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", fake_create_orchestrator)

    response = client.get(
        "/api/llm/models?provider=groq",
        headers={"x-groq-api-key": "Bearer gsk_test_models"},
    )

    assert response.status_code == 200
    assert response.json() == ["llama-3.3-70b-versatile"]
    assert captured["api_key"] == "gsk_test_models"


def test_enhance_prompt_context_aware_prevents_test_plan_drift(monkeypatch) -> None:
    class DummyOrchestrator:
        async def generate(self, prompt, system_prompt=None):
            return SimpleNamespace(content="Generate test cases for endpoints: GET /users, POST /users")

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_test", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", lambda **kwargs: DummyOrchestrator())

    response = client.post(
        "/api/llm/enhance-prompt",
        json={
            "prompt": "For test plan, only high priority tasks",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_type": "test_plan",
            "context": {
                "jira_ids": ["PROJ-123"],
                "files": [
                    {
                        "filename": "requirements.md",
                        "content_type": "text/markdown",
                        "extracted_snippet": "Critical payment flow and auth scope",
                    }
                ],
            },
        },
    )

    assert response.status_code == 200
    enhanced = response.json()["enhanced_prompt"].lower()
    assert "test plan" in enhanced
    assert "not generate test case" in enhanced or "not generate test case lists" in enhanced
    assert "high-priority" in enhanced or "high priority" in enhanced


def test_enhance_prompt_test_plan_rewrites_user_reported_testcase_style_output(monkeypatch) -> None:
    testcase_style = (
        "Generate high-priority tests for endpoint coverage, including positive tests for successful requests, "
        "negative tests for error handling, edge cases for unexpected inputs, boundary value tests for field limits, "
        "security tests for authentication and authorization, and performance tests for load and stress conditions."
    )

    class DummyOrchestrator:
        async def generate(self, prompt, system_prompt=None):
            return SimpleNamespace(content=testcase_style)

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_test", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", lambda **kwargs: DummyOrchestrator())

    response = client.post(
        "/api/llm/enhance-prompt",
        json={
            "prompt": "create only high priority task",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_type": "test_plan",
            "context": {
                "jira_ids": ["PROJ-123"],
                "valueedge_ids": ["4567"],
            },
        },
    )

    assert response.status_code == 200
    enhanced = response.json()["enhanced_prompt"].lower()
    assert "test plan" in enhanced
    assert "not testcase checklist" in enhanced or "not generate test case" in enhanced
    assert "high-priority" in enhanced or "high priority" in enhanced


def test_enhance_prompt_test_case_rewrites_plan_style_output(monkeypatch) -> None:
    plan_style = (
        "Create a test plan with scope, objectives, milestones, timeline, entry criteria, "
        "exit criteria, risks, and dependencies."
    )

    class DummyOrchestrator:
        async def generate(self, prompt, system_prompt=None):
            return SimpleNamespace(content=plan_style)

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_test", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", lambda **kwargs: DummyOrchestrator())

    response = client.post(
        "/api/llm/enhance-prompt",
        json={
            "prompt": "Generate API test cases for login and signup",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_type": "test_case",
            "context": {
                "jira_ids": ["PROJ-201"],
                "constraints": ["Cover only high-priority scenarios."],
            },
        },
    )

    assert response.status_code == 200
    enhanced = response.json()["enhanced_prompt"].lower()
    assert "test case" in enhanced or "testcase" in enhanced
    assert "high-priority" in enhanced or "high priority" in enhanced


def test_enhance_prompt_review_test_cases_rewrites_user_guide_style_output(monkeypatch) -> None:
    user_guide_style = (
        "Review the user guide for installation steps, onboarding clarity, UI walkthrough, "
        "and screenshot consistency."
    )

    class DummyOrchestrator:
        async def generate(self, prompt, system_prompt=None):
            return SimpleNamespace(content=user_guide_style)

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_test", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", lambda **kwargs: DummyOrchestrator())

    response = client.post(
        "/api/llm/enhance-prompt",
        json={
            "prompt": "Review uploaded test cases and prioritize critical defects",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_type": "review_test_cases",
            "context": {
                "review_test_cases": True,
                "review_user_guide": False,
                "jira_ids": ["PROJ-301"],
            },
        },
    )

    assert response.status_code == 200
    enhanced = response.json()["enhanced_prompt"].lower()
    assert "test case review" in enhanced or "coverage" in enhanced


def test_enhance_prompt_review_user_guide_rewrites_testcase_style_output(monkeypatch) -> None:
    testcase_style = (
        "Review test cases for positive tests, negative tests, edge cases, boundary value checks, "
        "and endpoint coverage completeness."
    )

    class DummyOrchestrator:
        async def generate(self, prompt, system_prompt=None):
            return SimpleNamespace(content=testcase_style)

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_test", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", lambda **kwargs: DummyOrchestrator())

    response = client.post(
        "/api/llm/enhance-prompt",
        json={
            "prompt": "Review user guide quality and correctness",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_type": "review_user_guide",
            "context": {
                "review_test_cases": False,
                "review_user_guide": True,
                "user_guide_url": "https://example.com/guide",
            },
        },
    )

    assert response.status_code == 200
    enhanced = response.json()["enhanced_prompt"].lower()
    assert "user guide review" in enhanced or "user guide" in enhanced


def test_enhance_prompt_review_rewrites_generation_style_output(monkeypatch) -> None:
    generation_style = (
        "Create a detailed test plan with scope, timeline, milestones, and exit criteria for release validation."
    )

    class DummyOrchestrator:
        async def generate(self, prompt, system_prompt=None):
            return SimpleNamespace(content=generation_style)

    monkeypatch.setattr(
        llm_router,
        "get_settings",
        lambda: SimpleNamespace(groq_api_key="gsk_test", ollama_base_url="http://localhost:11434"),
    )
    monkeypatch.setattr(llm_router, "create_orchestrator", lambda **kwargs: DummyOrchestrator())

    response = client.post(
        "/api/llm/enhance-prompt",
        json={
            "prompt": "Review generated assets and provide prioritized quality findings",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt_type": "review",
            "context": {
                "review_test_cases": True,
                "review_user_guide": True,
                "jira_ids": ["PROJ-401"],
            },
        },
    )

    assert response.status_code == 200
    enhanced = response.json()["enhanced_prompt"].lower()
    assert "review" in enhanced
    assert "test plan" not in enhanced or "enhance review instructions" in enhanced


def _review_inputs_with_artifacts() -> dict:
    return {
        "jira_id": "PROJ-101",
        "user_guide_url": "https://example.com/user-guide",
        "files": [
            {
                "filename": "login_test_cases.feature",
                "extracted_text": "Scenario: Login success\nGiven valid user\nWhen user logs in",
                "content_type": "text/plain",
            },
            {
                "filename": "user_guide.md",
                "extracted_text": "# User Guide\nSetup and login flow.",
                "content_type": "text/markdown",
            },
        ],
        "review_test_cases": True,
        "review_user_guide": True,
    }


def test_review_test_cases_requires_test_case_attachment() -> None:
    response = client.post(
        "/api/review/test-cases",
        json={
            "inputs": {
                "review_test_cases": True,
                "review_user_guide": False,
                "files": [],
            },
            "configuration": {"provider": "groq"},
        },
    )

    assert response.status_code == 400
    assert "Please attach test case files" in response.json()["detail"]


def test_review_both_returns_clarification_questions_for_ambiguous_input() -> None:
    payload = _review_inputs_with_artifacts()
    payload["files"][0]["extracted_text"] = "Scenario: Login\nTODO: add expected result"

    response = client.post(
        "/api/review/both",
        json={"inputs": payload, "configuration": {"provider": "groq"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "clarification_required"
    assert body["metadata"]["clarification_required"] is True
    assert len(body["metadata"]["clarification_questions"]) >= 1


def test_review_both_enforces_max_clarification_rounds() -> None:
    payload = _review_inputs_with_artifacts()
    payload["files"][0]["extracted_text"] = "Scenario: Login\nTODO: add expected result"
    payload["clarification_history"] = [
        {"questions": ["Q1"], "answer": "A1"},
        {"questions": ["Q2"], "answer": "A2"},
        {"questions": ["Q3"], "answer": "A3"},
    ]

    response = client.post(
        "/api/review/both",
        json={"inputs": payload, "configuration": {"provider": "groq"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["metadata"]["assumptions_applied"] is True


def test_review_status_returns_partial_results() -> None:
    payload = _review_inputs_with_artifacts()
    payload["files"][0]["extracted_text"] = "Scenario: Login\nTODO: add expected result"

    start = client.post(
        "/api/review/both",
        json={"inputs": payload, "configuration": {"provider": "groq"}},
    )
    body = start.json()
    review_id = body["review_id"]

    status = client.get(f"/api/review/{review_id}/status")
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["review_id"] == review_id
    if status_body["status"] == "clarification_required":
        assert "partial_results" in status_body


def test_review_user_guide_requires_uploaded_guide_documents() -> None:
    response = client.post(
        "/api/review/user-guide",
        json={
            "inputs": {
                "review_test_cases": False,
                "review_user_guide": True,
                "files": [
                    {
                        "filename": "login_test_cases.feature",
                        "extracted_text": "Scenario: login",
                        "content_type": "text/plain",
                    }
                ],
            },
            "configuration": {"provider": "groq"},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please attach user guide files (.pdf, .docx, .txt, .md)"


def test_review_user_guide_accepts_uploaded_guide_file_without_url() -> None:
    response = client.post(
        "/api/review/user-guide",
        json={
            "inputs": {
                "review_test_cases": False,
                "review_user_guide": True,
                "files": [
                    {
                        "filename": "user_guide.md",
                        "extracted_text": "# User Guide\nSetup instructions",
                        "content_type": "text/markdown",
                    }
                ],
            },
            "configuration": {"provider": "groq"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"completed", "clarification_required"}


def test_review_user_guide_does_not_ask_test_case_specific_clarifications() -> None:
    response = client.post(
        "/api/review/user-guide",
        json={
            "inputs": {
                "review_test_cases": False,
                "review_user_guide": True,
                "user_guide_url": "https://example.com/theme-guide",
                "files": [
                    {
                        "filename": "theme_setting.feature",
                        "extracted_text": "Scenario: Update theme\nGiven user opens settings\nWhen user changes header color",
                        "content_type": "text/plain",
                    },
                    {
                        "filename": "theme-guide.md",
                        "extracted_text": "# Theme Settings\nSteps to change theme colors.",
                        "content_type": "text/markdown",
                    },
                ],
            },
            "configuration": {"provider": "groq"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    joined_questions = " ".join(body["metadata"]["clarification_questions"])
    assert "Gherkin" not in joined_questions
    assert "expected-result" not in joined_questions


def test_documents_upload_accepts_feature_file_with_generic_mime(monkeypatch, tmp_path) -> None:
    class DummyParser:
        async def parse_file(self, file_path, content_type):
            assert content_type == "text/x-gherkin"
            return SimpleNamespace(text="Feature: Theme settings", page_count=1)

    monkeypatch.setattr(documents_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(documents_router, "get_document_parser", lambda: DummyParser())

    response = client.post(
        "/api/documents/upload",
        files={"file": ("theme_setting.feature", b"Feature: Theme settings", "application/octet-stream")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "theme_setting.feature"
    assert body["content_type"] == "text/x-gherkin"


def test_documents_upload_accepts_feature_file_with_text_plain_mime(monkeypatch, tmp_path) -> None:
    class DummyParser:
        async def parse_file(self, file_path, content_type):
            assert content_type == "text/x-gherkin"
            return SimpleNamespace(text="Scenario: Save theme", page_count=1)

    monkeypatch.setattr(documents_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(documents_router, "get_document_parser", lambda: DummyParser())

    response = client.post(
        "/api/documents/upload",
        files={"file": ("theme_setting.feature", b"Scenario: Save theme", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["content_type"] == "text/x-gherkin"
