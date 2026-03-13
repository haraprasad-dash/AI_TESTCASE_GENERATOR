from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.models import GenerationResponse, GenerationOutputs, GenerationMetadata
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


def _review_inputs_with_artifacts() -> dict:
    return {
        "jira_id": "PROJ-101",
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


def test_review_user_guide_rejects_invalid_url() -> None:
    response = client.post(
        "/api/review/user-guide",
        json={
            "inputs": {
                "review_test_cases": False,
                "review_user_guide": True,
                "user_guide_url": "not-a-valid-url",
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
    assert response.json()["detail"] == "Please provide a valid URL"
