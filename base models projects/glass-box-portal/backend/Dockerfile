# backend/Dockerfile

# We use the official Playwright image which has browsers pre-installed
# This is a large image (~1GB) but necessary for "Real" automation.
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the browsers specifically (just to be safe)
RUN playwright install chromium
RUN playwright install-deps

COPY . .

# Run with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]