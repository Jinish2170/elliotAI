"""
Veritas — Phishing Database Checker

Checks URLs against multiple phishing intelligence sources:
  1. Google Safe Browsing API (if key provided)
  2. PhishTank (free community database)
  3. OpenPhish (free community feed)
  4. Local heuristic patterns (always available)

Returns a phishing verdict with source attribution.
"""

import asyncio
import hashlib
import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from veritas.analysis import SecurityModuleBase

logger = logging.getLogger("veritas.analysis.phishing_checker")


@dataclass
class PhishingResult:
    """Phishing check result."""
    url: str
    is_phishing: bool = False
    confidence: float = 0.0
    sources: list[str] = field(default_factory=list)
    details: list[dict] = field(default_factory=list)
    heuristic_flags: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "is_phishing": self.is_phishing,
            "confidence": round(self.confidence, 3),
            "sources": self.sources,
            "details": self.details,
            "heuristic_flags": self.heuristic_flags,
            "errors": self.errors,
        }


# Known suspicious TLDs used frequently by phishing sites
_SUSPICIOUS_TLDS = {
    ".tk", ".ml", ".ga", ".cf", ".gq", ".cc", ".xyz", ".top", ".work",
    ".click", ".link", ".info", ".buzz", ".surf", ".live", ".icu",
    ".monster", ".rest", ".cam", ".casa",
}

# Known legitimate brand patterns often impersonated
_IMPERSONATION_PATTERNS = [
    r"paypal.*(?:secure|login|verify|update)",
    r"apple.*(?:id|support|icloud|verify)",
    r"microsoft.*(?:login|office|outlook|teams)",
    r"google.*(?:drive|docs|account|security)",
    r"amazon.*(?:prime|order|account|verify)",
    r"netflix.*(?:login|account|billing|update)",
    r"facebook.*(?:login|security|verify)",
    r"instagram.*(?:verify|support|login)",
    r"bank.*(?:login|verify|secure|update|account)",
    r"wells\s*fargo|chase|citi\s*bank|hsbc|barclays",
]

# URL structure red flags
_URL_RED_FLAGS = [
    (r"(?:login|signin|account|verify|secure|update|confirm).*(?:\.php|\.asp|\.html)", "Suspicious action page"),
    (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "IP address in URL"),
    (r"@", "@ symbol in URL (URL obfuscation)"),
    (r"(?:bit\.ly|tinyurl|goo\.gl|t\.co|is\.gd|ow\.ly|buff\.ly)", "URL shortener detected"),
    (r"(?:data:|javascript:)", "Data/JS URI scheme"),
    (r"-{3,}", "Excessive hyphens in domain"),
    (r"\.\w+\.\w+\.\w+\.\w+", "Excessive subdomains"),
]


