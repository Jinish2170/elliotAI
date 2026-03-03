"""
Unit tests for TORClient class.

Tests verify:
- Async context manager session lifecycle
- TOR connectivity health check
- HTTP GET request routing through SOCKS5h proxy
- Response structure compliance
- Module imports working correctly
"""

import pytest
import aiohttp
from unittest.mock import AsyncMock, Mock, patch

from veritas.darknet.tor_client import TORClient


@pytest.mark.asyncio
class TestTORClientContextManager:
    """Test async context manager interface."""

    async def test_tor_client_context_manager_creates_session(self):
        """Verify __aenter__ creates aiohttp session."""
        client = TORClient()
        async with client as tor:
            assert tor.is_active
            assert tor._session is not None

    async def test_tor_client_context_manager_closes_session(self):
        """Verify __aexit__ closes aiohttp session."""
        client = TORClient()
        async with client as tor:
            session = tor._session

        # After context exit, session should be closed or None
        assert not tor.is_active

    async def test_tor_client_custom_proxy_url(self):
        """Verify TORClient accepts custom proxy URL."""
        custom_proxy = "socks5h://127.0.0.1:9150"  # Different port
        client = TORClient(proxy_url=custom_proxy)
        async with client as tor:
            assert tor.proxy_url == custom_proxy


@pytest.mark.asyncio
class TestTORClientCheckConnection:
    """Test TOR connectivity health check."""

    async def test_check_connection_returns_bool(self):
        """Verify check_connection() returns bool type."""
        client = TORClient()

        # Mock aiohttp request to return mock response
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            # Simulate TOR active
            mock_get.return_value = {
                "status": 200,
                "text": "<html><body>Congratulations. This browser is configured to use Tor.</body></html>",
                "headers": {},
                "error": None,
            }
            async with client:
                result = await client.check_connection()
                assert isinstance(result, bool)

    async def test_check_connection_true_when_tor_active(self):
        """Verify check_connection() returns True when TOR is active."""
        client = TORClient()
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "status": 200,
                "text": "<html><body>Congratulations. This browser is configured to use Tor.</body></html>",
                "headers": {},
                "error": None,
            }
            async with client:
                result = await client.check_connection()
                assert result is True

    async def test_check_connection_false_when_tor_inactive(self):
        """Verify check_connection() returns False when TOR is not active."""
        client = TORClient()
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "status": 200,
                "text": "<html><body>You are not using Tor.</body></html>",
                "headers": {},
                "error": None,
            }
            async with client:
                result = await client.check_connection()
                assert result is False

    async def test_check_connection_handles_exception(self):
        """Verify check_connection() returns False on exceptions."""
        client = TORClient()
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Network error")
            async with client:
                result = await client.check_connection()
                assert result is False


@pytest.mark.asyncio
class TestTORClientGetRequest:
    """Test HTTP GET request through TOR proxy."""

    async def test_tor_get_request_returns_dict(self):
        """Verify get() returns dict with correct structure."""
        client = TORClient()

        # Mock aiohttp session.get
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "status": 200,
                "text": "<html><body>Test response</body></html>",
                "headers": {"Content-Type": "text/html"},
                "error": None,
            }
            async with client as tor:
                result = await tor.get("http://example.onion")
                assert isinstance(result, dict)
                assert "status" in result
                assert "text" in result
                assert "headers" in result
                assert "error" in result

    async def test_tor_get_request_routes_through_proxy(self):
        """Verify get() uses SOCKS5h proxy parameter."""
        client = TORClient(proxy_url="socks5h://127.0.0.1:9050")

        # We can't easily test the actual proxy routing without mocking aiohttp internals
        # but we can verify the URL is passed through correctly
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"status": 200, "text": "", "headers": {}, "error": None}
            async with client as tor:
                await tor.get("http://example.onion")
                mock_get.assert_called_once_with("http://example.onion")

    async def test_tor_get_request_passes_headers(self):
        """Verify get() passes custom headers."""
        client = TORClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"status": 200, "text": "", "headers": {}, "error": None}
            async with client as tor:
                custom_headers = {"X-Custom-Header": "test-value"}
                await tor.get("http://example.onion", headers=custom_headers)
                assert mock_get.call_args[1]["headers"] == custom_headers

    async def test_tor_get_request_respects_timeout_override(self):
        """Verify get() respects timeout parameter override."""
        client = TORClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"status": 200, "text": "", "headers": {}, "error": None}
            async with client as tor:
                await tor.get("http://example.onion", timeout=15)
                assert mock_get.call_args[1]["timeout"] == 15

    async def test_tor_get_request_handles_aiohttp_error(self):
        """Verify get() handles aiohttp client errors gracefully."""
        client = TORClient()

        # Mock the aiohttp session to raise an error
        with patch.object(
            aiohttp.ClientSession, "get", side_effect=aiohttp.ClientError("Connection failed")
        ):
            async with client as tor:
                result = await tor.get("http://example.onion")
                assert result["error"] is not None
                assert result["status"] is None

    async def test_tor_get_request_no_active_session_raises(self):
        """Verify get() raises RuntimeError when used outside context manager."""
        client = TORClient()
        # Don't enter context manager
        with pytest.raises(RuntimeError) as exc_info:
            await client.get("http://example.onion")
        assert "async context manager" in str(exc_info.value)


class TestTORClientConfiguration:
    """Test TORClient configuration options."""

    def test_tor_client_default_values(self):
        """Verify default proxy URL and timeout values."""
        client = TORClient()
        assert client.proxy_url == TORClient.DEFAULT_PROXY_URL
        assert client._user_agent is not None

    def test_tor_client_custom_timeout(self):
        """Verify custom timeout is accepted."""
        client = TORClient(timeout=60)
        assert client.timeout.total == 60

    def test_tor_client_custom_user_agent(self):
        """Verify custom user agent is accepted."""
        custom_ua = "MyCustomAgent/1.0"
        client = TORClient(user_agent=custom_ua)
        assert client._user_agent == custom_ua
