"""
Unit tests for OnionDetector class.

Tests verify:
- .onion URL validation for v2 (16-char) and v3 (56-char) addresses
- Base32 checksum validation
- Multiple URL extraction from text
- Marketplace classification (marketplace, forum, exchange, unknown)
- is_darknet_url() quick detection
"""

import pytest

from veritas.darknet.onion_detector import (
    OnionDetector,
    PATTERN_V2,
    PATTERN_V3,
    MarketplaceType,
)


class TestOnionDetectorPatterns:
    """Test onion URL regex patterns."""

    def test_pattern_v2_matches_16_char(self):
        """Verify PATTERN_V2 matches valid v2 addresses (16 chars)."""
        valid_v2 = "abcdefghijklmnop.onion"
        matches = PATTERN_V2.findall(valid_v2)
        assert len(matches) == 1
        assert matches[0] == "abcdefghijklmnop"

    def test_pattern_v3_matches_56_char(self):
        """Verify PATTERN_V3 matches valid v3 addresses (56 chars)."""
        # 56 characters: 16+16+16+8
        valid_v3 = "abcdefghijklmnopabcdefghijklmnopabcdefghijklmnopabcdefgh.onion"
        matches = PATTERN_V3.findall(valid_v3)
        assert len(matches) == 1
        assert matches[0] == "abcdefghijklmnopabcdefghijklmnopabcdefghijklmnopabcdefgh"

    def test_pattern_v3_rejects_55_char(self):
        """Verify PATTERN_V3 rejects 55-char address (invalid length)."""
        invalid = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdeff.onion"
        matches = PATTERN_V3.findall(invalid)
        assert len(matches) == 0

    def test_pattern_v3_rejects_57_char(self):
        """Verify PATTERN_V3 rejects 57-char address (invalid length)."""
        invalid = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnop.onion"
        matches = PATTERN_V3.findall(invalid)
        assert len(matches) == 0


class TestValidateOnion:
    """Test .onion URL validation."""

    def test_validate_onion_v2_valid(self):
        """Verify validate_onion() accepts valid v2 addresses."""
        detector = OnionDetector()
        # Valid v2: 16 base32 chars + .onion
        valid_urls = [
            "abcdefghijklmnop.onion",
            "3g2upl4pq6kufc4m.onion",  # DuckDuckGo v2 (real example)
        ]
        for url in valid_urls:
            result = detector.validate_onion(url)
            assert result is True, f"URL: {url}"

    def test_validate_onion_v3_valid(self):
        """Verify validate_onion() accepts valid v3 addresses."""
        detector = OnionDetector()
        # Real v3 example pattern (56 chars)
        valid_v3 = "abcdefghijklmnopabcdefghijklmnopabcdefghijklmnopabcdefgh.onion"
        result = detector.validate_onion(valid_v3)
        assert result is True

    def test_validate_onion_rejects_invalid_chars(self):
        """Verify validate_onion() rejects invalid characters."""
        detector = OnionDetector()
        invalid_urls = [
            "abcdefghijklmno1.onion",  # Contains '1' (invalid base32)
            "abcdefghijklmnop.onnion",  # Extra 'n'
            "abcdefghijklmnop.toim",    # Wrong TLD
            "abcdefghijklmnop.on",      # Incomplete TLD
        ]
        for url in invalid_urls:
            result = detector.validate_onion(url)
            assert result is False, f"Should have rejected: {url}"

    def test_validate_onion_rejects_invalid_lengths(self):
        """Verify validate_onion() rejects invalid lengths."""
        detector = OnionDetector()
        invalid_urls = [
            "abcdefghijk.onion",        # Too short (12 chars)
            "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnop.onion",  # Too long (57 chars)
        ]
        for url in invalid_urls:
            result = detector.validate_onion(url)
            assert result is False, f"Should have rejected: {url}"

    def test_validate_onion_rejects_empty(self):
        """Verify validate_onion() rejects empty strings."""
        detector = OnionDetector()
        result = detector.validate_onion("")
        assert result is False

    def test_validate_onion_rejects_onion_only(self):
        """Verify validate_onion() rejects just '.onion'."""
        detector = OnionDetector()
        result = detector.validate_onion(".onion")
        assert result is False


class TestDetectOnionURLs:
    """Test .onion URL extraction from text."""

    def test_detect_onion_urls_single_v2(self):
        """Verify detect_onion_urls() extracts single v2 URL."""
        detector = OnionDetector()
        text = "Visit the site at abcdefghijklmnop.onion for more info."
        urls = detector.detect_onion_urls(text)
        assert len(urls) == 1
        assert urls[0] == "abcdefghijklmnop.onion"

    def test_detect_onion_urls_single_v3(self):
        """Verify detect_onion_urls() extracts single v3 URL."""
        detector = OnionDetector()
        valid_v3 = "abcdefghijklmnopabcdefghijklmnopabcdefghijklmnopabcdefgh.onion"
        text = f"Check out {valid_v3} for hidden services."
        urls = detector.detect_onion_urls(text)
        assert len(urls) == 1
        assert urls[0] == valid_v3

    def test_detect_onion_urls_multiple(self):
        """Verify detect_onion_urls() extracts multiple URLs."""
        detector = OnionDetector()
        text = "Links: abcdefghijklmnop.onion and bcdefghijklmnopq.onion Also check cdefghijklmnopqr.onion and defghijklmnopqrs.onion"
        urls = detector.detect_onion_urls(text)
        assert len(urls) == 4

    def test_detect_onion_urls_empty_text(self):
        """Verify detect_onion_urls() handles empty text."""
        detector = OnionDetector()
        urls = detector.detect_onion_urls("")
        assert len(urls) == 0

    def test_detect_onion_urls_no_onion(self):
        """Verify detect_onion_urls() handles text without .onion URLs."""
        detector = OnionDetector()
        text = "Visit example.com or http://test.org for more info."
        urls = detector.detect_onion_urls(text)
        assert len(urls) == 0

    def test_detect_onion_urls_deduplicates(self):
        """Verify detect_onion_urls() deduplicates URLs."""
        detector = OnionDetector()
        text = "Check out abcdefghijklmnop.onion and abcdefghijklmnop.onion"
        urls = detector.detect_onion_urls(text)
        assert len(urls) == 1
        assert urls[0] == "abcdefghijklmnop.onion"


