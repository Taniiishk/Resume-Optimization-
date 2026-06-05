@echo off
title ATS Resume Optimizer

echo ========================================
echo   ATS Resume Optimizer - Starting...
echo ========================================
echo.

:: Start Backend
echo [1/2] Starting backend on http://localhost:8001 ...
start /b "" "backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --app-dir backend
timeout /t 4 /nobreak > nul

:: Start Frontend (static file server)
echo [2/2] Starting frontend on http://localhost:3000 ...
start /b "" node "%~dp0serve-static.js"
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo   Both servers should be running!
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo   API docs: http://localhost:8001/docs
echo ========================================
echo.
echo   Close this window to stop all servers.
pause
