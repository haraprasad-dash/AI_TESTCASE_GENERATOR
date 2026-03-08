# 📋 Task Plan: TestGen AI Agent

> **Project:** Intelligent Test Plan & Test Case Creation Agent  
> **Created:** 2026-03-08  
> **Protocol:** B.L.A.S.T.  
> **Estimated Duration:** 10 working days

---

## 🔴 Phase 0: Initialization [✅ COMPLETE]

- [x] Create `gemini.md` (Project Constitution)
- [x] Create `task_plan.md` (This file)
- [x] Create `findings.md` (Research log)
- [x] Create `progress.md` (Execution log)
- [x] Analyze PRD and Implementation Checklist
- [x] Answer 5 Discovery Questions
- [x] Define Data Schemas in `gemini.md`

---

## 🟡 Phase 1: B - Blueprint [✅ COMPLETE]

### Discovery Questions Answered (from PRD)

| # | Question | Answer |
|---|----------|--------|
| 1 | **North Star** | Build an Intelligent Test Plan & Test Case Creation Agent that uses LLMs to auto-generate test artifacts from JIRA/ValueEdge/docs |
| 2 | **Integrations** | JIRA REST API, OpenText ValueEdge API, Groq.com API, Ollama Local API. Keys needed: JIRA API Token, ValueEdge Client ID/Secret, Groq API Key |
| 3 | **Source of Truth** | JIRA tickets, ValueEdge work items, uploaded PDF/Word/Image files |
| 4 | **Delivery Payload** | Generated Test Plans and Test Cases in Markdown, PDF, Excel, JSON, Gherkin formats. Downloadable or copy-to-clipboard |
| 5 | **Behavioral Rules** | Temperature 0.2 for deterministic output, structured templates (IEEE 829), anti-hallucination rules, no assumptions on undocumented features |

### Data Schemas Defined
- [x] Configuration Schema (JIRA, ValueEdge, LLM, Templates, Export settings)
- [x] Generation Request Schema (inputs, files, configuration)
- [x] Generation Response Schema (test_plan, test_cases, metadata)
- [x] Export Format specifications

### Technology Stack Confirmed
| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| Document Processing | PyPDF2, python-docx, Pillow, pytesseract |
| LLM Integration | Groq SDK, Ollama REST API |
| Storage | SQLite (config), Local filesystem (uploads) |
| Export | markdown-pdf, pandas/openpyxl |

---

## 🟠 Phase 2: L - Link [IN PROGRESS]

### Connectivity Verification
- [ ] Create `.env.example` with all required variables
- [ ] Test Groq API connection
- [ ] Test Ollama connection (if available)
- [ ] Document connection test results

### Handshake Scripts
- [ ] Build `tools/test_groq_connection.py`
- [ ] Build `tools/test_ollama_connection.py`
- [ ] Build `tools/test_jira_connection.py`
- [ ] Build `tools/test_valueedge_connection.py`

---

## 🔵 Phase 3: A - Architect [PENDING]

### Layer 1: Architecture (SOPs in `architecture/`)
- [ ] `architecture/01_project_setup.md` - Project structure, dependencies
- [ ] `architecture/02_backend_core.md` - Config, models, database
- [ ] `architecture/03_jira_integration.md` - JIRA client, auth, endpoints
- [ ] `architecture/04_valueedge_integration.md` - ValueEdge client, OAuth
- [ ] `architecture/05_document_processing.md` - PDF, DOCX, Image parsing
- [ ] `architecture/06_llm_orchestration.md` - Groq/Ollama abstraction
- [ ] `architecture/07_generation_service.md` - Context assembly, prompts
- [ ] `architecture/08_frontend_structure.md` - React components, state
- [ ] `architecture/09_export_service.md` - PDF, Excel generation
- [ ] `architecture/10_error_handling.md` - Error codes, retry logic

### Layer 2: Navigation (Routing Logic)
- [ ] API endpoint routing table
- [ ] WebSocket event flow
- [ ] Input validation flow
- [ ] Generation orchestration flow

### Layer 3: Tools (`tools/`)
- [ ] `backend/app/main.py` - FastAPI entry point
- [ ] `backend/app/config.py` - Settings management
- [ ] `backend/app/models.py` - Pydantic schemas
- [ ] `backend/app/routers/jira.py` - JIRA endpoints
- [ ] `backend/app/routers/valueedge.py` - ValueEdge endpoints
- [ ] `backend/app/routers/documents.py` - File upload/processing
- [ ] `backend/app/routers/llm.py` - LLM integration
- [ ] `backend/app/routers/generation.py` - Main generation logic
- [ ] `backend/app/routers/settings.py` - Configuration endpoints
- [ ] `backend/app/services/jira_client.py` - JIRA API wrapper
- [ ] `backend/app/services/valueedge_client.py` - ValueEdge API wrapper
- [ ] `backend/app/services/document_parser.py` - PDF/DOCX/Image processing
- [ ] `backend/app/services/llm_orchestrator.py` - Groq/Ollama abstraction
- [ ] `backend/app/services/template_engine.py` - Template processing
- [ ] `backend/app/services/generation_service.py` - Generation orchestration
- [ ] `backend/app/utils/encryption.py` - API key encryption
- [ ] `backend/app/utils/validators.py` - Input validation
- [ ] `frontend/src/` - React frontend components

---

## 🟢 Phase 4: S - Stylize [PENDING]

### UI/UX Implementation
- [ ] Tailwind CSS theming
- [ ] Responsive layout (mobile/tablet/desktop)
- [ ] Loading skeletons and spinners
- [ ] Toast notifications (react-hot-toast)
- [ ] Markdown rendering with syntax highlighting
- [ ] File upload drag-and-drop with preview

### Output Refinement
- [ ] Professional Markdown formatting
- [ ] PDF export styling
- [ ] Excel export column formatting
- [ ] Copy-to-clipboard functionality

---

## 🟣 Phase 5: T - Trigger [PENDING]

### Docker Deployment
- [ ] `backend/Dockerfile`
- [ ] `frontend/Dockerfile`
- [ ] `docker-compose.yml`
- [ ] Environment variable configuration

### Documentation
- [ ] `README.md` with setup instructions
- [ ] API documentation (auto-generated from FastAPI)
- [ ] User guide with screenshots
- [ ] Troubleshooting guide

### Final Testing
- [ ] Fresh installation test
- [ ] Docker deployment test
- [ ] Cross-browser testing

---

## ✅ Completion Criteria

> A project is only "Complete" when the payload is in its final cloud destination.

- [x] All 5 BLAST phases completed
- [ ] Full-stack application running locally
- [ ] Docker deployment tested
- [ ] All integrations tested (JIRA, ValueEdge, Groq, Ollama)
- [ ] Export functionality working (MD, PDF, Excel)
- [ ] Documentation complete

---

## 📌 Project Structure (Target)

```
test-plan-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── utils/
│   ├── templates/
│   ├── data/
│   ├── uploads/
│   ├── outputs/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── architecture/
├── tools/
└── .env
```
