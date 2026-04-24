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

36. `RG-036` Enhance alignment coverage across all prompt types
- Endpoint: `POST /api/llm/enhance-prompt`
- Input: mocked misaligned model outputs for `test_plan`, `test_case`, `review_test_cases`, `review_user_guide`, and `review`.
- Expectation: fallback/normalization preserves target section intent and avoids cross-type drift.

37. `RG-037` Enhance context is compact snapshot (by design)
- Endpoint: `POST /api/llm/enhance-prompt`
- Input: large attachment set and verbose text.
- Expectation: enhance behavior remains grounded in compact context digest (IDs + limited attachment snippets), not full raw payload bodies.

38. `RG-038` Review upload accepts `.feature` files even with generic browser MIME
- Endpoint: `POST /api/documents/upload`
- Input: `.feature` attachment uploaded as `application/octet-stream` or `text/plain`.
- Expectation: upload succeeds, content is normalized to Gherkin/text handling, and review flow can use the artifact.

39. `RG-039` Review instruction merge preserves shared and mode-specific guidance
- Function: `app.services.review_service.ReviewService._merged_custom_instructions`
- Input: shared review instructions plus test-case and user-guide specific instructions.
- Expectation: merged text includes all applicable instruction blocks with deterministic labels.

40. `RG-040` Mode-specific review instructions count as custom review guidance
- Function: `app.services.review_service.ReviewService._collect_sources`
- Input: request with only mode-specific review instructions.
- Expectation: sources include `custom_instructions` for downstream handling.

41. `RG-041` User-guide review requires uploaded guide file(s)
- Endpoint: `POST /api/review/user-guide`
- Input: `review_user_guide=true`, no guide file uploaded.
- Expectation: request fails with `Please attach user guide files (.pdf, .docx, .txt, .md)`.

42. `RG-042` User-guide review does not ask test-case-only clarification questions
- Endpoint: `POST /api/review/user-guide`
- Input: uploaded guide document plus uploaded `.feature` reference file.
- Expectation: clarification questions can ask about guide completeness, but must not ask Gherkin or test-case expected-result questions.

43. `RG-043` Answered clarification questions are not repeated
- Function: `app.services.review_service.ReviewService.review`
- Input: second-round user-guide review request carrying prior `clarification_history` answers.
- Expectation: previously answered questions are filtered out from the next clarification round.

44. `RG-044` Clarification answer with empty question-history does not loop
- Function: `app.services.review_service.ReviewService.review`
- Input: `clarification_history` has answer text but empty question array.
- Expectation: review completes without repeating the same clarification loop.

45. `RG-045` User-guide report includes clarification-applied summary
- Function: `app.services.review_service.ReviewService.review`
- Input: completed review with submitted clarification history.
- Expectation: final report contains `Clarification Applied` section with round count and latest answer considered.

46. `RG-046` User-guide report includes testcase-driven focus-gap checks
- Function: `app.services.review_service.ReviewService._build_user_guide_review`
- Input: user-guide review with reference `.feature` content focused on specific capability.
- Expectation: report includes focus terms and targeted missing topics tied to testcase obligations (defaults, validation, picker, upgrade) when absent in guide.

47. `RG-047` User-guide report includes line-level modification references and quality score
- Function: `app.services.review_service.ReviewService._build_user_guide_review`
- Input: user-guide content containing ambiguous terms (e.g., `etc`) and clarification history.
- Expectation: payload includes `summary.quality_score` and `modification_recommendations[*].line_reference`; markdown includes explicit `Line to modify: Lx` guidance.

48. `RG-048` Review template toggle materially changes review mode
- Function: `app.services.review_service.ReviewService.review`
- Input: same user-guide input with template enabled (`review_user_guide=true`) vs disabled (`review_user_guide=false`) plus instructions.
- Expectation: summary includes distinct `review_mode` values (`template_guided` vs `instruction_only`) and template-guided mode applies broader checklist gaps.

49. `RG-049` Test-case review summary exposes active mode
- Function: `app.services.review_service.ReviewService.review`
- Input: test-case review with template enabled.
- Expectation: `report_json.test_case_review.summary.review_mode == template_guided`.

50. `RG-050` Review excludes negative/edge/exploratory scenarios from customer-facing guide coverage
- Function: `app.services.review_service.ReviewService._customer_facing_topics_from_testcases`
- Input: `.feature` content with mixed positive + `@Negative` + `@Exploratory/@EdgeCase` scenarios.
- Expectation: only customer-facing positive/integration topics remain in guide-coverage topic list.

