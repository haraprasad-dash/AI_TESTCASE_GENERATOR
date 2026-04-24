# TestGen AI — Intelligent Test Case Generator

> **AI-Powered Test Plan & Test Case Generation**  
> Transforms requirements into professional test artifacts in seconds.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Node](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-teal?logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [How to Use](#how-to-use)
7. [Review Workflows](#review-workflows)
8. [Input Sources](#input-sources)
9. [AI Configuration](#ai-configuration)
10. [Export Options](#export-options)
11. [Regression Suite](#regression-suite)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

---

## ⚡ Quick Start (TL;DR)

For teammates who already cloned the repo, use the same steps on every machine:

```powershell
# One-time setup
.\setup.ps1

# Terminal 1 — Backend
.\start-backend.ps1

# Terminal 2 — Frontend
.\start-frontend.ps1
```

Open **http://localhost:3000** in your browser.

Requirements:

- Add `GROQ_API_KEY=...` to `backend/.env`
- Keep `frontend/.env` as `VITE_API_URL=`

> **Windows Note:** Ports 8000 and 8080 are reserved by Windows `svchost`. Use backend port **7010**.  
> **Critical:** `frontend/.env` must have `VITE_API_URL=` (empty value) so all requests route through the Vite proxy.

---

## Overview

**TestGen AI** is a full-stack web application that uses Large Language Models to automatically generate:

- **Test Plans** — IEEE 829-style: scope, approach, environment, entry/exit criteria, risks
- **Test Cases** — Functional, negative, boundary value, edge case, and BDD-format test cases

### Supported Input Sources

| Source | Description |
|--------|-------------|
| JIRA | Fetch ticket details by issue key (e.g. `PROJ-123`) |
| OpenText ValueEdge | Fetch work items by numeric ID |
| PDF Documents | Text extraction with OCR for scanned PDFs |
| Word / DOCX | Full text and table extraction |
| Images (PNG/JPG) | OCR-powered text recognition |

### 🎨 Vision & Multi-Modal Analysis (NEW)

| Capability | Description |
|------------|-------------|
| **Image Analysis** | Semantic understanding of UI screenshots, diagrams, charts |
| **PDF Image Extraction** | Extract and analyze images embedded in PDFs |
| **Multi-Modal Context** | Combines text, tables, and visual understanding for test generation |
| **UI-Aware Testing** | Test cases understand UI components from mockups |
| **Architecture Understanding** | System diagrams analyzed for integration testing |
| **Data Visualization** | Charts analyzed for test data and thresholds |

#### Vision Providers (auto-detected)

| Provider | Tier | Model | Requirement |
|----------|------|-------|-------------|
| **Groq Cloud** | FREE ⭐ | Llama 4 Scout 17B | `GROQ_API_KEY` (reuses existing key) |
| **Ollama** | FREE | LLaVA, Gemma 3, Llama 3.2 Vision | Ollama running + `ollama pull llava` |
| **Claude Vision** | Paid | Claude 3.5 Sonnet | `ANTHROPIC_API_KEY` |
| **GPT-4 Vision** | Paid | GPT-4V | `OPENAI_API_KEY` |

Auto-detect priority: Groq → Ollama → Claude → GPT-4V → OCR fallback.
Override with `VISION_PROVIDER=groq|ollama|claude|gpt4` in `.env`.

> **See:** [VISION_QUICKSTART.md](VISION_QUICKSTART.md) for setup instructions

### LLM Providers

| Provider | Mode | Notes |
|----------|------|-------|
| **Groq Cloud** | Cloud | Fast inference — Llama 3.3, Mixtral, etc. Requires API key |
| **Ollama** | Local | Private, offline. No API key. Requires local install |

#### Supported Groq Models (Active)

| Model | Recommended For |
|-------|----------------|
| `llama-3.3-70b-versatile` | Best quality — highest reasoning capability |
| `openai/gpt-oss-120b` | Fast, low token budget |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Vision + generation tasks |

> **Decommissioned (do not use):** `mixtral-8x7b-32768`, `llama-3.1-70b-versatile`, `llama-3.1-8b-instant` — these are no longer available on Groq. The app automatically filters them from fallback chains.

#### Advanced Generation Behavior

| Behavior | Detail |
|----------|--------|
| **Advanced sampling** | `top_p=0.9`, `frequency_penalty=0.0`, `presence_penalty=0.0` sent to Groq by default. Pass custom values in `GenerationConfiguration`. |
| **Sectioned generation** | When initial test-case output is thin (weak coverage or low count), the system automatically makes 3 focused API calls (positive/negative, edge/boundary, security/performance) and merges the results. |
| **Zero-shot mode** | Requests with no custom prompt always return best-effort artifacts directly — never blocked by the clarification flow. |
| **Legacy `.env` keys** | `extra="ignore"` in Settings allows older `.env` keys (e.g. `export_default_format`) without crashing the config layer. |
| **Ollama model selection** | No Ollama model is hardcoded. Runtime model comes from user-selected model in UI or `OLLAMA_DEFAULT_MODEL` when explicitly configured. |
| **Ollama resilience fallback** | On Ollama `LLMError`, the service returns deterministic artifacts instead of failing. Fallback BDD suite now includes **28 scenarios** (previously 12) across positive, negative, edge, boundary, security, and performance categories. |
| **Ollama timeout budget** | Ollama HTTP timeout is increased to **300s** for both standard and streaming generation paths to reduce first-load timeout failures for larger local models. |
| **Fallback diagnostics** | When fallback is triggered, backend logs a provider-scoped warning with the underlying `LLMError` message for root-cause tracing. |

---

## Features

| Feature | Description |
|---------|-------------|
| Multi-Source Input | Combine JIRA, ValueEdge, and document uploads in one generation |
| Multi-Ticket Support | Add and fetch multiple JIRA and ValueEdge IDs in a single run |
| Fetch & Validate | Fetch button validates ticket/item IDs before generation |
| AI-Powered Generation | LLM-driven extraction and structuring of test scenarios |
| BDD-First Test Cases | Default test-case output is Gherkin-style BDD unless explicitly opted out |
| Clarification Workflow | UI asks follow-up questions when clarification is required before final case output |
| Review Workflows | Dedicated Test Case Review and User Guide Review modes with intelligent clarification |
| Context-Aware Prompt Enhancement | `✨ Enhance` uses selected section context (IDs/files/toggles/review mode) via a compact context digest to produce practical prompts |
| Refresh Output | Re-generate without re-entering inputs using the Refresh button |
| Multiple Export Formats | Markdown, PDF, Excel (styled), JSON, Gherkin (.feature) |
| BDD-Ready Gherkin | Properly formatted Given/When/Then scenarios from table data |
| Secure Key Storage | API keys stored in `.env`, never in source code |
| Ollama Private Mode | 100% local — no data leaves your machine |

---

## System Requirements

### Prerequisites

| Component | Version | Required |
|-----------|---------|----------|
| Python | 3.9+ | ✅ Required |
| Node.js | 18+ | ✅ Required |
| Tesseract OCR | 4.0+ | For image/scanned-PDF OCR |
| Poppler | Any | For PDF-to-image conversion |
| Ollama | Latest | Only for local LLM mode |
| Docker Desktop | Latest | Only for Docker deployment |

### Installing Optional Tools (Windows via Scoop)

```powershell
# Install Scoop (if not installed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Install Tesseract OCR
scoop install tesseract

# Install Poppler
scoop install poppler
```

The backend auto-detects Scoop-installed paths — no manual configuration needed.

---

## Installation

### Local Development Setup

### Team Setup On A New Machine

If you already cloned the repo, the fastest path is:

```powershell
.\setup.ps1
```

Then create `backend/.env` with your team credentials and start the app with:

```powershell
.\start-backend.ps1
.\start-frontend.ps1
```

### Manual Setup Details

#### 1. Clone the Repository

```bash
git clone https://github.com/haraprasad-dash/AI_TESTCASE_GENERATOR.git
cd AI_TESTCASE_GENERATOR
```

#### 2. One-Time Setup

```powershell
.\setup.ps1
```

This script:

- Creates the root `.venv` if it does not exist
- Installs backend Python dependencies from `backend/requirements.txt`
- Installs frontend npm dependencies
- Creates `frontend/.env` with `VITE_API_URL=` if it is missing

#### 3. Configure Environment Variables

Create `backend/.env`:

```env
# Groq Cloud (required for cloud mode)
GROQ_API_KEY=gsk_your_key_here

# JIRA Integration (optional)
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_token_here

# ValueEdge Integration (optional)
VALUEEDGE_BASE_URL=https://valueedge.yourcompany.com
VALUEEDGE_CLIENT_ID=your_client_id
VALUEEDGE_CLIENT_SECRET=your_client_secret

```

Create `frontend/.env`:

```env
VITE_API_URL=
```

> ⚠️ **`VITE_API_URL` must be empty.** Setting it to any URL (e.g. `http://localhost:5000`) bypasses the Vite proxy and breaks all API calls.

#### 4. Start the Application

```powershell
# Terminal 1 — Backend
.\start-backend.ps1

# Terminal 2 — Frontend
.\start-frontend.ps1
```

#### 5. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:7010 |
| Swagger UI | http://localhost:7010/docs |
| Health Check | http://localhost:7010/api/health |

---

### Docker Deployment

> ⚠️ Docker Desktop daemon must be running.

#### 1. Create root `.env` file

```env
GROQ_API_KEY=gsk_your_key_here
JIRA_BASE_URL=
JIRA_USERNAME=
JIRA_API_TOKEN=
VALUEEDGE_BASE_URL=
VALUEEDGE_CLIENT_ID=
VALUEEDGE_CLIENT_SECRET=
```

#### 2. Build and Run

```bash
docker-compose up --build
```

#### 3. Stop

```bash
docker-compose down
```

---

## Configuration

### Groq API Key

1. Visit [https://console.groq.com/keys](https://console.groq.com/keys)
2. Create an API key
3. Add to `backend/.env`:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```
4. Restart the backend (env changes require restart — `lru_cache` caches settings on first load)

### JIRA Integration

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new token
3. Add to `backend/.env`:
   ```env
   JIRA_BASE_URL=https://yourcompany.atlassian.net
   JIRA_USERNAME=your-email@company.com    # Must be full email address
   JIRA_API_TOKEN=your_token_here
   ```
4. Use the **Fetch** button in the UI to validate any ticket ID before generating

### ValueEdge Integration

Contact your ValueEdge administrator for credentials:

```env
VALUEEDGE_BASE_URL=https://valueedge.yourcompany.com
VALUEEDGE_CLIENT_ID=your_client_id
VALUEEDGE_CLIENT_SECRET=your_client_secret
VALUEEDGE_SHARED_SPACE_ID=your_space_id    # optional
```

### Ollama (Local LLM)

```bash
# Install from https://ollama.com
ollama pull llama3.2        # lightweight, fast
ollama pull codellama       # code-focused
ollama serve
```

Default URL: `http://localhost:11434` — no API key needed.

---

## How to Use

### Step-by-Step

#### 1. Provide Input

Choose one or more sources:

- **JIRA ID** — Enter ticket key (e.g. `PROJ-123`), click **Fetch** to validate
- **ValueEdge ID** — Enter numeric item ID, click **Fetch** to validate
- **Attach Requirement Details** — Drag & drop PDF, DOCX, XLSX, TXT, FEATURE, MD, PNG, or JPG files (max 20MB each)
- **Combine** — Use multiple sources for richer context

#### 2. Configure AI

| Setting | Recommendation |
|---------|---------------|
| **Provider** | Groq (fast) or Ollama (private) |
| **Model** | `llama-3.3-70b-versatile` for best quality |
| **Temperature** | `0.2` for formal docs, `0.5` for brainstorming |
| **Advanced params** | `top_p`, `frequency_penalty`, `presence_penalty` available in `GenerationConfiguration` |

Click **Test Connection** to verify your AI config before generating.

#### 3. Add Custom Prompt (Optional)

```
"Focus on security and authentication edge cases."
"Generate BDD-format test cases for the payment module."
"Include boundary value analysis and negative scenarios."
```

#### 4. Generate

Click **Generate Test Plan & Cases**.

#### 5. Review Output

Use the tab selector to switch between:
- **Both** — Full output (test plan + test cases)
- **Test Plan** — IEEE 829 structured document
- **Test Cases** — Detailed test case table

Click **Refresh** to regenerate with the same inputs.

#### 6. Export

| Format | Best For |
|--------|----------|
| Markdown | Version control, editing |
| PDF | Stakeholder sharing, printing |
| Excel | Test management tools (JIRA, TestRail) — clean, no markdown artifacts |
| JSON | API integration, automation |
| Gherkin | BDD frameworks (Cucumber, Behave, SpecFlow) |

---

## Review Workflows

Use these when you need quality/completeness assessment of existing artifacts, not fresh generation.

### Available Actions

- **Review Test Cases** — analyzes coverage, quality, gaps, and duplicates
- **Review User Guide** — verifies documentation accuracy/completeness against requirements/test artifacts
- **Run Both Reviews** — executes both analyses in one request
- **Enhance Review Instructions** — rewrites the optional review custom instructions for stronger clarity and coverage before running review

### Review Custom Instructions Enhancer

- Located under the per-mode review instruction fields in the Review section
- Uses the same AI configuration selected in UI (provider + model)
- Calls `POST /api/llm/enhance-prompt` and replaces the textarea content with the enhanced version
- Disabled when instructions are empty; shows loading state while enhancement is in progress

### Review Instruction Fields

- **Test Case Review Section** has its own mode toggle, instructions field, and file attachment area
- **User Guide Review Section** has its own mode toggle, instructions field, and dedicated user-guide document attachment area
- **Test Case Review** requires attached test case files
- **User Guide Review** requires attached user guide documents (`.pdf`, `.docx`, `.txt`, `.md`)
- **User Guide Review** supports attaching multiple guide files in one run
- **Template Enabled vs Disabled behavior is now explicit**:
   - Template enabled (`review_* = true`) => template-guided checklist review using system review skill prompts
   - Template disabled + instructions => instruction-only review mode
   - Output now shows current mode in Review Results (`template_guided` / `instruction_only`)

### Context-Aware Enhance (Plan / Case / Review)

- Enhance is section-aware and context-aware:
   - **Test Plan Prompt Enhance** uses generation context (`jira_ids`, `valueedge_ids`, uploaded file snippets, template toggle state)
   - **Test Case Prompt Enhance** uses the same generation context but applies testcase-focused enhancement rules
   - **Per-mode Review Enhance** uses fixed subtype targeting for test-case or user-guide review fields
- Context scope note (important):
   - enhance uses a **compact context digest**, not full raw payload text
   - only the first 8 attachments are passed for enhance context
   - attachment content is snippet-based (trimmed), then compacted again server-side for token safety
- Backend applies quality guards:
   - preserves explicit user constraints (e.g., high-priority-only scope)
   - prevents section drift (e.g., testcase checklist returned for test-plan enhancement)
   - applies deterministic fallback rewrite when model output is misaligned
- API contract:
   - endpoint: `POST /api/llm/enhance-prompt`
   - request fields: `prompt`, `provider`, `model`, `prompt_type`, `context`

### Review Clarification UX

- Partial results are shown while clarification is pending
- Clarification questions are scoped to the selected review mode, so user-guide review does not ask test-case-only questions
- Clarification templates are available for quick responses
- Clarification history is preserved and editable across rounds
- Previously answered clarification questions are not repeated in the next round
- Additional files can be attached during clarification
- Max clarification rounds: 3 (then best-effort assumptions are applied)
- Completed reports include a **Clarification Applied** summary so final output explicitly reflects submitted clarification answers
- **Refresh Status** now returns user feedback (current status or actionable error when session is missing)

### User Guide Review Quality Signals

- User-guide review analyzes uploaded guide documents and testcase-derived focus terms
- Multi-file guide uploads are supported and merged as review context
- If attached guide documents are unreadable/empty after parsing, review reports a **Source Access Gap** instead of producing misleading coverage results
- In Source Access Gap cases, attach readable guide artifacts (`.pdf`, `.docx`, `.md`, `.txt`) and rerun to unlock full traceability/coverage analysis
- Section-scoped reading is supported from instructions: if user asks to review specific section(s) only, review is constrained to those sections
- Customer-facing filtering is enforced for testcase-guided guide review: negative/edge/exploratory/performance scenarios are excluded from coverage analysis
- For testcase-guided review (e.g., `Agent interface header text color`), missing-topic findings include targeted gaps such as default color behavior, validation rules, color picker behavior, and upgrade compatibility notes
- Review output now includes a structured summary dashboard (grade, quality score, missing/modification counts) instead of plain raw text only
- User-guide report output now uses fixed sections for consistency: properly documented features, coverage gaps, clarity issues, defect log, and severity-prioritized actions
- User-guide report now starts with a deterministic gap-analysis preface (`Status | Meaning | Customer Impact`) and includes a recommended documentation structure checklist with key customer questions
- User-guide review output now maps findings to testcase-level references (`TC-xxx`) across all three buckets: matching, missing, and needs-modification
- Needs-modification items now include exact guide line reference, current text, required change, and example corrected wording
- For modification findings, review now reports **line-level pointers** (e.g., `L12`) with current text and suggested rewrite guidance
- Ambiguous phrases (e.g., `TBD`, `etc`, `as needed`) are flagged as high-priority rewrite items with deterministic correction guidance
- When template mode is enabled, additional mandatory checklist gaps are evaluated from repository skills (`skill-prompt-userguide-review.md`, `skill-prompt-testcase-review.md`)
- For detailed user-guide instruction prompts, clarification questions are kept non-blocking so review can complete in one pass

### Review Endpoints

- `POST /api/review/test-cases`
- `POST /api/review/user-guide`
- `POST /api/review/both`
- `GET /api/review/{review_id}/status`
- `POST /api/review/clarification/{review_id}/attach`
- `POST /api/review/{review_id}/export`

---

## Input Sources

### JIRA

**Format:** `PROJECT-123` (project key dash number)

**Multi-ID:** Fetch and retain multiple JIRA IDs in the input panel; all selected tickets are included in AI context.

**Data Extracted:** Summary, description, issue type, priority, labels, status, assignee

### ValueEdge

**Format:** Numeric ID (e.g. `12345`)

**Multi-ID:** Fetch and retain multiple ValueEdge IDs; all selected items are included in AI context.

**Data Extracted:** Item name, description, type, phase, story points

### Document Upload

| Format | Extension | Processing |
|--------|-----------|-----------|
| PDF | .pdf | Direct text extraction; OCR fallback for scanned |
| Word | .docx | Text and table extraction |
| Excel | .xlsx/.xls | Sheet flattening for review/test artifact analysis |
| Text/Markdown/Feature | .txt/.md/.feature | Direct text extraction |
| PNG | .png | Tesseract OCR |
| JPG/JPEG | .jpg | Tesseract OCR |

Max file size: 20MB per file. Max 5 files per generation.

`.feature` uploads are accepted by extension, including Windows/browser combinations that report them as generic text or octet-stream files.

---

## AI Configuration

### Temperature Guide

| Temperature | Use Case |
|-------------|----------|
| `0.0` | Deterministic — identical output each run |
| `0.2` | Balanced — recommended for formal documentation |
| `0.5` | Moderate variation — good for brainstorming |
| `0.7+` | Creative — exploratory/edge case generation |

### Groq Recommended Models

The model list in UI is loaded dynamically from Groq live availability and known decommissioned model IDs are filtered.

| Model | Speed | Quality |
|-------|-------|---------|
| `llama-3.3-70b-versatile` | Medium | Best |
| `llama-3.1-8b-instant` | Fast | Good |
| `mixtral-8x7b-32768` | Medium | Good (long context) |
| `gemma2-9b-it` | Fast | Good |

### Groq Rate-Limit Behavior

- Generation now preserves your selected Groq model on rate-limit retries (no silent downgrade to another model).
- If token budget is temporarily constrained, backend uses bounded delayed backoff and retries with the same selected model.
- If remaining quota is too low to retry safely, generation fails with a user-friendly quota message.

### Ollama Models (Local)

```bash
ollama pull qwen2.5:14b-instruct   # recommended for testcase generation
ollama pull qwen2.5:32b-instruct   # higher quality, slower
ollama pull llama3.1               # fallback
```

Notes:
- The app does not force any Ollama model id.
- Choose an installed model from AI Configuration, or set `OLLAMA_DEFAULT_MODEL` in settings/.env.

### Vision Provider (Multi-Modal PDFs)

The **Vision Provider** is **independent** of the LLM Provider. Auto-detected priority: **Groq → Ollama → Claude → GPT-4V**.

| Setting | Purpose | Can Use With |
|---------|---------|--------------|
| **LLM Provider** (Groq/Ollama) | Test case generation | **Groq** ✅ or **Ollama** ✅ |
| **Vision Provider** (Groq/Ollama/Claude/GPT-4V) | Image analysis in PDFs | **Any LLM provider** ✅ |

**Example configurations:**
- ✅ Groq LLM + Groq Vision (fast generation + free image analysis) ← **Recommended FREE setup**
- ✅ Ollama LLM + Ollama Vision (fully local + private)
- ✅ Groq + Claude Vision (fast generation + premium images)
- ✅ Any LLM + No vision (text-only mode) ← **Works immediately**

**To use PDFs with images:**

```env
# Test generation (choose one)
GROQ_API_KEY=gsk_...                    # Also enables FREE Groq Vision!
OLLAMA_BASE_URL=http://localhost:11434  # Also enables FREE Ollama Vision (needs `ollama pull llava`)

# Optional paid vision (higher quality)
# ANTHROPIC_API_KEY=sk-ant-...          # Claude Vision
# OPENAI_API_KEY=sk-...                 # GPT-4 Vision

# Optional: force a specific vision provider
# VISION_PROVIDER=groq                  # groq | ollama | claude | gpt4
```

**What happens without any Vision provider:**
- ✅ PDFs still upload successfully
- ✅ Text extraction works (OCR on images)
- ✅ Test cases generate normally
- ℹ️ No semantic understanding of images (component recognition, layout analysis)
- 💡 Recommended: Set `GROQ_API_KEY` for free vision, or `ollama pull llava` for local vision

See [PROVIDER_INDEPENDENCE.md](PROVIDER_INDEPENDENCE.md) for detailed configuration matrix and [VISION_OPTIONAL_GUIDE.md](VISION_OPTIONAL_GUIDE.md) for fallback behavior and cost examples.

---

## Export Options

### Excel (.xlsx)

- Blue header row with white bold text
- Alternating row shading
- Cell borders and word-wrap
- Frozen header row (scroll-friendly)
- All markdown formatting stripped (no `**bold**` artifacts)

### Gherkin (.feature)

- Automatically detects `Given/When/Then` keywords in BDD steps column
- Scenario titles built from Feature + Description columns
- Fallback to Test ID or step snippet if description is empty
- Compatible with Cucumber, Behave, SpecFlow, pytest-bdd

### PDF (.pdf)

- Renders headings (H1–H4), tables, lists, blockquotes, code blocks
- Table headers: blue background with white text
- Alternating row shading in tables
- Page numbers in footer

---

## Regression Suite

Run this suite after any code change to prevent regressions in settings, LLM connection flow, and generation input validation.

### Automated Regression Command

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q tests/test_regression_api.py tests/test_regression_units.py
```

### What It Covers

- Empty vs valid generation input gating (including custom-instructions-only flow)
- Multi-ticket input detection and routing (`jira_ids` / `valueedge_ids`)
- BDD-first testcase generation with explicit non-BDD opt-out handling
- Template-toggle precedence and template+custom prompt fusion behavior
- Friendly error mapping for Groq rate-limit failures
- Groq same-model retry policy and rate-limit backoff parsing
- Secret normalization (`Bearer` prefix handling, masked placeholder preservation)
- LLM test-connection and model-list key handling
- Settings API secret masking and default-provider behavior
- Review API validation, clarification rounds, and status behavior
- Review smart-default clarification prompts and timeout fallback

### Release Gate Recommendation

Before merge/deploy:

1. Run the automated regression command above.
2. Execute manual smoke checks in `REGRESSION_TESTCASES.md`.
3. Fix any failing case and rerun until all pass.

---

## Troubleshooting

### "Cannot connect to backend"

1. Verify backend is running:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:7010/api/health" -UseBasicParsing
   ```
2. On Windows — ports 8000 and 8080 are reserved by the OS. Use port **7010**.
3. Check `frontend/.env` has `VITE_API_URL=` (empty).
4. Check `frontend/vite.config.ts` proxy target is `http://localhost:7010`.
5. Restart the Vite dev server after any `.env` changes.

### "GROQ_API_KEY not configured"

1. Check `backend/.env` contains `GROQ_API_KEY=gsk_...`
2. **Restart** the backend — env changes are cached at startup (`lru_cache`)
3. Get a key at https://console.groq.com/keys

### "Generation failed: Groq API key not provided"

The backend `generation_service.py` reads the key from settings — this requires a backend restart after adding/changing the key. Hot-reload does NOT refresh env settings.

### "JIRA authentication failed — 401"

1. `JIRA_USERNAME` must be your **full email address** (not just username)
2. Re-create the API token — tokens can expire
3. Ensure there are **no line breaks** inside the token value in `.env`

### "File upload failed"

- Max 20MB per file
- Supported formats: PDF, DOCX, XLSX, XLS, TXT, MD, FEATURE, PNG, JPG
- For OCR (images / scanned PDFs): Tesseract must be installed

### "No content extracted from file"

- For scanned PDFs: Tesseract OCR is used automatically (requires `tesseract` installed)
- For images: ensure text is clearly visible and not rotated
- Install Tesseract via Scoop: `scoop install tesseract`

### Debugging

```powershell
# Backend debug logs
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --log-level debug --host 127.0.0.1 --port 7010

# Test individual connections
python tools/test_groq_connection.py
python tools/test_ollama_connection.py
python tools/test_jira_connection.py
python tools/test_valueedge_connection.py
```

---

## Best Practices

### For Best Generation Quality

1. **Combine sources** — JIRA ticket + uploaded spec document gives the richest context
2. **Use custom prompts** to focus on specific areas (security, performance, etc.)
3. **Temperature 0.2** for formal test documentation; 0.5 for brainstorming
4. **Review AI output** before export — verify business logic, add org-specific standards

### Security

1. Never commit `backend/.env` or `frontend/.env` to version control
2. Rotate API keys regularly
3. Use Ollama local mode for sensitive/confidential requirements
4. Clean up the `uploads/` directory periodically

---

## Project Structure

```
AI_TESTCASE_GENERATOR/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Settings (reads from .env)
│   │   ├── models.py         # Pydantic data models
│   │   ├── routers/          # API route handlers
│   │   │   ├── generation.py # POST /api/generate
│   │   │   ├── export.py     # POST /api/export/{id}, GET /api/export/download/{file}
│   │   │   ├── jira.py       # JIRA integration endpoints
│   │   │   ├── valueedge.py  # ValueEdge integration endpoints
│   │   │   ├── documents.py  # File upload/delete
│   │   │   └── llm.py        # LLM test-connection, model listing
│   │   └── services/
│   │       ├── generation_service.py  # Orchestrates test generation
│   │       ├── llm_orchestrator.py    # Groq / Ollama abstraction
│   │       ├── export_service.py      # MD / PDF / Excel / JSON / Gherkin export
│   │       ├── document_parser.py     # PDF, DOCX, image text extraction
│   │       ├── jira_client.py         # JIRA REST API client
│   │       └── valueedge_client.py    # ValueEdge REST API client
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                  # ⚠️ Not committed — create manually
│
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── components/
│   │   │   ├── InputSection.tsx      # Multi-ticket JIRA/ValueEdge inputs + Fetch cards
│   │   │   ├── AIConfigSection.tsx   # Provider/model/temperature selector
│   │   │   ├── OutputPreview.tsx     # Markdown renderer + Export buttons + Refresh
│   │   │   ├── PromptSection.tsx     # Test plan/test case prompts + template toggles
│   │   │   ├── ReviewSection.tsx     # Review workflow controls
│   │   │   ├── ReviewOutput.tsx      # Review result/clarification panel
│   │   │   └── SettingsModal.tsx     # Settings overlay
│   │   ├── pages/HomePage.tsx        # Main page layout
│   │   ├── services/api.ts           # Axios API client
│   │   ├── store/settingsStore.ts    # Zustand state
│   │   └── types/index.ts            # TypeScript types
│   ├── vite.config.ts                # Proxy: /api -> localhost:7010
│   ├── package.json
│   ├── Dockerfile
│   └── .env                          # ⚠️ Must have VITE_API_URL= (empty)
│
├── architecture/             # Technical SOPs (BLAST framework)
├── tools/                    # Connection test scripts
├── templates/                # LLM prompt templates
├── docker-compose.yml
└── README.md
```

---

## Support

- API docs: http://localhost:7010/docs (when backend is running)
- Architecture docs: `architecture/` folder
- Connection tests: `tools/` folder

---

*Built with the [BLAST Protocol](BLAST.md) for reliable automation development.*
