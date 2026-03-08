# Test Plan Agent - Implementation Checklist

## Quick Reference for Developers

---

## ✅ Phase 1: Project Setup (Day 1)

### 1.1 Initialize Project Structure
```
test-plan-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Settings management
│   │   ├── models.py               # Pydantic schemas
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── jira.py             # JIRA endpoints
│   │       ├── valueedge.py        # ValueEdge endpoints
│   │       ├── documents.py        # File upload/processing
│   │       ├── llm.py              # LLM integration
│   │       ├── generation.py       # Main generation logic
│   │       └── settings.py         # Configuration endpoints
│   │   ├── services/
│   │       ├── __init__.py
│   │       ├── jira_client.py      # JIRA API wrapper
│   │       ├── valueedge_client.py # ValueEdge API wrapper
│   │       ├── document_parser.py  # PDF/DOCX/Image processing
│   │       ├── llm_orchestrator.py # Groq/Ollama abstraction
│   │       └── template_engine.py  # Template processing
│   │   └── utils/
│   │       ├── encryption.py       # API key encryption
│   │       └── validators.py       # Input validation
│   ├── templates/
│   │   ├── test_plan_generation.md
│   │   └── test_case_generation.md
│   ├── data/
│   │   └── settings.db             # SQLite database
│   ├── uploads/                    # Temp file storage
│   ├── outputs/                    # Generated files
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── InputSection.tsx
│   │   │   ├── AIConfigSection.tsx
│   │   │   ├── PromptSection.tsx
│   │   │   ├── OutputPreview.tsx
│   │   │   └── SettingsModal.tsx
│   │   ├── pages/
│   │   │   └── HomePage.tsx
│   │   ├── services/
│   │   │   └── api.ts              # API client
│   │   ├── store/
│   │   │   └── settingsStore.ts    # State management
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
└── docker-compose.yml
```

### 1.2 Backend Dependencies (`requirements.txt`)
```txt
# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
websockets>=12.0

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Document Processing
pypdf2>=3.0.0
python-docx>=1.1.0
pillow>=10.1.0
pytesseract>=0.3.10
pdf2image>=1.16.3

# AI/LLM Integration
groq>=0.4.0
httpx>=0.25.0
aiohttp>=3.9.0

# Database
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# Security
cryptography>=41.0.0

# Utilities
python-dotenv>=1.0.0
jinja2>=3.1.0
pandas>=2.1.0
openpyxl>=3.1.0
markdown>=3.5.0
markdown-pdf>=0.1.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
```

### 1.3 Frontend Dependencies (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.48.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "react-dropzone": "^14.2.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.294.0",
    "clsx": "^2.0.0",
    "react-hot-toast": "^2.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

---

## ✅ Phase 2: Backend Implementation (Days 2-4)

### 2.1 Core Configuration (`app/config.py`)
- [ ] Create Pydantic settings model
- [ ] Load from environment variables
- [ ] SQLite database initialization
- [ ] Encryption key generation from machine UUID

### 2.2 Database Models (`app/models.py`)
- [ ] Settings table schema
- [ ] Generation history table
- [ ] Pydantic request/response models

### 2.3 JIRA Client (`app/services/jira_client.py`)
- [ ] Basic authentication with API token
- [ ] Fetch issue details endpoint
- [ ] Error handling for auth failures
- [ ] Connection test method

### 2.4 ValueEdge Client (`app/services/valueedge_client.py`)
- [ ] OAuth 2.0 client credentials flow
- [ ] Token refresh mechanism
- [ ] Fetch work item details
- [ ] Connection test method

### 2.5 Document Parser (`app/services/document_parser.py`)
- [ ] PDF text extraction (PyPDF2)
- [ ] PDF OCR fallback (pytesseract)
- [ ] DOCX text extraction
- [ ] Image OCR processing
- [ ] File validation (type, size)

### 2.6 LLM Orchestrator (`app/services/llm_orchestrator.py`)
- [ ] Base provider interface
- [ ] Groq provider implementation
- [ ] Ollama provider implementation
- [ ] Model listing for Ollama
- [ ] Connection test for both providers
- [ ] Retry logic with exponential backoff

### 2.7 Template Engine (`app/services/template_engine.py`)
- [ ] Load template from file
- [ ] Replace placeholders
- [ ] Default template fallbacks

### 2.8 Generation Service (`app/services/generation_service.py`)
- [ ] Assemble context from all sources
- [ ] Build LLM prompts
- [ ] Stream response handling
- [ ] Token usage tracking
- [ ] Progress reporting via WebSocket

### 2.9 API Routers
- [ ] `jira.py` - `/api/jira/*` endpoints
- [ ] `valueedge.py` - `/api/valueedge/*` endpoints
- [ ] `documents.py` - `/api/documents/*` endpoints
- [ ] `llm.py` - `/api/llm/*` endpoints
- [ ] `generation.py` - `/api/generate` endpoints
- [ ] `settings.py` - `/api/settings` endpoints

### 2.10 WebSocket Implementation
- [ ] Connection manager
- [ ] Generation progress events
- [ ] Error broadcasting

---

## ✅ Phase 3: Frontend Implementation (Days 5-7)

### 3.1 Project Setup
- [ ] Initialize Vite + React + TypeScript
- [ ] Configure Tailwind CSS
- [ ] Setup folder structure
- [ ] Install dependencies

