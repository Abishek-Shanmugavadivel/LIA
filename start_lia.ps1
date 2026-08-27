# LIA 5.0 JARVIS PowerShell Desktop Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  LIA 5.0 — GRANDMASTER JARVIS DESKTOP LAUNCHER" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

python start_lia.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] LIA 5.0 backend & voice engine initialized successfully." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to start LIA 5.0." -ForegroundColor Red
}
