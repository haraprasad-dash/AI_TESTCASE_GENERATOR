from types import SimpleNamespace
from datetime import datetime, timedelta

import pytest

from app.routers import generation as generation_router
from app.routers import llm as llm_router
from app.routers import settings as settings_router
from app.models import ReviewInputs
from app.services.generation_service import GenerationService
from app.services.jira_client import JiraClient
from app.services.review_service import ReviewService, ReviewValidationError


def test_has_any_input_accepts_custom_instruction_only() -> None:
    inputs = SimpleNamespace(
        jira_id=None,
        valueedge_id=None,
        files=[],
        custom_prompt=None,
        test_plan_prompt="Plan prompt",
        test_case_prompt=None,
    )

    assert generation_router._has_any_input(inputs) is True


def test_has_any_input_accepts_jira_without_files_or_prompt() -> None:
    inputs = SimpleNamespace(
        jira_id="PROJ-123",
        valueedge_id=None,
        files=[],
        custom_prompt=None,
        test_plan_prompt=None,
        test_case_prompt=None,
    )

    assert generation_router._has_any_input(inputs) is True


def test_has_any_input_accepts_multiple_ticket_ids_without_files_or_prompt() -> None:
    inputs = SimpleNamespace(
        jira_id=None,
        jira_ids=["PROJ-101", "PROJ-102"],
        valueedge_id=None,
        valueedge_ids=["2001"],
        files=[],
        custom_prompt=None,
        test_plan_prompt=None,
        test_case_prompt=None,
    )

    assert generation_router._has_any_input(inputs) is True


def test_has_any_input_rejects_whitespace_only_prompts() -> None:
    inputs = SimpleNamespace(
        jira_id=None,
        valueedge_id=None,
        files=[],
        custom_prompt="   ",
        test_plan_prompt="\n",
        test_case_prompt="\t",
    )

    assert generation_router._has_any_input(inputs) is False


def test_normalize_secret_value_strips_bearer_prefix() -> None:
    normalized = settings_router._normalize_secret_value("Bearer gsk_live_123", current_value="")
    assert normalized == "gsk_live_123"


def test_normalize_secret_value_trims_spaces() -> None:
    normalized = settings_router._normalize_secret_value("   gsk_trim_me   ", current_value="")
    assert normalized == "gsk_trim_me"


def test_normalize_secret_value_keeps_real_current_for_masked_input() -> None:
    normalized = settings_router._normalize_secret_value("***", current_value="gsk_live_123")
    assert normalized == "gsk_live_123"


def test_normalize_secret_value_drops_mask_if_current_is_masked() -> None:
    normalized = settings_router._normalize_secret_value("***", current_value="***")
    assert normalized == ""


def test_normalize_groq_key_handles_bearer_prefix() -> None:
    assert llm_router._normalize_groq_key("Bearer gsk_live_123") == "gsk_live_123"


def test_normalize_groq_key_returns_none_for_empty() -> None:
    assert llm_router._normalize_groq_key("   ") == ""


@pytest.mark.asyncio
async def test_get_settings_prefers_ollama_when_no_groq_key(monkeypatch) -> None:
    monkeypatch.setattr(
        settings_router,
        "get_runtime_settings",
        lambda: SimpleNamespace(
            jira_base_url=None,
            jira_username=None,
            jira_api_token=None,
            jira_default_project=None,
            valueedge_base_url=None,
            valueedge_client_id=None,
            valueedge_client_secret=None,
            valueedge_shared_space_id=None,
            groq_api_key=None,
            groq_default_model="llama-3.3-70b-versatile",
            groq_default_temperature=0.2,
            ollama_base_url="http://localhost:11434",
            ollama_default_model="llama3.1",
        ),
    )

    payload = await settings_router.get_app_settings()

    assert payload["llm"]["default_provider"] == "ollama"


@pytest.mark.asyncio
async def test_get_settings_masks_secrets(monkeypatch) -> None:
    monkeypatch.setattr(
        settings_router,
        "get_runtime_settings",
        lambda: SimpleNamespace(
            jira_base_url="https://example.atlassian.net",
            jira_username="qa@example.com",
            jira_api_token="jira_secret",
            jira_default_project=None,
            valueedge_base_url=None,
            valueedge_client_id=None,
            valueedge_client_secret=None,
            valueedge_shared_space_id=None,
            groq_api_key="gsk_live_123",
            groq_default_model="llama-3.3-70b-versatile",
            groq_default_temperature=0.2,
            ollama_base_url="http://localhost:11434",
            ollama_default_model="llama3.1",
        ),
    )

    payload = await settings_router.get_app_settings()

    assert payload["jira"]["api_token"] == "***"
    assert payload["llm"]["groq"]["api_key"] == "***"


