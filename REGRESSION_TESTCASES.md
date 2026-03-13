# Regression Testcases

Use this suite after any code change affecting settings, LLM connection, generation inputs, or prompt/template behavior.

## Automated Regression Suite

Run from `backend/`:

```powershell
pytest -q tests/test_regression_api.py tests/test_regression_units.py
```

## Included Regression Cases

1. `RG-001` Generation rejects empty request
- Endpoint: `POST /api/generate`
- Expectation: returns `status=failed` and clear "at least one input" error.

2. `RG-002` Custom instructions only are accepted
- Endpoint: `POST /api/generate`
- Input: no ticket, no document, only test plan/case prompts.
- Expectation: returns `status=completed` (service mocked in test) and source includes `custom_instructions`.

3. `RG-003` Bearer-prefixed Groq key in header is normalized
- Endpoint: `POST /api/llm/test-connection?provider=groq`
- Input: `x-groq-api-key: Bearer <key>`
- Expectation: orchestrator receives raw `<key>`.

4. `RG-004` Input detector treats custom instructions as valid
- Function: `app.routers.generation._has_any_input`
- Expectation: returns `True` when only custom prompts are present.

5. `RG-005` Secret normalizer strips `Bearer ` on save path
- Function: `app.routers.settings._normalize_secret_value`
- Expectation: `Bearer gsk_x` becomes `gsk_x`.

6. `RG-006` Masked secret placeholder does not overwrite real saved secret
- Function: `app.routers.settings._normalize_secret_value`
- Expectation: incoming `***` keeps current real key.

7. `RG-007` Runtime key normalizer strips `Bearer ` in LLM router
- Function: `app.routers.llm._normalize_groq_key`
- Expectation: `Bearer gsk_x` becomes `gsk_x`.

8. `RG-008` Settings read API masks secrets
- Function: `app.routers.settings.get_app_settings`
- Expectation: response returns `***` for sensitive fields when configured.

9. `RG-009` Legacy `custom_prompt` only request is accepted
- Endpoint: `POST /api/generate`
- Input: no ticket/file, only `custom_prompt`.
- Expectation: `status=completed` (service mocked in regression test).

10. `RG-010` Whitespace-only custom prompts are rejected
- Endpoint: `POST /api/generate`
- Input: prompt fields containing only spaces/newlines.
- Expectation: clear "at least one input" failure.

11. `RG-011` Friendly message mapping for Groq rate-limit errors
- Endpoint: `POST /api/generate`
- Expectation: failed response error is transformed into user-friendly quota guidance.

12. `RG-012` LLM test-connection falls back to persisted key when no header override is sent
- Endpoint: `POST /api/llm/test-connection?provider=groq`
- Expectation: stored key is used.

13. `RG-013` LLM model listing normalizes Bearer key in header
- Endpoint: `GET /api/llm/models?provider=groq`
- Expectation: orchestrator receives raw key.

14. `RG-014` Input detector accepts Jira-only requests
- Function: `app.routers.generation._has_any_input`
- Expectation: returns `True` with Jira ID and no files/prompts.

15. `RG-015` Secret normalizer trims whitespace and prevents masked-overwrite edge case
- Function: `app.routers.settings._normalize_secret_value`
- Expectation: trims valid secrets and drops masked placeholders if current is also masked.

16. `RG-016` LLM settings default provider resolves to `ollama` when Groq key is absent
- Function: `app.routers.settings.get_app_settings`
- Expectation: `default_provider` is `ollama`.

17. `RG-017` Clarification workflow triggers for ambiguous test cases
- Endpoint: `POST /api/review/test-cases`
- Input: test case artifact with missing expected results/TODO markers.
- Expectation: response returns `clarification_required=true` with specific questions.

18. `RG-018` Clarification context is accepted in follow-up review calls
- Endpoint: `POST /api/review/test-cases` or `POST /api/review/both`
- Input: original request plus `clarification_history` answers.
- Expectation: response avoids duplicate clarification prompts when ambiguity is resolved.

19. `RG-019` Max clarification rounds are enforced
- Endpoint: `POST /api/review/both`
- Input: 3 clarification rounds in `clarification_history`.
- Expectation: system proceeds with best-effort completion and sets assumptions metadata.

20. `RG-020` Partial results are available during clarification
- Endpoint: `GET /api/review/{review_id}/status`
- Input: review run currently in `clarification_required` state.
- Expectation: response includes `partial_results` for completed analysis sections.

21. `RG-021` Clarification attachments are accepted
- Endpoint: `POST /api/review/clarification/{review_id}/attach`
- Input: image/document file upload.
- Expectation: file is stored and linked to review session for follow-up analysis.

