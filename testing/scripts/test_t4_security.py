"""
Veritas Independent Module Testing — Phase T4: Security Agent
==============================================================
Tests the SecurityAgent with full rule-based analysis (no NIM).
Feeds it real data from T2/T3 (HTML, headers, DOM metadata).

Usage:
    python testing/scripts/test_t4_security.py

Output:
    testing/results/T4_security/T4.X_<module>.md
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

RESULTS_DIR = ROOT / "testing" / "results" / "T4_security"
DATA_DIR = ROOT / "testing" / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
HTML_DIR = DATA_DIR / "html"
METADATA_DIR = DATA_DIR / "metadata"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DOMAIN = "avrut.com"
TARGET_URL = "https://avrut.com"
PER_TEST_TIMEOUT = 120  # security agent can be slow


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
# T4.1 — Security Agent (Full Rule-Based, No NIM)
# ============================================================
async def test_t4_1_security_full():
    test_id = "T4.1_security_full"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Security Agent (Full, No NIM)")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.agents.security_agent import SecurityAgent

        # Load real data from T2 if available
        html_path = HTML_DIR / "avrut_landing.html"
        headers_path = METADATA_DIR / "avrut_headers.json"
        scout_path = METADATA_DIR / "avrut_scout_result.json"

        page_content = None
        headers = None

        if html_path.exists():
            page_content = html_path.read_text(encoding="utf-8")
            print(f"  Loaded HTML: {len(page_content)} chars")

        if headers_path.exists():
            headers = json.loads(headers_path.read_text(encoding="utf-8"))
            print(f"  Loaded headers: {len(headers)} keys")

        # Create agent without NIM (rule-based only)
        agent = SecurityAgent(nim_client=None)

        result = await agent.analyze(
            url=TARGET_URL,
            page_content=page_content,
            headers=headers,
        )

        duration = time.time() - start
        output = format_output(result)

        score = getattr(result, 'composite_score', None)
        findings = getattr(result, 'findings', []) or []
        modules_run = getattr(result, 'modules_run', []) or []
        modules_failed = getattr(result, 'modules_failed', []) or []
        modules_results = getattr(result, 'modules_results', {}) or {}
        errors = getattr(result, 'errors', []) or []
        analysis_time = getattr(result, 'analysis_time_ms', 0)

        analysis_lines = [
            f"- Composite score: {score}",
            f"- Findings: {len(findings)}",
            f"- Modules run: {len(modules_run)} — {modules_run}",
            f"- Modules failed: {len(modules_failed)} — {modules_failed}",
            f"- Analysis time: {analysis_time}ms",
            f"- Errors: {len(errors)}",
            "",
            "### Findings:",
        ]
        for f in findings[:30]:
            sev = getattr(f, 'severity', '?')
            cat = getattr(f, 'category', getattr(f, 'module', '?'))
            desc = getattr(f, 'description', getattr(f, 'title', str(f)))
            analysis_lines.append(f"  - [{sev}] {cat}: {str(desc)[:200]}")

        if modules_results:
            analysis_lines.append("")
            analysis_lines.append("### Per-Module Scores:")
            for mod, mod_result in modules_results.items():
                mod_score = mod_result.get('score', '?') if isinstance(mod_result, dict) else getattr(mod_result, 'score', '?')
                analysis_lines.append(f"  - {mod}: {mod_score}")

        if errors:
            analysis_lines.append("")
            analysis_lines.append("### Errors:")
            for e in errors[:10]:
                analysis_lines.append(f"  - {e}")

        status = "PASS"
        verdict = f"Security Agent: composite_score={score}, {len(findings)} findings, {len(modules_run)} modules run, {len(modules_failed)} failed"

        write_report(test_id, "Security Agent (Full, No NIM)", duration, status,
                     f"URL: `{TARGET_URL}`\nPage content: {'Yes' if page_content else 'No'} ({len(page_content) if page_content else 0} chars)\nHeaders: {'Yes' if headers else 'No'}\nNIM: None (rule-based only)",
                     output[:15000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Security Agent (Full, No NIM)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T4.2 — Security Agent with Playwright Page
# ============================================================
async def test_t4_2_security_with_page():
    test_id = "T4.2_security_with_page"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Security Agent (With Playwright Page)")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.agents.security_agent import SecurityAgent

        agent = SecurityAgent(nim_client=None)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Get HTML and headers from page
            page_content = await page.content()
            headers = {}  # response headers would need interception

            result = await agent.analyze(
                url=TARGET_URL,
                page_content=page_content,
                headers=headers,
                page=page,
            )

            await browser.close()

        duration = time.time() - start
        output = format_output(result)

        score = getattr(result, 'composite_score', None)
        findings = getattr(result, 'findings', []) or []
        modules_run = getattr(result, 'modules_run', []) or []
        modules_failed = getattr(result, 'modules_failed', []) or []

        analysis_lines = [
            f"- Composite score: {score}",
            f"- Findings: {len(findings)}",
            f"- Modules run: {len(modules_run)} — {modules_run}",
            f"- Modules failed: {len(modules_failed)} — {modules_failed}",
            "",
            "### Findings (top 30):",
        ]
        for f in findings[:30]:
            sev = getattr(f, 'severity', '?')
            cat = getattr(f, 'category', getattr(f, 'module', '?'))
            desc = getattr(f, 'description', getattr(f, 'title', str(f)))
            analysis_lines.append(f"  - [{sev}] {cat}: {str(desc)[:200]}")

        status = "PASS"
        verdict = f"Security Agent (with page): composite_score={score}, {len(findings)} findings, {len(modules_run)} modules"

        write_report(test_id, "Security Agent (With Page)", duration, status,
                     f"URL: `{TARGET_URL}`\nPage: Playwright (live)\nNIM: None (rule-based only)",
                     output[:15000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Security Agent (With Page)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# Main Runner
# ============================================================
async def main():
    print("=" * 60)
    print("VERITAS — Phase T4: Security Agent")
    print(f"Target: {TARGET_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tests = [
        ("T4.1", "Security (Full)", test_t4_1_security_full),
        ("T4.2", "Security (Page)", test_t4_2_security_with_page),
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

    print(f"\n{'='*60}")
    print("PHASE T4 SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.1f}s")

    pass_count = sum(1 for v in results.values() if v == "PASS")
    fail_count = sum(1 for v in results.values() if v in ("FAIL", "ERROR", "TIMEOUT"))

    for tid, r in results.items():
        icon = "✅" if r == "PASS" else ("⚠️" if r == "PARTIAL" else "❌")
        print(f"  {icon} {tid}: {r}")

    print(f"\n  PASS: {pass_count} | FAIL/ERROR: {fail_count} | TOTAL: {len(results)}")

    summary = RESULTS_DIR / "T4_SUMMARY.md"
    rows = "\n".join(f"| {tid} | {name} | {'✅' if results[tid] == 'PASS' else '❌'} {results[tid]} |"
                     for tid, name, _ in tests)
    summary.write_text(f"""# Phase T4 — Security Agent Summary
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
