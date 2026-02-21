"""
Veritas — HTTP Security Headers Analyzer

Checks response headers for security best-practices:
  CSP, HSTS, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy, X-XSS-Protection.

Returns a score (0–1) and per-header status breakdown.
"""

import asyncio
import logging
import ssl
from dataclasses import dataclass, field
from typing import Optional

from veritas.analysis import SecurityModuleBase

logger = logging.getLogger("veritas.analysis.security_headers")


@dataclass
class HeaderCheck:
    """Result for a single security header."""
    header: str
    present: bool
    value: str = ""
    severity: str = "medium"     # low / medium / high / critical
    status: str = "missing"      # present / missing / weak
    recommendation: str = ""


@dataclass
class SecurityHeadersResult:
    """Full header analysis result."""
    url: str
    score: float = 1.0           # 0.0 – 1.0
    checks: list[HeaderCheck] = field(default_factory=list)
    response_code: int = 0
    server: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "score": round(self.score, 3),
            "response_code": self.response_code,
            "server": self.server,
            "checks": [
                {
                    "header": c.header,
                    "present": c.present,
                    "value": c.value[:200],
                    "severity": c.severity,
                    "status": c.status,
                    "recommendation": c.recommendation,
                }
                for c in self.checks
            ],
            "errors": self.errors,
        }


# Header definitions: (header_name, severity_if_missing, recommendation)
_HEADER_DEFS: list[tuple[str, str, str]] = [
    (
        "Content-Security-Policy",
        "high",
        "Add a CSP header to prevent XSS, clickjacking, and data injection attacks.",
    ),
    (
        "Strict-Transport-Security",
        "high",
        "Add HSTS with max-age ≥ 31536000 to enforce HTTPS.",
    ),
    (
        "X-Frame-Options",
        "medium",
        "Set X-Frame-Options to DENY or SAMEORIGIN to prevent clickjacking.",
    ),
    (
        "X-Content-Type-Options",
        "medium",
        "Set to 'nosniff' to prevent MIME-type sniffing.",
    ),
    (
        "Referrer-Policy",
        "low",
        "Set Referrer-Policy to 'strict-origin-when-cross-origin' or stricter.",
    ),
    (
        "Permissions-Policy",
        "low",
        "Define a Permissions-Policy to restrict browser features (camera, mic, geolocation).",
    ),
    (
        "X-XSS-Protection",
        "low",
        "Set to '1; mode=block' (deprecated but still signals security awareness).",
    ),
]

# Weight per severity for score calculation
_SEVERITY_WEIGHT = {"critical": 0.25, "high": 0.20, "medium": 0.12, "low": 0.05}


class SecurityHeaderAnalyzer(SecurityModuleBase):
    """Analyze HTTP security headers of a URL."""

    # Module metadata for auto-discovery
    module_name = "security_headers"
    category = "headers"
    requires_page = False

    async def analyze(self, url: str, timeout: int = 15, page=None) -> SecurityHeadersResult:
        """Fetch URL headers and evaluate security posture."""
        result = SecurityHeadersResult(url=url)
        try:
            headers = await self._fetch_headers(url, timeout)
            if headers is None:
                result.errors.append("Failed to fetch headers")
                result.score = 0.0
                return result

            resp_headers, result.response_code, result.server = headers

            total_penalty = 0.0
            for hdr_name, severity, rec in _HEADER_DEFS:
                value = resp_headers.get(hdr_name, "")
                present = bool(value)
                status = "present" if present else "missing"

                # Check for weak values
                if present:
                    status = self._evaluate_strength(hdr_name, value)

                check = HeaderCheck(
                    header=hdr_name,
                    present=present,
                    value=value,
                    severity=severity if status != "present" else "info",
                    status=status,
                    recommendation=rec if status != "present" else "",
                )
                result.checks.append(check)

                if status != "present":
                    total_penalty += _SEVERITY_WEIGHT.get(severity, 0.1)

            result.score = max(0.0, 1.0 - total_penalty)

        except Exception as e:
            logger.error("Security header analysis failed: %s", e)
            result.errors.append(str(e))
            result.score = 0.0

        return result

    async def _fetch_headers(
        self, url: str, timeout: int
    ) -> Optional[tuple[dict[str, str], int, str]]:
        """Fetch response headers using urllib (no extra deps)."""
        import urllib.error
        import urllib.request

        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=timeout, context=ctx),
            )
            hdrs = {k: v for k, v in resp.headers.items()}
            code = resp.status
            server = hdrs.get("Server", "")
            return hdrs, code, server
        except urllib.error.HTTPError as e:
            hdrs = {k: v for k, v in e.headers.items()} if e.headers else {}
            return hdrs, e.code, hdrs.get("Server", "")
        except Exception as e:
            logger.warning("Header fetch failed for %s: %s", url, e)
            return None

    @staticmethod
    def _evaluate_strength(header: str, value: str) -> str:
        """Check if a present header has a strong configuration."""
        val_lower = value.lower()

        if header == "Strict-Transport-Security":
            # Check max-age >= 1 year
            if "max-age=" in val_lower:
                try:
                    age = int(val_lower.split("max-age=")[1].split(";")[0].strip())
                    if age < 31536000:
                        return "weak"
                except (ValueError, IndexError):
                    return "weak"
            else:
                return "weak"

        if header == "Content-Security-Policy":
            # Very permissive CSP is almost worse than none
            if "unsafe-inline" in val_lower and "unsafe-eval" in val_lower:
                return "weak"

        if header == "X-Frame-Options":
            if val_lower not in ("deny", "sameorigin"):
                return "weak"

        if header == "X-Content-Type-Options":
            if val_lower != "nosniff":
                return "weak"

        return "present"