def test_fallback_table_cases_do_not_default_to_purge_domain() -> None:
    service = GenerationService()
    output = service._build_fallback_table_test_cases("", "Generate test cases for gitlab pipeline error handling")

    assert "purge" not in output.lower()
    assert "gitlab" in output.lower()


def test_default_clarification_questions_are_domain_neutral() -> None:
    service = GenerationService()
    questions = service._default_clarification_questions("Need testcase for gitlab error handling")

    assert questions
    assert all("purge" not in q.lower() for q in questions)
    assert "gitlab" in questions[0].lower()


def test_bdd_mode_inferred_from_template_when_prompt_unspecified() -> None:
    service = GenerationService()
    prompt = service._build_test_case_prompt(
        context="JIRA Issue: PROJ-900",
        custom_prompt=None,
        include_template=True,
    )

    assert "# BDD MODE" in prompt
    assert "Generate Gherkin BDD scenarios only." in prompt


def test_bdd_mode_honors_explicit_non_bdd_opt_out() -> None:
    service = GenerationService()
    template_hint = "BDD-Gherkin format with Feature and Scenario"

    assert service._is_bdd_requested("Please generate in non-bdd table format", template_hint) is False


def test_bdd_mode_defaults_true_when_no_prompt_or_template() -> None:
    service = GenerationService()

    assert service._is_bdd_requested(None, "") is True


def test_test_case_prompt_template_disabled_prioritizes_custom_instruction() -> None:
    service = GenerationService()
    custom = "Follow strict enterprise validation flow"

    prompt = service._build_test_case_prompt(
        context="JIRA Issue: PROJ-777",
        custom_prompt=custom,
        include_template=False,
    )

    assert "# CUSTOM INSTRUCTIONS" in prompt
    assert custom in prompt
    assert "Template disabled by user selection" in prompt
    assert "# OUTPUT TEMPLATE (REFERENCE, NOT MANDATORY)" in prompt


def test_test_case_prompt_template_enabled_fuses_custom_and_template() -> None:
    service = GenerationService()
    custom = "Prioritize risk-based coverage"
    template_marker = "TEMPLATE_FUSION_MARKER_CASE"

    service._resolve_test_case_template = lambda include_template: template_marker if include_template else ""  # type: ignore[assignment]

    prompt = service._build_test_case_prompt(
        context="JIRA Issue: PROJ-778",
        custom_prompt=custom,
        include_template=True,
    )

    assert custom in prompt
    assert template_marker in prompt
    assert "Template disabled by user selection" not in prompt


def test_test_plan_prompt_template_disabled_prioritizes_custom_instruction() -> None:
    service = GenerationService()
    custom = "Keep plan concise with explicit risks"

    prompt = service._build_test_plan_prompt(
        context="JIRA Issue: PROJ-779",
        custom_prompt=custom,
        include_template=False,
    )

    assert "# CUSTOM INSTRUCTIONS" in prompt
    assert custom in prompt
    assert "Template disabled by user selection" in prompt
    assert "# OUTPUT TEMPLATE (REFERENCE, NOT MANDATORY)" in prompt


def test_test_plan_prompt_template_enabled_fuses_custom_and_template() -> None:
    service = GenerationService()
    custom = "Add cross-browser test strategy"
    template_marker = "TEMPLATE_FUSION_MARKER_PLAN"

    service._load_valid_template = lambda template_path, fallback_template, required_markers: template_marker  # type: ignore[assignment]

    prompt = service._build_test_plan_prompt(
        context="JIRA Issue: PROJ-780",
        custom_prompt=custom,
        include_template=True,
    )

    assert custom in prompt
    assert template_marker in prompt
    assert "Template disabled by user selection" not in prompt


def test_groq_retry_specs_rate_limit_preserves_selected_model() -> None:
    service = GenerationService()
    error_message = "Rate limit reached. Limit 200000, Used 198500, Requested 2500"

    specs = service._build_groq_retry_specs(
        error_message=error_message,
        requested_model="openai/gpt-oss-120b",
        ollama_default_model="llama3.1",
    )

    assert specs
    assert all(spec["provider"] == "groq" for spec in specs)
    assert all(spec["model"] == "openai/gpt-oss-120b" for spec in specs)


