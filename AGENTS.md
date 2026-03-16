# B.L.A.S.T. Framework - Agent Guide

## Project Overview

This repository contains the **B.L.A.S.T. (Blueprint, Link, Architect, Stylize, Trigger)** master system prompt and protocol documentation. It is **not** a traditional codebase but rather a **methodology framework** for building deterministic, self-healing automation systems in Antigravity.

The framework emphasizes reliability over speed and enforces a structured approach to automation development using the **A.N.T. 3-layer architecture**.

---

## Technology Stack

- **Target Platform**: Antigravity (automation platform)
- **Primary Language**: Python (for tools layer)
- **Documentation Format**: Markdown
- **Configuration**: Environment variables via `.env` files

---

## Project Structure

When a project is initialized using this framework, the following structure is created:

```
project-root/
├── gemini.md          # Project Constitution - Data schemas, behavioral rules, architectural invariants
├── task_plan.md       # Phases, goals, and checklists
├── findings.md        # Research, discoveries, constraints
├── progress.md        # Execution history: what was done, errors encountered, tests, results
├── BLAST.md           # This framework documentation (master system prompt)
├── .env               # API Keys/Secrets (created during Link phase)
├── architecture/      # Layer 1: SOPs (Standard Operating Procedures)
│   └── *.md           # Technical documentation defining goals, inputs, tool logic, edge cases
├── tools/             # Layer 3: Python scripts (deterministic, atomic, testable)
│   └── *.py
└── .tmp/              # Temporary workbench for intermediate files (scraped data, logs)
```

---

## Core Concepts

### The B.L.A.S.T. Protocol (5 Phases)

| Phase | Name | Purpose | Key Deliverables |
|-------|------|---------|------------------|
| 0 | **Protocol 0: Initialization** | Project setup and planning | `task_plan.md`, `findings.md`, `progress.md`, `gemini.md` |
| 1 | **B - Blueprint** | Vision & Logic definition | JSON Data Schema, discovery answers |
| 2 | **L - Link** | Connectivity verification | Tested API connections, verified `.env` credentials |
| 3 | **A - Architect** | 3-Layer implementation | SOPs in `architecture/`, Python scripts in `tools/` |
| 4 | **S - Stylize** | Refinement & UI | Formatted outputs, professional delivery |
| 5 | **T - Trigger** | Deployment & automation | Cloud transfer, cron jobs, webhooks, maintenance log |

### The A.N.T. 3-Layer Architecture

1. **Layer 1: Architecture (`architecture/`)**
   - Technical SOPs written in Markdown
   - Defines goals, inputs, tool logic, and edge cases
   - **Golden Rule**: If logic changes, update the SOP BEFORE updating code

2. **Layer 2: Navigation (Decision Making)**
   - Reasoning layer that routes data between SOPs and Tools
   - Complex tasks are delegated to execution tools

3. **Layer 3: Tools (`tools/`)**
   - Deterministic Python scripts
   - Atomic and testable
   - Environment variables stored in `.env`
   - Use `.tmp/` for intermediate file operations

---

## Key Files Reference

### Core Files

| File | Purpose | When to Update |
|------|---------|----------------|
| `gemini.md` | Project Constitution - Data schemas, behavioral rules, architectural invariants | Only when schema changes, rules added, or architecture modified |
| `task_plan.md` | Phases, goals, and checklists | During planning and phase transitions |
| `findings.md` | Research, discoveries, constraints | When new discoveries are made |
| `progress.md` | Execution history, errors, tests, results | After every meaningful task |

### Framework Documentation

| File | Purpose |
|------|---------|
| `BLAST.md` | Master system prompt and protocol documentation (framework reference) |

---

## Operating Principles

### 1. Data-First Rule

- **Define the JSON Data Schema in `gemini.md` BEFORE building any Tool**
- What does the raw input look like?
- What does the processed output look like?
- Coding only begins once the "Payload" shape is confirmed

