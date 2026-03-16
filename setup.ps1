$repoRoot = $PSScriptRoot
$venvRoot = Join-Path $repoRoot ".venv"
$pythonExe = Join-Path $venvRoot "Scripts\python.exe"
$frontendRoot = Join-Path $repoRoot "frontend"
$frontendEnv = Join-Path $frontendRoot ".env"
$backendEnv = Join-Path $repoRoot "backend\.env"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Error "Python 3.9+ is required and 'python' was not found in PATH."
    exit 1
}

$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    Write-Error "Node.js 18+ is required and 'npm' was not found in PATH."
    exit 1
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "Creating Python virtual environment at .venv ..."
    & $pythonCommand.Source -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Installing backend dependencies ..."
& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $pythonExe -m pip install -r (Join-Path $repoRoot "backend\requirements.txt")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Installing frontend dependencies ..."
Set-Location $frontendRoot
npm install
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (-not (Test-Path $frontendEnv)) {
    Set-Content -Path $frontendEnv -Value "VITE_API_URL="
    Write-Host "Created frontend/.env with VITE_API_URL=."
}

if (-not (Test-Path $backendEnv)) {
    Write-Warning "backend/.env was not found. Create backend/.env and add GROQ_API_KEY before using Groq-backed features."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run these in two PowerShell windows from the repository root:"
Write-Host "  .\start-backend.ps1"
Write-Host "  .\start-frontend.ps1"