@echo off
setlocal enabledelayedexpansion
title Veritas — Startup
color 0B

:: Resolve project root (handles spaces in path)
set "ROOT=%~dp0"
:: Remove trailing backslash
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║        VERITAS — Autonomous Web Auditor      ║
echo  ║             Starting Services...             ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Kill any existing processes on ports 8000 and 3000
echo [1/5] Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano 2^>NUL ^| findstr ":8000.*LISTENING"') do (
    taskkill /PID %%a /F >NUL 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>NUL ^| findstr ":3000.*LISTENING"') do (
    taskkill /PID %%a /F >NUL 2>&1
)
ping -n 3 127.0.0.1 >NUL 2>&1

:: Verify .venv exists
echo [2/5] Checking dependencies...
if not exist "%ROOT%\.venv\Scripts\python.exe" (
    echo        [ERROR] Python venv not found at "%ROOT%\.venv"
    echo         Run: python -m venv .venv
    echo         Then: .venv\Scripts\pip install -r veritas\requirements.txt
    pause
    exit /b 1
)
echo        Python venv .......... OK

:: Verify node_modules exists
if not exist "%ROOT%\frontend\node_modules" (
    echo        [ERROR] Frontend dependencies not installed.
    echo         Run: cd frontend ^&^& npm install
    pause
    exit /b 1
)
echo        node_modules ......... OK

:: Verify .env exists
if exist "%ROOT%\veritas\.env" (
    echo        veritas/.env ......... OK
) else (
    echo        [WARN] veritas/.env not found — API keys may be missing
)

:: Start Backend (FastAPI)
echo [3/5] Starting Backend (FastAPI on port 8000)...
start "Veritas Backend" cmd /k "cd /d "%ROOT%\backend" && "%ROOT%\.venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000"

:: Wait for backend to be ready (max 30 seconds)
echo [4/5] Waiting for backend...
set /a TRIES=0
:wait_backend
if !TRIES! GEQ 30 (
    echo        [ERROR] Backend did not start within 30 seconds.
    echo        Check the "Veritas Backend" terminal window for errors.
    pause
    exit /b 1
)
ping -n 2 127.0.0.1 >NUL 2>&1
set /a TRIES+=1
"%ROOT%\.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" >NUL 2>&1
if %errorlevel% neq 0 goto wait_backend
echo        Backend is UP — http://localhost:8000

:: Start Frontend (Next.js)
echo [5/5] Starting Frontend (Next.js on port 3000)...
start "Veritas Frontend" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"

:: Wait for frontend (max 30 seconds)
set /a TRIES=0
:wait_frontend
if !TRIES! GEQ 30 (
    echo        [WARN] Frontend may still be compiling. Opening browser anyway...
    goto open_browser
)
ping -n 2 127.0.0.1 >NUL 2>&1
set /a TRIES+=1
"%ROOT%\.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://localhost:3000')" >NUL 2>&1
if %errorlevel% neq 0 goto wait_frontend
echo        Frontend is UP — http://localhost:3000

:open_browser
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║           All Services Running!              ║
echo  ║                                              ║
echo  ║   Frontend:  http://localhost:3000            ║
echo  ║   Backend:   http://localhost:8000            ║
echo  ║   Health:    http://localhost:8000/api/health ║
echo  ║                                              ║
echo  ║   To stop: run stop.bat or close terminals   ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Open browser
start "" http://localhost:3000

echo Done.
ping -n 4 127.0.0.1 >NUL 2>&1