### 3.2 API Client (`services/api.ts`)
- [ ] Axios instance with base URL
- [ ] Request/response interceptors
- [ ] Type definitions for all endpoints
- [ ] Error handling

### 3.3 State Management (`store/settingsStore.ts`)
- [ ] Zustand store for settings
- [ ] Persist to localStorage
- [ ] Actions for CRUD operations

### 3.4 Components

#### InputSection Component
- [ ] JIRA ID input with validation
- [ ] ValueEdge ID input
- [ ] File upload with drag-drop
- [ ] File preview thumbnails
- [ ] Remove file functionality

#### AIConfigSection Component
- [ ] Provider radio buttons (Groq/Ollama)
- [ ] Model dropdown (dynamic based on provider)
- [ ] Temperature slider
- [ ] Connection test button
- [ ] Status indicators

#### PromptSection Component
- [ ] Multi-line text area
- [ ] Character counter
- [ ] Template info tooltip

#### OutputPreview Component
- [ ] Tab switching (Plan/Cases/Both)
- [ ] Markdown rendering
- [ ] Copy to clipboard button
- [ ] Download buttons (MD/PDF/XLSX)
- [ ] Syntax highlighting

#### SettingsModal Component
- [ ] JIRA configuration form
- [ ] ValueEdge configuration form
- [ ] LLM configuration form
- [ ] Template file upload
- [ ] Test connection buttons
- [ ] Save/Cancel actions

### 3.5 Main Page (`pages/HomePage.tsx`)
- [ ] Layout structure
- [ ] Form submission handling
- [ ] Loading states
- [ ] Error display
- [ ] WebSocket connection for progress

### 3.6 Styling & UX
- [ ] Responsive design
- [ ] Loading skeletons
- [ ] Toast notifications
- [ ] Error boundaries

---

## ✅ Phase 4: Integration & Testing (Day 8)

### 4.1 End-to-End Testing
- [ ] JIRA connection flow
- [ ] ValueEdge connection flow
- [ ] File upload and processing
- [ ] LLM generation with Groq
- [ ] LLM generation with Ollama
- [ ] Export functionality

### 4.2 Error Scenarios
- [ ] Invalid JIRA credentials
- [ ] Network failures
- [ ] LLM rate limiting
- [ ] File processing errors
- [ ] Empty input validation

### 4.3 Performance Testing
- [ ] Large file upload (20MB)
- [ ] Concurrent generation requests
- [ ] Memory usage monitoring

---

## ✅ Phase 5: Documentation & Deployment (Day 9-10)

### 5.1 Documentation
- [ ] README.md with setup instructions
- [ ] API documentation (auto-generated from FastAPI)
- [ ] User guide with screenshots
- [ ] Troubleshooting guide

### 5.2 Docker Setup
- [ ] Backend Dockerfile
- [ ] Frontend Dockerfile
- [ ] docker-compose.yml
- [ ] Environment variable examples

### 5.3 Final Testing
- [ ] Fresh installation test
- [ ] Docker deployment test
- [ ] Cross-browser testing

---

## 🔧 Quick Reference: Key Implementation Details

### JIRA API Request Pattern
```python
async def fetch_jira_issue(key: str, config: JiraConfig) -> dict:
    url = f"{config.base_url}/rest/api/3/issue/{key}"
    auth = base64.b64encode(f"{config.username}:{config.api_token}".encode()).decode()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Basic {auth}", "Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()
```

### Ollama API Request Pattern
```python
async def ollama_generate(prompt: str, model: str, base_url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            }
        )
        response.raise_for_status()
        return response.json()["response"]
```

### File Upload Handler
```python
@app.post("/api/documents/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate file type
    allowed = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Invalid file type")
    
    # Save to temp location
    file_id = str(uuid.uuid4())
    file_path = f"uploads/{file_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Extract text
    text = await extract_text(file_path, file.content_type)
    
    return {"file_id": file_id, "filename": file.filename, "extracted_text": text}
```

### WebSocket Progress Updates
```python
async def generate_with_progress(request_id: str, context: str, websocket: WebSocket):
    await websocket.accept()
    
    await websocket.send_json({"type": "started", "request_id": request_id})
    
    # Step 1: Analyzing
    await websocket.send_json({"type": "progress", "step": "analyzing", "percent": 20})
    await asyncio.sleep(0.5)
    
    # Step 2: Generating
    await websocket.send_json({"type": "progress", "step": "generating", "percent": 50})
    
    # Stream LLM response
    async for chunk in llm.generate_stream(context):
        await websocket.send_json({"type": "chunk", "content": chunk})
    
    await websocket.send_json({"type": "completed", "request_id": request_id})
```

---

## 📋 Pre-Launch Checklist

- [ ] All API endpoints tested
- [ ] Frontend responsive on mobile/tablet/desktop
- [ ] No console errors
- [ ] All environment variables documented
- [ ] Security audit (no hardcoded secrets)
- [ ] README complete with screenshots
- [ ] Docker compose tested
- [ ] License file added
- [ ] .gitignore configured (no uploads/, data/, .env)

---

**Estimated Total Development Time**: 10 working days (2 weeks)  
**Team Size**: 1-2 developers  
**Complexity**: Medium
