"""
Veritas — Tor Client Stub (Experimental)

Provides .onion site support through SOCKS5 proxy (Tor default: 127.0.0.1:9050).
Currently a STUB — requires a local Tor daemon to be running.

Future: full integration with Tor Browser Bundle for .onion crawling.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("veritas.core.tor_client")


@dataclass
class TorConfig:
    """Configuration for Tor SOCKS5 proxy."""
    enabled: bool = False
    socks_host: str = "127.0.0.1"
    socks_port: int = 9050
    control_port: int = 9051
    control_password: str = ""


class TorClient:
    """
    Tor browser client for .onion site access.

    EXPERIMENTAL — requires:
    1. Tor daemon running locally (tor service or Tor Browser Bundle)
    2. SOCKS5 proxy on 127.0.0.1:9050 (default)

    Usage with Playwright:
        browser = await playwright.chromium.launch(
            proxy={"server": f"socks5://{config.socks_host}:{config.socks_port}"}
        )
    """

    def __init__(self, config: TorConfig | None = None):
        self.config = config or TorConfig()
        self._available: bool | None = None

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    async def check_availability(self) -> bool:
        """Check if Tor SOCKS5 proxy is reachable."""
        if self._available is not None:
            return self._available

        import asyncio
        import socket

        loop = asyncio.get_event_loop()
        try:
            def _check():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                try:
                    s.connect((self.config.socks_host, self.config.socks_port))
                    return True
                except (ConnectionRefusedError, OSError, socket.timeout):
                    return False
                finally:
                    s.close()

            self._available = await loop.run_in_executor(None, _check)
        except Exception:
            self._available = False

        if not self._available:
            logger.warning(
                "Tor SOCKS5 proxy not available at %s:%d — .onion support disabled",
                self.config.socks_host,
                self.config.socks_port,
            )
        return self._available

    def get_proxy_settings(self) -> dict:
        """Get Playwright-compatible proxy settings."""
        return {
            "server": f"socks5://{self.config.socks_host}:{self.config.socks_port}",
        }

    @staticmethod
    def is_onion_url(url: str) -> bool:
        """Check if a URL is a .onion address."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = (parsed.netloc or parsed.path.split("/")[0]).lower()
        return host.endswith(".onion")
