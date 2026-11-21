"""A client disconnecting from /audit/stream must cancel the run it started.

Regression: React StrictMode (dev) opens the stream twice; the first run used
to keep going after its socket closed, so every UI audit ran twice.
"""
import asyncio
import threading
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes import audit as audit_routes
from elliot.db import get_db


class FakeRunner:
    """Runs until cancelled; records each instance's cancellation."""

    instances: list["FakeRunner"] = []

    def __init__(self, **kwargs):
        self.started = threading.Event()
        self.cancelled = threading.Event()
        FakeRunner.instances.append(self)

    async def run(self, send):
        self.started.set()
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            self.cancelled.set()
            raise


@pytest.fixture
def client():
    FakeRunner.instances = []
    app = FastAPI()
    app.include_router(audit_routes.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: None
    with patch.object(audit_routes, "AuditRunner", FakeRunner), \
         patch.object(audit_routes, "should_use_db_persistence", return_value=False):
        yield TestClient(app)
    audit_routes._audits.pop("vrts_disc0001", None)


def _register():
    audit_routes._audits["vrts_disc0001"] = {
        "status": "queued", "url": "https://example.com", "tier": "quick_scan",
        "verdict_mode": "expert", "result": None, "error": None,
    }


def test_disconnect_cancels_run(client):
    _register()
    with client.websocket_connect("/api/audit/stream/vrts_disc0001"):
        assert FakeRunner.instances[0].started.wait(5)
    assert FakeRunner.instances[0].cancelled.wait(5)
    # Status is updated after cancellation completes; give the handler a moment.
    for _ in range(50):
        if audit_routes._audits["vrts_disc0001"]["status"] == "disconnected":
            break
        threading.Event().wait(0.05)
    assert audit_routes._audits["vrts_disc0001"]["status"] == "disconnected"


def test_strictmode_double_connect_keeps_second_run(client):
    """StrictMode order: open #1, open #2, close #1 -> only #2 keeps running."""
    _register()
    first = client.websocket_connect("/api/audit/stream/vrts_disc0001")
    first.__enter__()
    assert FakeRunner.instances[0].started.wait(5)
    second = client.websocket_connect("/api/audit/stream/vrts_disc0001")
    second.__enter__()
    assert FakeRunner.instances[1].started.wait(5)
    first.__exit__(None, None, None)  # StrictMode cleanup closes the first socket
    assert FakeRunner.instances[0].cancelled.wait(5)
    threading.Event().wait(0.2)
    assert not FakeRunner.instances[1].cancelled.is_set()
    assert audit_routes._audits["vrts_disc0001"]["status"] == "running"
    second.__exit__(None, None, None)
    assert FakeRunner.instances[1].cancelled.wait(5)


def test_completed_audit_replays_result_without_rerun(client):
    """Reloading the audit page reconnects the stream; a finished audit must
    replay its stored result, not start a new run (and reset its status)."""
    _register()
    audit_routes._audits["vrts_disc0001"].update(status="completed", result={"trust_score": 90})
    with client.websocket_connect("/api/audit/stream/vrts_disc0001") as ws:
        assert ws.receive_json() == {
            "type": "audit_result", "audit_id": "vrts_disc0001", "result": {"trust_score": 90},
        }
        assert ws.receive_json()["type"] == "audit_complete"
    assert FakeRunner.instances == []
    assert audit_routes._audits["vrts_disc0001"]["status"] == "completed"
