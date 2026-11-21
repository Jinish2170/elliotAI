"""Public-deployment guards: SSRF block, rate limit, tier allowlist."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes import audit as audit_routes
from backend.services import guards
from elliot.db import get_db


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(audit_routes.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(guards, "target_is_private",
                        lambda url: "169.254" in url or "localhost" in url)
    return TestClient(app)


@pytest.mark.parametrize("url", ["http://169.254.169.254/latest/meta-data/", "http://localhost:8010/api"])
def test_private_targets_refused(client, url):
    r = client.post("/api/audit/start", json={"url": url, "tier": "quick_scan"})
    assert r.status_code == 400 and "SSRF" in r.json()["detail"]


def test_rate_limit_per_client(client, monkeypatch):
    monkeypatch.setattr(guards, "rate_limiter", guards.RateLimiter(2))
    codes = [client.post("/api/audit/start", json={"url": "https://example.com", "tier": "quick_scan"},
                         headers={"x-forwarded-for": "203.0.113.7"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_tier_allowlist(client, monkeypatch):
    monkeypatch.setenv("ALLOWED_TIERS", "quick_scan")
    r = client.post("/api/audit/start", json={"url": "https://example.com", "tier": "deep_forensic"})
    assert r.status_code == 403


def test_real_private_ip_detection():
    assert guards.target_is_private("http://127.0.0.1/")
    assert guards.target_is_private("http://10.0.0.5/")
    assert not guards.target_is_private("http://93.184.215.14/")


def test_client_ip_prefers_cloudflare_header():
    h = {"cf-connecting-ip": "198.51.100.9", "x-forwarded-for": "6.6.6.6, 10.0.0.1"}
    assert guards.client_ip(h, "127.0.0.1") == "198.51.100.9"
    assert guards.client_ip({"x-forwarded-for": "6.6.6.6"}, "127.0.0.1") == "6.6.6.6"
    assert guards.client_ip({}, "127.0.0.1") == "127.0.0.1"
