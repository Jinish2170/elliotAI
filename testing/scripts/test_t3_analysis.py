"""
Veritas Independent Module Testing — Phase T3: Analysis Modules
================================================================
Tests DOM, form, JS, redirect, security headers, temporal, pattern matcher,
and exploitation advisor independently. No NIM calls.

Usage:
    python testing/scripts/test_t3_analysis.py

Output:
    testing/results/T3_analysis/T3.X_<module>.md
"""

import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "testing" / "results" / "T3_analysis"
DATA_DIR = ROOT / "testing" / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DOMAIN = "avrut.com"
TARGET_URL = "https://avrut.com"
PER_TEST_TIMEOUT = 60  # seconds


def write_report(test_id: str, module_name: str, duration: float, status: str,
                 input_desc: str, output_data: str, analysis: str, verdict: str):
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
    try:
        if hasattr(data, 'to_dict'):
            return json.dumps(data.to_dict(), indent=2, default=str)
        elif hasattr(data, '__dict__'):
            d = {}
            for k, v in data.__dict__.items():
                if k.startswith('_'):
                    continue
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
# T3.1 — DOM Analyzer
# ============================================================
async def test_t3_1_dom():
    test_id = "T3.1_dom"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: DOM Analyzer")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.analysis.dom_analyzer import DOMAnalyzer

        analyzer = DOMAnalyzer()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            result = await analyzer.analyze(page)
            await browser.close()

        duration = time.time() - start
        output = format_output(result)

        findings = getattr(result, 'findings', []) or []
        score = getattr(result, 'structural_score', None)
        health = getattr(result, 'page_health', None)

        analysis_lines = [
            f"- Structural score: {score}",
            f"- Total findings: {len(findings)}",
            f"- Page health: {format_output(health)[:2000] if health else 'N/A'}",
            "",
            "### Findings:",
        ]
        for f in findings[:20]:
            sev = getattr(f, 'severity', '?')
            cat = getattr(f, 'category', '?')
            desc = getattr(f, 'description', str(f))
            analysis_lines.append(f"  - [{sev}] {cat}: {desc[:200]}")

        status = "PASS"
        verdict = f"DOM Analyzer: structural_score={score}, {len(findings)} findings"

        write_report(test_id, "DOM Analyzer", duration, status,
                     f"URL: `{TARGET_URL}`\nMethod: analyze(page)",
                     output[:10000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "DOM Analyzer", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.2 — Form Validator
# ============================================================
async def test_t3_2_form():
    test_id = "T3.2_form"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Form Validator")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.analysis.form_validator import FormActionValidator

        validator = FormActionValidator()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            result = await validator.analyze(TARGET_URL, page=page)
            await browser.close()

        duration = time.time() - start
        output = format_output(result)

        total = getattr(result, 'total_forms', 0)
        critical = getattr(result, 'critical_count', 0)
        score = getattr(result, 'score', None)
        forms = getattr(result, 'forms', []) or []

        analysis_lines = [
            f"- Score: {score}",
            f"- Total forms: {total}",
            f"- Critical issues: {critical}",
            "",
            "### Form Details:",
        ]
        for f in forms[:10]:
            action = getattr(f, 'action', '?')
            method = getattr(f, 'method', '?')
            issues = getattr(f, 'issues', [])
            analysis_lines.append(f"  - Form: {method} {action}")
            for iss in (issues or [])[:5]:
                analysis_lines.append(f"    - {iss}")

        status = "PASS"
        verdict = f"Form Validator: score={score}, {total} forms, {critical} critical issues"

        write_report(test_id, "Form Validator", duration, status,
                     f"URL: `{TARGET_URL}`\nMethod: analyze(url, page=page)",
                     output[:10000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Form Validator", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.3 — JS Analyzer
# ============================================================
async def test_t3_3_js():
    test_id = "T3.3_js"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: JS Analyzer")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.analysis.js_analyzer import JSObfuscationDetector

        analyzer = JSObfuscationDetector()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            result = await analyzer.analyze(TARGET_URL, page=page)
            await browser.close()

        duration = time.time() - start
        output = format_output(result)

        score = getattr(result, 'score', None)
        flags = getattr(result, 'flags', []) or []
        total = getattr(result, 'total_scripts', 0)
        inline = getattr(result, 'inline_scripts', 0)
        external = getattr(result, 'external_scripts', 0)

        analysis_lines = [
            f"- Score: {score}",
            f"- Total scripts: {total} (inline={inline}, external={external})",
            f"- Flags: {len(flags)}",
            "",
            "### JS Flags:",
        ]
        for f in flags[:20]:
            sev = getattr(f, 'severity', '?')
            cat = getattr(f, 'category', '?')
            desc = getattr(f, 'description', str(f))
            analysis_lines.append(f"  - [{sev}] {cat}: {desc[:200]}")

        status = "PASS"
        verdict = f"JS Analyzer: score={score}, {total} scripts ({inline} inline, {external} external), {len(flags)} flags"

        write_report(test_id, "JS Analyzer", duration, status,
                     f"URL: `{TARGET_URL}`\nMethod: analyze(url, page=page)",
                     output[:10000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "JS Analyzer", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.4 — Redirect Analyzer
# ============================================================
async def test_t3_4_redirect():
    test_id = "T3.4_redirect"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Redirect Analyzer")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.analysis.redirect_analyzer import RedirectAnalyzer

        analyzer = RedirectAnalyzer(max_hops=10)
        result = await analyzer.analyze(TARGET_URL, timeout=15)

        duration = time.time() - start
        output = format_output(result)

        chain = getattr(result, 'chain', []) or []
        hops = getattr(result, 'total_hops', 0)
        cross = getattr(result, 'has_cross_domain', False)
        downgrade = getattr(result, 'has_downgrade', False)
        tracking = getattr(result, 'has_tracking_redirect', False)
        score = getattr(result, 'score', None)

        analysis_lines = [
            f"- Score: {score}",
            f"- Total hops: {hops}",
            f"- Cross-domain redirect: {cross}",
            f"- HTTPS→HTTP downgrade: {downgrade}",
            f"- Tracking redirect: {tracking}",
            "",
            "### Redirect Chain:",
        ]
        for i, hop in enumerate(chain[:15]):
            url = getattr(hop, 'url', '?')
            status_code = getattr(hop, 'status_code', '?')
            analysis_lines.append(f"  {i+1}. [{status_code}] {url}")

        status = "PASS"
        verdict = f"Redirect Analyzer: score={score}, {hops} hops, cross_domain={cross}, downgrade={downgrade}"

        write_report(test_id, "Redirect Analyzer", duration, status,
                     f"URL: `{TARGET_URL}`\nMethod: analyze(url, timeout=15)\nmax_hops=10",
                     output[:10000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Redirect Analyzer", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.5 — Security Header Analyzer
# ============================================================
async def test_t3_5_headers():
    test_id = "T3.5_security_headers"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Security Header Analyzer")
    print(f"{'='*60}")

    start = time.time()
    try:
        # Try common class name patterns
        try:
            from veritas.analysis.security_headers import SecurityHeaderAnalyzer
            analyzer = SecurityHeaderAnalyzer()
        except (ImportError, AttributeError):
            from veritas.analysis import security_headers
            # Find the analyzer class
            for name in dir(security_headers):
                obj = getattr(security_headers, name)
                if isinstance(obj, type) and name != 'SecurityModule' and 'header' in name.lower():
                    analyzer = obj()
                    break
            else:
                raise ImportError("Could not find SecurityHeaderAnalyzer class")

        result = await analyzer.analyze(TARGET_URL, timeout=15)

        duration = time.time() - start
        output = format_output(result)

        checks = getattr(result, 'checks', []) or []
        score = getattr(result, 'score', None)
        resp_code = getattr(result, 'response_code', None)
        server = getattr(result, 'server', None)

        analysis_lines = [
            f"- Score: {score}",
            f"- Response code: {resp_code}",
            f"- Server: {server}",
            f"- Header checks: {len(checks)}",
            "",
            "### Header Checks:",
        ]
        for c in checks[:20]:
            name = getattr(c, 'header', getattr(c, 'name', '?'))
            present = getattr(c, 'present', getattr(c, 'found', '?'))
            value = getattr(c, 'value', '')
            sev = getattr(c, 'severity', '?')
            analysis_lines.append(f"  - {name}: present={present}, value='{str(value)[:100]}' [{sev}]")

        status = "PASS"
        verdict = f"Security Headers: score={score}, {len(checks)} checks, server={server}"

        write_report(test_id, "Security Header Analyzer", duration, status,
                     f"URL: `{TARGET_URL}`\nMethod: analyze(url, timeout=15)",
                     output[:10000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Security Header Analyzer", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.6 — Temporal Analyzer
# ============================================================
async def test_t3_6_temporal():
    test_id = "T3.6_temporal"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Temporal Analyzer")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.analysis.temporal_analyzer import TemporalAnalyzer

        analyzer = TemporalAnalyzer()

        # Find T2 screenshots to use as t0 and t_delay
        t0_candidates = list(SCREENSHOTS_DIR.glob("*_t0.*"))
        t5_candidates = list(SCREENSHOTS_DIR.glob("*_t5.*"))

        if not t0_candidates or not t5_candidates:
            # Fall back: use any two screenshots from T2
            all_screenshots = sorted(SCREENSHOTS_DIR.glob("*.jpg"))
            if len(all_screenshots) >= 2:
                t0_path = str(all_screenshots[0])
                t5_path = str(all_screenshots[1])
            else:
                raise FileNotFoundError("No T2 screenshots found. Run T2 first.")
        else:
            t0_path = str(t0_candidates[0])
            t5_path = str(t5_candidates[0])

        print(f"  Using t0: {Path(t0_path).name}")
        print(f"  Using t5: {Path(t5_path).name}")

        # Try compare_screenshots first
        try:
            findings = analyzer.compare_screenshots(t0_path, t5_path, delay_seconds=5.0)
        except TypeError:
            # Might be async
            findings = await analyzer.compare_screenshots(t0_path, t5_path, delay_seconds=5.0)

        # Try analyze_temporal_changes
        try:
            changes = analyzer.analyze_temporal_changes(t0_path, t5_path)
        except TypeError:
            changes = await analyzer.analyze_temporal_changes(t0_path, t5_path)

        duration = time.time() - start

        findings_output = format_output(findings) if findings else "No findings"
        changes_output = format_output(changes) if changes else "No changes data"

        analysis_lines = [
            f"- t0 screenshot: {Path(t0_path).name}",
            f"- t_delay screenshot: {Path(t5_path).name}",
            f"- Temporal findings: {len(findings) if isinstance(findings, list) else 'N/A'}",
            "",
            "### compare_screenshots():",
            findings_output[:3000],
            "",
            "### analyze_temporal_changes():",
            changes_output[:3000],
        ]

        if isinstance(changes, dict):
            ssim = changes.get('ssim_score', None)
            has_changes = changes.get('has_changes', None)
            analysis_lines.insert(3, f"- SSIM score: {ssim}")
            analysis_lines.insert(4, f"- Has changes: {has_changes}")

        status = "PASS"
        verdict = f"Temporal Analyzer: analyzed 2 screenshots, findings={len(findings) if isinstance(findings, list) else '?'}"

        write_report(test_id, "Temporal Analyzer", duration, status,
                     f"Screenshots: `{Path(t0_path).name}` vs `{Path(t5_path).name}`\ndelay_seconds=5.0",
                     f"### Findings:\n{findings_output[:5000]}\n\n### Changes:\n{changes_output[:5000]}",
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Temporal Analyzer", duration, "ERROR",
                     f"Screenshots from T2",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.7 — Pattern Matcher
# ============================================================
async def test_t3_7_pattern():
    test_id = "T3.7_pattern_matcher"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Pattern Matcher")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.analysis.pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        # Test prompt generation (no API needed)
        screenshot_prompts = matcher.get_screenshot_prompts()
        temporal_prompts = matcher.get_temporal_prompts()

        # Test batched prompt generation
        try:
            batched = matcher.build_batched_prompt(max_categories=3)
        except Exception:
            batched = []

        # Test VLM response parsing with a mock response
        mock_response = "DETECTED: Fake countdown timer showing '2:34:21 remaining' that resets on page reload"
        try:
            parsed = matcher.parse_vlm_response(mock_response, "urgency", "countdown_timer")
        except Exception as pe:
            parsed = f"Parse error: {pe}"

        duration = time.time() - start

        output_data = {
            "screenshot_prompts_count": len(screenshot_prompts),
            "temporal_prompts_count": len(temporal_prompts),
            "batched_prompts_count": len(batched) if isinstance(batched, list) else 0,
            "sample_screenshot_prompt": screenshot_prompts[0] if screenshot_prompts else None,
            "sample_temporal_prompt": temporal_prompts[0] if temporal_prompts else None,
            "parsed_mock_response": format_output(parsed),
        }

        analysis_lines = [
            f"- Screenshot prompts generated: {len(screenshot_prompts)}",
            f"- Temporal prompts generated: {len(temporal_prompts)}",
            f"- Batched prompts: {len(batched) if isinstance(batched, list) else 0}",
            f"- Mock VLM parse result: {format_output(parsed)[:500]}",
            "",
            "### Screenshot Prompt Categories:",
        ]
        for i, prompt in enumerate(screenshot_prompts[:10]):
            cat = prompt.get('category', '?') if isinstance(prompt, dict) else '?'
            analysis_lines.append(f"  {i+1}. {cat}")

        status = "PASS" if screenshot_prompts else "FAIL"
        verdict = f"Pattern Matcher: {len(screenshot_prompts)} screenshot prompts, {len(temporal_prompts)} temporal prompts"

        write_report(test_id, "Pattern Matcher", duration, status,
                     "Methods: get_screenshot_prompts(), get_temporal_prompts(), build_batched_prompt(), parse_vlm_response()",
                     json.dumps(output_data, indent=2, default=str)[:10000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Pattern Matcher", duration, "ERROR",
                     "PatternMatcher()",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T3.8 — Exploitation Advisor
# ============================================================
async def test_t3_8_exploit():
    test_id = "T3.8_exploitation_advisor"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Exploitation Advisor")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.analysis.exploitation_advisor import ExploitationAdvisor

        advisor = ExploitationAdvisor()

        # Feed it realistic test vulnerabilities
        test_vulns = [
            {"cve": "CVE-2023-44487", "severity": "CRITICAL", "title": "HTTP/2 Rapid Reset Attack"},
            {"cve": "CVE-2024-21762", "severity": "HIGH", "title": "FortiOS Out-of-Bound Write"},
            {"cve": "CVE-2023-4863", "severity": "MEDIUM", "title": "libwebp Heap Buffer Overflow"},
        ]

        advisories = advisor.generate_advisory(test_vulns)

        duration = time.time() - start
        output = format_output(advisories)

        analysis_lines = [
            f"- Input vulnerabilities: {len(test_vulns)}",
            f"- Advisories generated: {len(advisories) if isinstance(advisories, list) else '?'}",
            "",
            "### Advisories:",
        ]
        if isinstance(advisories, list):
            for a in advisories[:10]:
                if isinstance(a, dict):
                    cve = a.get('cve', '?')
                    pri = a.get('priority', '?')
                    rem = a.get('remediation', '?')
                    analysis_lines.append(f"  - {cve} [{pri}]: {str(rem)[:200]}")
                else:
                    analysis_lines.append(f"  - {format_output(a)[:200]}")

        status = "PASS" if advisories else "FAIL"
        verdict = f"Exploitation Advisor: generated {len(advisories) if isinstance(advisories, list) else 0} advisories from {len(test_vulns)} vulnerabilities"

        write_report(test_id, "Exploitation Advisor", duration, status,
                     f"Input: {len(test_vulns)} test vulnerabilities (CRITICAL, HIGH, MEDIUM)\nMethod: generate_advisory(vulns)",
                     output[:10000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Exploitation Advisor", duration, "ERROR",
                     "Test vulnerabilities",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# Main Runner
# ============================================================
async def main():
    print("=" * 60)
    print("VERITAS — Phase T3: Analysis Modules")
    print(f"Target: {TARGET_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tests = [
        ("T3.1", "DOM Analyzer", test_t3_1_dom),
        ("T3.2", "Form Validator", test_t3_2_form),
        ("T3.3", "JS Analyzer", test_t3_3_js),
        ("T3.4", "Redirect Analyzer", test_t3_4_redirect),
        ("T3.5", "Security Headers", test_t3_5_headers),
        ("T3.6", "Temporal Analyzer", test_t3_6_temporal),
        ("T3.7", "Pattern Matcher", test_t3_7_pattern),
        ("T3.8", "Exploit Advisor", test_t3_8_exploit),
    ]

    results = {}
    total_start = time.time()

    for tid, name, func in tests:
        try:
            r = await asyncio.wait_for(func(), timeout=PER_TEST_TIMEOUT)
        except asyncio.TimeoutError:
            r = "TIMEOUT"
            write_report(f"{tid}_{name.lower().replace(' ', '_')}", name, PER_TEST_TIMEOUT, "TIMEOUT",
                         f"URL: `{TARGET_URL}`", f"Test exceeded {PER_TEST_TIMEOUT}s timeout",
                         "- Test timed out", f"TIMEOUT after {PER_TEST_TIMEOUT}s")
        results[tid] = r
        print(f"  → {tid} {name}: {r}")

    total_duration = time.time() - total_start

    # Summary
    print(f"\n{'='*60}")
    print("PHASE T3 SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.1f}s")

    pass_count = sum(1 for v in results.values() if v == "PASS")
    fail_count = sum(1 for v in results.values() if v in ("FAIL", "ERROR", "TIMEOUT"))

    for tid, r in results.items():
        icon = "✅" if r == "PASS" else ("⚠️" if r == "PARTIAL" else "❌")
        print(f"  {icon} {tid}: {r}")

    print(f"\n  PASS: {pass_count} | FAIL/ERROR: {fail_count} | TOTAL: {len(results)}")

    # Write summary
    summary = RESULTS_DIR / "T3_SUMMARY.md"
    rows = "\n".join(f"| {tid} | {name} | {'✅' if results[tid] == 'PASS' else '❌'} {results[tid]} |"
                     for tid, name, _ in tests)
    summary.write_text(f"""# Phase T3 — Analysis Modules Summary
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Target:** {TARGET_DOMAIN}
**Duration:** {total_duration:.1f}s
**Results:** {pass_count} PASS / {fail_count} FAIL

| # | Module | Status |
|---|--------|--------|
{rows}
""", encoding="utf-8")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())
