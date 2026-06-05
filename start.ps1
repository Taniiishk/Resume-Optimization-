# ATS Resume Optimizer — Launcher
# Run this to start both backend and frontend servers.
# Press Ctrl+C in each terminal to stop.

Write-Host "=== ATS Resume Optimizer ===" -ForegroundColor Cyan
Write-Host ""

# Start Backend
$backend = Start-Process -FilePath "$PSScriptRoot\backend\venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001" `
    -WorkingDirectory "$PSScriptRoot\backend" `
    -WindowStyle Hidden -PassThru
Write-Host "[Backend] Starting on http://localhost:8001 ..." -ForegroundColor Green

Start-Sleep -Seconds 3

# Start Frontend
$frontend = Start-Process -FilePath "npm" `
    -ArgumentList "run","dev" `
    -WorkingDirectory "$PSScriptRoot\frontend" `
    -WindowStyle Hidden -PassThru
Write-Host "[Frontend] Starting on http://localhost:3000 ..." -ForegroundColor Green

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "=== Both servers should be running ===" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend:  http://localhost:8001" -ForegroundColor Yellow
Write-Host "API docs: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to stop both servers..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
Write-Host "Servers stopped." -ForegroundColor Red