def test_groq_retry_specs_rate_limit_low_remaining_returns_no_fallback() -> None:
    service = GenerationService()
    error_message = "Rate limit reached. Limit 200000, Used 199980, Requested 1200"

    specs = service._build_groq_retry_specs(
        error_message=error_message,
        requested_model="openai/gpt-oss-120b",
        ollama_default_model="llama3.1",
    )

    assert specs == []


def test_groq_retry_specs_decommissioned_allows_supported_fallbacks() -> None:
    service = GenerationService()
    error_message = "model_decommissioned: selected model is no longer supported"

    specs = service._build_groq_retry_specs(
        error_message=error_message,
        requested_model="deepseek-r1-distill-qwen-32b",
        ollama_default_model="llama3.1",
    )

    providers = [spec["provider"] for spec in specs]
    models = [spec["model"] for spec in specs]
    assert "groq" in providers
    assert "ollama" in providers
    assert "llama-3.3-70b-versatile" in models


def test_extract_requested_groq_tokens_parses_value() -> None:
    service = GenerationService()
    message = "Rate limit reached. Limit 200000, Used 198500, Requested 2500"

    requested = service._extract_requested_groq_tokens(message)
    assert requested == 2500


def test_rate_limit_backoff_seconds_is_bounded_and_positive() -> None:
    service = GenerationService()
    message = "Rate limit reached. Limit 200000, Used 199900, Requested 2500"

    backoff = service._rate_limit_backoff_seconds(message)
    assert 15 <= backoff <= 60


def test_fallback_test_plan_reflects_jenkins_gitlab_context() -> None:
    service = GenerationService()
    prompt = "Jenkins pipeline failed while cloning from GitLab with StringIndexOutOfBoundsException"
    output = service._build_fallback_test_plan("", prompt)

    lower = output.lower()
    assert "jenkins" in lower
    assert "gitlab" in lower
    assert "stringindexoutofboundsexception" in lower or "string parsing" in lower
    assert "target feature" not in lower


def test_test_plan_prompt_includes_source_traceability_rules() -> None:
    service = GenerationService()
    context = "JIRA Issue: SCRUM-5\nSummary: VWO requirement details"
    prompt = service._build_test_plan_prompt(context=context, custom_prompt="Focus on end-to-end coverage", include_template=False)

    assert "# SOURCE TRACEABILITY (MANDATORY)" in prompt
    assert "include that key exactly" in prompt.lower()
    assert "SCRUM-5" in prompt


def test_ensure_test_plan_source_reference_inserts_jira_key_and_summary() -> None:
    service = GenerationService()
    context = "## JIRA Issue: SCRUM-5\n**Summary:** VWO requirement details"
    content = "# Test Plan\n## 1. Introduction\n### 1.1 Purpose\nPlan content"

    updated = service._ensure_test_plan_source_reference(content, context)

    assert "Source Reference" in updated
    assert "SCRUM-5" in updated
    assert "VWO requirement details" in updated


def test_review_validation_requires_one_mode_or_custom_instruction() -> None:
    service = ReviewService()
    inputs = ReviewInputs(
        files=[],
        review_test_cases=False,
        review_user_guide=False,
        custom_instructions="",
    )

    with pytest.raises(ReviewValidationError):
        service._validate_review_request(inputs)


def test_review_clarification_questions_are_bounded_and_non_duplicate() -> None:
    service = ReviewService()
    questions = service._clarification_questions(
        reqs=["Short requirement"],
        test_case_text="TODO TBD etc",
        guide_text="Guide without prerequisites",
    )

    assert len(questions) <= 5
    assert len(questions) == len(set(questions))


def test_review_smart_default_questions_include_bdd_excel_and_url_prompts() -> None:
    service = ReviewService()
    inputs = ReviewInputs(
        jira_id="PROJ-1",
        valueedge_id="2001",
        user_guide_url="https://example.com/guide",
        files=[
            {"filename": "suite.feature", "extracted_text": "Scenario: login"},
            {"filename": "cases.xlsx", "extracted_text": "Test ID,Name\nTC-1,Login"},
        ],
    )

    questions = service._smart_default_questions(inputs, "Test ID,Name\nTC-1,Login")
    joined = " ".join(questions)
    assert "Gherkin" in joined
    assert "Test ID" in joined
    assert "latest version" in joined
    assert "authoritative version" in joined


