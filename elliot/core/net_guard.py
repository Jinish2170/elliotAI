"""SSRF guard for everything the audit browser loads: a local egress proxy.

The API checks the submitted URL, but a public page can redirect, frame or
fetch http://127.0.0.1:8000 or a cloud metadata address, and the browser
would follow. On a public deployment that lets anyone point the auditor at
the host's private services.

Request interception (page.route) is not enough: Playwright only routes the
first URL of a redirect chain, so public -> public -> private redirects
slipped through (verified). Instead Chromium sends all traffic through this
proxy, which resolves each destination itself, refuses non-public IPs and
connects to the exact IP it checked (no DNS-rebinding gap).
Enabled by BLOCK_PRIVATE_TARGETS. Not used when Tor is active.
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import os
import socket
import time
from typing import Optional
from urllib.parse import urlsplit

logger = logging.getLogger("elliot.net_guard")

_BLOCKED = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
_HOP_HEADERS = {"proxy-connection", "connection", "keep-alive", "proxy-authorization"}


def enabled() -> bool:
    return os.getenv("BLOCK_PRIVATE_TARGETS", "false").lower() in ("1", "true", "yes")


def _ip_is_private(ip: str) -> bool:
    addr = ipaddress.ip_address(ip.split("%")[0])
    return (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
            or addr.is_reserved or addr.is_unspecified)


_RESOLVED: dict[str, tuple[Optional[str], float]] = {}
_TTL_S = 60.0


def resolve_public(host: str) -> Optional[str]:
    """A public IP to connect to, or None if the host is (or resolves to) anything non-public.

    Cached per host for a minute. Safe: the proxy dials the cached, already
    checked IP, so a later DNS change cannot redirect it to a private address.
    """
    now = time.monotonic()
    hit = _RESOLVED.get(host)
    if hit and hit[1] > now:
        return hit[0]
    ip = _resolve_public_uncached(host)
    _RESOLVED[host] = (ip, now + _TTL_S)
    return ip


def _resolve_public_uncached(host: str) -> Optional[str]:
    host = host.strip("[]")
    try:
        return None if _ip_is_private(host) else host
    except ValueError:
        pass
    try:
        ips = [i[4][0] for i in socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)]
    except socket.gaierror:
        return None
    if not ips or any(_ip_is_private(ip) for ip in ips):
        return None  # conservative: one private answer is enough to refuse
    return ips[0]


class EgressProxy:
    """Minimal HTTP/CONNECT forward proxy that only dials public IPs."""

    def __init__(self) -> None:
        self._server: Optional[asyncio.base_events.Server] = None
        self.port = 0
        self.blocked: list[str] = []

    async def start(self) -> "EgressProxy":
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        upstream_w = None
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=30)
            first, *headers = head.decode("latin-1").split("\r\n")
            method, target, version = first.split(" ", 2)
            if method.upper() == "CONNECT":
                host, _, port = target.rpartition(":")
                port = int(port or 443)
            else:
                parts = urlsplit(target)
                host, port = parts.hostname or "", parts.port or 80
                path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
            ip = await asyncio.to_thread(resolve_public, host)
            if ip is None:
                self.blocked.append(host)
                logger.warning(f"SSRF guard blocked browser connection to {host}")
                writer.write(_BLOCKED)
                await writer.drain()
                return
            upstream_r, upstream_w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=20)
            if method.upper() == "CONNECT":
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()
            else:
                # One request per connection, so a reused client socket can
                # never carry a second request to a different (unchecked) host.
                kept = [h for h in headers if h and h.split(":", 1)[0].strip().lower() not in _HOP_HEADERS]
                upstream_w.write(f"{method} {path} {version}\r\n".encode("latin-1")
                                 + "\r\n".join(kept + ["Connection: close"]).encode("latin-1") + b"\r\n\r\n")
                await upstream_w.drain()
            await asyncio.gather(self._pipe(reader, upstream_w), self._pipe(upstream_r, writer))
        except Exception as e:
            logger.debug(f"egress proxy connection ended: {e}")
        finally:
            for w in (writer, upstream_w):
                if w is not None:
                    w.close()

    @staticmethod
    async def _pipe(src: asyncio.StreamReader, dst: asyncio.StreamWriter) -> None:
        try:
            while data := await src.read(65536):
                dst.write(data)
                await dst.drain()
        finally:
            if dst.can_write_eof():
                try:
                    dst.write_eof()
                except Exception:
                    pass


def chromium_args(proxy: EgressProxy) -> list[str]:
    # "<-loopback>" removes Chromium's implicit localhost bypass, so requests
    # to 127.0.0.1 also go through (and are refused by) the proxy.
    return [f"--proxy-server={proxy.url}", "--proxy-bypass-list=<-loopback>"]
