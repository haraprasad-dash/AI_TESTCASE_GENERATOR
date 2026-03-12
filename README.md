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

```powershell
# Terminal 1 — Backend (port 7010)
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 7010

# Terminal 2 — Frontend (port 3000)
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

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

### LLM Providers

| Provider | Mode | Notes |
|----------|------|-------|
| **Groq Cloud** | Cloud | Fast inference — Llama 3.3, Mixtral, etc. Requires API key |
| **Ollama** | Local | Private, offline. No API key. Requires local install |

---

## Features

| Feature | Description |
|---------|-------------|
| Multi-Source Input | Combine JIRA, ValueEdge, and document uploads in one generation |
| Fetch & Validate | Fetch button validates ticket/item IDs before generation |
| AI-Powered Generation | LLM-driven extraction and structuring of test scenarios |
| Clarification Workflow | UI asks follow-up questions when clarification is required before final case output |
| Review Workflows | Dedicated Test Case Review and User Guide Review modes with intelligent clarification |
| Review Prompt Enhancement | `✨ Enhance` button improves Review Custom Instructions using selected provider/model |
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

#### 1. Clone the Repository

```bash
git clone https://github.com/haraprasad-dash/AI_TESTCASE_GENERATOR.git
cd AI_TESTCASE_GENERATOR
```

#### 2. Backend Setup

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

#### 4. Configure Environment Variables

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

#### 5. Start the Application

```powershell
# Terminal 1 — Backend
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 7010

# Terminal 2 — Frontend
cd frontend
npm run dev
```

#### 6. Access the Application

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

- Located under **Review Custom Instructions (optional)** in the Review section
- Uses the same AI configuration selected in UI (provider + model)
- Calls `POST /api/llm/enhance-prompt` and replaces the textarea content with the enhanced version
- Disabled when instructions are empty; shows loading state while enhancement is in progress

### Review Clarification UX

- Partial results are shown while clarification is pending
- Clarification templates are available for quick responses
- Clarification history is preserved and editable across rounds
- Additional files can be attached during clarification
- Max clarification rounds: 3 (then best-effort assumptions are applied)

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

**Data Extracted:** Summary, description, issue type, priority, labels, status, assignee

### ValueEdge

**Format:** Numeric ID (e.g. `12345`)

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

### Ollama Models (Local)

```bash
ollama pull llama3.2        # 3B — fast, lightweight
ollama pull codellama       # code/test-focused
ollama pull llama3.1        # 8B — better quality
```

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
- Friendly error mapping for Groq rate-limit failures
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
│   │   │   ├── InputSection.tsx      # JIRA/ValueEdge inputs + Fetch buttons
│   │   │   ├── AIConfigSection.tsx   # Provider/model/temperature selector
│   │   │   ├── OutputPreview.tsx     # Markdown renderer + Export buttons + Refresh
│   │   │   ├── PromptSection.tsx     # Custom prompt textarea
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
