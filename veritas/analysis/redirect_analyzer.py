"""
Veritas — HTTP Redirect Chain Analyzer

Follows the full redirect chain manually (no auto-follow) to detect:
  - Excessive redirects (> 3 hops)
  - Cross-domain redirects
  - HTTP → HTTPS downgrade
  - Redirect to known ad/tracking domains
  - Suspicious redirect patterns

Returns the complete chain and a risk assessment.
"""

import asyncio
import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

logger = logging.getLogger("veritas.analysis.redirect_analyzer")


@dataclass
class RedirectHop:
    """A single hop in the redirect chain."""
    url: str
    status_code: int
    location: str = ""
    server: str = ""
    is_cross_domain: bool = False
    is_downgrade: bool = False  # HTTPS → HTTP


@dataclass
class RedirectResult:
    """Full redirect chain analysis."""
    original_url: str
    final_url: str = ""
    chain: list[RedirectHop] = field(default_factory=list)
    total_hops: int = 0
    has_cross_domain: bool = False
    has_downgrade: bool = False
    has_tracking_redirect: bool = False
    suspicion_flags: list[str] = field(default_factory=list)
    score: float = 1.0   # 0.0 – 1.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "original_url": self.original_url,
            "final_url": self.final_url,
            "total_hops": self.total_hops,
            "has_cross_domain": self.has_cross_domain,
            "has_downgrade": self.has_downgrade,
            "has_tracking_redirect": self.has_tracking_redirect,
            "suspicion_flags": self.suspicion_flags,
            "score": round(self.score, 3),
            "chain": [
                {
                    "url": h.url,
                    "status_code": h.status_code,
                    "location": h.location,
                    "is_cross_domain": h.is_cross_domain,
                    "is_downgrade": h.is_downgrade,
                }
                for h in self.chain
            ],
            "errors": self.errors,
        }


# Domains commonly used in ad/tracking redirects
_TRACKING_DOMAINS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "facebook.com/tr", "analytics.google.com", "pixel.quantserve.com",
    "ad.doubleclick.net", "ads.yahoo.com", "clickserve.dartsearch.net",
    "click.linksynergy.com", "go.redirectingat.com", "anrdoezrs.net",
    "dpbolvw.net", "jdoqocy.com", "kqzyfj.com", "tkqlhce.com",
    "emjcd.com", "afcyhf.com",
}


class RedirectAnalyzer:
    """Analyze the HTTP redirect chain of a URL."""

    def __init__(self, max_hops: int = 10):
        self.max_hops = max_hops

    async def analyze(self, url: str, timeout: int = 10) -> RedirectResult:
        """Follow redirects manually and analyze the chain."""
        result = RedirectResult(original_url=url)
        current_url = url
        visited = set()

        try:
            loop = asyncio.get_event_loop()

            for _ in range(self.max_hops):
                if current_url in visited:
                    result.suspicion_flags.append("Redirect loop detected")
                    break
                visited.add(current_url)

                hop = await loop.run_in_executor(
                    None, self._fetch_no_follow, current_url, timeout
                )
                if hop is None:
                    break

                result.chain.append(hop)

                # Check cross-domain
                if hop.is_cross_domain:
                    result.has_cross_domain = True

                # Check HTTPS → HTTP downgrade
                if hop.is_downgrade:
                    result.has_downgrade = True
                    result.suspicion_flags.append(
                        f"HTTPS → HTTP downgrade: {hop.url} → {hop.location}"
                    )

                # Check tracking redirect
                loc_domain = self._extract_domain(hop.location)
                if any(td in loc_domain for td in _TRACKING_DOMAINS):
                    result.has_tracking_redirect = True
                    result.suspicion_flags.append(f"Tracking redirect via {loc_domain}")

                # Follow or stop
                if hop.status_code in (301, 302, 303, 307, 308) and hop.location:
                    current_url = urllib.parse.urljoin(current_url, hop.location)
                else:
                    break

            result.final_url = current_url
            result.total_hops = len(result.chain)

            # Flag excessive redirects
            if result.total_hops > 3:
                result.suspicion_flags.append(
                    f"Excessive redirect chain ({result.total_hops} hops)"
                )

            # Compute score
            penalty = 0.0
            if result.total_hops > 3:
                penalty += 0.15
            if result.total_hops > 5:
                penalty += 0.15
            if result.has_cross_domain:
                penalty += 0.15
            if result.has_downgrade:
                penalty += 0.30
            if result.has_tracking_redirect:
                penalty += 0.10

            result.score = max(0.0, 1.0 - penalty)

        except Exception as e:
            logger.error("Redirect analysis failed: %s", e)
            result.errors.append(str(e))
            result.score = 0.5  # Unknown, don't penalize harshly

        return result

    def _fetch_no_follow(self, url: str, timeout: int) -> RedirectHop | None:
        """Fetch URL without following redirects."""
        try:

            class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None  # Don't follow

            opener = urllib.request.build_opener(
                NoRedirectHandler,
                urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            )
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

            try:
                resp = opener.open(req, timeout=timeout)
                return RedirectHop(
                    url=url,
                    status_code=resp.status,
                    location="",
                    server=resp.headers.get("Server", ""),
                )
            except urllib.error.HTTPError as e:
                location = e.headers.get("Location", "") if e.headers else ""
                is_cross = self._is_cross_domain(url, location) if location else False
                is_down = (
                    url.startswith("https://") and location.startswith("http://")
                    if location
                    else False
                )
                return RedirectHop(
                    url=url,
                    status_code=e.code,
                    location=location,
                    server=e.headers.get("Server", "") if e.headers else "",
                    is_cross_domain=is_cross,
                    is_downgrade=is_down,
                )
        except Exception as e:
            logger.debug("Fetch failed for %s: %s", url, e)
            return None

    @staticmethod
    def _extract_domain(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        return (parsed.netloc or "").lower()

    @staticmethod
    def _is_cross_domain(url1: str, url2: str) -> bool:
        d1 = urllib.parse.urlparse(url1).netloc.lower().split(":")[0]
        d2 = urllib.parse.urlparse(url2).netloc.lower().split(":")[0]
        if not d2:
            return False
        # Extract registrable domain (last two parts)
        parts1 = d1.rsplit(".", 2)
        parts2 = d2.rsplit(".", 2)
        root1 = ".".join(parts1[-2:]) if len(parts1) >= 2 else d1
        root2 = ".".join(parts2[-2:]) if len(parts2) >= 2 else d2
        return root1 != root2