def test_review_status_timeout_applies_assumptions_fallback() -> None:
    service = ReviewService()
    review_id = "timeout-case"
    state = {
        "review_id": review_id,
        "status": "clarification_required",
        "timestamp": (datetime.utcnow() - timedelta(minutes=31)).isoformat(),
        "report_markdown": "partial",
        "report_json": {},
        "partial_results": {"analysis_completed": []},
        "metadata": {
            "review_type": "test-cases",
            "clarification_required": True,
            "clarification_questions": ["Q1"],
            "clarification_round": 0,
            "max_clarification_rounds": 3,
            "assumptions_applied": False,
            "sources": ["files"],
        },
        "error": None,
    }
    service._states[review_id] = state

    updated = service.get_status(review_id)
    assert updated is not None
    assert updated["status"] == "completed"
    assert updated["metadata"]["assumptions_applied"] is True
    assert "assumptions_disclaimer" in updated["partial_results"]


def test_jira_extract_relevant_fields_preserves_legacy_keys() -> None:
    client = JiraClient(SimpleNamespace(base_url="https://example.atlassian.net", username="u", api_token="t"))
    issue_data = {
        "key": "PROJ-123",
        "fields": {
            "summary": "Login flow update",
            "description": "Update login requirements",
            "issuetype": {"name": "Story"},
            "priority": {"name": "High"},
            "labels": ["login", "security"],
            "components": [{"name": "Web"}],
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "created": "2026-03-13T09:00:00.000+0000",
            "updated": "2026-03-13T10:00:00.000+0000",
        },
    }

    extracted = client.extract_relevant_fields(issue_data)

    assert extracted["key"] == "PROJ-123"
    assert extracted["summary"] == "Login flow update"
    assert extracted["description"] == "Update login requirements"
    assert extracted["issue_type"] == "Story"
    assert extracted["priority"] == "High"
    assert extracted["labels"] == ["login", "security"]
    assert extracted["components"] == ["Web"]
    assert extracted["status"] == "In Progress"
    assert extracted["assignee"] == "Alice"
    assert extracted["reporter"] == "Bob"


def test_jira_extract_relevant_fields_includes_additional_details() -> None:
    client = JiraClient(SimpleNamespace(base_url="https://example.atlassian.net", username="u", api_token="t"))
    issue_data = {
        "key": "PROJ-456",
        "names": {
            "customfield_10010": "Acceptance Criteria",
            "project": "Project",
        },
        "fields": {
            "summary": "Checkout changes",
            "description": {"type": "doc", "content": [{"type": "text", "text": "Main description"}]},
            "issuetype": {"name": "Task"},
            "priority": {"name": "Medium"},
            "labels": [],
            "components": [],
            "status": {"name": "To Do"},
            "assignee": None,
            "reporter": None,
            "created": "2026-03-13T09:00:00.000+0000",
            "updated": "2026-03-13T10:00:00.000+0000",
            "customfield_10010": {
                "type": "doc",
                "content": [{"type": "text", "text": "User can pay with card"}],
            },
            "project": {"key": "PROJ", "name": "Payments"},
        },
    }

    extracted = client.extract_relevant_fields(issue_data)

    assert "additional_details" in extracted
    assert extracted["additional_details"]["customfield_10010"]["name"] == "Acceptance Criteria"
    assert extracted["additional_details"]["customfield_10010"]["value"] == "User can pay with card"
    assert extracted["additional_details"]["project"]["name"] == "Project"
    assert extracted["additional_details"]["project"]["value"]["key"] == "PROJ"


def test_review_extract_requirements_supports_multiple_ticket_ids() -> None:
    service = ReviewService()
    inputs = ReviewInputs(
        jira_id="PROJ-1",
        jira_ids=["PROJ-2"],
        valueedge_id="1001",
        valueedge_ids=["1002"],
        files=[],
    )

    requirements = service._extract_requirements(inputs)

    assert "Requirement from JIRA: PROJ-1" in requirements
    assert "Requirement from JIRA: PROJ-2" in requirements
    assert "Requirement from ValueEdge: 1001" in requirements
    assert "Requirement from ValueEdge: 1002" in requirements
