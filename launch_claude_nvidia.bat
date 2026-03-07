@echo off
title Claude Code (GLM-5)
echo 🚀 Launching Claude Code with GLM-5...

:: Start the proxy in the background if not already running
echo 📡 Starting CC-NIM Proxy...
start "CC-NIM Proxy" /min powershell -NoExit -Command "cd 'c:\files\coding dev era\claude code\cc-nim'; python -m uvicorn server:app --host 0.0.0.0 --port 8082 --reload"

echo ⏳ Waiting for server to initialize...
timeout /t 3 /nobreak > nul

:: Set Claude Code environment variables
set ANTHROPIC_BASE_URL=http://localhost:8082
set ANTHROPIC_AUTH_TOKEN=ccnim

echo 🤖 Connecting Claude Code...
echo.
claude
echo.
echo 👋 Session ended.
pause
