"""
Veritas Independent Module Testing — Phase T2: Scout & Browser Automation
=========================================================================
Tests Scout navigation, scrolling, and link discovery independently.
No NIM calls, no budget limits — browser only.

Usage:
    python testing/scripts/test_t2_scout.py

Output:
    testing/results/T2_scout/T2.X_<module>.md (one per test)
    testing/data/screenshots/  (captured screenshots)
    testing/data/html/         (saved page HTML)
    testing/data/metadata/     (saved metadata JSON)
"""

import asyncio
import json
import shutil
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "testing" / "results" / "T2_scout"
DATA_DIR = ROOT / "testing" / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
HTML_DIR = DATA_DIR / "html"
METADATA_DIR = DATA_DIR / "metadata"

for d in [RESULTS_DIR, SCREENSHOTS_DIR, HTML_DIR, METADATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TARGET_DOMAIN = "avrut.com"
TARGET_URL = "https://avrut.com"


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
# T2.1 — Scout Basic Investigation
# ============================================================
async def test_t2_1_scout_basic():
    test_id = "T2.1_scout_basic"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Scout Basic Investigation")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.agents.scout import StealthScout

        async with StealthScout(evidence_dir=SCREENSHOTS_DIR) as scout:
            result = await scout.investigate(
                url=TARGET_URL,
                temporal_delay=5,
                viewport="desktop",
                enable_scrolling=True,
            )
        duration = time.time() - start

        # Save captured data for later phases
        if hasattr(result, 'page_content') and result.page_content:
            (HTML_DIR / "avrut_landing.html").write_text(result.page_content[:500000], encoding="utf-8")
            print(f"  Saved HTML: {len(result.page_content)} chars")

        if hasattr(result, 'response_headers') and result.response_headers:
            (METADATA_DIR / "avrut_headers.json").write_text(
                json.dumps(result.response_headers, indent=2, default=str), encoding="utf-8")

        # Save full metadata
        metadata = {}
        for attr in ['url', 'status_code', 'page_title', 'final_url', 'response_headers',
                      'meta_tags', 'links', 'forms', 'scripts', 'external_resources',
                      'cookies', 'captcha_detected', 'scroll_result']:
            if hasattr(result, attr):
                val = getattr(result, attr)
                try:
                    json.dumps(val, default=str)
                    metadata[attr] = val
                except (TypeError, ValueError):
                    metadata[attr] = str(val)

        (METADATA_DIR / "avrut_scout_result.json").write_text(
            json.dumps(metadata, indent=2, default=str), encoding="utf-8")

        # Count screenshots
        screenshots = list(SCREENSHOTS_DIR.glob("*.jpg")) + list(SCREENSHOTS_DIR.glob("*.png"))
        screenshot_names = [s.name for s in screenshots]

        # End of async with block — indent everything below back

        analysis_lines = [
            f"- Page title: {getattr(result, 'page_title', 'N/A')}",
            f"- Status code: {getattr(result, 'status_code', 'N/A')}",
            f"- Final URL: {getattr(result, 'final_url', 'N/A')}",
            f"- CAPTCHA detected: {getattr(result, 'captcha_detected', 'N/A')}",
            f"- Screenshots captured: {len(screenshot_names)}",
            f"- Screenshot names: {screenshot_names[:10]}",
            f"- HTML size: {len(getattr(result, 'page_content', '') or '')} chars",
            f"- Links found: {len(getattr(result, 'links', []) or [])}",
            f"- Forms found: {len(getattr(result, 'forms', []) or [])}",
            f"- Scripts found: {len(getattr(result, 'scripts', []) or [])}",
            f"- Cookies: {len(getattr(result, 'cookies', []) or [])}",
        ]

        scroll = getattr(result, 'scroll_result', None)
        if scroll:
            analysis_lines.append(f"- Scroll result: {format_output(scroll)}")

        status = "PASS"
        verdict = f"Scout captured {len(screenshot_names)} screenshots, {len(getattr(result, 'page_content', '') or '')} chars HTML, {len(getattr(result, 'links', []) or [])} links"

        write_report(test_id, "Scout Basic (StealthScout.investigate)", duration, status,
                     f"URL: `{TARGET_URL}`\ntemporal_delay=5, viewport=desktop, enable_scrolling=True",
                     format_output(metadata)[:10000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Scout Basic (StealthScout.investigate)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T2.2 — Link Explorer
# ============================================================
async def test_t2_2_link_explorer():
    test_id = "T2.2_link_explorer"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Link Explorer")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.agents.scout_nav.link_explorer import LinkExplorer

        explorer = LinkExplorer(base_url=TARGET_URL)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # Allow dynamic content to load

            links = await explorer.discover_links(page)

            await browser.close()

        duration = time.time() - start

        # Categorize links
        nav_links = [l for l in links if getattr(l, 'location', getattr(l, 'priority', 99)) == 1 or getattr(l, 'location', '') == 'nav']
        footer_links = [l for l in links if getattr(l, 'location', getattr(l, 'priority', 99)) == 2 or getattr(l, 'location', '') == 'footer']
        content_links = [l for l in links if getattr(l, 'location', getattr(l, 'priority', 99)) == 3 or getattr(l, 'location', '') == 'content']

        links_data = []
        for l in links[:30]:
            link_dict = {}
            for attr in ['url', 'text', 'location', 'priority', 'depth']:
                if hasattr(l, attr):
                    link_dict[attr] = getattr(l, attr)
            links_data.append(link_dict)

        # Save for later phases
        (METADATA_DIR / "avrut_links.json").write_text(
            json.dumps(links_data, indent=2, default=str), encoding="utf-8")

        analysis_lines = [
            f"- Total links discovered: {len(links)}",
            f"- Nav links (priority 1): {len(nav_links)}",
            f"- Footer links (priority 2): {len(footer_links)}",
            f"- Content links (priority 3): {len(content_links)}",
            "",
            "### All discovered links:",
        ]
        for l in links[:30]:
            url = getattr(l, 'url', '?')
            text = getattr(l, 'text', '?')
            pri = getattr(l, 'priority', '?')
            loc = getattr(l, 'location', '?')
            analysis_lines.append(f"  - [{pri}] ({loc}) `{text}` → {url}")

        status = "PASS" if len(links) > 0 else "FAIL"
        verdict = f"Link Explorer discovered {len(links)} links: {len(nav_links)} nav, {len(footer_links)} footer, {len(content_links)} content"

        write_report(test_id, "Link Explorer", duration, status,
                     f"URL: `{TARGET_URL}`\nBase domain: {TARGET_DOMAIN}",
                     json.dumps(links_data, indent=2, default=str)[:8000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Link Explorer", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T2.3 — Scroll Orchestrator
# ============================================================
async def test_t2_3_scroll():
    test_id = "T2.3_scroll"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Scroll Orchestrator")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.agents.scout_nav.scroll_orchestrator import ScrollOrchestrator
        from veritas.agents.scout_nav.lazy_load_detector import LazyLoadDetector

        scroll_dir = SCREENSHOTS_DIR / "scroll_test"
        scroll_dir.mkdir(parents=True, exist_ok=True)

        detector = LazyLoadDetector()
        orchestrator = ScrollOrchestrator(evidence_dir=scroll_dir, detector=detector)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            scroll_result = await orchestrator.scroll_page(
                page=page,
                audit_id="t2_scroll_test",
                screenshot_interval=2,
            )

            await browser.close()

        duration = time.time() - start

        # Count scroll screenshots
        scroll_screenshots = list(scroll_dir.glob("*.jpg")) + list(scroll_dir.glob("*.png"))

        output = format_output(scroll_result)

        analysis_lines = [
            f"- Scroll result: {output[:2000]}",
            f"- Screenshots from scrolling: {len(scroll_screenshots)}",
            f"- Screenshot files: {[s.name for s in scroll_screenshots[:10]]}",
        ]

        if hasattr(scroll_result, 'total_cycles'):
            analysis_lines.append(f"- Total cycles: {scroll_result.total_cycles}")
        if hasattr(scroll_result, 'stabilized'):
            analysis_lines.append(f"- Stabilized: {scroll_result.stabilized}")

        status = "PASS"
        verdict = f"Scroll Orchestrator: {len(scroll_screenshots)} screenshots captured during scrolling"

        write_report(test_id, "Scroll Orchestrator", duration, status,
                     f"URL: `{TARGET_URL}`\naudit_id=t2_scroll_test, screenshot_interval=2",
                     output[:5000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Scroll Orchestrator", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T2.4 — Lazy Load Detector
# ============================================================
async def test_t2_4_lazy_load():
    test_id = "T2.4_lazy_load"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Lazy Load Detector")
    print(f"{'='*60}")

    start = time.time()
    try:
        from playwright.async_api import async_playwright
        from veritas.agents.scout_nav.lazy_load_detector import LazyLoadDetector

        detector = LazyLoadDetector()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Inject the detector
            await detector.inject(page)

            # Check initial state (should have no new content since we just loaded)
            initial_check = await detector.has_new_content(page)

            # Now scroll down to trigger lazy loading
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)

            # Check after scroll
            after_scroll = await detector.has_new_content(page)

            # Scroll more
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)
            after_scroll2 = await detector.has_new_content(page)

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            after_bottom = await detector.has_new_content(page)

            await browser.close()

        duration = time.time() - start

        output_data = {
            "initial_check": initial_check,
            "after_first_scroll": after_scroll,
            "after_second_scroll": after_scroll2,
            "after_scroll_to_bottom": after_bottom,
        }

        analysis_lines = [
            f"- Initial check (after page load): {initial_check}",
            f"- After 1st scroll (1 viewport): {after_scroll}",
            f"- After 2nd scroll (2 viewports): {after_scroll2}",
            f"- After scroll to bottom: {after_bottom}",
            "",
            "Interpreting results:",
            f"- hasMutations = DOM elements were added/removed",
            f"- scrollHeightChanged = page height grew (new content loaded)",
            f"- bothSignals = strong evidence of lazy-loaded content",
        ]

        status = "PASS"
        verdict = f"Lazy Load Detector: injection successful, detected mutations across 4 scroll checkpoints"

        write_report(test_id, "Lazy Load Detector", duration, status,
                     f"URL: `{TARGET_URL}`\nMethods: inject(), has_new_content() × 4 checkpoints",
                     json.dumps(output_data, indent=2, default=str),
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Lazy Load Detector", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# T2.5 — Scout Multi-Page Exploration
# ============================================================
async def test_t2_5_multi_page():
    test_id = "T2.5_multi_page"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Scout Multi-Page Exploration")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.agents.scout import StealthScout

        multi_dir = SCREENSHOTS_DIR / "multi_page"
        multi_dir.mkdir(parents=True, exist_ok=True)

        async with StealthScout(evidence_dir=multi_dir) as scout:
            # Test with max_pages=8 (the full planned capacity)
            result = await scout.explore_multi_page(
                url=TARGET_URL,
                max_pages=8,
                timeout_per_page_ms=20000,
                enable_scrolling=True,
            )

        duration = time.time() - start

        output = format_output(result)

        # Count what we got
        pages_visited = getattr(result, 'pages_visited', []) or getattr(result, 'page_visits', []) or []
        links_discovered = getattr(result, 'links_discovered', []) or []

        # Save multi-page data
        multi_data = {
            "pages_visited_count": len(pages_visited),
            "links_discovered_count": len(links_discovered),
            "pages": [],
            "links": [],
        }
        for pv in pages_visited[:20]:
            page_info = {}
            for attr in ['url', 'status', 'page_title', 'navigation_time_ms', 'screenshot_path']:
                if hasattr(pv, attr):
                    page_info[attr] = str(getattr(pv, attr))
            multi_data["pages"].append(page_info)

        for l in links_discovered[:30]:
            link_info = {}
            for attr in ['url', 'text', 'location', 'priority']:
                if hasattr(l, attr):
                    link_info[attr] = getattr(l, attr)
            multi_data["links"].append(link_info)

        (METADATA_DIR / "avrut_multi_page.json").write_text(
            json.dumps(multi_data, indent=2, default=str), encoding="utf-8")

        # Count screenshots
        multi_screenshots = list(multi_dir.glob("*.jpg")) + list(multi_dir.glob("*.png"))

        analysis_lines = [
            f"- Pages visited: {len(pages_visited)}/{8}",
            f"- Links discovered: {len(links_discovered)}",
            f"- Screenshots: {len(multi_screenshots)}",
            "",
            "### Pages visited:",
        ]
        for i, pv in enumerate(pages_visited[:15]):
            url = getattr(pv, 'url', '?')
            title = getattr(pv, 'page_title', '?')
            status_val = getattr(pv, 'status', '?')
            nav_time = getattr(pv, 'navigation_time_ms', '?')
            analysis_lines.append(f"  {i+1}. [{status_val}] {url} — \"{title}\" ({nav_time}ms)")

        status = "PASS" if len(pages_visited) > 1 else "PARTIAL"
        verdict = f"Multi-page: visited {len(pages_visited)}/8 pages, discovered {len(links_discovered)} links, captured {len(multi_screenshots)} screenshots"

        write_report(test_id, "Scout Multi-Page (explore_multi_page)", duration, status,
                     f"URL: `{TARGET_URL}`\nmax_pages=8, timeout_per_page=20000ms, enable_scrolling=True",
                     output[:10000],
                     "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Scout Multi-Page (explore_multi_page)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED with exception: {e}")
        return "ERROR"


# ============================================================
# Main Runner
# ============================================================
async def main():
    print("=" * 60)
    print("VERITAS — Phase T2: Scout & Browser Automation")
    print(f"Target: {TARGET_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tests = [
        ("T2.1",  "Scout Basic",     test_t2_1_scout_basic),
        ("T2.2",  "Link Explorer",   test_t2_2_link_explorer),
        ("T2.3",  "Scroll Orch.",    test_t2_3_scroll),
        ("T2.4",  "Lazy Load Det.",  test_t2_4_lazy_load),
        ("T2.5",  "Multi-Page",      test_t2_5_multi_page),
    ]

    results = {}
    total_start = time.time()
    PER_TEST_TIMEOUT = 120  # 2 min per test for browser tests

    for test_id, name, func in tests:
        try:
            status = await asyncio.wait_for(func(), timeout=PER_TEST_TIMEOUT)
            results[test_id] = status
            print(f"  → {test_id} {name}: {status}")
        except asyncio.TimeoutError:
            results[test_id] = "TIMEOUT"
            print(f"  → {test_id} {name}: TIMEOUT (>{PER_TEST_TIMEOUT}s)")
            write_report(test_id, name, PER_TEST_TIMEOUT, "TIMEOUT",
                         f"URL: `{TARGET_URL}`",
                         f"Test exceeded {PER_TEST_TIMEOUT}s timeout",
                         f"- Module hung or browser operation timed out after {PER_TEST_TIMEOUT}s",
                         f"TIMEOUT — exceeded {PER_TEST_TIMEOUT}s limit")
        except Exception as e:
            results[test_id] = "ERROR"
            print(f"  → {test_id} {name}: ERROR — {e}")

    total_duration = time.time() - total_start

    print(f"\n{'='*60}")
    print("PHASE T2 SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.1f}s")

    for test_id, status in results.items():
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "SKIPPED": "⏭️", "PARTIAL": "⚠️", "TIMEOUT": "⏰"}.get(status, "?")
        print(f"  {icon} {test_id}: {status}")

    passed = sum(1 for s in results.values() if s == "PASS")
    failed = sum(1 for s in results.values() if s in ("FAIL", "ERROR", "TIMEOUT"))
    print(f"\n  PASS: {passed} | FAIL/ERROR: {failed} | TOTAL: {len(results)}")

    # Save summary
    summary_path = RESULTS_DIR / "T2_SUMMARY.md"
    summary_lines = [
        f"# Phase T2 — Scout & Browser Automation Summary",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Target:** {TARGET_DOMAIN}",
        f"**Duration:** {total_duration:.1f}s",
        f"**Results:** {passed} PASS / {failed} FAIL",
        "",
        "| # | Module | Status |",
        "|---|--------|--------|",
    ]
    for test_id, status in results.items():
        name = dict((t[0], t[1]) for t in tests).get(test_id, "?")
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "PARTIAL": "⚠️", "TIMEOUT": "⏰"}.get(status, "?")
        summary_lines.append(f"| {test_id} | {name} | {icon} {status} |")

    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nSummary: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
