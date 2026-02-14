@echo off
title Veritas — Startup
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║        VERITAS — Autonomous Web Auditor      ║
echo  ║             Starting Services...             ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Kill any existing processes on ports 8000 and 3000
echo [1/4] Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>NUL') do (
    taskkill /PID %%a /F >NUL 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>NUL') do (
    taskkill /PID %%a /F >NUL 2>&1
)
timeout /t 2 /nobreak >NUL

:: Verify .venv exists
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found at %~dp0.venv
    echo         Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r veritas\requirements.txt
    pause
    exit /b 1
)

:: Verify node_modules exists
if not exist "%~dp0frontend\node_modules" (
    echo [ERROR] Frontend dependencies not installed.
    echo         Run: cd frontend ^&^& npm install
    pause
    exit /b 1
)

:: Start Backend (FastAPI)
echo [2/4] Starting Backend (FastAPI on port 8000)...
start "Veritas Backend" cmd /k "cd /d %~dp0backend && %~dp0.venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 && pause"

:: Wait for backend to be ready
echo [3/4] Waiting for backend to be ready...
:wait_backend
timeout /t 1 /nobreak >NUL
curl -s http://localhost:8000/api/health >NUL 2>&1
if %errorlevel% neq 0 goto wait_backend
echo        Backend is UP — http://localhost:8000

:: Start Frontend (Next.js)
echo [4/4] Starting Frontend (Next.js on port 3000)...
start "Veritas Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait for frontend
:wait_frontend
timeout /t 1 /nobreak >NUL
curl -s http://localhost:3000 -o NUL 2>&1
if %errorlevel% neq 0 goto wait_frontend
echo        Frontend is UP — http://localhost:3000

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║           All Services Running!              ║
echo  ║                                              ║
echo  ║   Frontend:  http://localhost:3000            ║
echo  ║   Backend:   http://localhost:8000            ║
echo  ║   Health:    http://localhost:8000/api/health  ║
echo  ║                                              ║
echo  ║   Close the terminal windows to stop.        ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Open browser
echo Opening browser...
start http://localhost:3000

echo Done. You can close this window.
timeout /t 5 /nobreak >NUL