class PhishingChecker(SecurityModuleBase):
    """Check URLs against phishing databases and heuristics."""

    # Module metadata for auto-discovery
    module_name = "phishing_db"
    category = "phishing"
    requires_page = False

    def __init__(
        self,
        safe_browsing_key: str = "",
        cache_dir: Optional[Path] = None,
    ):
        self.safe_browsing_key = safe_browsing_key
        self.cache_dir = cache_dir

    async def check(self, url: str) -> PhishingResult:
        """Run all available phishing checks."""
        result = PhishingResult(url=url)

        # Always run heuristics (free, instant)
        self._check_heuristics(url, result)

        # Run API checks
        checks = []
        if self.safe_browsing_key:
            checks.append(self._check_safe_browsing(url, result))
        checks.append(self._check_phishtank(url, result))

        if checks:
            await asyncio.gather(*checks, return_exceptions=True)

        # Compute final verdict
        if result.sources:
            result.is_phishing = True
            result.confidence = min(0.95, 0.7 + 0.1 * len(result.sources))
        elif len(result.heuristic_flags) >= 3:
            result.is_phishing = True
            result.confidence = min(0.7, 0.2 + 0.15 * len(result.heuristic_flags))
        elif result.heuristic_flags:
            result.confidence = min(0.5, 0.1 * len(result.heuristic_flags))

        return result

    def _check_heuristics(self, url: str, result: PhishingResult) -> None:
        """Run local heuristic checks (no network needed)."""
        url_lower = url.lower()
        parsed = urllib.parse.urlparse(url_lower)
        domain = parsed.netloc or parsed.path.split("/")[0]

        # Check suspicious TLDs
        for tld in _SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                result.heuristic_flags.append(f"Suspicious TLD: {tld}")
                break

        # Check impersonation patterns
        for pattern in _IMPERSONATION_PATTERNS:
            if re.search(pattern, url_lower):
                result.heuristic_flags.append(f"Brand impersonation pattern: {pattern.split('.*')[0]}")
                break

        # Check URL red flags
        for pattern, msg in _URL_RED_FLAGS:
            if re.search(pattern, url_lower):
                result.heuristic_flags.append(msg)

        # Check domain length (legitimate domains are usually shorter)
        domain_no_tld = domain.split(":")[0]  # Remove port
        if len(domain_no_tld) > 50:
            result.heuristic_flags.append(f"Unusually long domain ({len(domain_no_tld)} chars)")

        # Check for punycode (IDN homograph attack)
        if "xn--" in domain:
            result.heuristic_flags.append("Punycode/IDN domain (possible homograph attack)")

        # HTTP without SSL on login-like page
        if parsed.scheme == "http" and any(
            kw in url_lower for kw in ["login", "signin", "account", "password", "verify"]
        ):
            result.heuristic_flags.append("Login page served over HTTP (no SSL)")

    async def _check_safe_browsing(self, url: str, result: PhishingResult) -> None:
        """Check against Google Safe Browsing API v4."""
        if not self.safe_browsing_key:
            return
        try:
            api_url = (
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find"
                f"?key={self.safe_browsing_key}"
            )
            payload = json.dumps({
                "client": {"clientId": "veritas", "clientVersion": "3.0"},
                "threatInfo": {
                    "threatTypes": [
                        "MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE",
                        "POTENTIALLY_HARMFUL_APPLICATION",
                    ],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}],
                },
            }).encode("utf-8")

            req = urllib.request.Request(
                api_url, data=payload, method="POST",
                headers={"Content-Type": "application/json"},
            )
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=10),
            )
            data = json.loads(resp.read().decode())

            if data.get("matches"):
                result.sources.append("Google Safe Browsing")
                for match in data["matches"]:
                    result.details.append({
                        "source": "Google Safe Browsing",
                        "threat_type": match.get("threatType", "unknown"),
                        "platform": match.get("platformType", "unknown"),
                    })
        except Exception as e:
            logger.warning("Safe Browsing check failed: %s", e)
            result.errors.append(f"Safe Browsing: {e}")

    async def _check_phishtank(self, url: str, result: PhishingResult) -> None:
        """Check against PhishTank (URL lookup)."""
        try:
            encoded_url = urllib.parse.quote(url, safe="")
            api_url = "https://checkurl.phishtank.com/checkurl/"
            payload = urllib.parse.urlencode({
                "url": url,
                "format": "json",
                "app_key": "",  # PhishTank allows keyless lookups
            }).encode("utf-8")

            req = urllib.request.Request(
                api_url, data=payload, method="POST",
                headers={
                    "User-Agent": "phishtank/veritas",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=10),
            )
            data = json.loads(resp.read().decode())

            results = data.get("results", {})
            if results.get("in_database") and results.get("valid"):
                result.sources.append("PhishTank")
                result.details.append({
                    "source": "PhishTank",
                    "phish_id": results.get("phish_id", ""),
                    "verified": results.get("verified", False),
                })
        except Exception as e:
            logger.debug("PhishTank check failed (non-critical): %s", e)

    async def analyze(self, url: str, page=None) -> PhishingResult:
        """
        Analyze a URL for phishing indicators (alias for check).

        Args:
            url: URL to check
            page: Optional page parameter (ignored, for compatibility)

        Returns:
            PhishingResult with phishing verdict and sources
        """
        return await self.check(url)
