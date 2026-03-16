# Start Frontend Script
$frontendRoot = Join-Path $PSScriptRoot "frontend"

Set-Location $frontendRoot

if (-not (Test-Path "node_modules")) {
	Write-Host "Frontend dependencies not found. Running npm install ..."
	npm install
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
}

if (-not (Test-Path ".env")) {
	Set-Content -Path ".env" -Value "VITE_API_URL="
	Write-Host "Created frontend/.env with VITE_API_URL=."
}

npm run dev