> **Hierarchy**: `gemini.md` is *law*. Planning files are *memory*.

### 2. Self-Annealing (The Repair Loop)

When a Tool fails:

1. **Analyze**: Read the stack trace and error message. Do not guess.
2. **Patch**: Fix the Python script in `tools/`.
3. **Test**: Verify the fix works.
4. **Update Architecture**: Update the corresponding `.md` file in `architecture/` with new learnings (e.g., "API requires specific header", "Rate limit is 5 calls/sec")

### 3. Deliverables vs. Intermediates

| Type | Location | Description |
|------|----------|-------------|
| **Local (Intermediates)** | `.tmp/` | Scraped data, logs, temporary files. Ephemeral - can be deleted. |
| **Global (Deliverables)** | Cloud | The "Payload": Google Sheets, Databases, UI updates. **Project is only "Complete" when payload reaches final destination.** |

---

## Development Workflow

### Initialization (Protocol 0)

```
1. Create task_plan.md, findings.md, progress.md, gemini.md
2. Define Data Schema in gemini.md
3. Get Blueprint approved
4. HALT: Do NOT write scripts in tools/ until above is complete
```

### Blueprint Phase Questions

When starting a new project, answer these 5 Discovery Questions:

1. **North Star**: What is the singular desired outcome?
2. **Integrations**: Which external services (Slack, Shopify, etc.)? Are keys ready?
3. **Source of Truth**: Where does primary data live?
4. **Delivery Payload**: How and where should final result be delivered?
5. **Behavioral Rules**: How should the system "act"? (Tone, logic constraints, "Do Not" rules)

### Before Writing Tools

Before creating any Python scripts in `tools/`:

- [ ] Discovery Questions are answered
- [ ] Data Schema is defined in `gemini.md`
- [ ] `task_plan.md` has an approved Blueprint

---

## Testing Strategy

- **Unit Testing**: Each tool in `tools/` should be atomic and testable individually
- **Integration Testing**: Verify API connections in Link phase before full implementation
- **Handshake Testing**: Build minimal scripts to verify external services respond correctly
- **Self-Healing**: When errors occur, follow the Repair Loop and update documentation

### Regression Gate (Mandatory After Code Changes)

After any code update that touches API routing, settings, generation logic, or provider connectivity:

