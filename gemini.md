# 🏛️ Project Constitution: Gemini.md

> **Project:** Intelligent Test Plan & Test Case Creation Agent  
> **Status:** Phase 5 - Complete ✅  
> **Last Updated:** 2026-03-08  
> **System Pilot:** Active

---

## 📋 Project Overview

| Field | Value |
|-------|-------|
| **Project Name** | TestGen AI Agent |
| **North Star** | Build a modern web application that leverages LLMs to automatically generate comprehensive test plans and detailed test cases from multiple input sources (JIRA, ValueEdge, PDF/Word/Screenshots) |
| **Status** | ✅ Phase 5 - Trigger Complete |
| **Deployment Modes** | ☁️ Cloud (Groq), 🏠 Local (Ollama), 🔀 Hybrid |

---

## 🗂️ Data Schemas

### Configuration Schema (Input)
```json
{
  "jira": {
    "enabled": true,
    "base_url": "https://company.atlassian.net",
    "username": "user@company.com",
    "api_token": "encrypted_token",
    "default_project": "PROJ"
  },
  "valueedge": {
    "enabled": false,
    "base_url": "https://valueedge.company.com",
    "client_id": "client_id",
    "client_secret": "encrypted_secret",
    "shared_space_id": 1001
  },
  "llm": {
    "default_provider": "groq",
    "groq": {
      "api_key": "encrypted_key",
      "default_model": "llama-3.3-70b-versatile",
      "default_temperature": 0.2
    },
    "ollama": {
      "base_url": "http://localhost:11434",
      "default_model": "llama3.1"
    }
  },
  "templates": {
    "test_plan_path": "./templates/test_plan_generation.md",
    "test_case_path": "./templates/test_case_generation.md"
  },
  "export": {
    "default_format": "markdown",
    "auto_save": true,
    "output_directory": "./outputs"
  }
}
```

### Generation Request Schema (Input)
```json
{
  "request_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "inputs": {
    "jira_id": "PROJ-123",
    "valueedge_id": null,
    "files": [
      {
        "filename": "requirements.pdf",
        "path": "/uploads/temp/requirements.pdf",
        "extracted_text": "..."
      }
    ],
    "custom_prompt": "Focus on security testing..."
  },
  "configuration": {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.2,
    "max_tokens": 4096
  }
}
```

### Generation Response Schema (Output/Payload)
```json
{
  "request_id": "uuid",
  "status": "completed",
  "timestamp": "2024-01-15T10:31:30Z",
  "outputs": {
    "test_plan": {
      "content": "# Test Plan...",
      "format": "markdown",
      "token_usage": 2500,
      "generation_time_ms": 45000
    },
    "test_cases": {
      "content": "## Test Cases...",
      "format": "markdown",
      "count": 15,
      "token_usage": 3500,
      "generation_time_ms": 60000
    }
  },
  "metadata": {
    "model_used": "llama-3.3-70b-versatile",
    "temperature": 0.2,
    "total_tokens": 6000,
    "sources": ["jira", "pdf"]
  }
}
```

### Export Formats (Output Variants)
| Format | Extension | Library | Use Case |
|--------|-----------|---------|----------|
| Markdown | .md | Native | Version control, editing |
| PDF | .pdf | markdown-pdf/weasyprint | Sharing, documentation |
| Excel | .xlsx | pandas/openpyxl | Test management tools |
| JSON | .json | Native | Integration with other tools |
| Gherkin | .feature | Native | BDD framework import |

---

## 📐 Architectural Invariants

> These are the non-negotiable rules that govern the system.

1. **Data-First Rule:** No code is written until the Payload shape is confirmed.
2. **Self-Annealing:** All errors are analyzed, patched, tested, and documented.
3. **Layer Separation:** Architecture (SOPs) → Navigation (Logic) → Tools (Scripts)
4. **Security-First:** API keys encrypted with AES-256, never exposed client-side
5. **Provider Abstraction:** LLM orchestrator must support Groq and Ollama interchangeably
6. **Template-Driven:** All outputs use customizable markdown templates

---

## 🚫 Behavioral Constraints

> "Do Not" rules and system behavior guidelines.

- **Do Not** store API keys in plaintext
- **Do Not** make client-side API calls with credentials
- **Do Not** allow file uploads larger than 20MB
- **Do Not** assume undocumented behavior in LLM outputs
- **Do Not** proceed with generation if no input sources provided
- **Do Not** retain uploaded files after processing (temp only)
- **Do Not** expose stack traces in user-facing errors
- **Do Not** hardcode default credentials

---

## 🔧 Maintenance Log

| Date | Phase | Change | Reason |
|------|-------|--------|--------|
| 2026-03-08 | 0 | Project initialized | BLAST protocol initiated |
| 2026-03-08 | 1 | Discovery completed | PRD and Checklist analyzed |
| 2026-03-08 | 1 | Data schemas defined | Configuration, Request, Response schemas confirmed |
| 2026-03-08 | 2 | Link phase complete | Connection test scripts created |
| 2026-03-08 | 3 | Architecture SOPs created | 10 SOPs covering all system aspects |
| 2026-03-08 | 3 | Backend implementation complete | FastAPI + services + routers |
| 2026-03-08 | 3 | Frontend implementation complete | React + TypeScript + Tailwind |
| 2026-03-08 | 4 | UI/UX complete | All components styled and responsive |
| 2026-03-08 | 5 | Docker deployment ready | Dockerfile and docker-compose.yml |
| 2026-03-08 | 5 | Documentation complete | README.md with full instructions |

---

## 📎 External References

- **BLAST.md** - Master System Protocol
- **task_plan.md** - Project phases and checklists
- **findings.md** - Research and discoveries
- **progress.md** - Execution history
- **TEST_PLAN_AGENT_PRD.md** - Full Product Requirements Document
- **TEST_PLAN_AGENT_IMPLEMENTATION_CHECKLIST.md** - Implementation checklist
- **README.md** - User documentation

---

## ✅ Project Completion Status

| Phase | Status |
|-------|--------|
| Phase 0: Initialization | ✅ Complete |
| Phase 1: Blueprint | ✅ Complete |
| Phase 2: Link | ✅ Complete |
| Phase 3: Architect | ✅ Complete |
| Phase 4: Stylize | ✅ Complete |
| Phase 5: Trigger | ✅ Complete |

**All BLAST phases completed successfully!**
