"""
OWASP A06: Vulnerable and Outdated Components Module

Detects vulnerable and outdated components including:
- Outdated JavaScript libraries (jQuery, Bootstrap, React, Angular)
- Known vulnerable library versions
- Exposed package management files
- Missing integrity checks on CDNs

CWE Mappings:
- CWE-937: Outdated Components (High)
- CWE-434: Unrestricted Upload of File (High)
- CWE-502: Deserialization of Untrusted Data (Critical)
- CWE-829: Inclusion of Functionality from Untrusted Control Sphere (Medium)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class VulnerableComponentsModule(SecurityModule):
    """
    OWASP A06: Vulnerable and Outdated Components detection module.

    Analyzes scripts and library references for outdated versions,
    known vulnerabilities, and missing integrity checks.
    """

    # MEDIUM tier for component analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 10

    # Known vulnerable library versions (simplified thresholds)
    VULNERABLE_VERSIONS = {
        "jquery": {
            "threshold": (3, 5, 0),  # < 3.5.0
            "cwe": "CWE-937",
            "cvss": 7.5,
            "severity": "high",
        },
        "bootstrap": {
            "threshold": (4, 5, 0),  # < 4.5.0
            "cwe": "CWE-937",
            "cvss": 6.5,
            "severity": "medium",
        },
        "react": {
            "threshold": (16, 9, 0),  # < 16.9.0
            "cwe": "CWE-937",
            "cvss": 6.5,
            "severity": "medium",
        },
        "angular": {
            "threshold": (1, 7, 0),  # < 1.7.0
            "cwe": "CWE-937",
            "cvss": 6.5,
            "severity": "medium",
        },
        "vue": {
            "threshold": (2, 6, 0),  # < 2.6.0
            "cwe": "CWE-937",
            "cvss": 6.5,
            "severity": "medium",
        },
        "d3": {
            "threshold": (5, 0, 0),  # < 5.0.0
            "cwe": "CWE-937",
            "cvss": 5.9,
            "severity": "low",
        },
        "moment": {
            "threshold": (2, 24, 0),  # < 2.24.0
            "cwe": "CWE-937",
            "cvss": 6.1,
            "severity": "medium",
        },
        "lodash": {
            "threshold": (4, 17, 15),  # < 4.17.15
            "cwe": "CWE-937",
            "cvss": 7.5,
            "severity": "high",
        },
    }

    @property
    def category_id(self) -> str:
        return "owasp_a06"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for vulnerable and outdated components.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze page content for scripts and libraries
        if page_content:
            findings.extend(self._analyze_scripts(page_content))
            findings.extend(self._analyze_package_files(page_content))
            findings.extend(self._analyze_cdn_integrity(page_content, url))

        # Analyze DOM metadata for script references
        if dom_meta:
            findings.extend(self._analyze_dom_scripts(dom_meta))

        return findings

    def _analyze_scripts(self, page_content: str) -> List[SecurityFinding]:
        """Analyze script tags for outdated library versions."""
        findings = []

        # Pattern to extract script sources
        script_src_pattern = r"""<script[^>]*src\s*=\s*['"]([^'"]+)['"][^>]*>"""
        script_matches = re.findall(script_src_pattern, page_content, re.IGNORECASE)

        for script_src in script_matches:
            # Check script source for library names and versions
            for lib_name, config in self.VULNERABLE_VERSIONS.items():
                lib_pattern = rf"{lib_name}[-.]?(\d+(?:\.\d+)?(?:\.\d+)?)"
                match = re.search(lib_pattern, script_src, re.IGNORECASE)

                if match:
                    version_str = match.group(1)

                    # Parse version (may be 1.2.3 format or 1.2 format)
                    version_parts = version_str.split(".")
                    while len(version_parts) < 3:
                        version_parts.append("0")

                    try:
                        version_tuple = tuple(int(v) for v in version_parts)

                        # Check if version is below threshold
                        threshold = config["threshold"]
                        if version_tuple < threshold:
                            findings.append(SecurityFinding(
                                category_id=self.category_id,
                                pattern_type=f"outdated_{lib_name}",
                                severity=config["severity"],
                                confidence=0.80,
                                description=f"Outdated {lib_name.capitalize()} library detected (v{version_str}). Current vulnerable: versions less than v{'.'.join(str(p) for p in threshold)}",
                                evidence=f"Script source: {script_src}",
                                cwe_id=config["cwe"],
                                cvss_score=config["cvss"],
                                recommendation=f"Update {lib_name.capitalize()} to version v{'.'.join(str(p) for p in threshold)} or later. Check security advisories for vulnerabilities in older versions.",
                            ))
                    except ValueError:
                        # Could not parse version, skip
                        pass

        # Check for scripts without integrity attribute on CDNs
        # (further analyzed in _analyze_cdn_integrity)

        return findings

    def _analyze_package_files(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for exposed package management files."""
        findings = []

        # Pattern for package file references
        package_file_patterns = [
            (r"""['"]package-lock\.json['"]""", "package-lock.json (npm)", "high"),
            (r"""['"]package\.json['"]""", "package.json (npm)", "high"),
            (r"""['"]yarn\.lock['"]""", "yarn.lock (yarn)", "medium"),
            (r"""['"]requirements\.txt['"]""", "requirements.txt (Python)", "medium"),
            (r"""['"]composer\.lock['"]""", "composer.lock (PHP)", "medium"),
            (r"""['"]Gemfile\.lock['"]""", "Gemfile.lock (Ruby)", "medium"),
            (r"""['"]pom\.xml['"]""", "pom.xml (Maven)", "low"),
            (r"""['"]build\.gradle['"]""", "build.gradle (Gradle)", "low"),
        ]

        for pattern, description, severity in package_file_patterns:
            matches = re.finditer(pattern, page_content, re.IGNORECASE)
            for match in matches:
                # Skip comments
                match_start = max(0, match.start() - 30)
                context = page_content[match_start:match.start()]
                if any(comment in context for comment in ["<!--", "//", "/*", "#"]):
                    continue

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="exposed_package_file",
                    severity=severity,
                    confidence=0.70,
                    description=f"Package management file reference found: {description}. Exposed package files may reveal dependency information for attackers.",
                    evidence=f"Reference to {description}",
                    cwe_id="CWE-200",
                    cvss_score=7.5 if severity == "high" else 5.3,
                    recommendation="Package management files should not be served or referenced from client-side code. Use build tools to bundle dependencies.",
                ))
                break  # One finding per file type is sufficient

        return findings

    def _analyze_cdn_integrity(self, page_content: str, url: str) -> List[SecurityFinding]:
        """Analyze CDN script tags for missing integrity checks (SRI)."""
        findings = []

        # Extract complete script tags
        script_tag_pattern = r"""<script[^>]*src\s*=\s*['"]([^'"]+)['"][^>]*integrity\s*=\s*['"]([^'"]+)['"][^>]*>"""
        script_with_integrity = re.findall(script_tag_pattern, page_content, re.IGNORECASE)

        # All script tags (including those without integrity)
        all_script_pattern = r"""<script[^>]*src\s*=\s*['"]([^'"]+)['"][^>]*>"""
        all_scripts = re.findall(all_script_pattern, page_content, re.IGNORECASE)

        # Count CDN scripts
        cdn_domains = [
            "cdn.jsdelivr.net",
            "unpkg.com",
            "cdnjs.cloudflare.com",
            "code.jquery.com",
            "ajax.googleapis.com",
            "browsercdn.net",
            "cdnjs.com",
        ]

        cdn_scripts_with_integrity = set(src for src, _ in script_with_integrity
                                        if any(cdn in src.lower() for cdn in cdn_domains))

        cdn_scripts_without_integrity = set()
        for src in all_scripts:
            if any(cdn in src.lower() for cdn in cdn_domains):
                if src not in cdn_scripts_with_integrity:
                    cdn_scripts_without_integrity.add(src)

        if cdn_scripts_without_integrity:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="cdn_missing_integrity",
                severity="medium",
                confidence=0.75,
                description=f"CDN script(s) without Subresource Integrity (SRI) attribute: {len(cdn_scripts_without_integrity)} script(s). SRI ensures the CDN hasn't been compromised.",
                evidence=f"Examples: {', '.join(list(cdn_scripts_without_integrity)[:3])}",
                cwe_id="CWE-829",
                cvss_score=5.9,
                recommendation="Add integrity attribute (e.g., integrity='sha384-...') to all CDN script tags. Consider using a package manager instead of CDNs.",
            ))

        return findings

    def _analyze_dom_scripts(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze DOM metadata for script issues."""
        findings = []

        scripts = dom_meta.get("scripts", [])

        # Check for scripts from multiple CDNs (increases attack surface)
        cdn_domains = set()
        for script in scripts:
            src = script.get("src", "")
            cdn_indicators = ["cdn", "unpkg", "jsdelivr", "cloudflare", "googleapis"]
            if any(indicator in src.lower() for indicator in cdn_indicators):
                # Extract domain
                try:
                    # Simple domain extraction
                    protocol_part = src.split("://")[1] if "://" in src else src
                    domain = protocol_part.split("/")[0]
                    cdn_domains.add(domain)
                except (IndexError, AttributeError):
                    pass

        if len(cdn_domains) > 3:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="multiple_cdn_domains",
                severity="low",
                confidence=0.60,
                description=f"Multiple CDN domains detected ({len(cdn_domains)}). Using many external CDNs increases supply chain attack risk.",
                evidence=f"CDN domains: {', '.join(list(cdn_domains)[:4])}",
                cwe_id="CWE-829",
                cvss_score=4.3,
                recommendation="Consolidate CDN usage or use a single trusted CDN. Consider bundling dependencies locally.",
            ))

        # Check for inline scripts with eval() or similar
        for script in scripts:
            content = script.get("content", "").lower()

            if not src and content and ("eval(" in content or "document.write(" in content):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="inline_dangerous_script",
                    severity="medium",
                    confidence=0.70,
                    description="Inline script with dangerous functions (eval/document.write) detected. Inline scripts cannot use SRI for integrity checking.",
                    evidence="Inline script contains eval() or document.write()",
                    cwe_id="CWE-829",
                    cvss_score=6.1,
                    recommendation="Move inline scripts to external files. Avoid eval() and similar dangerous functions. Use CSP with script-src hashes or nonces.",
                ))
                break  # One finding is sufficient

        # Check for forms with multipart/form-data without validation indicators
        forms = dom_meta.get("forms", [])
        for form in forms:
            enctype = (form.get("enctype") or "").lower()
            if enctype == "multipart/form-data":
                # File upload via multipart/form-data
                inputs = form.get("inputs", [])
                has_accept = any(inp.get("type") == "file" and inp.get("accept") for inp in inputs)
                has_file_input = any(inp.get("type") == "file" for inp in inputs)

                if has_file_input and not has_accept:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="file_upload_no_accept",
                        severity="high",
                        confidence=0.70,
                        description="Multipart/form-data form with file upload without file type restrictions (accept attribute). This may allow malicious file uploads.",
                        evidence=f"Form enctype: multipart/form-data",
                        cwe_id="CWE-434",
                        cvss_score=8.6,
                        recommendation="Add accept attribute to file input fields with allowed file types (e.g., accept='.jpg,.png'). Validate file types server-side.",
                    ))

        return findings

    def _compare_versions(self, version: str, threshold: tuple) -> bool:
        """
        Compare version string to threshold tuple.

        Args:
            version: Version string (e.g., "3.14.5")
            threshold: Threshold tuple (major, minor, patch)

        Returns:
            True if version < threshold (vulnerable), False otherwise
        """
        parts = version.split(".")
        while len(parts) < 3:
            parts.append("0")

        try:
            version_tuple = tuple(int(v) for v in parts)
            return version_tuple < threshold
        except ValueError:
            return False