51. `RG-051` Section-only guide instruction narrows extracted content
- Function: `app.services.review_service.ReviewService._filter_text_by_section_hints`
- Input: guide text with multiple sections and section hint requesting one specific section.
- Expectation: strict section filter keeps requested section context and excludes unrelated sections.

52. `RG-052` User-guide report output shape is deterministic and layout-stable
- Function: `app.services.review_service.ReviewService._build_user_guide_review`
- Input: user-guide review with testcase reference artifacts.
- Expectation: markdown includes fixed sections for documented features, coverage gaps, clarity issues, defect log, and priority actions.

53. `RG-053` Ollama fallback BDD suite returns expanded scenario count
- Function: `app.services.generation_service.GenerationService._build_fallback_bdd_test_cases`
- Input: BDD-mode fallback path after simulated `LLMError` on provider `ollama`.
- Expectation: fallback output contains at least 24 scenarios (target 28) spanning positive, negative, edge, boundary, security, and performance tags.

54. `RG-054` Ollama fallback path emits diagnostic warning log
- Function: `app.services.generation_service.GenerationService.generate`
- Input: forced `LLMError` during Ollama generation.
- Expectation: warning log includes provider and original error text before deterministic fallback response is returned.

55. `RG-055` Ollama provider timeout configured to 300 seconds
- Function: `app.services.llm_orchestrator.OllamaProvider.generate` and `generate_stream`
- Input: inspect AsyncClient configuration during request dispatch.
- Expectation: both non-stream and stream clients use `timeout=300.0`.

53. `RG-053` User-guide review supports multi-file document context
- Endpoint: `POST /api/review/user-guide`
- Input: multiple guide artifacts (`.pdf`, `.docx`, `.md`) attached together with testcase reference file.
- Expectation: review merges all guide document text into one deterministic analysis context and returns completed report.

54. `RG-054` User-guide review succeeds without URL when guide documents are attached
- Endpoint: `POST /api/review/user-guide`
- Input: uploaded guide document(s), no `user_guide_url`.
- Expectation: request succeeds and returns structured user-guide review output.

55. `RG-055` Detailed user-guide instruction prompts run in non-blocking clarification mode
- Function: `app.services.review_service.ReviewService.review`
- Input: long user-guide instruction prompt (detailed scope constraints) with attached guide document and testcase reference.
- Expectation: review returns `status=completed` even if optional clarification candidates exist, and report is generated in a single pass.

56. `RG-056` Unreadable guide source returns explicit source-access report
- Function: `app.services.review_service.ReviewService._build_user_guide_review`
- Input: user-guide review where attached guide files cannot be parsed into meaningful text.
- Expectation: report includes `Source Access Gap` and `Action Required` guidance instead of low-confidence bulk coverage mapping.

57. `RG-057` User-guide gap-analysis framing includes status matrix and section-4 checklist
- Function: `app.services.review_service.ReviewService._build_user_guide_review`
- Input: user-guide review with valid extracted guide content and testcase reference artifacts.
- Expectation: markdown includes deterministic preface (`Status | Meaning | Customer Impact`) and `4) RECOMMENDED DOCUMENTATION STRUCTURE` with key customer questions.

58. `RG-058` User-guide output preserves testcase-level traceability for matching/missing/modification
- Function: `app.services.review_service.ReviewService._build_user_guide_review`
- Input: user-guide review with `.feature` testcases and guide text containing full/partial/missing coverage patterns.
- Expectation: payload and markdown include testcase references (`TC-xxx`) for matching and missing items, and modification entries include exact line reference, current text, required change, and suggested corrected text.

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

7. Attach a `.feature` file from the Review section using **Attach Review Files**.
- Expectation: upload succeeds on Windows/browser combinations that send `application/octet-stream` or `text/plain` for `.feature` files.

8. Enable both review modes and enter separate test-case and user-guide instructions.
- Expectation: each section keeps its own instructions, each Enhance button targets the correct subtype, and review request completes without dropping section instructions.

9. Try running user-guide review with no attached guide document.
- Expectation: UI blocks submit and backend returns `Please attach user guide files (.pdf, .docx, .txt, .md)` if called directly.

10. In **User Guide Review Section**, attach multiple guide documents and run user-guide review.
- Expectation: upload succeeds, all files remain visible in the user-guide card, and review uses merged guide context without turning the request into test-case review.

