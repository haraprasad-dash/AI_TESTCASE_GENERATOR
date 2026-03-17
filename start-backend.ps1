[CmdletBinding()]
param(
	[switch]$SkipCleanup
)

# Start Backend Script
$env:PYTHONIOENCODING = "utf-8"
$repoRoot = $PSScriptRoot
$backendRoot = Join-Path $repoRoot "backend"
$pythonCandidates = @(
	(Join-Path $repoRoot ".venv\Scripts\python.exe"),
	(Join-Path $backendRoot "venv\Scripts\python.exe")
)
$pythonExe = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $pythonExe) {
	Write-Error "Python environment not found. Run .\setup.ps1 from the repository root first."
	exit 1
}

Set-Location $backendRoot

if (-not (Test-Path ".env")) {
	Write-Warning "backend/.env was not found. Add GROQ_API_KEY and other settings before using the app."
}

if (-not $SkipCleanup) {
	# Clean up stale backend listeners that can leave old code serving on port 7010.
	try {
		$listeners = Get-NetTCPConnection -LocalPort 7010 -State Listen -ErrorAction SilentlyContinue |
			Select-Object -ExpandProperty OwningProcess -Unique
		foreach ($listenerPid in $listeners) {
			if ($listenerPid) {
				Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue
			}
		}
	} catch {
		# Best-effort cleanup; continue startup.
	}

	# Also stop any uvicorn app.main workers from prior sessions.
	try {
		$backendProcs = Get-CimInstance Win32_Process |
			Where-Object {
				($_.Name -in @('python.exe', 'uvicorn.exe')) -and
				($_.CommandLine -match 'app\.main:app') -and
				($_.CommandLine -match '--port\s+7010')
			}
		foreach ($p in $backendProcs) {
			Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
		}
	} catch {
		# Best-effort cleanup; continue startup.
	}
} else {
	Write-Host "Skipping stale process cleanup for faster startup (-SkipCleanup)."
}

Start-Sleep -Seconds 1
Write-Host "Starting backend on http://0.0.0.0:7010 ..."
Write-Host "This terminal stays attached while the server runs. Use Ctrl+C to stop."
& $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 7010
