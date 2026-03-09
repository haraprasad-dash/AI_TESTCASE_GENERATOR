# Start Backend Script
$env:PYTHONIOENCODING = "utf-8"
Set-Location "$PSScriptRoot\backend"

# Clean up stale backend listeners that can leave old code serving on port 7010.
try {
	$listeners = Get-NetTCPConnection -LocalPort 7010 -State Listen -ErrorAction SilentlyContinue |
		Select-Object -ExpandProperty OwningProcess -Unique
	foreach ($pid in $listeners) {
		if ($pid) {
			Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
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

Start-Sleep -Seconds 1
& ".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 7010
