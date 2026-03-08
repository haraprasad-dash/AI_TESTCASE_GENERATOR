# SOP 01: Project Setup

## Goal
Establish the complete project structure for the TestGen AI Agent with all necessary directories and configuration files.

## Prerequisites
- Python 3.9+
- Node.js 18+
- Git

## Project Structure

```
test-plan-agent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI entry point
│   │   ├── config.py       # Settings management
│   │   ├── models.py       # Pydantic schemas
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── templates/          # Markdown templates
│   ├── data/               # SQLite database
│   ├── uploads/            # Temp file storage
│   ├── outputs/            # Generated files
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   ├── store/          # State management
│   │   ├── types/          # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
├── architecture/           # SOPs (Layer 1)
├── tools/                  # Connection tests
├── docker-compose.yml
├── .env.example
└── README.md
```

## Backend Dependencies

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

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

## Frontend Dependencies

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

## Edge Cases
- Ensure `uploads/` and `outputs/` directories exist at runtime
- SQLite database should auto-initialize on first run
- Templates should have fallback defaults if user templates are missing
