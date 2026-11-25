"""One run per audit, independent of WebSocket connections.

History: (1) React StrictMode opened the stream twice and every UI audit ran
twice; (2) the fix tied the run to its socket and cancelled it on disconnect,
so any page refresh or network blip threw away minutes of work and left the
row "running". Now the first connection starts a background run; later
connections replay the event log and follow live; disconnects only unsubscribe.
"""
import asyncio
import threading
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes import audit as audit_routes
from elliot.db import get_db

AID = "vrts_disc0001"


class FakeRunner:
    """Emits one event, then waits until released (or cancelled)."""

    instances: list["FakeRunner"] = []

    def __init__(self, **kwargs):
        self.started = threading.Event()
        self.cancelled = threading.Event()
        self.release = threading.Event()
        FakeRunner.instances.append(self)

    async def run(self, send):
        self.started.set()
        await send({"type": "log_entry", "message": "step 1"})
        try:
            while not self.release.is_set():
                await asyncio.sleep(0.02)
        except asyncio.CancelledError:
            self.cancelled.set()
            raise
        await send({"type": "audit_result", "audit_id": AID, "result": {"trust_score": 90}})


@pytest.fixture
def client():
    FakeRunner.instances = []
    app = FastAPI()
    app.include_router(audit_routes.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: None
    with patch.object(audit_routes, "AuditRunner", FakeRunner), \
         patch.object(audit_routes, "should_use_db_persistence", return_value=False):
        # `with` keeps one event loop for the whole test, like uvicorn; without
        # it each connection gets its own loop and background runs die with it.
        with TestClient(app) as c:
            yield c
    audit_routes._audits.pop(AID, None)


def _register():
    audit_routes._audits[AID] = {
        "status": "queued", "url": "https://example.com", "tier": "quick_scan",
        "verdict_mode": "expert", "result": None, "error": None,
    }


def _wait(pred, timeout=5.0):
    for _ in range(int(timeout / 0.05)):
        if pred():
            return True
        threading.Event().wait(0.05)
    return pred()


def test_disconnect_does_not_cancel_run(client):
    _register()
    with client.websocket_connect(f"/api/audit/stream/{AID}") as ws:
        meta = ws.receive_json()
        assert meta["type"] == "audit_meta" and meta["started_at"] > 0  # clock survives reloads
        assert ws.receive_json()["message"] == "step 1"
    threading.Event().wait(0.3)
    run = FakeRunner.instances[0]
    assert not run.cancelled.is_set()
    assert audit_routes._audits[AID]["status"] == "running"
    run.release.set()
    assert _wait(lambda: audit_routes._audits[AID]["status"] == "completed")


def test_reconnect_replays_events_and_follows_live_without_rerun(client):
    _register()
    with client.websocket_connect(f"/api/audit/stream/{AID}") as ws:
        first_meta = ws.receive_json()
        assert ws.receive_json()["message"] == "step 1"
    with client.websocket_connect(f"/api/audit/stream/{AID}") as ws:
        assert ws.receive_json() == first_meta  # same start time on reconnect
        assert ws.receive_json()["message"] == "step 1"  # replayed backlog
        FakeRunner.instances[0].release.set()
        assert ws.receive_json()["type"] == "audit_result"  # live
    assert len(FakeRunner.instances) == 1


def test_strictmode_double_connect_starts_one_run(client):
    _register()
    first = client.websocket_connect(f"/api/audit/stream/{AID}")
    first.__enter__()
    second = client.websocket_connect(f"/api/audit/stream/{AID}")
    second.__enter__()
    first.__exit__(None, None, None)
    assert len(FakeRunner.instances) == 1
    FakeRunner.instances[0].release.set()
    assert _wait(lambda: audit_routes._audits[AID]["status"] == "completed")
    second.__exit__(None, None, None)


def test_completed_audit_replays_result_without_rerun(client):
    """Finished before a restart (no event log): replay the stored result."""
    _register()
    audit_routes._audits[AID].update(status="completed", result={"trust_score": 90})
    with client.websocket_connect(f"/api/audit/stream/{AID}") as ws:
        assert ws.receive_json() == {
            "type": "audit_result", "audit_id": AID, "result": {"trust_score": 90},
        }
        assert ws.receive_json()["type"] == "audit_complete"
    assert FakeRunner.instances == []
    assert audit_routes._audits[AID]["status"] == "completed"


def test_event_log_survives_restart_and_only_reads_own_screenshots(client, tmp_path, monkeypatch):
    """History links must replay every panel after a server restart."""
    monkeypatch.setattr(audit_routes, "_EVENTS_DIR", tmp_path / "events")
    shots = tmp_path / "shots"
    shots.mkdir()
    (shots / "a.png").write_bytes(b"PNG")
    secret = tmp_path / "secret.txt"
    secret.write_text("nope")
    monkeypatch.setattr(audit_routes, "_screenshot_roots", lambda: [shots.resolve()])
    aid = "vrts_0000abcd"
    audit_routes._save_event_log(aid, [
        {"type": "log_entry", "message": "step 1"},
        {"type": "screenshot", "url": str(shots / "a.png"), "data": "x"},
        {"type": "screenshot", "url": str(secret), "data": "x"},
        {"type": "audit_complete", "audit_id": aid},
    ])
    audit_routes._audits.pop(aid, None)  # simulate restart: nothing in memory
    with client.websocket_connect(f"/api/audit/stream/{aid}") as ws:
        got = [ws.receive_json() for _ in range(4)]
    assert got[0]["message"] == "step 1"
    assert got[1]["data"] == "UE5H"          # base64("PNG") re-read from disk
    assert "data" not in got[2]               # outside allowed roots: not read
    assert got[3]["type"] == "audit_complete"
    assert audit_routes._load_event_log("../etc/passwd") is None
