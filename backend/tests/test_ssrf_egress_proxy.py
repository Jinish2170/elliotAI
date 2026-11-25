"""SSRF egress proxy: the audit browser must not reach private addresses,
including via redirect hops (page.route missed those; verified 2026-11-25)."""
import asyncio

from elliot.core import net_guard


def test_resolver_classifies_addresses():
    for private in ("127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "[::1]", "0.0.0.0", "localhost"):
        assert net_guard.resolve_public(private) is None, private
    assert net_guard.resolve_public("93.184.215.14") == "93.184.215.14"


async def _ask(proxy, request: bytes) -> bytes:
    r, w = await asyncio.open_connection("127.0.0.1", proxy.port)
    w.write(request)
    await w.drain()
    data = await asyncio.wait_for(r.read(200), timeout=5)
    w.close()
    return data


def test_proxy_refuses_private_targets_for_http_and_connect():
    async def run():
        proxy = await net_guard.EgressProxy().start()
        try:
            http = await _ask(proxy, b"GET http://127.0.0.1:8010/docs HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
            tls = await _ask(proxy, b"CONNECT 169.254.169.254:443 HTTP/1.1\r\nHost: x\r\n\r\n")
        finally:
            await proxy.stop()
        return http, tls, proxy.blocked
    http, tls, blocked = asyncio.run(run())
    assert http.startswith(b"HTTP/1.1 403") and tls.startswith(b"HTTP/1.1 403")
    assert blocked == ["127.0.0.1", "169.254.169.254"]


def test_chromium_is_told_not_to_bypass_the_proxy_for_loopback():
    proxy = net_guard.EgressProxy()
    proxy.port = 1234
    assert "--proxy-bypass-list=<-loopback>" in net_guard.chromium_args(proxy)
