# 🔍 Findings Log: TestGen AI Agent

> **Project:** Intelligent Test Plan & Test Case Creation Agent  
> **Created:** 2026-03-08  
> **Purpose:** Research, discoveries, constraints

---

## 📚 Research Notes

### External APIs to Integrate

#### JIRA REST API v3
- **Base URL:** `https://{instance}.atlassian.net/rest/api/3`
- **Auth:** Basic Auth with email + API Token
- **Key Endpoints:**
  - `GET /rest/api/3/issue/{issueIdOrKey}` - Fetch issue details
  - `GET /rest/api/3/issue/{id}/transitions` - Get transitions
  - `GET /rest/api/3/search?jql={query}` - Search issues

#### OpenText ValueEdge API
- **Auth:** OAuth 2.0 Client Credentials flow
- **Key Endpoints:**
  - `GET /api/shared_spaces/{space_id}/work_items/{item_id}`
  - Token expires ~1 hour, needs refresh mechanism

#### Groq.com API
- **Docs:** https://console.groq.com/docs
- **SDK:** `groq` Python package
- **Models:** llama-3.3-70b, llama-3.1-8b, mixtral-8x7b
- **Fast inference**, no local GPU required

#### Ollama API
- **Local LLM server**
- **Base URL:** `http://localhost:11434`
- **Endpoints:**
  - `POST /api/generate` - Generate text
  - `GET /api/tags` - List models
- **Privacy-focused**, works offline

### Document Processing Libraries

| Format | Library | Method |
|--------|---------|--------|
| PDF | PyPDF2 | Text extraction |
| PDF (scanned) | pytesseract | OCR fallback |
| DOCX | python-docx | Paragraph extraction |
| Images | Pillow + pytesseract | OCR |

---

## 💡 Discoveries

| Date | Discovery | Impact | Status |
|------|-----------|--------|--------|
| 2026-03-08 | Project uses 3-layer architecture (Presentation, Application, External APIs) | Guides our BLAST implementation | ✅ Confirmed |
| 2026-03-08 | Requires AES-256 encryption for API keys using machine UUID | Security implementation | 🔍 Needs research |
| 2026-03-08 | Supports both streaming and non-streaming LLM responses | WebSocket implementation needed | 🔍 Investigating |
| 2026-03-08 | File uploads limited to 20MB, temp storage only | Storage configuration | ✅ Confirmed |
| 2026-03-08 | Temperature 0.2 recommended for deterministic output | LLM configuration default | ✅ Confirmed |

---

## ⚠️ Constraints & Limitations

### Technical Constraints
1. **Python 3.9+** required for FastAPI/Pydantic v2
2. **Node.js 18+** required for frontend
3. **4GB RAM minimum** (8GB recommended)
4. **Tesseract OCR** must be installed system-wide for image processing
5. **Ollama** must be running locally for local mode

### API Limitations
1. **Groq rate limits** may require retry logic
2. **ValueEdge OAuth tokens** expire hourly
3. **JIRA API** has rate limits per account tier
4. **File size limit:** 20MB per file, max 5 files

### Security Constraints
1. API keys must be **encrypted at rest** (AES-256)
2. No credentials in **browser console/network logs**
3. All API calls with credentials **proxied through backend**
4. Uploaded files **deleted after processing**

---

## 🤔 Open Questions (Resolved)

All Discovery Questions answered from PRD:

1. ✅ **North Star:** Auto-generate test plans/test cases from JIRA/ValueEdge/docs
2. ✅ **Integrations:** JIRA, ValueEdge, Groq, Ollama - keys in settings
3. ✅ **Source of Truth:** JIRA tickets, ValueEdge items, uploaded files
4. ✅ **Delivery Payload:** Markdown, PDF, Excel, JSON, Gherkin exports
5. ✅ **Behavioral Rules:** Temperature 0.2, structured templates, no assumptions

---

## 🔗 Links & References

### Documentation
- [BLAST.md](./BLAST.md) - Master System Protocol
- [TEST_PLAN_AGENT_PRD.md](./TEST_PLAN_AGENT_PRD.md) - Full PRD
- [TEST_PLAN_AGENT_IMPLEMENTATION_CHECKLIST.md](./TEST_PLAN_AGENT_IMPLEMENTATION_CHECKLIST.md) - Implementation Guide
- [test_plan_generation.md](./test_plan_generation.md) - Test Plan Template
- [test_case_generation.md](./test_case_generation.md) - Test Case Template

### External Resources
- Groq API Docs: https://console.groq.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com/
- JIRA REST API: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Ollama Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
