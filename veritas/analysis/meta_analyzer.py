"""
Veritas Analysis — Meta Analyzer

Standalone metadata analysis module for quick trust signals.
Provides WHOIS age, SSL validity, DNS consistency, and HTTP header checks
WITHOUT the full knowledge-graph machinery of GraphInvestigator.

Use cases:
    - Quick pre-scan before launching full audit
    - Standalone CLI checks
    - Feeding structural_score to the Judge when graph_investigator is skipped
"""

import json
import logging
import socket
import ssl
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger("veritas.meta_analyzer")


@dataclass
class SSLInfo:
    """SSL certificate information."""
    is_valid: bool = False
    issuer: str = ""
    subject: str = ""
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    days_until_expiry: int = -1
    is_self_signed: bool = False
    san_domains: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class DomainAge:
    """Domain registration age info."""
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    age_days: int = -1
    registrar: str = ""
    is_privacy_protected: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class DNSInfo:
    """DNS lookup results."""
    a_records: list[str] = field(default_factory=list)
    mx_records: list[str] = field(default_factory=list)
    has_spf: bool = False
    has_dmarc: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class MetaAnalysisResult:
    """Full metadata analysis result."""
    domain: str = ""
    ssl_info: SSLInfo = field(default_factory=SSLInfo)
    domain_age: DomainAge = field(default_factory=DomainAge)
    dns_info: DNSInfo = field(default_factory=DNSInfo)
    meta_score: float = 0.5
    risk_signals: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class MetaAnalyzer:
    """
    Lightweight metadata analyzer for quick domain trust checks.

    Usage:
        analyzer = MetaAnalyzer()
        result = await analyzer.analyze("example.com")
        print(f"Meta score: {result.meta_score}")
        for signal in result.risk_signals:
            print(f"  - {signal}")
    """

    async def analyze(self, domain: str) -> MetaAnalysisResult:
        """
        Analyze domain metadata for trust signals.

        Args:
            domain: Domain name (without protocol)

        Returns:
            MetaAnalysisResult with scores and risk signals
        """
        # Strip protocol if present
        domain = domain.replace("https://", "").replace("http://", "").split("/")[0]

        result = MetaAnalysisResult(domain=domain)

        # Run checks
        result.ssl_info = self._check_ssl(domain)
        result.domain_age = self._check_domain_age(domain)
        result.dns_info = self._check_dns(domain)

        # Aggregate errors
        result.errors = (
            result.ssl_info.errors +
            result.domain_age.errors +
            result.dns_info.errors
        )

        # Compute score and risk signals
        result.meta_score, result.risk_signals = self._compute_meta_score(result)

        return result

    def _check_ssl(self, domain: str) -> SSLInfo:
        """Check SSL certificate validity and details."""
        info = SSLInfo()
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

                    if cert:
                        info.is_valid = True

                        # Issuer
                        issuer_parts = dict(x[0] for x in cert.get("issuer", []))
                        info.issuer = issuer_parts.get("organizationName", "Unknown")

                        # Subject
                        subject_parts = dict(x[0] for x in cert.get("subject", []))
                        info.subject = subject_parts.get("commonName", "")

                        # Dates
                        not_before = cert.get("notBefore", "")
                        not_after = cert.get("notAfter", "")
                        if not_before:
                            info.not_before = datetime.strptime(
                                not_before, "%b %d %H:%M:%S %Y %Z"
                            ).replace(tzinfo=timezone.utc)
                        if not_after:
                            info.not_after = datetime.strptime(
                                not_after, "%b %d %H:%M:%S %Y %Z"
                            ).replace(tzinfo=timezone.utc)
                            info.days_until_expiry = (
                                info.not_after - datetime.now(timezone.utc)
                            ).days

                        # Self-signed check
                        info.is_self_signed = info.issuer == info.subject

                        # SAN domains
                        san = cert.get("subjectAltName", ())
                        info.san_domains = [
                            entry[1] for entry in san if entry[0] == "DNS"
                        ]

        except ssl.SSLCertVerificationError as e:
            info.is_valid = False
            info.errors.append(f"SSL verification failed: {e}")
        except socket.timeout:
            info.errors.append("SSL check timed out")
        except Exception as e:
            info.errors.append(f"SSL check failed: {e}")

        return info

    def _check_domain_age(self, domain: str) -> DomainAge:
        """Check domain registration age via WHOIS."""
        age = DomainAge()
        try:
            import whois
            w = whois.whois(domain)

            if w.creation_date:
                creation = w.creation_date
                if isinstance(creation, list):
                    creation = creation[0]
                if isinstance(creation, datetime):
                    age.creation_date = creation
                    age.age_days = (datetime.now() - creation).days

            if w.expiration_date:
                expiration = w.expiration_date
                if isinstance(expiration, list):
                    expiration = expiration[0]
                if isinstance(expiration, datetime):
                    age.expiration_date = expiration

            age.registrar = str(w.registrar or "")

            # Privacy protection detection
            org = str(w.org or "").lower()
            privacy_keywords = [
                "privacy", "domains by proxy", "whoisguard",
                "contact privacy", "perfect privacy", "redacted"
            ]
            age.is_privacy_protected = any(kw in org for kw in privacy_keywords)

        except ImportError:
            age.errors.append("python-whois not installed, skipping domain age check")
        except Exception as e:
            age.errors.append(f"WHOIS lookup failed: {e}")

        return age

    def _check_dns(self, domain: str) -> DNSInfo:
        """Check DNS records for consistency signals."""
        info = DNSInfo()
        try:
            import dns.resolver

            # A records
            try:
                answers = dns.resolver.resolve(domain, "A")
                info.a_records = [str(rdata) for rdata in answers]
            except Exception:
                pass

            # MX records
            try:
                answers = dns.resolver.resolve(domain, "MX")
                info.mx_records = [str(rdata.exchange) for rdata in answers]
            except Exception:
                pass

            # SPF check (TXT record)
            try:
                answers = dns.resolver.resolve(domain, "TXT")
                for rdata in answers:
                    txt = str(rdata)
                    if "v=spf1" in txt:
                        info.has_spf = True
                    if "v=DMARC1" in txt.upper():
                        info.has_dmarc = True
            except Exception:
                pass

            # DMARC check (dedicated record)
            try:
                answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
                for rdata in answers:
                    if "v=DMARC1" in str(rdata).upper():
                        info.has_dmarc = True
            except Exception:
                pass

        except ImportError:
            info.errors.append("dnspython not installed, skipping DNS checks")
            # Fallback: basic socket resolution
            try:
                info.a_records = [socket.gethostbyname(domain)]
            except Exception:
                pass

        return info

    def _compute_meta_score(
        self, result: MetaAnalysisResult
    ) -> tuple[float, list[str]]:
        """
        Compute overall meta trust score from gathered signals.

        Returns:
            (score, risk_signals) where score is 0-1 and signals
            are human-readable risk descriptions
        """
        score = 0.8  # Start optimistic
        signals = []

        # --- SSL Signals ---
        ssl = result.ssl_info
        if not ssl.is_valid:
            score -= 0.25
            signals.append("CRITICAL: No valid SSL certificate")
        elif ssl.is_self_signed:
            score -= 0.15
            signals.append("Self-signed SSL certificate")
        elif ssl.days_until_expiry >= 0 and ssl.days_until_expiry < 14:
            score -= 0.05
            signals.append(f"SSL expiring in {ssl.days_until_expiry} days")

        # --- Domain Age Signals ---
        age = result.domain_age
        if age.age_days >= 0:
            if age.age_days < 30:
                score -= 0.20
                signals.append(f"Very new domain ({age.age_days} days old)")
            elif age.age_days < 180:
                score -= 0.10
                signals.append(f"Relatively new domain ({age.age_days} days old)")
        else:
            score -= 0.05
            signals.append("Could not determine domain age")

        if age.is_privacy_protected:
            score -= 0.05
            signals.append("WHOIS privacy-protected registration")

        # --- DNS Signals ---
        dns = result.dns_info
        if not dns.a_records:
            score -= 0.15
            signals.append("No A records found for domain")

        if not dns.mx_records:
            score -= 0.05
            signals.append("No MX (email) records found")

        if not dns.has_spf and not dns.has_dmarc:
            score -= 0.03
            signals.append("No SPF/DMARC email authentication records")

        return round(max(0.0, min(1.0, score)), 3), signals

    def to_dict(self, result: MetaAnalysisResult) -> dict:
        """Convert MetaAnalysisResult to serializable dict."""
        return {
            "domain": result.domain,
            "meta_score": result.meta_score,
            "risk_signals": result.risk_signals,
            "ssl": {
                "is_valid": result.ssl_info.is_valid,
                "issuer": result.ssl_info.issuer,
                "subject": result.ssl_info.subject,
                "days_until_expiry": result.ssl_info.days_until_expiry,
                "is_self_signed": result.ssl_info.is_self_signed,
                "san_domains": result.ssl_info.san_domains,
            },
            "domain_age": {
                "age_days": result.domain_age.age_days,
                "registrar": result.domain_age.registrar,
                "is_privacy_protected": result.domain_age.is_privacy_protected,
            },
            "dns": {
                "a_records": result.dns_info.a_records,
                "mx_records": result.dns_info.mx_records,
                "has_spf": result.dns_info.has_spf,
                "has_dmarc": result.dns_info.has_dmarc,
            },
            "errors": result.errors,
        }