1. Run automated regression suite:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q tests/test_regression_api.py tests/test_regression_units.py
```

2. Run manual smoke checks listed in `REGRESSION_TESTCASES.md`.
3. If any regression fails, fix the issue first, then rerun the full suite.
4. Record test result summary in `progress.md`.

---

## Security Considerations

1. **Environment Variables**: Store all API keys and secrets in `.env` file
2. **No Hardcoded Secrets**: Never commit credentials to version control
3. **Temporary Data**: Keep sensitive intermediate data in `.tmp/` and clean up regularly
4. **Credential Verification**: Always verify `.env` credentials during Link phase before proceeding

---

## Build and Deployment

### Local Development
- Create and test scripts in `tools/`
- Use `.tmp/` for all intermediate file operations
- Update `progress.md` after each task

### Cloud Transfer (Trigger Phase)
- Move finalized logic from local testing to production cloud environment
- Set up execution triggers (Cron jobs, Webhooks, Listeners)
- Finalize Maintenance Log in `gemini.md`

---

## Code Style Guidelines

### Python Scripts (`tools/`)
- Scripts must be **deterministic** - same input always produces same output
- Keep scripts **atomic** - each script does one thing well
- Scripts must be **testable** independently
- Store configuration in `.env`, not hardcoded
- Use `.tmp/` for file I/O operations

### Markdown Documentation (`architecture/`)
- Technical SOPs should define: goals, inputs, tool logic, edge cases
- Update SOPs BEFORE changing code when logic changes
- Use clear, structured formatting

---

## Important Notes

- This is a **framework/template repository**, not a runnable application
- The `BLAST.md` file is the master system prompt
- Projects built using this framework will create the actual code, configuration, and deployment artifacts
- Always refer to `gemini.md` as the single source of truth for project state

---

## Repository Addendum (TestGen AI)

This workspace now includes production-facing implementation artifacts in addition to framework docs.

### Review Workflow Components

- Backend router: `backend/app/routers/review.py`
- Backend service: `backend/app/services/review_service.py`
- Frontend review UI: `frontend/src/components/ReviewSection.tsx`, `frontend/src/components/ReviewOutput.tsx`
- Frontend page integration: `frontend/src/pages/HomePage.tsx`

### Clarification Behavior (Implemented)

- Multi-round clarification with history tracking
- Smart default questions (BDD strictness, Excel Test ID column, URL freshness, multi-source version alignment)
- Instruction-aware clarification prompts (custom instruction mismatches now generate explicit clarification prompts)
- Previously answered clarification prompts are filtered out across rounds (history-driven de-dup)
- Clarification attachment uploads
- Timeout fallback on status polling (best-effort assumptions after 30 minutes)

### Review Mode + Instruction Impact (Implemented)

- Review outputs now expose explicit mode in summary:
   - `template_guided`
   - `instruction_only`
- Template-guided mode loads repository review skills as checklist signals:
   - `skill-prompt-userguide-review.md`
   - `skill-prompt-testcase-review.md`
- Custom instructions now produce measurable impact in review payload:
   - `instruction_influence_count`
   - `instruction_checks` (`matched` / `missing`)

### Multi-Source Input Behavior (Implemented)

- Generation and review support both legacy single IDs and list-based IDs:
   - `jira_id` + `jira_ids`
   - `valueedge_id` + `valueedge_ids`
- Backend uses all unique provided IDs when assembling AI requirement context.
- Frontend `InputSection` supports fetch/add/remove flows for multiple Jira and ValueEdge items.

### Generation Quality/Provider Behavior (Implemented)

- Test case generation is BDD-first by default, with explicit non-BDD opt-out respected.
- Template toggle precedence is enforced:
   - template disabled => custom prompt priority
   - template enabled => template+custom fusion
- Groq rate-limit handling preserves selected model on retries; bounded delayed retry is same-model only.
- User-friendly quota guidance is returned when retry is not feasible.

### Review Prompt Enhancement (Implemented)

- Review UI now includes `✨ Enhance` for **Review Custom Instructions** in `frontend/src/components/ReviewSection.tsx`
- Enhancement uses current UI AI settings (provider/model from `frontend/src/pages/HomePage.tsx`)
- Backend endpoint used: `POST /api/llm/enhance-prompt`

### Context-Aware Prompt Enhancement (Implemented)

- Enhance now supports section/subtype targeting:
   - `test_plan`
   - `test_case`
   - `review_test_cases`
   - `review_user_guide`
   - `review` (mixed fallback)
- Frontend passes context snapshots for enhancement quality:
   - generation: selected Jira/ValueEdge IDs, uploaded file snippets, template toggles
   - review: mode flags, guide URL, uploaded file snippets, source IDs
- Scope note:
   - enhancement context is intentionally compact (first 8 files + trimmed snippets), not full raw document bodies
- Backend uses context digest + quality guards:
   - explicit constraint retention (e.g., high-priority-only requests)
   - section-alignment checks to prevent drift
   - deterministic fallback rewrite if model output is misaligned

### Documentation Sync Rule

When review/generation/settings workflow logic changes, update all of the following together:

1. `README.md` (workflows + API/provider behavior)
2. `REGRESSION_TESTCASES.md` (test IDs / expectations)
3. `progress.md` (execution + verification summary)

### Verification Gate

After modifying review/generation/settings behavior, run:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q tests/test_regression_api.py tests/test_regression_units.py
```

And confirm frontend build:

```powershell
cd frontend
npm run build
```
