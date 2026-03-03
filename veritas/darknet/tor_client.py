"""
TOR Client with SOCKS5h proxy support for darknet (.onion) URL auditing.

This wrapper provides async context manager pattern for TOR connectivity
with DNS resolution happening on the proxy server (socks5h://) for privacy.

Legal/Privacy Compliance:
- Read-only OSINT only
- No transaction or purchase capability
- User agent headers set appropriately
- No logging of user-provided .onion URLs
"""

import aiohttp
from typing import Dict, Optional, Any


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
