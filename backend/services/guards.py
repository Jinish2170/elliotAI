"""
Abuse guards for a publicly deployed auditor.

A public elliotAI deployment drives a real browser to any URL a stranger submits and spends
LLM credits on it. Guards (all env-configurable, all off-able for local dev):

- BLOCK_PRIVATE_TARGETS (default true): refuse URLs whose host resolves to a
  private, loopback, link-local, multicast or reserved address (SSRF: e.g.
  http://169.254.169.254/ cloud metadata, http://localhost:8010/ internal API).
- AUDIT_RATE_LIMIT_PER_HOUR (default 0 = off): audits per client IP per hour.
- MAX_CONCURRENT_AUDITS (default 0 = off): running audits at once (RAM bound:
  each audit runs its own Chromium).
- ALLOWED_TIERS (default empty = all): e.g. "quick_scan,standard_audit".
"""

from __future__ import annotations

import ipaddress
import os
import socket
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlparse


def _env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def block_private_targets() -> bool:
    return os.getenv("BLOCK_PRIVATE_TARGETS", "true").lower() == "true"


def target_is_private(url: str) -> bool:
    """True if any address the host resolves to is non-public (or unresolvable)."""
    host = urlparse(url).hostname
    if not host:
        return True
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False  # unresolvable → the audit itself will report it; not SSRF
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
                or ip.is_reserved or ip.is_unspecified):
            return True
    return False


class RateLimiter:
    """Sliding-window limit per key. In-memory: fine for a single-instance demo."""

    def __init__(self, per_hour: int):
        self.per_hour = per_hour
        self._hits: dict[str, deque] = defaultdict(deque)
        self._mu = threading.Lock()

    def allow(self, key: str) -> bool:
        if self.per_hour <= 0:
            return True
        now = time.monotonic()
        with self._mu:
            q = self._hits[key]
            while q and now - q[0] > 3600:
                q.popleft()
            if len(q) >= self.per_hour:
                return False
            q.append(now)
            return True


rate_limiter = RateLimiter(_env_int("AUDIT_RATE_LIMIT_PER_HOUR"))


def max_concurrent_audits() -> int:
    return _env_int("MAX_CONCURRENT_AUDITS")


def allowed_tiers() -> set[str]:
    raw = os.getenv("ALLOWED_TIERS", "").strip()
    return {t.strip() for t in raw.split(",") if t.strip()}


def client_ip(headers, fallback: str) -> str:
    """First hop of X-Forwarded-For (set by HF Spaces / Vercel proxies), else peer."""
    xff = headers.get("x-forwarded-for", "")
    return xff.split(",")[0].strip() or fallback
