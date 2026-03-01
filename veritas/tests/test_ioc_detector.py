"""
Tests for IOCDetector — Indicators of Compromise detection.

Tests cover:
- Onion address detection (V2 and V3)
- IP address detection
- Hash detection (MD5, SHA1, SHA256, SHA512)
- URL and link scanning
- Edge cases and error handling
"""

import pytest

from veritas.osint.ioc_detector import (
    IOCDetector,
    IOCIndicator,
    IOCDetectionResult,
    IOCType,
    IOCSeverity,
    is_onion_url,
    detect_onion_addresses,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def detector():
    """Create an IOCDetector instance."""
    return IOCDetector()


# ============================================================
# Onion Address Detection Tests
# ============================================================

class TestOnionDetection:
    """Tests for onion address detection."""

    @pytest.mark.asyncio
    async def test_detect_v3_onion_url(self, detector):
        """Detect V3 onion address in URL."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        url = f"http://{onion}.onion/page"
        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS
        assert result.value == f"{onion}.onion"
        assert result.severity == IOCSeverity.HIGH
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_detect_v3_onion_exact_56_chars(self, detector):
        """Detect V3 onion with exact 56 base32 characters."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        url = f"http://{onion}.onion/path"

        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS
        assert result.value == f"{onion}.onion"

    @pytest.mark.asyncio
    async def test_detect_v2_onion_in_url(self, detector):
        """Detect V2 onion address in URL (deprecated but detected)."""
        url = "http://abcdefghijklmnop.onion/page"
        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS
        assert result.value == "abcdefghijklmnop.onion"

    @pytest.mark.asyncio
    async def test_detect_https_onion(self, detector):
        """Detect onion address with HTTPS."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        url = f"https://{onion}.onion"

        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS
        assert result.value == f"{onion}.onion"

    @pytest.mark.asyncio
    async def test_detect_onion_with_port(self, detector):
        """Detect onion address with port number."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        url = f"http://{onion}.onion:8080/path"

        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS
        # Should strip port from value
        assert result.value == f"{onion}.onion"
        assert result.context.get("source") == "url"

    @pytest.mark.asyncio
    async def test_no_normal_url_detected(self, detector):
        """Normal URLs should not trigger IOC detection."""
        url = "http://example.com/page"
        result = detector.detect_url(url)

        assert result is None


class TestOnionDetectionInContent:
    """Tests for onion detection in HTML/page content."""

    @pytest.mark.asyncio
    async def test_detect_onion_in_html_content(self, detector):
        """Detect onion addresses in HTML content."""
        # Valid V3 onion: 56 base32 characters
        onion1 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        onion2 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        content = f"""
        <html>
            <body>
                <a href="http://{onion1}.onion">Link 1</a>
                <p>Visit http://{onion2}.onion for more</p>
            </body>
        </html>
        """

        result = await detector.detect_content("http://example.com", content)

        assert result.found is True
        assert result.onion_detected is True
        assert result.onion_count >= 2

    @pytest.mark.asyncio
    async def test_detect_onion_in_links(self, detector):
        """Detect onion addresses in extracted links."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        links = [
            "http://example.com/about",
            f"http://{onion}.onion",
            "http://normal-site.com",
        ]

        result = await detector.detect_content("http://example.com", links=links)

        assert result.found is True
        assert result.onion_detected is True
        assert result.onion_count == 1

    @pytest.mark.asyncio
    async def test_multiple_onion_addresses(self, detector):
        """Detect multiple different onion addresses."""
        onions = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ]
        content = " ".join([f"http://{o}.onion" for o in onions])

        result = await detector.detect_content("http://example.com", content)

        assert result.onion_count >= 2


# ============================================================
# IP Address Detection Tests
# ============================================================

class TestIPAddressDetection:
    """Tests for IP address detection."""

    @pytest.mark.asyncio
    async def test_detect_ipv4_in_url(self, detector):
        """Detect IPv4 address in URL."""
        url = "http://192.168.1.1/page"
        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.IP_ADDRESS
        assert result.value == "192.168.1.1"
        assert result.severity == IOCSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_detect_ipv4_in_content(self, detector):
        """Detect IPv4 addresses in content."""
        content = "Server IP: 10.0.0.5 and backup: 192.168.1.100"

        result = await detector.detect_content("http://example.com", content)

        assert result.ip_detected is True
        ips = [ind.value for ind in result.indicators if ind.type == IOCType.IP_ADDRESS]
        assert "10.0.0.5" in ips
        assert "192.168.1.100" in ips

    @pytest.mark.asyncio
    async def test_no_private_ips_flagged_low_risk(self, detector):
        """Private IPs should have appropriate severity."""
        private_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]

        for ip in private_ips:
            url = f"http://{ip}/"
            result = detector.detect_url(url)
            # Should detect but with reasonable severity
            if result:
                assert result.severity in [IOCSeverity.LOW, IOCSeverity.MEDIUM]


# ============================================================
# Hash Detection Tests
# ============================================================

class TestHashDetection:
    """Tests for hash detection."""

    @pytest.mark.asyncio
    async def test_detect_md5_hash(self, detector):
        """Detect MD5 hash in content."""
        md5_hash = "5d41402abc4b2a76b9719d911017c592"
        content = f"File hash: {md5_hash}"

        result = await detector.detect_content("http://example.com", content)

        assert result.hash_detected is True
        hashes = [ind for ind in result.indicators if ind.type == IOCType.HASH]
        assert any(h.value == md5_hash and h.context.get("hash_type") == "MD5" for h in hashes)

    @pytest.mark.asyncio
    async def test_detect_sha1_hash(self, detector):
        """Detect SHA1 hash in content."""
        sha1_hash = "2fd4e1c67a2d28fced849ee1bb76e7391b93ebdd"
        content = f"File checksum: {sha1_hash}"

        result = await detector.detect_content("http://example.com", content)

        assert result.hash_detected is True
        hashes = [ind for ind in result.indicators if ind.type == IOCType.HASH]
        assert any(h.value == sha1_hash and h.context.get("hash_type") == "SHA1" for h in hashes)

    @pytest.mark.asyncio
    async def test_detect_sha256_hash(self, detector):
        """Detect SHA256 hash in content."""
        sha256_hash = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        content = f"SHA256: {sha256_hash}"

        result = await detector.detect_content("http://example.com", content)

        assert result.hash_detected is True
        hashes = [ind for ind in result.indicators if ind.type == IOCType.HASH]
        sha256_hashes = [h for h in hashes if h.context.get("hash_type") == "SHA256"]
        assert len(sha256_hashes) > 0
        assert sha256_hashes[0].severity == IOCSeverity.HIGH

    @pytest.mark.asyncio
    async def test_detect_sha512_hash(self, detector):
        """Detect SHA512 hash in content."""
        sha512_hash = "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a" \
                     "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"
        content = f"SHA512: {sha512_hash}"

        result = await detector.detect_content("http://example.com", content)

        assert result.hash_detected is True
        hashes = [ind for ind in result.indicators if ind.type == IOCType.HASH]
        sha512_hashes = [h for h in hashes if h.context.get("hash_type") == "SHA512"]
        assert len(sha512_hashes) > 0


# ============================================================
# IOCDetectionResult Tests
# ============================================================

class TestIOCDetectionResult:
    """Tests for IOCDetectionResult."""

    def test_add_indicator_updates_stats(self):
        """Adding indicator updates result statistics."""
        result = IOCDetectionResult()

        onion_indicator = IOCIndicator(
            type=IOCType.ONION_ADDRESS,
            value="test.onion",
            severity=IOCSeverity.HIGH,
        )
        result.add_indicator(onion_indicator)

        assert result.found is True
        assert result.onion_detected is True
        assert result.onion_count == 1
        assert result.ioc_counts["ONION_ADDRESS"] == 1
        assert result.highest_severity == IOCSeverity.HIGH

    def test_to_dict_serialization(self):
        """Test IOCDetectionResult serialization."""
        result = IOCDetectionResult()
        indicator = IOCIndicator(
            type=IOCType.ONION_ADDRESS,
            value="test.onion",
            severity=IOCSeverity.HIGH,
        )
        result.add_indicator(indicator)

        result_dict = result.to_dict()

        assert "found" in result_dict
        assert "indicators" in result_dict
        assert "ioc_counts" in result_dict
        assert "onion_detected" in result_dict
        assert len(result_dict["indicators"]) == 1

    def test_highest_severity_updates(self):
        """Test that highest severity updates correctly."""
        result = IOCDetectionResult()

        result.add_indicator(IOCIndicator(
            type=IOCType.IP_ADDRESS,
            value="1.2.3.4",
            severity=IOCSeverity.LOW,
        ))
        assert result.highest_severity == IOCSeverity.LOW

        result.add_indicator(IOCIndicator(
            type=IOCType.ONION_ADDRESS,
            value="test.onion",
            severity=IOCSeverity.HIGH,
        ))
        assert result.highest_severity == IOCSeverity.HIGH


# ============================================================
# Convenience Function Tests
# ============================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_is_onion_url_v3(self):
        """Test is_onion_url for V3 addresses."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        assert is_onion_url(f"http://{onion}.onion") is True
        assert is_onion_url(f"https://{onion}.onion/path") is True

    @pytest.mark.asyncio
    async def test_is_onion_url_v2(self):
        """Test is_onion_url for V2 addresses."""
        assert is_onion_url("http://abcdefghijklmnop.onion") is True

    @pytest.mark.asyncio
    async def test_is_onion_url_false(self):
        """Test is_onion_url returns False for normal URLs."""
        assert is_onion_url("http://example.com") is False
        assert is_onion_url("https://site.org/page") is False
        assert is_onion_url("http://onion.com") is False

    @pytest.mark.asyncio
    async def test_detect_onion_addresses(self):
        """Test detect_onion_addresses convenience function."""
        onion1 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        onion2 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        content = f"Visit http://{onion1}.onion or http://{onion2}.onion"

        onions = await detect_onion_addresses("http://example.com", content)

        assert len(onions) == 2
        assert f"{onion1}.onion" in onions
        assert f"{onion2}.onion" in onions


# ============================================================
# Edge Cases
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_content(self, detector):
        """Test with empty content."""
        result = await detector.detect_content("http://example.com", "", [])

        assert result.found is False
        assert len(result.indicators) == 0

    @pytest.mark.asyncio
    async def test_none_content(self, detector):
        """Test with None content."""
        result = await detector.detect_content("http://example.com", None, None)

        assert result.found is False
        assert len(result.indicators) == 0

    @pytest.mark.asyncio
    async def test_malformed_url(self, detector):
        """Test with malformed URL."""
        result = detector.detect_url("not-a-valid-url")

        assert result is None

    @pytest.mark.asyncio
    async def test_duplicate_onions_deduped(self, detector):
        """Test duplicate onions handled (detector lists all, convenience dedupes)."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        content = f"http://{onion}.onion repeated http://{onion}.onion"

        # Detector will find multiple occurrences
        result = await detector.detect_content("http://example.com", content)
        assert result.onion_count >= 1

        # Convenience function dedupes
        onions = await detect_onion_addresses("http://example.com", content)
        assert len(onions) == 1

    @pytest.mark.asyncio
    async def test_onion_with_subdomain_style(self, detector):
        """Test malformed onion attempts are handled."""
        # Real onions don't have subdomains, but we should detect .onion TLD
        url = "http://subdomain.example.onion"
        result = detector.detect_url(url)

        # Should detect it as onion (ends with .onion)
        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS

    @pytest.mark.asyncio
    async def test_case_insensitive_onion(self, detector):
        """Test onion detection is case insensitive."""
        # Onion addresses use base32 which is lowercase, but TLD might vary
        url = "http://abcdefghijklmnopqrstuvwxyzabcdefghijklmnop.ONION"

        result = detector.detect_url(url)

        assert result is not None
        assert result.type == IOCType.ONION_ADDRESS


# ============================================================
# Integration Tests
# ============================================================

class TestIOCDetectorIntegration:
    """Integration tests for IOC detection."""

    @pytest.mark.asyncio
    async def test_full_html_page_scan(self, detector):
        """Test scanning a full HTML page."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        page_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Welcome</h1>
            <p>Links:</p>
            <ul>
                <li><a href="http://{onion}.onion">Hidden Service</a></li>
                <li><a href="http://example.com">Normal Site</a></li>
            </ul>
            <p>Contact: admin@{onion}.onion</p>
            <p>Server: 192.168.1.100</p>
            <p>Md5: 5d41402abc4b2a76b9719d911017c592</p>
        </body>
        </html>
        """

        result = await detector.detect_content(
            url="http://example.com",
            content=page_html,
        )

        assert result.found is True
        assert result.onion_detected is True
        assert result.ip_detected is True
        assert result.hash_detected is True

    @pytest.mark.asyncio
    async def test_links_only_detection(self, detector):
        """Test detection from links list only."""
        onion = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        links = [
            "http://example.com/home",
            f"http://{onion}.onion",
            f"https://{onion}.onion/about",
            "http://normal.org",
        ]

        result = await detector.detect_content("http://example.com", links=links)

        assert result.onion_detected is True
        assert result.onion_count == 2  # Two onion links

    @pytest.mark.asyncio
    async def test_combined_url_content_links(self, detector):
        """Test detection across URL, content, and links."""
        onion1 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        onion2 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        url = f"http://{onion1}.onion"
        content = f"Also visit http://{onion2}.onion"
        links = [f"http://{onion1}.onion/path", "http://normal.com"]

        result = await detector.detect_content(url, content, links)

        # Should find onions from all sources
        assert result.onion_detected is True
        assert result.onion_count >= 2
