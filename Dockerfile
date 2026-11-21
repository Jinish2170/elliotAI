# elliotAI backend (FastAPI + audit engine + headless Chromium).
# Runs on any container host with ~1 GB RAM per concurrent audit (measured);
# runs anywhere: docker build -t elliotai . && docker run -p 7860:7860 --env-file elliot/.env elliotai
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=7860

WORKDIR /app

COPY requirements.txt ./
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --retries 10 --timeout 60 -r requirements.txt -r backend/requirements.txt \
 && python -m playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*

# Run as a non-root uid 1000 user (common container-platform requirement).
RUN useradd -m -u 1000 app
COPY --chown=app:app . .
RUN mkdir -p elliot/data backend/data && chown -R app:app elliot/data backend/data
USER app

EXPOSE 7860
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
