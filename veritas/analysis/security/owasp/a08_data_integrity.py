"""
OWASP A08: Software and Data Integrity Failures Module

Detects integrity failures including:
- Insecure deserialization
- Unverified CDN dependencies
- Missing Subresource Integrity (SRI)
- Software supply chain risks
- Package tampering indicators

CWE Mappings:
- CWE-502: Deserialization of Untrusted Data (Critical)
- CWE-494: Download of Code Without Integrity Check (Medium)
- CWE-347: Improper Verification of Cryptographic Signature (Medium)
- CWE-829: Inclusion of Functionality from Untrusted Control Sphere (Medium)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class DataIntegrityFailuresModule(SecurityModule):
    """
    OWASP A08: Software and Data Integrity Failures detection module.

    Analyzes scripts, libraries, and deserialization patterns for integrity
    vulnerabilities including insecure deserialization, missing SRI, and
    unverified dependencies.
    """

    # MEDIUM tier for integrity analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 10

    @property
    def category_id(self) -> str:
        return "owasp_a08"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for data integrity failures.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze page content for insecure deserialization patterns
        if page_content:
            findings.extend(self._analyze_deserialization(page_content))
            findings.extend(self._analyze_sri(page_content))

        # Analyze DOM metadata for integrity issues
        if dom_meta:
            findings.extend(self._analyze_dom_integrity(dom_meta))

        # Analyze URL for supply chain indicators
        findings.extend(self._analyze_supply_chain(url))

        return findings

    def _analyze_deserialization(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for insecure deserialization patterns."""
        findings = []

        # Insecure deserialization patterns
        deserialization_patterns = [
            (r"""pickle\.loads\s*\(""", "pickle.loads()", "Python pickle deserialization", 0.90),
            (r"""pickle\.load\s*\(""", "pickle.load()", "Python pickle deserialization", 0.90),
            (r"""yaml\.load\s*\(""", "yaml.load()", "YAML deserialization", 0.85),
            (r"""YAML\.load\s*\(""", "YAML.load()", "YAML deserialization", 0.85),
            (r"""eval\s*\(\s*['\"]base64""", "eval with base64", "Potential unsafe eval", 0.75),
            (r"""eval\s*\(\s*atob\s*\(""", "eval with atob", "Browser eval of base64", 0.70),
            (r"""JSON\.parse\s*\([^)]*\)\s*\.\s*\w+\.apply\s*\(""", "JSON.parse with apply", "Potential deserialization", 0.65),
            (r"""Object\.assign\s*\([^)]*JSON\.parse""", "Object.assign with JSON.parse", "Potential object injection", 0.60),
            (r"""Marshal\.load\s*\(""", "Marshal.load()", "Ruby Marshal deserialization", 0.90),
            (r"""serial\.unserialize\s*\(""", "serial.unserialize()", "PHP unserialize", 0.90),
            (r"""XmlSerializer\.Deserialize\s*\(""", "XmlSerializer.Deserialize()", "XML deserialization", 0.70),
        ]

        page_content_lower = page_content.lower()

        for pattern, name, description, confidence in deserialization_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                # Skip if in comment
                matches = list(re.finditer(pattern, page_content, re.IGNORECASE))
                for match in matches:
                    match_start = max(0, match.start() - 30)
                    context = page_content[match_start:match.start()]
                    if any(comment in context for comment in ["<!--", "//", "/*", "#"]):
                        continue

                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="insecure_deserialization",
                        severity="critical",
                        confidence=confidence,
                        description=f"Insecure deserialization pattern detected: {name}. {description}. Deserializing untrusted data can lead to RCE.",
                        evidence=f"Pattern: {pattern}",
                        cwe_id="CWE-502",
                        cvss_score=9.8,
                        recommendation="Avoid deserialization of untrusted data. Use safe alternatives (JSON with schema validation), signed serialization formats, or reject deserialization entirely.",
                    ))
                    break
                if findings:
                    break

        # Check for JavaScript unsafe code patterns
        unsafe_js_patterns = [
            (r"""eval\s*\(\s*""", "eval()", 0.80),
            (r"""new\s+Function\s*\(""", "new Function()", 0.80),
            (r"""setTimeout\s*\(\s*['\"]""", "setTimeout with string", 0.65),
            (r"""setInterval\s*\(\s*['\"]""", "setInterval with string", 0.65),
        ]

        for pattern, name, confidence in unsafe_js_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                # Check if it processes external data
                context_length = 200
                for match in re.finditer(pattern, page_content, re.IGNORECASE):
                    context = page_content[max(0, match.start() - context_length):match.start() + match.end() + context_length]
                    if re.search(r"(?:location\.|window\.|document\.|params|query|body|cookie)", context, re.IGNORECASE):
                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="unsafe_code_generation",
                            severity="high",
                            confidence=confidence,
                            description=f"Unsafe code generation pattern ({name}) that may process external data. This can lead to XSS or injection attacks.",
                            evidence=f"Pattern: {pattern}",
                            cwe_id="CWE-937",
                            cvss_score=8.6,
                            recommendation="Avoid eval(), new Function(), and setTimeout with string arguments. Use safer alternatives like createElement or arrow functions.",
                        ))
                        break
                if findings:
                    break

        return findings

    def _analyze_sri(self, page_content: str) -> List[SecurityFinding]:
        """Analyze Subresource Integrity (SRI) usage."""
        findings = []

        # Find all script tags
        script_tag_pattern = r"""<script[^>]*(?:src\s*=\s*['"]([^'"]+)['"][^>]*)>"""
        script_matches = re.finditer(script_tag_pattern, page_content, re.IGNORECASE)

        # CDN domains that should have SRI
        cdn_domains = [
            "cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com",
            "code.jquery.com", "ajax.googleapis.com", "browsercdn.net",
        ]

        external_scripts_without_sri = []

        for match in script_matches:
            script_src = match.group(1)
            script_tag = match.group(0)

            # Check if it's a CDN script
            is_cdn = any(cdn in script_src.lower() for cdn in cdn_domains)

            if is_cdn:
                # Check if script tag has integrity attribute
                has_integrity = "integrity=" in script_tag.lower()

                if not has_integrity:
                    external_scripts_without_sri.append(script_src)

        if external_scripts_without_sri:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_sri",
                severity="medium",
                confidence=0.75,
                description=f"CDN script(s) without Subresource Integrity (SRI): {len(external_scripts_without_sri)} script(s). SRI prevents serving tampered resources.",
                evidence=f"Examples: {', '.join(list(external_scripts_without_sri)[:3])}",
                cwe_id="CWE-494",
                cvss_score=5.9,
                recommendation="Add integrity attribute to all CDN script tags. Use: integrity='sha384-...' crossorigin='anonymous'. Consider using package managers instead of CDNs.",
            ))

        return findings

    def _analyze_dom_integrity(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze DOM metadata for integrity issues."""
        findings = []

        scripts = dom_meta.get("scripts", [])

        # Check for scripts from unpkg.com (npm CDNs)
        for script in scripts:
            src = script.get("src", "")
            if "unpkg.com" in src.lower():
                integrity_attr = script.get("integrity", "")
                if not integrity_attr:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="unpkg_no_integrity",
                        severity="medium",
                        confidence=0.70,
                        description="Script loaded from unpkg.com (npm CDN) without Subresource Integrity (SRI) attribute.",
                        evidence=f"Script source: {src}",
                        cwe_id="CWE-494",
                        cvss_score="5.9",
                        recommendation="Add integrity and crossorigin attributes to unpkg.com scripts. Consider installing via npm instead.",
                    ))
                    break

            # Check for jsdelivr scripts
            if "jsdelivr.net" in src.lower():
                integrity_attr = script.get("integrity", "")
                if not integrity_attr:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="jsdelivr_no_integrity",
                        severity="medium",
                        confidence=0.70,
                        description="Script loaded from jsdelivr.net without Subresource Integrity (SRI) attribute.",
                        evidence=f"Script source: {src}",
                        cwe_id="CWE-494",
                        cvss_score="5.9",
                        recommendation="Add integrity and crossorigin attributes to jsdelivr.net scripts. Consider using package managers.",
                    ))
                    break

        # Check for integrity attributes on local scripts (rarely needed but indicates concern)
        for script in scripts:
            src = script.get("src", "")
            integrity_attr = script.get("integrity", "")

            # Integrity on non-CDN script (unusual)
            if integrity_attr and not any(cdn in src.lower() for cdn in ["cdn", "unpkg", "jsdelivr", "cloudflare"]):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="integrity_on_non_cdn",
                    severity="low",
                    confidence=0.50,
                    description="Integrity attribute found on non-CDN script. Consider hosting scripts locally instead of using integrity checks for local resources.",
                    evidence=f"Script source: {src}",
                    cwe_id="CWE-347",
                    cvss_score=2.1,
                    recommendation="Consider bundling local dependencies. Use integrity primarily for external CDN resources.",
                ))

        return findings

    def _analyze_supply_chain(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for software supply chain indicators."""
        findings = []

        # Detect usage of public npm/PyPI/etc CDNs (supply chain risk)
        supply_chain_domains = [
            "unpkg.com",      # npm
            "jsdelivr.net",   # npm
            "cdn.jsdelivr.net",
            "pypi.org",       # Python
            "rubygems.org",   # Ruby
            "packagist.org",  # PHP
        ]

        url_lower = url.lower()
        supply_chain_found = False

        for domain in supply_chain_domains:
            if domain in url_lower:
                supply_chain_found = True
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="supply_chain_dependency",
                    severity="low",
                    confidence=0.55,
                    description=f"Public package dependency detected: {domain}. Public CDN usage introduces supply chain risk if dependencies are compromised.",
                    evidence=f"URL contains: {domain}",
                    cwe_id="CWE-829",
                    cvss_score=3.5,
                    recommendation="Consider using package managers to host dependencies locally. Monitor for security advisories. Use locked dependency versions.",
                    url_finding=True,
                ))
                break

        # Check for generic indicators of package managers in URL
        package_manager_patterns = [
            r"node_modules",  # npm
            r"vendor",  # Composer / Bundler
            r"bower_components",  # Bower
        ]

        for pattern in package_manager_patterns:
            if re.search(pattern, url_lower):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="dev_artifact_url",
                    severity="low",
                    confidence=0.50,
                    description="Development artifact directory pattern found in URL. Development files should not be served in production.",
                    evidence=f"URL contains pattern: {pattern}",
                    cwe_id="CWE-200",
                    cvss_score=3.1,
                    recommendation="Ensure production builds exclude development artifacts. Use appropriate build processes.",
                    url_finding=True,
                ))
                break

        return findings
