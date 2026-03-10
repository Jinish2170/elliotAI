"""
Veritas — Tor Client (Canonical Implementation)

Provides .onion site support through SOCKS5 proxy (Tor default: 127.0.0.1:9050).

Two clients are available:
- TORClient: Full async HTTP client with aiohttp SOCKS5 proxy support
- TorClient: Playwright-oriented stub for browser proxy configuration

Legal/Privacy Compliance:
- Read-only OSINT only
- No transaction or purchase capability
- User agent headers set appropriately
- No logging of user-provided .onion URLs
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Any

import aiohttp

logger = logging.getLogger("veritas.core.tor_client")


# ============================================================
# TORClient — Full async HTTP client with SOCKS5 support
# ============================================================

class TORClient:
    """Async TOR client wrapper with SOCKS5h proxy support.

    Routes HTTP requests through TOR SOCKS5h proxy for accessing .onion
    URLs with DNS resolution happening on the proxy (preserves privacy).

    Usage:
        async with TORClient() as tor:
            if await tor.check_connection():
                response = await tor.get("http://example.onion")
    """

    DEFAULT_PROXY_URL = "socks5h://127.0.0.1:9050"
    TOR_CHECK_URL = "https://check.torproject.org/"

    def __init__(
        self,
        proxy_url: str = DEFAULT_PROXY_URL,
        timeout: int = 30,
        user_agent: Optional[str] = None,
    ):
        """Initialize TOR client with proxy configuration.

        Args:
            proxy_url: SOCKS5h proxy URL (default: socks5h://127.0.0.1:9050)
            timeout: Request timeout in seconds (default: 30)
            user_agent: Custom User-Agent header (default: None, uses sensible default)
        """
        self.proxy_url = proxy_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    async def __aenter__(self) -> "TORClient":
        """Create aiohttp session on context entry.

        Returns:
            Self for chaining
        """
        connector = aiohttp.TCPConnector(
            limit=10,  # Connection pool size
            limit_per_host=5,
            force_close=False,
            enable_cleanup_closed=True,
        )

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"User-Agent": self._user_agent},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close aiohttp session on context exit.

        Ensures proper cleanup of network resources.
        """
        if self._session:
            await self._session.close()
            self._session = None

    async def check_connection(self) -> bool:
        """Verify TOR connectivity via check.torproject.org.

        Returns:
            True if TOR is active and working, False otherwise
        """
        try:
            response = await self.get(self.TOR_CHECK_URL, timeout=10)
            # check.torproject.org returns HTML containing "Congratulations"
            # if TOR is working
            is_tor = "Congratulations" in response.get("text", "") or (
                "Congratulations" in (response.get("headers", {}).get("X-IP", ""))
            )
            return is_tor
        except Exception:
            return False

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make HTTP GET request through TOR proxy.

        Args:
            url: Target URL (http:// or https://)
            headers: Additional HTTP headers
            timeout: Override default timeout
            **kwargs: Additional aiohttp.ClientSession.get() parameters

        Returns:
            Dict with keys:
                - status: HTTP status code (int)
                - text: Response body text (str or None)
                - headers: Response headers (dict)
                - error: Error message if request failed (str or None)
        """
        if not self._session:
            raise RuntimeError("TORClient must be used as async context manager")

        proxy = self.proxy_url
        request_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else self.timeout

        try:
            async with self._session.get(
                url,
                proxy=proxy,
                headers=headers,
                timeout=request_timeout,
                **kwargs,
            ) as response:
                return {
                    "status": response.status,
                    "text": await response.text(),
                    "headers": dict(response.headers),
                    "error": None,
                }
        except aiohttp.ClientError as e:
            return {
                "status": None,
                "text": None,
                "headers": {},
                "error": str(e),
            }
        except Exception as e:
            return {
                "status": None,
                "text": None,
                "headers": {},
                "error": f"Unexpected error: {e}",
            }

    @property
    def is_active(self) -> bool:
        """Check if session is active.

        Returns:
            True if session exists and is not closed
        """
        return self._session is not None and not self._session.closed


# ============================================================
# TorClient — Playwright browser proxy configuration stub
# ============================================================

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