22. `RG-022` Input detector accepts multi-ticket list fields
- Function: `app.routers.generation._has_any_input`
- Input: `jira_ids` and/or `valueedge_ids` with no files/prompts.
- Expectation: returns `True`.

23. `RG-023` BDD mode defaults on when prompt/template hints are absent
- Function: `app.services.generation_service._is_bdd_requested`
- Input: no custom prompt and no template hint.
- Expectation: returns `True`.

24. `RG-024` Explicit non-BDD opt-out overrides BDD defaults
- Function: `app.services.generation_service._is_bdd_requested`
- Input: custom prompt containing explicit non-BDD instructions.
- Expectation: returns `False`.

25. `RG-025` Test case prompt honors template-disabled custom-priority
- Function: `app.services.generation_service._build_test_case_prompt`
- Input: `include_template=False` with custom instructions.
- Expectation: prompt uses custom instructions and avoids template fusion.

26. `RG-026` Test case prompt fuses template and custom instructions when enabled
- Function: `app.services.generation_service._build_test_case_prompt`
- Input: `include_template=True` with custom instructions.
- Expectation: prompt contains both custom instruction block and template content.

27. `RG-027` Test plan prompt honors template toggle precedence
- Function: `app.services.generation_service._build_test_plan_prompt`
- Input: template enabled/disabled combinations with custom instructions.
- Expectation: disabled => custom-priority; enabled => template+custom fusion.

28. `RG-028` Groq rate-limit retry preserves selected model
- Function: `app.services.generation_service._build_groq_retry_specs`
- Input: rate-limit error + selected model (e.g., `openai/gpt-oss-120b`).
- Expectation: retry specs remain provider `groq` with same selected model.

29. `RG-029` Low remaining quota yields no unsafe fallback retry
- Function: `app.services.generation_service._build_groq_retry_specs`
- Input: rate-limit error with very low remaining tokens.
- Expectation: returns empty retry spec list.

30. `RG-030` Rate-limit token parsing/backoff stay bounded
- Functions: `app.services.generation_service._extract_requested_groq_tokens`, `_rate_limit_backoff_seconds`
- Input: Groq rate-limit message including requested token count.
- Expectation: requested tokens are parsed correctly; backoff stays within bounded window.

31. `RG-031` Jira extraction retains legacy fields and exposes additional details
- Function: `app.services.jira_client.extract_relevant_fields`
- Input: Jira issue payload with both core and custom fields.
- Expectation: legacy keys remain stable; non-core fields appear in `additional_details`.

32. `RG-032` Enhance endpoint uses section-specific context digest
- Endpoint: `POST /api/llm/enhance-prompt`
- Input: prompt + `prompt_type` + context (`jira_ids`, `valueedge_ids`, attachments metadata).
- Expectation: enhancement request remains grounded in provided context facts.

33. `RG-033` Test plan enhancement prevents testcase drift
- Endpoint: `POST /api/llm/enhance-prompt`
- Input: `prompt_type=test_plan`, prompt with high-priority constraint, mocked misaligned LLM output.
- Expectation: response is corrected to test-plan-focused instruction and preserves priority constraint.

34. `RG-034` Constraint retention in enhancement output
- Function: `app.routers.llm._enforce_constraints`
- Input: enhanced prompt missing explicit user constraints.
- Expectation: missing constraints are appended to final enhanced prompt.

35. `RG-035` Review enhancement subtype alignment
- Endpoint/Function: enhance prompt with `review_test_cases` or `review_user_guide` subtype.
- Expectation: output aligns to selected review subtype and avoids cross-domain drift.

## Manual Smoke Checks (recommended)

1. Open UI Settings -> LLM Settings, save valid Groq key, reopen modal.
- Expectation: key field remains hidden but indicates saved key exists.

2. In AI Configuration, click Test Connection (Groq).
- Expectation: `Connected` status and no invalid key error.

3. Generate with only custom instructions (no ticket/file).
- Expectation: generation request is accepted.

4. Toggle template selection independently for Test Plan/Test Case sections.
- Expectation: selected template only is fused with corresponding custom prompt.

5. Add multiple Jira and ValueEdge IDs via fetch cards, then run generation.
- Expectation: request succeeds using all selected IDs without losing backward compatibility.

6. Run generation with Groq selected model under normal and rate-limit conditions.
- Expectation: selected model is preserved across retry attempts; no silent cross-model fallback.

## Regression Gate

Treat this as required gate before merge:

- Automated suite passes.
- Manual smoke checks pass for any changed area.
- If a regression fails, fix code and rerun all regression cases.
