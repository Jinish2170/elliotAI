"""
ELLIOT V3 — OSINT Enrichment Layer

Runs DNS, WHOIS, and SSL checks in parallel after Scout loads a page.
Results flow into ScoutResult.osint_enrichment.

Phase 1: Uses existing OSINT sources already built but not wired.
Phase 2: Plugs into the full Intelligence Fusion engine.

Usage:
    enrichment = await osint_enrich(url)

    enrichment["dns"]    # DNS records (A, MX, SPF, DMARC, etc.)
    enrichment["whois"]  # Domain age, registrar, privacy status
    enrichment["ssl"]    # Certificate validity, issuer, expiry
    enrichment["findings"]  # List of Evidence items derived from OSINT results
    enrichment["trust_modifier"]  # Score adjustment based on OSINT findings
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger("elliot.osint_enrichment")


@dataclass
class OSINTEnrichment:
    """Combined OSINT intelligence from all sources."""
    dns: dict = field(default_factory=dict)
    whois: dict = field(default_factory=dict)
    ssl: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)
    trust_modifier: float = 0.0
    trust_notes: list = field(default_factory=list)
    scan_duration_ms: float = 0.0
    sources_ran: list = field(default_factory=list)
    sources_failed: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "dns": self.dns,
            "whois": self.whois,
            "ssl": self.ssl,
            "findings": [f.to_dict() if hasattr(f, 'to_dict') else f for f in self.findings],
            "trust_modifier": self.trust_modifier,
            "trust_notes": self.trust_notes,
            "scan_duration_ms": self.scan_duration_ms,
            "sources_ran": self.sources_ran,
            "sources_failed": self.sources_failed,
        }


async def osint_enrich(url: str) -> OSINTEnrichment:
    """
    Run all OSINT checks in parallel for a URL.

    Queries DNS, WHOIS, and SSL simultaneously.
    Derives Evidence findings from the raw results.
    Returns an OSINTEnrichment object.
    """
    from elliot.core.evidence import Evidence, EvidenceCategory, EvidenceSeverity, EvidenceType, osint_finding

    start = time.time()
    domain = _extract_domain(url)
    is_https = url.lower().startswith("https")

    enrichment = OSINTEnrichment()
    findings = []
    trust_mod = 0.0
    trust_notes = []

    logger.info(f"OSINT enrichment starting for {url} (domain: {domain})")

    # Run DNS, WHOIS, SSL in parallel
    dns_task = asyncio.create_task(_run_dns(domain))
    whois_task = asyncio.create_task(_run_whois(domain))
    ssl_task = asyncio.create_task(_run_ssl(domain)) if is_https else None

    tasks = [dns_task, whois_task]
    if ssl_task:
        tasks.append(ssl_task)

    done = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed_ms = (time.time() - start) * 1000
    enrichment.scan_duration_ms = elapsed_ms

    # Process DNS results
    dns_result = done[0]
    if isinstance(dns_result, Exception) or dns_result is None:
        enrichment.sources_failed.append("dns")
        logger.warning(f"DNS enrichment failed: {dns_result}")
    else:
        enrichment.dns = dns_result.get("data", {}) or {}
        enrichment.sources_ran.append("dns")
        dns_findings = _analyze_dns(dns_result, domain)
        findings.extend(dns_findings)
        trust_mod += sum(f.get("trust_mod", 0) for f in dns_findings)
        trust_notes.extend(f.get("note", "") for f in dns_findings if f.get("note"))

    # Process WHOIS results
    whois_result = done[1]
    if isinstance(whois_result, Exception) or whois_result is None:
        enrichment.sources_failed.append("whois")
        logger.warning(f"WHOIS enrichment failed: {whois_result}")
    else:
        enrichment.whois = whois_result.get("data", {}) or {}
        enrichment.sources_ran.append("whois")
        whois_findings = _analyze_whois(whois_result, domain)
        findings.extend(whois_findings)
        trust_mod += sum(f.get("trust_mod", 0) for f in whois_findings)
        trust_notes.extend(f.get("note", "") for f in whois_findings if f.get("note"))

    # Process SSL results
    if ssl_task and done[2] is not None:
        ssl_result = done[2]
        if isinstance(ssl_result, Exception):
            enrichment.sources_failed.append("ssl")
            logger.warning(f"SSL enrichment failed: {ssl_result}")
        else:
            enrichment.ssl = ssl_result.get("data", {}) or {}
            enrichment.sources_ran.append("ssl")
            ssl_findings = _analyze_ssl(ssl_result, domain)
            findings.extend(ssl_findings)
            trust_mod += sum(f.get("trust_mod", 0) for f in ssl_findings)
            trust_notes.extend(f.get("note", "") for f in ssl_findings if f.get("note"))

    # Store findings as Evidence
    enrichment.findings = findings
    enrichment.trust_modifier = trust_mod
    enrichment.trust_notes = [n for n in trust_notes if n]

    logger.info(
        f"OSINT enrichment complete: {elapsed_ms:.0f}ms, "
        f"{len(enrichment.sources_ran)} sources ran, "
        f"{len(enrichment.sources_failed)} failed, "
        f"{len(findings)} findings, trust_mod={trust_mod:.2f}"
    )
    return enrichment


# ============================================================
# Source runners —— wrap existing OSINT sources
# ============================================================

async def _run_dns(domain: str) -> Optional[dict]:
    """Run DNS lookup via existing DNSSource."""
    try:
        from elliot.osint.sources.dns_lookup import DNSSource
        source = DNSSource()
        result = await source.query(domain)
        return result.to_dict() if result else None
    except ImportError:
        logger.warning("DNSSource not available")
        return None
    except Exception as e:
        logger.warning(f"DNS runner failed: {e}")
        return None


async def _run_whois(domain: str) -> Optional[dict]:
    """Run WHOIS lookup via existing WHOISSource."""
    try:
        from elliot.osint.sources.whois_lookup import WHOISSource
        source = WHOISSource()
        result = await source.query(domain)
        return result.to_dict() if result else None
    except ImportError:
        logger.warning("WHOISSource not available")
        return None
    except Exception as e:
        logger.warning(f"WHOIS runner failed: {e}")
        return None


async def _run_ssl(domain: str) -> Optional[dict]:
    """Run SSL certificate check via existing SSLSource."""
    try:
        from elliot.osint.sources.ssl_verify import SSLSource
        source = SSLSource()
        result = await source.query(domain)
        return result.to_dict() if result else None
    except ImportError:
        logger.warning("SSLSource not available")
        return None
    except Exception as e:
        logger.warning(f"SSL runner failed: {e}")
        return None


# ============================================================
# Analysis —— derive Evidence from raw OSINT results
# ============================================================

def _analyze_dns(result: dict, domain: str) -> list:
    """Analyze DNS results for security signals."""
    from elliot.core.evidence import Evidence, EvidenceCategory, EvidenceSeverity, EvidenceType, osint_finding

    findings = []
    data = result.get("data") or {}

    if not data:
        return findings

    # Check SPF record
    txt_records = data.get("TXT", {}).get("records", []) or []
    has_spf = any("v=spf1" in str(r) for r in txt_records)
    if not has_spf:
        findings.append({
            "evidence": osint_finding(
                source="dns",
                title="No SPF record found",
                detail=f"Domain {domain} has no SPF (Sender Policy Framework) record. "
                       "This allows email spoofing as the domain.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"has_spf": False},
                remediation="Add a SPF TXT record to DNS to authorize legitimate mail senders.",
            ),
            "trust_mod": -0.05,
            "note": "No SPF record",
        })
    else:
        findings.append({
            "evidence": osint_finding(
                source="dns",
                title="SPF record present",
                detail=f"Domain has SPF configured.",
                severity=EvidenceSeverity.INFO,
                raw_data={"has_spf": True, "records": txt_records},
            ),
            "trust_mod": 0.02,
            "note": None,
        })

    # Check DMARC record
    has_dmarc = any("v=DMARC1" in str(r) for r in txt_records)
    if not has_dmarc:
        findings.append({
            "evidence": osint_finding(
                source="dns",
                title="No DMARC record found",
                detail=f"Domain {domain} has no DMARC record. Email authentication policy is incomplete.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"has_dmarc": False},
                remediation="Add a DMARC TXT record at _dmarc.{domain} to complete email authentication.",
            ),
            "trust_mod": -0.05,
            "note": "No DMARC record",
        })
    else:
        findings.append({
            "evidence": osint_finding(
                source="dns",
                title="DMARC record present",
                detail=f"Domain has DMARC configured.",
                severity=EvidenceSeverity.INFO,
                raw_data={"has_dmarc": True},
            ),
            "trust_mod": 0.02,
            "note": None,
        })

    # Check MX records (important for email-enabled domains)
    mx_records = data.get("MX", {}).get("records", []) or []
    has_mx = len(mx_records) > 0
    if has_mx and not has_spf:
        findings.append({
            "evidence": osint_finding(
                source="dns",
                title="MX records present but no SPF — email spoofing risk",
                detail=f"Domain {domain} accepts email (has MX records) but lacks SPF protection.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"has_mx": True, "mx_count": len(mx_records)},
                remediation="Add SPF record to protect domain email reputation.",
            ),
            "trust_mod": -0.05,
            "note": "MX without SPF",
        })

    return findings


def _analyze_whois(result: dict, domain: str) -> list:
    """Analyze WHOIS results for domain reputation signals."""
    from elliot.core.evidence import Evidence, EvidenceCategory, EvidenceSeverity, EvidenceType, osint_finding

    findings = []
    data = result.get("data") or {}

    if not data:
        return findings

    # Newly registered domain (high risk)
    age_days = data.get("age_days", -1)
    if age_days > 0 and age_days < 30:
        findings.append({
            "evidence": osint_finding(
                source="whois",
                title=f"Newly registered domain ({age_days} days old)",
                detail=f"Domain {domain} was registered only {age_days} days ago. "
                       f"Newly registered domains are statistically more likely to be used for phishing/malware.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"age_days": age_days, "created_date": data.get("created_date")},
                remediation="Exercise caution — newly registered domains have higher fraud rates.",
            ),
            "trust_mod": -0.15,
            "note": f"Very new domain: {age_days} days",
        })
    elif age_days > 0 and age_days < 365:
        findings.append({
            "evidence": osint_finding(
                source="whois",
                title=f"Domain registered {age_days} days ago (< 1 year)",
                detail=f"Domain {domain} is less than a year old.",
                severity=EvidenceSeverity.INFO,
                raw_data={"age_days": age_days},
            ),
            "trust_mod": -0.05,
            "note": f"Domain < 1 year old: {age_days} days",
        })
    elif age_days > 365:
        findings.append({
            "evidence": osint_finding(
                source="whois",
                title=f"Established domain ({age_days} days old)",
                detail=f"Domain {domain} has been registered for {age_days} days.",
                severity=EvidenceSeverity.INFO,
                raw_data={"age_days": age_days},
            ),
            "trust_mod": 0.05,
            "note": f"Established domain: {age_days} days",
        })

    # Privacy protection (can be legitimate but also suspicious)
    registrant = data.get("registrant")
    if registrant and ("privacy" in registrant.lower() or "redacted" in registrant.lower()):
        findings.append({
            "evidence": osint_finding(
                source="whois",
                title="WHOIS privacy protection enabled",
                detail=f"Domain owner identity is hidden behind a privacy proxy.",
                severity=EvidenceSeverity.INFO,
                raw_data={"registrant": registrant},
            ),
            "trust_mod": -0.02,
            "note": "WHOIS privacy enabled",
        })

    # No registrar info (suspicious for active sites)
    if not data.get("registrar"):
        findings.append({
            "evidence": osint_finding(
                source="whois",
                title="No registrar information available",
                detail="Domain registrar could not be determined — this may indicate a new or unusual registration.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"registrar": None},
            ),
            "trust_mod": -0.05,
            "note": "No registrar info",
        })

    # Expiry check
    expiry_date = data.get("expiry_date")
    if expiry_date:
        from datetime import datetime
        try:
            exp_dt = datetime.fromisoformat(expiry_date)
            days_to_expiry = (exp_dt - datetime.utcnow()).days
            if days_to_expiry < 30:
                findings.append({
                    "evidence": osint_finding(
                        source="whois",
                        title=f"Domain expires in {days_to_expiry} days",
                        detail=f"Domain {domain} is close to expiration.",
                        severity=EvidenceSeverity.WARNING,
                        raw_data={"days_to_expiry": days_to_expiry, "expiry_date": expiry_date},
                    ),
                    "trust_mod": -0.05,
                    "note": f"Domain expires in {days_to_expiry} days",
                })
        except (ValueError, TypeError):
            pass

    return findings


def _analyze_ssl(result: dict, domain: str) -> list:
    """Analyze SSL certificate for security signals."""
    from elliot.core.evidence import Evidence, EvidenceCategory, EvidenceSeverity, EvidenceType, osint_finding

    findings = []
    data = result.get("data") or {}

    if not data:
        return findings

    # Certificate validity
    if not data.get("is_valid"):
        findings.append({
            "evidence": osint_finding(
                source="ssl",
                title="SSL certificate is not valid",
                detail=f"SSL certificate for {domain} has expired or is not yet valid.",
                severity=EvidenceSeverity.CRITICAL,
                raw_data={"is_valid": False, "days_until_expiry": data.get("days_until_expiry")},
                remediation="Renew or replace the SSL certificate immediately.",
            ),
            "trust_mod": -0.20,
            "note": "SSL certificate invalid",
        })
    elif data.get("is_expiring_soon"):
        findings.append({
            "evidence": osint_finding(
                source="ssl",
                title=f"SSL certificate expires soon ({data.get('days_until_expiry', '?')} days)",
                detail=f"SSL certificate will expire soon and needs renewal.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"days_until_expiry": data.get("days_until_expiry")},
                remediation="Renew the SSL certificate before expiration.",
            ),
            "trust_mod": -0.05,
            "note": f"SSL expires soon: {data.get('days_until_expiry', '?')} days",
        })
    else:
        findings.append({
            "evidence": osint_finding(
                source="ssl",
                title="SSL certificate valid",
                detail=f"SSL certificate is valid and not expiring soon.",
                severity=EvidenceSeverity.INFO,
                raw_data={"issuer": data.get("issuer_org"), "days_until_expiry": data.get("days_until_expiry")},
            ),
            "trust_mod": 0.05,
            "note": None,
        })

    # Self-signed certificate check (no recognized CA)
    issuer_org = data.get("issuer_org")
    known_issuers = ["Let's Encrypt", "DigiCert", "Sectigo", "GlobalSign", "GoDaddy", "Cloudflare", "Amazon", "Google Trust"]
    if issuer_org and not any(issuer.lower() in issuer_org.lower() for issuer in known_issuers):
        findings.append({
            "evidence": osint_finding(
                source="ssl",
                title=f"Unknown SSL certificate issuer: {issuer_org}",
                detail=f"Certificate was issued by {issuer_org}, which is not a widely recognized Certificate Authority.",
                severity=EvidenceSeverity.WARNING,
                raw_data={"issuer_org": issuer_org},
            ),
            "trust_mod": -0.05,
            "note": f"Unknown SSL issuer: {issuer_org}",
        })

    return findings


# ============================================================
# Helpers
# ============================================================

def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.hostname or parsed.netloc
    except Exception:
        return url.split("/")[0] if "/" in url else url