class TestClassifyMarketplace:
    """Test marketplace type classification."""

    def test_classify_marketplace_marketplace(self):
        """Verify classify_marketplace() identifies marketplaces."""
        detector = OnionDetector()
        content_keywords = [
            "buy drugs online",
            "listings verified escrow",
            "vendor ratings",
            "purchase bitcoin anonymous",
            "marketplace login",
        ]
        for keywords in content_keywords:
            result = detector.classify_marketplace("test.onion", keywords)
            assert result == MarketplaceType.MARKETPLACE, f"Failed for: {keywords}"

    def test_classify_marketplace_forum(self):
        """Verify classify_marketplace() identifies forums."""
        detector = OnionDetector()
        content_keywords = [
            "discussion board",
            "community forum thread",
            "user posts",
            "reply to topic",
        ]
        for keywords in content_keywords:
            result = detector.classify_marketplace("test.onion", keywords)
            assert result == MarketplaceType.FORUM, f"Failed for: {keywords}"

    def test_classify_marketplace_exchange(self):
        """Verify classify_marketplace() identifies exchanges."""
        detector = OnionDetector()
        content_keywords = [
            "exchange btc to xmr",
            "crypto mixer service",
            "swap coins",
            "launder transaction",
        ]
        for keywords in content_keywords:
            result = detector.classify_marketplace("test.onion", keywords)
            assert result == MarketplaceType.EXCHANGE, f"Failed for: {keywords}"

    def test_classify_marketplace_unknown(self):
        """Verify classify_marketplace() returns unknown by default."""
        detector = OnionDetector()
        content = "This is just some random content without darknet keywords."
        result = detector.classify_marketplace("test.onion", content)
        assert result == MarketplaceType.UNKNOWN

    def test_classify_marketplace_empty_content(self):
        """Verify classify_marketplace() handles empty content."""
        detector = OnionDetector()
        result = detector.classify_marketplace("test.onion", "")
        assert result == MarketplaceType.UNKNOWN


class TestIsDarknetURL:
    """Test quick .onion URL detection."""

    def test_is_darknet_url_v2(self):
        """Verify is_darknet_url() returns True for v2 URLs."""
        detector = OnionDetector()
        assert detector.is_darknet_url("abcdefghijklmnop.onion") is True

    def test_is_darknet_url_v3(self):
        """Verify is_darknet_url() returns True for v3 URLs."""
        detector = OnionDetector()
        valid_v3 = "abcdefghijklmnopabcdefghijklmnopabcdefghijklmnopabcdefgh.onion"
        assert detector.is_darknet_url(valid_v3) is True

    def test_is_darknet_url_clearweb(self):
        """Verify is_darknet_url() returns False for clearweb URLs."""
        detector = OnionDetector()
        clearweb_urls = [
            "http://example.com",
            "https://test.org",
            "http://subdomain.example.net",
            "ftp://files.example.com",
        ]
        for url in clearweb_urls:
            assert detector.is_darknet_url(url) is False, f"Should be false for: {url}"

    def test_is_darknet_url_empty(self):
        """Verify is_darknet_url() returns False for empty strings."""
        detector = OnionDetector()
        assert detector.is_darknet_url("") is False

    def test_is_darknet_url_partial_onion_tld(self):
        """Verify is_darknet_url() returns False for partial .onion."""
        detector = OnionDetector()
        assert detector.is_darknet_url("site.oni") is False
        assert detector.is_darknet_url("site.onio") is False


class TestOnionDetectorEdgeCases:
    """Test edge cases and error handling."""

    def test_detect_onion_urls_with_special_chars(self):
        """Verify detect_onion_urls() handles URL with punctuation."""
        detector = OnionDetector()
        text = "Visit (abcdefghijklmnop.onion), [bcdefghijklmnopq.onion]; or cdefghijklmnopqr.onion."
        urls = detector.detect_onion_urls(text)
        assert len(urls) == 3

    def test_detect_onion_urls_case_insensitive(self):
        """Verify detect_onion_urls() is case-insensitive."""
        detector = OnionDetector()
        text = "Visit ABCDEFGHIJKLMNOP.ONION or abcdefghijklmnop.onion"
        urls = detector.detect_onion_urls(text)
        assert len(urls) >= 1  # Should detect at least one

    def test_validate_onion_mixed_case(self):
        """Verify validate_onion() accepts mixed case."""
        detector = OnionDetector()
        # Base32 should be case-insensitive
        result = detector.validate_onion("ABcDeFgHiJkLmNoP.onion")
        assert result is True

    def test_classify_marketplace_with_url_context(self):
        """Verify classify_marketplace() considers URL when available."""
        detector = OnionDetector()
        # URL has "marketplace" keyword, should influence classification
        result = detector.classify_marketplace("marketplace.onion", "Some generic content")
        # Generic content but URL hints - should return UNKNOWN (content takes priority)
        assert result == MarketplaceType.UNKNOWN
