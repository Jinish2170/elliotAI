@echo off

set "SCRIPT_DIR=%~dp0cc-nim"
set "ENV_FILE=%SCRIPT_DIR%\.env"

if not exist "%ENV_FILE%" (
    echo [ERROR] Missing %ENV_FILE%.
    echo Please add your OPENROUTER_API_KEY to the .env file.
    pause
    exit /b 1
)

echo [INFO] Starting CC-NIM proxy with OpenRouter + Qwen 3.6 Plus...

:: Force all Claude model tiers to Qwen 3.6
set "MODEL_OPUS=qwen/qwen3.6-plus:free"
set "MODEL_SONNET=qwen/qwen3.6-plus:free"
set "MODEL_HAIKU=qwen/qwen3.6-plus:free"
set "MODEL=qwen/qwen3.6-plus:free"

:: Check if the proxy is already running on port 8085
netstat -ano | findstr "LISTENING" | findstr ":8085" >nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] CC-NIM Proxy is already running on port 8085 - skipping startup...
) else (
    echo [INFO] Starting CC-NIM proxy on port 8085...
    start "CC-NIM Proxy" /min /d "%SCRIPT_DIR%" cmd /c "python server.py"
    echo [INFO] Waiting for proxy to initialize...
    timeout /t 5 /nobreak > nul
)

:: Bypass Login & Route Traffic (CRITICAL STEP)
echo [INFO] Launching Claude Code with bypass...
echo.
set ANTHROPIC_API_KEY=freecc && set ANTHROPIC_BASE_URL=http://localhost:8085 && claude
