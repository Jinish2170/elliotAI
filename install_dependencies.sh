#!/bin/bash
# VERITAS v2 - Complete Dependency Installation Script
# Run this to install all required dependencies for v2 features

echo "=========================================="
echo "VERITAS v2 - Installing Dependencies"
echo "=========================================="

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "ERROR: pip is not installed. Please install Python 3.10+ first."
    exit 1
fi

echo ""
echo "Step 1: Installing core Python packages..."
pip install \
  playwright \
  numpy \
  networkx \
  python-dotenv \
  pillow \
  pytesseract \
  sqlalchemy \
  fastapi \
  uvicorn[standard] \
  pydantic \
  pydantic-settings \
  httpx \
  aiohttp \
  beautifulsoup4 \
  lxml \
  requests \
  whois \
  dnspython \
  pyOpenSSL \
  tldextract \
  validators \
  phonenumbers \
  email-validator

echo ""
echo "Step 2: Installing Playwright browsers..."
playwright install chromium

echo ""
echo "Step 3: Installing development tools (optional)..."
pip install pytest pytest-asyncio pytest-cov black pylint

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy veritas/.env.example to veritas/.env"
echo "2. Add your API keys to veritas/.env"
echo "3. Run: python -m veritas --help"
echo ""
