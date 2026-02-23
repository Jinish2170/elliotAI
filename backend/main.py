"""
Veritas Backend — FastAPI Application

Provides REST + WebSocket API for the Next.js frontend.
Routes:
  GET  /api/health             → Health check
  POST /api/audit/start        → Start a new audit, returns audit_id
  WS   /api/audit/stream/{id}  → Stream real-time audit events
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from veritas directory
env_path = Path(__file__).resolve().parent.parent / "veritas" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Ensure veritas is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "veritas"))

from veritas.db import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("✦ Veritas API — Online")
    # Initialize SQLite database with WAL mode and create tables
    await init_database()
    yield
    print("✦ Veritas API — Shutting down")


app = FastAPI(
    title="Veritas API",
    description="Autonomous Forensic Web Auditor — Backend",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from routes.audit import router as audit_router
from routes.health import router as health_router

app.include_router(health_router, prefix="/api")
app.include_router(audit_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
