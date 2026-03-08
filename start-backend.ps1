# Start Backend Script
$env:PYTHONIOENCODING = "utf-8"
cd $PSScriptRoot\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
