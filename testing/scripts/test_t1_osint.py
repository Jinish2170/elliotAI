"""
Veritas Independent Module Testing — Phase T1: OSINT & Data Sources
===================================================================
Tests each OSINT source independently against avrut.com.
No budget limits, no orchestrator — raw module output.

Usage:
    python testing/scripts/test_t1_osint.py

Output:
    testing/results/T1_osint/T1.X_<module>.md (one per test)
"""

import asyncio
import json
import socket
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Ensure project root is on PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "testing" / "results" / "T1_osint"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DOMAIN = "avrut.com"
TARGET_URL = "https://avrut.com"


def write_report(test_id: str, module_name: str, duration: float, status: str,
                 input_desc: str, output_data: str, analysis: str, verdict: str):
    """Write a standardized test report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    path = RESULTS_DIR / f"{test_id}.md"
    content = f"""# Test {test_id} — {module_name}
**Date:** {now}
**Target:** {TARGET_DOMAIN}
**Duration:** {duration:.1f}s
**Status:** {status}

## Input
{input_desc}

## Output
```
{output_data}
```

## Analysis
{analysis}

## Verdict
{verdict}
"""
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ Report written: {path.name}")
    return path


def format_output(data) -> str:
    """Safely format output data."""
    try:
        if hasattr(data, '__dict__'):
            d = {}
            for k, v in data.__dict__.items():
                try:
                    json.dumps(v, default=str)
                    d[k] = v
                except (TypeError, ValueError):
                    d[k] = str(v)
            return json.dumps(d, indent=2, default=str)
        elif isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)
    except Exception:
        return str(data)


# ============================================================
# T1.1 — DNS Lookup
# ============================================================
async def test_t1_1_dns():
    test_id = "T1.1_dns"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: DNS Lookup")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.sources.dns_lookup import DNSSource

        source = DNSSource()
        result = await source.query(TARGET_DOMAIN)
        duration = time.time() - start

        output = format_output(result)
        record_types = list(result.data.keys()) if result.data else []
        record_count = sum(
            len(v) if isinstance(v, (list, dict)) else 1
            for v in (result.data or {}).values()
        )

        analysis_lines = [
            f"- Status: {result.status}",
            f"- Record types returned: {record_types}",
            f"- Total records: {record_count}",
            f"- Confidence: {result.confidence_score}",
        ]
        if result.error_message:
            analysis_lines.append(f"- Error: {result.error_message}")

        for rtype, rdata in (result.data or {}).items():
            analysis_lines.append(f"- {rtype}: {rdata}")

        status = "PASS" if result.status.value == "success" else "FAIL"
        verdict = f"DNS lookup {'succeeded' if status == 'PASS' else 'failed'} — returned {len(record_types)} record types with {record_count} records"

        write_report(test_id, "DNS Lookup (DNSSource)", duration, status,
                     f"Domain: `{TARGET_DOMAIN}`\nRecord types: ALL (A, AAAA, MX, TXT, NS, SOA, CNAME)",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "DNS Lookup (DNSSource)", duration, "ERROR",
                     f"Domain: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.2 — WHOIS Lookup
# ============================================================
async def test_t1_2_whois():
    test_id = "T1.2_whois"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: WHOIS Lookup")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.sources.whois_lookup import WHOISSource

        source = WHOISSource()
        result = await source.query(TARGET_DOMAIN)
        duration = time.time() - start

        output = format_output(result)
        data = result.data or {}

        analysis_lines = [
            f"- Status: {result.status}",
            f"- Confidence: {result.confidence_score}",
            f"- Registrar: {data.get('registrar', 'N/A')}",
            f"- Age (days): {data.get('age_days', 'N/A')}",
            f"- Creation: {data.get('creation_date', 'N/A')}",
            f"- Expiry: {data.get('expiry_date', 'N/A')}",
            f"- Nameservers: {data.get('nameservers', 'N/A')}",
        ]
        if result.error_message:
            analysis_lines.append(f"- Error: {result.error_message}")

        status = "PASS" if result.status.value == "success" else "FAIL"
        age = data.get('age_days', 0)
        verdict = f"WHOIS {'succeeded' if status == 'PASS' else 'failed'} — domain is {age} days old, registrar: {data.get('registrar', 'unknown')}"

        write_report(test_id, "WHOIS Lookup (WHOISSource)", duration, status,
                     f"Domain: `{TARGET_DOMAIN}`",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "WHOIS Lookup (WHOISSource)", duration, "ERROR",
                     f"Domain: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.3 — SSL Certificate
# ============================================================
async def test_t1_3_ssl():
    test_id = "T1.3_ssl"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: SSL Certificate")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.sources.ssl_verify import SSLSource

        source = SSLSource()
        result = await source.query(TARGET_DOMAIN)
        duration = time.time() - start

        output = format_output(result)
        data = result.data or {}

        analysis_lines = [
            f"- Status: {result.status}",
            f"- Confidence: {result.confidence_score}",
            f"- Issuer: {data.get('issuer', 'N/A')}",
            f"- Subject: {data.get('subject', 'N/A')}",
            f"- Valid: {data.get('is_valid', 'N/A')}",
            f"- Self-signed: {data.get('is_self_signed', 'N/A')}",
            f"- SAN domains: {data.get('san_domains', 'N/A')}",
            f"- Validity days: {data.get('validity_days', 'N/A')}",
        ]
        if result.error_message:
            analysis_lines.append(f"- Error: {result.error_message}")

        status = "PASS" if result.status.value == "success" else "FAIL"
        verdict = f"SSL check {'succeeded' if status == 'PASS' else 'failed'} — issuer: {data.get('issuer', 'unknown')}, valid: {data.get('is_valid', 'unknown')}"

        write_report(test_id, "SSL Certificate (SSLSource)", duration, status,
                     f"Hostname: `{TARGET_DOMAIN}`, Port: 443",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "SSL Certificate (SSLSource)", duration, "ERROR",
                     f"Hostname: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.4 — IOC Detector
# ============================================================
async def test_t1_4_ioc():
    test_id = "T1.4_ioc"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: IOC Detector")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.ioc_detector import IOCDetector
        import aiohttp

        # Fetch the actual page HTML to analyze
        async with aiohttp.ClientSession() as session:
            async with session.get(TARGET_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                html = await resp.text()

        detector = IOCDetector()

        # Test all extraction methods
        text_iocs = detector.extract_from_text(html, source="page_html")
        html_iocs = detector.extract_from_html(html)
        url_ioc = detector.detect_url(TARGET_URL)

        duration = time.time() - start

        all_iocs = text_iocs + html_iocs
        if url_ioc:
            all_iocs.append(url_ioc)

        output_data = {
            "text_iocs_count": len(text_iocs),
            "html_iocs_count": len(html_iocs),
            "url_ioc": format_output(url_ioc) if url_ioc else None,
            "all_iocs": [
                {"type": str(i.ioc_type), "value": i.value[:100], "severity": str(i.severity), "confidence": i.confidence}
                for i in all_iocs[:50]  # Cap at 50 for readability
            ],
            "total_unique": len(set(i.value for i in all_iocs))
        }

        analysis_lines = [
            f"- IOCs from text extraction: {len(text_iocs)}",
            f"- IOCs from HTML extraction: {len(html_iocs)}",
            f"- URL IOC: {'detected' if url_ioc else 'none'}",
            f"- Total unique IOCs: {output_data['total_unique']}",
            f"- Page HTML size: {len(html)} chars",
        ]

        # Break down by type
        type_counts = {}
        for i in all_iocs:
            t = str(i.ioc_type)
            type_counts[t] = type_counts.get(t, 0) + 1
        for t, c in sorted(type_counts.items()):
            analysis_lines.append(f"  - {t}: {c}")

        status = "PASS"
        verdict = f"IOC detection found {output_data['total_unique']} unique indicators from {len(html)} chars of HTML"

        write_report(test_id, "IOC Detector (IOCDetector)", duration, status,
                     f"URL: `{TARGET_URL}`\nMethods: extract_from_text, extract_from_html, detect_url",
                     json.dumps(output_data, indent=2, default=str),
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "IOC Detector (IOCDetector)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.5 — Attack Pattern Mapper
# ============================================================
async def test_t1_5_attack_patterns():
    test_id = "T1.5_attack_patterns"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Attack Pattern Mapper")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.attack_patterns import AttackPatternMapper
        from veritas.osint.ioc_detector import IOCDetector
        import aiohttp

        # Get IOCs first (dependency on T1.4 data)
        async with aiohttp.ClientSession() as session:
            async with session.get(TARGET_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                html = await resp.text()

        detector = IOCDetector()
        iocs = detector.extract_from_text(html, source="page_html") + detector.extract_from_html(html)

        mapper = AttackPatternMapper()
        techniques = mapper.map_indicators_to_techniques(
            indicators=iocs,
            site_features={"url": TARGET_URL, "has_forms": True, "has_scripts": True}
        )
        attribution = mapper.generate_attribution_suggestion(techniques)

        duration = time.time() - start

        output_data = {
            "input_iocs": len(iocs),
            "techniques_mapped": len(techniques),
            "techniques": techniques[:20],
            "attribution": attribution
        }

        analysis_lines = [
            f"- Input IOCs: {len(iocs)}",
            f"- MITRE ATT&CK techniques mapped: {len(techniques)}",
        ]
        for t in techniques[:10]:
            analysis_lines.append(f"  - {t.get('technique_id', '?')}: {t.get('technique_name', '?')} (confidence: {t.get('confidence', '?')})")
        if attribution:
            analysis_lines.append(f"- Attribution: {attribution}")

        status = "PASS"
        verdict = f"Mapped {len(iocs)} IOCs to {len(techniques)} MITRE ATT&CK techniques"

        write_report(test_id, "Attack Pattern Mapper", duration, status,
                     f"Input: {len(iocs)} IOCs from avrut.com\nSite features: url, has_forms, has_scripts",
                     json.dumps(output_data, indent=2, default=str),
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Attack Pattern Mapper", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.6 — CTI (Cyber Threat Intelligence)
# ============================================================
async def test_t1_6_cti():
    test_id = "T1.6_cti"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Cyber Threat Intelligence")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.cti import CThreatIntelligence
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(TARGET_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                html = await resp.text()
                # Extract visible text (rough)
                import re
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text).strip()

        cti = CThreatIntelligence()
        result = await cti.analyze_threats(
            url=TARGET_URL,
            page_html=html,
            page_text=text[:5000],
            page_metadata={"domain": TARGET_DOMAIN, "url": TARGET_URL}
        )

        duration = time.time() - start

        analysis_lines = [
            f"- Threat level: {result.get('threat_level', 'N/A')}",
            f"- Confidence: {result.get('confidence', 'N/A')}",
            f"- Indicators found: {len(result.get('indicators', []))}",
            f"- MITRE techniques: {len(result.get('mitre_techniques', []))}",
            f"- Attribution: {result.get('attribution', 'N/A')}",
        ]

        status = "PASS"
        verdict = f"CTI analysis: threat_level={result.get('threat_level', 'unknown')}, {len(result.get('indicators', []))} indicators, {len(result.get('mitre_techniques', []))} techniques"

        write_report(test_id, "CTI (CThreatIntelligence)", duration, status,
                     f"URL: `{TARGET_URL}`\nHTML: {len(html)} chars\nText: {len(text)} chars",
                     json.dumps(result, indent=2, default=str)[:10000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "CTI (CThreatIntelligence)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.7 — URLVoid
# ============================================================
async def test_t1_7_urlvoid():
    test_id = "T1.7_urlvoid"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: URLVoid")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.config.settings import URLVOID_API_KEY
        if not URLVOID_API_KEY:
            duration = time.time() - start
            write_report(test_id, "URLVoid (URLVoidSource)", duration, "SKIPPED",
                         f"Domain: `{TARGET_DOMAIN}`",
                         "No URLVOID_API_KEY configured in .env",
                         "- URLVOID_API_KEY is empty — cannot test without API key\n- Set URLVOID_API_KEY in veritas/.env to enable",
                         "SKIPPED — no API key configured")
            return "SKIPPED"

        from veritas.osint.sources.urlvoid import URLVoidSource
        source = URLVoidSource(api_key=URLVOID_API_KEY)
        result = await source.query(TARGET_DOMAIN)
        duration = time.time() - start

        output = format_output(result)
        data = result.data or {}

        analysis_lines = [
            f"- Status: {result.status}",
            f"- Detections: {data.get('detections', 'N/A')}/{data.get('engines_count', 'N/A')}",
            f"- Is clean: {data.get('is_clean', 'N/A')}",
            f"- Risk level: {data.get('risk_level', 'N/A')}",
            f"- Confidence: {result.confidence_score}",
        ]
        if result.error_message:
            analysis_lines.append(f"- Error: {result.error_message}")

        status = "PASS" if result.status.value == "success" else "FAIL"
        verdict = f"URLVoid: {data.get('detections', '?')}/{data.get('engines_count', '?')} detections, risk: {data.get('risk_level', 'unknown')}"

        write_report(test_id, "URLVoid (URLVoidSource)", duration, status,
                     f"Domain: `{TARGET_DOMAIN}`\nAPI Key: present ({len(URLVOID_API_KEY)} chars)",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "URLVoid (URLVoidSource)", duration, "ERROR",
                     f"Domain: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.8 — AbuseIPDB
# ============================================================
async def test_t1_8_abuseipdb():
    test_id = "T1.8_abuseipdb"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: AbuseIPDB")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.config.settings import ABUSEIPDB_API_KEY
        if not ABUSEIPDB_API_KEY:
            duration = time.time() - start
            write_report(test_id, "AbuseIPDB (AbuseIPDBSource)", duration, "SKIPPED",
                         f"Domain: `{TARGET_DOMAIN}`",
                         "No ABUSEIPDB_API_KEY configured in .env",
                         "- ABUSEIPDB_API_KEY is empty — cannot test without API key\n- Set ABUSEIPDB_API_KEY in veritas/.env to enable",
                         "SKIPPED — no API key configured")
            return "SKIPPED"

        # Resolve domain to IP first
        ip_address = socket.gethostbyname(TARGET_DOMAIN)
        print(f"  Resolved {TARGET_DOMAIN} → {ip_address}")

        from veritas.osint.sources.abuseipdb import AbuseIPDBSource
        source = AbuseIPDBSource(api_key=ABUSEIPDB_API_KEY)
        result = await source.check_ip(ip_address)
        duration = time.time() - start

        output = format_output(result)
        data = result.data or {}

        analysis_lines = [
            f"- Status: {result.status}",
            f"- IP resolved: {ip_address}",
            f"- Abuse confidence: {data.get('abuse_confidence_score', 'N/A')}%",
            f"- Total reports: {data.get('total_reports', 'N/A')}",
            f"- Whitelisted: {data.get('is_whitelisted', 'N/A')}",
            f"- Country: {data.get('country', 'N/A')}",
            f"- Usage type: {data.get('usage_type', 'N/A')}",
        ]
        if result.error_message:
            analysis_lines.append(f"- Error: {result.error_message}")

        status = "PASS" if result.status.value == "success" else "FAIL"
        verdict = f"AbuseIPDB: IP {ip_address} has {data.get('abuse_confidence_score', '?')}% abuse confidence, {data.get('total_reports', '?')} reports"

        write_report(test_id, "AbuseIPDB (AbuseIPDBSource)", duration, status,
                     f"Domain: `{TARGET_DOMAIN}`\nResolved IP: `{ip_address}`\nAPI Key: present",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "AbuseIPDB (AbuseIPDBSource)", duration, "ERROR",
                     f"Domain: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.9 — OSINT Orchestrator (all sources together)
# ============================================================
async def test_t1_9_osint_orchestrator():
    test_id = "T1.9_osint_orchestrator"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: OSINT Orchestrator (all sources)")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.osint.orchestrator import OSINTOrchestrator
        from veritas.osint.types import OSINTCategory

        orch = OSINTOrchestrator()

        # Query all categories
        categories_to_test = [
            (OSINTCategory.DNS, "dns", TARGET_DOMAIN),
            (OSINTCategory.WHOIS, "whois", TARGET_DOMAIN),
            (OSINTCategory.SSL, "ssl", TARGET_DOMAIN),
            (OSINTCategory.THREAT_INTEL, "threat_intel", TARGET_DOMAIN),
            (OSINTCategory.REPUTATION, "reputation", TARGET_DOMAIN),
            (OSINTCategory.SOCIAL, "social", TARGET_DOMAIN),
        ]

        all_results = {}
        category_summaries = []

        for category, cat_name, query_value in categories_to_test:
            try:
                results = await orch.query_all(
                    category=category,
                    query_type=cat_name,
                    query_value=query_value,
                )
                all_results[cat_name] = {
                    src: format_output(r) for src, r in results.items()
                }
                category_summaries.append(f"- {cat_name}: {len(results)} sources responded — {list(results.keys())}")
            except Exception as e:
                all_results[cat_name] = {"error": str(e)}
                category_summaries.append(f"- {cat_name}: ERROR — {e}")

        # Also try individual source queries
        individual_results = {}
        for source_name in ["dns", "whois", "ssl"]:
            try:
                result = await orch.query_with_retry(source_name, "query", TARGET_DOMAIN)
                individual_results[source_name] = "SUCCESS" if result else "NO_RESULT"
            except Exception as e:
                individual_results[source_name] = f"ERROR: {e}"

        await orch.close()
        duration = time.time() - start

        output_data = {
            "category_queries": all_results,
            "individual_queries": individual_results,
        }

        analysis_lines = [
            "### Category-based query_all results:",
            *category_summaries,
            "",
            "### Individual source queries:",
        ]
        for src, status in individual_results.items():
            analysis_lines.append(f"- {src}: {status}")

        total_sources = sum(
            len(v) if isinstance(v, dict) and "error" not in v else 0
            for v in all_results.values()
        )

        status = "PASS" if total_sources > 0 else "FAIL"
        verdict = f"OSINT Orchestrator: {total_sources} total source responses across {len(categories_to_test)} categories"

        write_report(test_id, "OSINT Orchestrator", duration, status,
                     f"Domain: `{TARGET_DOMAIN}`\nCategories: {[c[1] for c in categories_to_test]}",
                     json.dumps(output_data, indent=2, default=str)[:15000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "OSINT Orchestrator", duration, "ERROR",
                     f"Domain: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.10 — Phishing Checker
# ============================================================
async def test_t1_10_phishing():
    test_id = "T1.10_phishing"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Phishing Checker")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.analysis.phishing_checker import PhishingChecker
        from veritas.config.settings import SAFE_BROWSING_API_KEY

        checker = PhishingChecker(safe_browsing_key=SAFE_BROWSING_API_KEY)
        result = await checker.check(TARGET_URL)
        duration = time.time() - start

        output = format_output(result)

        analysis_lines = [
            f"- Is phishing: {result.is_phishing}",
            f"- Confidence: {result.confidence}",
            f"- Sources checked: {result.sources}",
            f"- Heuristic flags: {result.heuristic_flags}",
            f"- Details: {len(result.details)} entries",
            f"- Errors: {result.errors}",
            f"- Safe Browsing API key: {'present' if SAFE_BROWSING_API_KEY else 'not set'}",
        ]

        status = "PASS"
        verdict = f"Phishing check: is_phishing={result.is_phishing}, confidence={result.confidence}, {len(result.heuristic_flags)} heuristic flags"

        write_report(test_id, "Phishing Checker", duration, status,
                     f"URL: `{TARGET_URL}`\nSafe Browsing key: {'yes' if SAFE_BROWSING_API_KEY else 'no'}",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Phishing Checker", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T1.11 — Meta Analyzer
# ============================================================
async def test_t1_11_meta():
    test_id = "T1.11_meta"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Meta Analyzer")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.analysis.meta_analyzer import MetaAnalyzer

        analyzer = MetaAnalyzer()
        result = await analyzer.analyze(TARGET_DOMAIN)
        duration = time.time() - start

        output = format_output(result)

        analysis_lines = [
            f"- Meta score: {result.meta_score}",
            f"- Risk signals: {result.risk_signals}",
            f"- SSL valid: {result.ssl_info.is_valid if result.ssl_info else 'N/A'}",
            f"- Domain age (days): {result.domain_age.age_days if result.domain_age else 'N/A'}",
            f"- Has SPF: {result.dns_info.has_spf if result.dns_info else 'N/A'}",
            f"- Has DMARC: {result.dns_info.has_dmarc if result.dns_info else 'N/A'}",
            f"- Errors: {result.errors}",
        ]

        status = "PASS" if result.meta_score > 0 else "PARTIAL"
        verdict = f"Meta analysis: score={result.meta_score:.2f}, {len(result.risk_signals)} risk signals, {len(result.errors)} errors"

        write_report(test_id, "Meta Analyzer", duration, status,
                     f"Domain: `{TARGET_DOMAIN}`",
                     output, "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Meta Analyzer", duration, "ERROR",
                     f"Domain: `{TARGET_DOMAIN}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# Main Runner
# ============================================================
async def main():
    print("=" * 60)
    print("VERITAS — Phase T1: OSINT & Data Sources")
    print(f"Target: {TARGET_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tests = [
        ("T1.1",  "DNS Lookup",       test_t1_1_dns),
        ("T1.2",  "WHOIS Lookup",     test_t1_2_whois),
        ("T1.3",  "SSL Certificate",  test_t1_3_ssl),
        ("T1.4",  "IOC Detector",     test_t1_4_ioc),
        ("T1.5",  "Attack Patterns",  test_t1_5_attack_patterns),
        ("T1.6",  "CTI",              test_t1_6_cti),
        ("T1.7",  "URLVoid",          test_t1_7_urlvoid),
        ("T1.8",  "AbuseIPDB",        test_t1_8_abuseipdb),
        ("T1.9",  "OSINT Orchestrator", test_t1_9_osint_orchestrator),
        ("T1.10", "Phishing Checker", test_t1_10_phishing),
        ("T1.11", "Meta Analyzer",    test_t1_11_meta),
    ]

    results = {}
    total_start = time.time()
    PER_TEST_TIMEOUT = 30  # seconds per individual test

    for test_id, name, func in tests:
        try:
            status = await asyncio.wait_for(func(), timeout=PER_TEST_TIMEOUT)
            results[test_id] = status
            print(f"  → {test_id} {name}: {status}")
        except asyncio.TimeoutError:
            results[test_id] = "TIMEOUT"
            print(f"  → {test_id} {name}: TIMEOUT (>{PER_TEST_TIMEOUT}s)")
            write_report(test_id, name, PER_TEST_TIMEOUT, "TIMEOUT",
                         f"Domain: `{TARGET_DOMAIN}`",
                         f"Test exceeded {PER_TEST_TIMEOUT}s timeout",
                         f"- Module hung or network request timed out after {PER_TEST_TIMEOUT}s",
                         f"TIMEOUT — exceeded {PER_TEST_TIMEOUT}s limit")
        except Exception as e:
            results[test_id] = "ERROR"
            print(f"  → {test_id} {name}: ERROR — {e}")

    total_duration = time.time() - total_start

    # Print summary
    print(f"\n{'='*60}")
    print("PHASE T1 SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"Results:")

    for test_id, status in results.items():
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "SKIPPED": "⏭️", "PARTIAL": "⚠️", "TIMEOUT": "⏰"}.get(status, "?")
        print(f"  {icon} {test_id}: {status}")

    passed = sum(1 for s in results.values() if s == "PASS")
    failed = sum(1 for s in results.values() if s in ("FAIL", "ERROR", "TIMEOUT"))
    skipped = sum(1 for s in results.values() if s == "SKIPPED")
    print(f"\n  PASS: {passed} | FAIL/ERROR: {failed} | SKIPPED: {skipped} | TOTAL: {len(results)}")

    # Save summary to file
    summary_path = RESULTS_DIR / "T1_SUMMARY.md"
    summary_lines = [
        f"# Phase T1 — OSINT & Data Sources Summary",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Target:** {TARGET_DOMAIN}",
        f"**Duration:** {total_duration:.1f}s",
        f"**Results:** {passed} PASS / {failed} FAIL / {skipped} SKIPPED",
        "",
        "| # | Module | Status | Report |",
        "|---|--------|--------|--------|",
    ]
    for test_id, status in results.items():
        name = dict((t[0], t[1]) for t in tests).get(test_id, "?")
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "SKIPPED": "⏭️", "PARTIAL": "⚠️", "TIMEOUT": "⏰"}.get(status, "?")
        summary_lines.append(f"| {test_id} | {name} | {icon} {status} | [{test_id}.md]({test_id.replace('.', '_')}.md) |")

    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nSummary written to: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
