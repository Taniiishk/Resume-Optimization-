@echo off
title ATS Resume Optimizer - Backend

:: Start Backend only
start /b "" "backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --app-dir backend
timeout /t 3 /nobreak > nul
echo Backend started on http://localhost:8001