11. Answer a user-guide clarification round, then submit follow-up clarification.
- Expectation: already answered questions do not reappear unless new unanswered ambiguity is introduced.

12. Run **Review User Guide** on a concise guide with ambiguous phrases (`etc`, `TBD`, `as needed`).
- Expectation: output shows a structured quality summary and line-level modification cards with suggested rewrites.

## Regression Gate

Treat this as required gate before merge:

- Automated suite passes.
- Manual smoke checks pass for any changed area.
- If a regression fails, fix code and rerun all regression cases.

---

59. `RG-059` settings.extra=ignore allows unknown .env keys without crashing
- Function: `app.config.Settings`
- Input: .env containing extra keys like `export_default_format`, `test_plan_template_path`.
- Expectation: Settings loads successfully without `Extra inputs are not permitted` Pydantic error.

60. `RG-060` GenerationConfiguration accepts advanced Groq sampling params
- Model: `app.models.GenerationConfiguration`
- Input: `top_p=0.9`, `frequency_penalty=0.0`, `presence_penalty=0.0`.
- Expectation: fields are accepted, defaulted when absent, and pass cleanly to orchestrator.

61. `RG-061` LLMConfig propagates top_p/frequency/presence to GroqProvider.generate
- Function: `app.services.llm_orchestrator.LLMOrchestrator.generate`
- Expectation: provider.generate is called with `top_p`, `frequency_penalty`, `presence_penalty` matching config.

62. `RG-062` Groq API call includes advanced sampling params in payload
- Function: `app.services.llm_orchestrator.GroqProvider.generate`
- Expectation: `client.chat.completions.create` receives `top_p`, `frequency_penalty`, `presence_penalty`.

63. `RG-063` Sectioned generation activates when initial test-case output is weak
- Function: `app.services.generation_service.GenerationService._generate_test_cases`
- Expectation: when initial output fails `_is_weak_test_cases`, `_generate_test_cases_sectioned` is called.

64. `RG-064` Sectioned generation merges positive/negative, edge/boundary, security/performance
- Function: `app.services.generation_service.GenerationService._generate_test_cases_sectioned`
- Expectation: merged output contains content from all three section groups.

65. `RG-065` Zero-shot scenario never triggers clarification flow
- Function: `app.services.generation_service.GenerationService._should_require_clarification`
- Input: empty `custom_prompt`, valid test plan and cases content.
- Expectation: returns `False` unconditionally for zero-shot requests.

66. `RG-066` No hardcoded Ollama default model in backend settings model
- Model: `app.models.OllamaConfig`
- Input: instantiate `OllamaConfig()` with no model provided.
- Expectation: `default_model` remains `None`; no implicit `llama3.1`/`qwen` literal is injected.

67. `RG-067` create_orchestrator fails fast when provider model is unset
- Function: `app.services.llm_orchestrator.create_orchestrator`
- Input: provider=`ollama` with no request model and no `OLLAMA_DEFAULT_MODEL` configured.
- Expectation: returns actionable `LLMError` instead of silently selecting a hardcoded model.

68. `RG-068` Settings save path does not hardcode OLLAMA_DEFAULT_MODEL
- Endpoint: `PUT /api/settings`
- Input: `llm.ollama.default_model` empty.
- Expectation: `OLLAMA_DEFAULT_MODEL` is cleared/omitted, not replaced with `llama3.1`.

69. `RG-069` UI initializes Ollama model from saved settings only
- File: `frontend/src/pages/HomePage.tsx`
- Input: provider=ollama with empty saved default model.
- Expectation: model state initializes empty and is filled only by live model-list selection.

## Free Vision Provider Regression Tests

| ID | Test | Automated | File |
|----|------|-----------|------|
| REG-VISION-001 | Auto-detect picks Groq when `GROQ_API_KEY` set | ✅ | `test_regression_units.py` |
| REG-VISION-002 | Auto-detect defaults to Groq when no provider available | ✅ | `test_regression_units.py` |
| REG-VISION-003 | Groq default model is Llama 4 Scout | ✅ | `test_regression_units.py` |
| REG-VISION-004 | `effective_model` returns explicit model when set | ✅ | `test_regression_units.py` |

### Manual Smoke Checks (Vision)

1. Set only `GROQ_API_KEY`, upload PDF with images → vision analysis uses Groq provider.
2. Remove all API keys, start Ollama with `llava` → vision auto-detects Ollama.
3. Call `GET /api/vision/health` → shows correct provider availability status.
4. Call `GET /api/vision/providers` → lists 4 providers with correct tier labels.
