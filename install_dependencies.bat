@echo off
REM VERITAS v2 - Complete Dependency Installation Script for Windows
REM Run this to install all required dependencies for v2 features

echo ==========================================
echo VERITAS v2 - Installing Dependencies
echo ==========================================
echo.

REM Check if pip is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed. Please install Python 3.10+ first.
    pause
    exit /b 1
)

echo Step 1: Installing core Python packages...
pip install playwright numpy networkx python-dotenv pillow pytesseract
pip install sqlalchemy fastapi uvicorn[standard] pydantic pydantic-settings
pip install httpx aiohttp beautifulsoup4 lxml requests
pip install whois dnspython pyOpenSSL tldextract validators
pip install phonenumbers email-validator

echo.
echo Step 2: Installing Playwright browsers...
playwright install chromium

echo.
echo Step 3: Installing development tools (optional)...
pip install pytest pytest-asyncio pytest-cov black pylint

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Copy veritas/.env.example to veritas/.env
echo 2. Add your API keys to veritas/.env
echo 3. Run: python -m veritas --help
echo.
pause
