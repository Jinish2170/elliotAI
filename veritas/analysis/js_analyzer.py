"""
Veritas — JavaScript Obfuscation & Malware Detector

Runs inside a Playwright page context to detect:
  - eval() usage in inline scripts
  - Base64-encoded script content
  - Known crypto miner signatures (CoinHive, JSEcoin, etc.)
  - Obfuscated variable names (high-entropy strings)
  - WebSocket connections to known mining pools
  - Suspicious dynamic script injection

Returns a risk score and list of flagged scripts.
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field

from veritas.analysis import SecurityModuleBase

logger = logging.getLogger("veritas.analysis.js_analyzer")


@dataclass
class JSFlag:
    """A single flagged JavaScript issue."""
    category: str      # eval, base64, miner, obfuscation, websocket, injection
    severity: str      # low / medium / high / critical
    description: str
    script_index: int = -1
    evidence: str = ""


@dataclass
class JSAnalysisResult:
    """Full JavaScript analysis result."""
    url: str
    total_scripts: int = 0
    inline_scripts: int = 0
    external_scripts: int = 0
    flags: list[JSFlag] = field(default_factory=list)
    score: float = 1.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "total_scripts": self.total_scripts,
            "inline_scripts": self.inline_scripts,
            "external_scripts": self.external_scripts,
            "score": round(self.score, 3),
            "flags": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "description": f.description,
                    "evidence": f.evidence[:200],
                }
                for f in self.flags
            ],
            "errors": self.errors,
        }


# Known crypto miner patterns
_MINER_SIGNATURES = [
    (r"coinhive\.min\.js|coinhive\.com/lib", "CoinHive miner", "critical"),
    (r"jsecoin\.com|load\.jsecoin\.com", "JSEcoin miner", "critical"),
    (r"cryptoloot\.pro|CryptoLoot", "CryptoLoot miner", "critical"),
    (r"coin-hive\.com|authedmine\.com", "CoinHive (alt domain)", "critical"),
    (r"webminepool\.com|minero\.cc", "Web mining pool", "critical"),
    (r"ppoi\.org|cryptonight", "CryptoNight miner", "critical"),
    (r"CoinImp\.com|coinimp\.min\.js", "CoinImp miner", "critical"),
    (r"miner\.start\(|startMining\(", "Miner start call", "high"),
    (r"new\s+(?:Client|Miner|Worker)\s*\(\s*['\"]", "Miner client init", "high"),
]

# Known mining pool WebSocket endpoints
_MINING_POOLS = [
    "wss://",
    "pool.coinhive.com",
    "pool.supportxmr.com",
    "xmr.pool.minergate.com",
    "mine.moneropool.com",
    "pool.hashvault.pro",
]

# JavaScript for extracting script data from page
_SCRIPT_EXTRACTION_JS = """
() => {
    const scripts = document.querySelectorAll('script');
    return Array.from(scripts).map((script, idx) => ({
        index: idx,
        src: script.getAttribute('src') || '',
        type: script.getAttribute('type') || '',
        content: (script.textContent || '').substring(0, 5000),
        isInline: !script.getAttribute('src'),
    }));
}
"""

# JS to detect WebSocket connections
_WEBSOCKET_DETECTION_JS = """
() => {
    const results = [];
    // Check for WebSocket patterns in page scripts
    const scripts = document.querySelectorAll('script');
    scripts.forEach((script, idx) => {
        const content = script.textContent || '';
        const wsMatches = content.match(/new\\s+WebSocket\\s*\\(\\s*['"]([^'"]+)['"]/g);
        if (wsMatches) {
            results.push({index: idx, matches: wsMatches});
        }
    });
    return results;
}
"""


class JSObfuscationDetector(SecurityModuleBase):
    """Detect obfuscated JavaScript and malware in a page."""

    # Module metadata for auto-discovery
    module_name = "js_analysis"
    category = "js"
    requires_page = True  # Needs Playwright Page object

    async def analyze(self, url: str, page=None) -> JSAnalysisResult:
        """
        Analyze all scripts on the page for suspicious patterns.

        Args:
            url: URL of the page
            page: Playwright Page object (navigated) - required for this module
        """
        result = JSAnalysisResult(url=url)

        if page is None:
            result.errors.append("JS analysis requires Playwright Page object")
            result.score = 0.0
            return result

        try:
            scripts = await page.evaluate(_SCRIPT_EXTRACTION_JS)
            result.total_scripts = len(scripts)
            result.inline_scripts = sum(1 for s in scripts if s.get("isInline"))
            result.external_scripts = result.total_scripts - result.inline_scripts

            for script in scripts:
                self._analyze_script(script, result)

            # Check for dynamic WebSocket connections
            try:
                ws_data = await page.evaluate(_WEBSOCKET_DETECTION_JS)
                for ws in ws_data:
                    for m in ws.get("matches", []):
                        for pool in _MINING_POOLS:
                            if pool in m.lower():
                                result.flags.append(JSFlag(
                                    category="websocket",
                                    severity="critical",
                                    description=f"WebSocket connection to mining pool",
                                    script_index=ws.get("index", -1),
                                    evidence=m[:100],
                                ))
            except Exception:
                pass

            # Compute score
            penalty = 0.0
            for flag in result.flags:
                if flag.severity == "critical":
                    penalty += 0.25
                elif flag.severity == "high":
                    penalty += 0.15
                elif flag.severity == "medium":
                    penalty += 0.08
                elif flag.severity == "low":
                    penalty += 0.03
            result.score = max(0.0, 1.0 - penalty)

        except Exception as e:
            logger.error("JS analysis failed: %s", e)
            result.errors.append(str(e))

        return result

    def _analyze_script(self, script: dict, result: JSAnalysisResult) -> None:
        """Analyze a single script element."""
        content = script.get("content", "")
        src = script.get("src", "")
        idx = script.get("index", -1)

        combined = f"{content} {src}"

        # 1. Check for crypto miner signatures
        for pattern, name, severity in _MINER_SIGNATURES:
            if re.search(pattern, combined, re.IGNORECASE):
                result.flags.append(JSFlag(
                    category="miner",
                    severity=severity,
                    description=f"Crypto miner detected: {name}",
                    script_index=idx,
                    evidence=re.search(pattern, combined, re.IGNORECASE).group(0)[:100],
                ))
                return  # No need to check further, it's already critical

        if not content or len(content) < 50:
            return

        # 2. Check for eval() usage
        eval_matches = re.findall(r'\beval\s*\(', content)
        if eval_matches:
            count = len(eval_matches)
            sev = "high" if count > 2 else "medium"
            result.flags.append(JSFlag(
                category="eval",
                severity=sev,
                description=f"eval() called {count} time(s) — dynamic code execution",
                script_index=idx,
                evidence=f"eval() ×{count}",
            ))

        # 3. Check for base64-encoded content
        b64_matches = re.findall(
            r'(?:atob|btoa)\s*\(\s*[\'"]([A-Za-z0-9+/=]{40,})[\'"]',
            content,
        )
        if b64_matches:
            result.flags.append(JSFlag(
                category="base64",
                severity="medium",
                description=f"Base64-encoded string execution ({len(b64_matches)} occurrences)",
                script_index=idx,
                evidence=b64_matches[0][:60] + "...",
            ))

        # 4. Check large encoded strings (possible obfuscation)
        hex_strings = re.findall(r'(?:\\x[0-9a-fA-F]{2}){20,}', content)
        unicode_strings = re.findall(r'(?:\\u[0-9a-fA-F]{4}){10,}', content)
        if hex_strings or unicode_strings:
            count = len(hex_strings) + len(unicode_strings)
            result.flags.append(JSFlag(
                category="obfuscation",
                severity="high",
                description=f"Encoded strings detected ({count} sequences) — possible obfuscation",
                script_index=idx,
                evidence="hex/unicode escape sequences",
            ))

        # 5. Check for high-entropy variable names (obfuscation indicator)
        entropy = self._compute_identifier_entropy(content)
        if entropy > 4.0 and len(content) > 500:
            result.flags.append(JSFlag(
                category="obfuscation",
                severity="medium",
                description=f"High identifier entropy ({entropy:.1f}) suggests code obfuscation",
                script_index=idx,
                evidence=f"Entropy: {entropy:.1f}/6.0",
            ))

        # 6. Check for document.write with external sources
        doc_writes = re.findall(
            r'document\.write\s*\(\s*(?:unescape|decodeURIComponent)',
            content,
        )
        if doc_writes:
            result.flags.append(JSFlag(
                category="injection",
                severity="high",
                description="document.write() with decode — possible DOM injection",
                script_index=idx,
                evidence="document.write(unescape/decode...)",
            ))

    @staticmethod
    def _compute_identifier_entropy(code: str) -> float:
        """
        Compute the Shannon entropy of JavaScript identifiers.
        High entropy (> 4.0) suggests obfuscated variable names.
        """
        # Extract identifiers (variable/function names)
        identifiers = re.findall(r'\b([a-zA-Z_$][a-zA-Z0-9_$]{2,})\b', code)
        if len(identifiers) < 10:
            return 0.0

        # Compute character-level entropy of all identifiers concatenated
        chars = "".join(identifiers)
        if not chars:
            return 0.0

        freq = Counter(chars)
        total = len(chars)
        entropy = -sum(
            (count / total) * math.log2(count / total)
            for count in freq.values()
            if count > 0
        )
        return round(entropy, 2)
