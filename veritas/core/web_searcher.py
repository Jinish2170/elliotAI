"""
Veritas — Multi-Engine Web Search System

Home-built search engine that queries multiple sources in parallel,
merges results, and optionally enriches them by following links.

Engines (tried in order of priority, first success wins):
    1. DuckDuckGo HTML  — lightweight, no JS, fast
    2. Google HTML      — better relevance for entity verification
    3. Bing HTML        — additional diversity

If multiple engines succeed, results are merged and deduplicated.

Returns results in Tavily-compatible format:
    [{"title": str, "url": str, "content": str, "source": str}, ...]

This module is designed to eventually replace Tavily entirely as it
matures. The Graph Investigator calls it as a fallback (or primary)
search provider.
"""

import asyncio
import hashlib
import logging
import random
from typing import Optional
from urllib.parse import quote_plus, urlparse

logger = logging.getLogger("veritas.web_searcher")

# ============================================================
# Shared Browser Pool
# ============================================================
_playwright_module = None
_browser_instance = None
_browser_lock = asyncio.Lock()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

STEALTH_SCRIPTS = [
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
    "window.chrome = {runtime: {}}",
    "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
    "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]})",
]


async def _get_browser():
    """Lazy-init a persistent Playwright Chromium browser."""
    global _playwright_module, _browser_instance

    async with _browser_lock:
        if _browser_instance and _browser_instance.is_connected():
            return _browser_instance

        from playwright.async_api import async_playwright

        _playwright_module = await async_playwright().start()
        _browser_instance = await _playwright_module.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        logger.info("WebSearcher: Playwright browser launched")
        return _browser_instance


async def _new_stealth_page(browser):
    """Create a stealth browser context + page."""
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
    )
    for script in STEALTH_SCRIPTS:
        await context.add_init_script(script)
    page = await context.new_page()
    return context, page


# ============================================================
# Engine: DuckDuckGo HTML
# ============================================================

async def _search_duckduckgo(query: str, max_results: int, timeout_ms: int) -> list[dict]:
    """Search DuckDuckGo HTML-only endpoint (no JS required)."""
    browser = await _get_browser()
    context, page = await _new_stealth_page(browser)
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        await page.goto(search_url, timeout=timeout_ms, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(0.3, 0.8))

        results = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('.result');
                const out = [];
                for (const item of items) {
                    const titleEl = item.querySelector('.result__title .result__a');
                    const snippetEl = item.querySelector('.result__snippet');
                    if (titleEl) {
                        let href = titleEl.getAttribute('href') || '';
                        const m = href.match(/[?&]uddg=([^&]+)/);
                        if (m) href = decodeURIComponent(m[1]);
                        out.push({
                            title: titleEl.textContent.trim(),
                            url: href,
                            content: snippetEl ? snippetEl.textContent.trim() : '',
                        });
                    }
                }
                return out;
            }
        """)
        return [dict(r, source="duckduckgo") for r in (results or [])[:max_results]]
    finally:
        await context.close()


# ============================================================
# Engine: Google HTML
# ============================================================

async def _search_google(query: str, max_results: int, timeout_ms: int) -> list[dict]:
    """Scrape Google search results via Playwright."""
    browser = await _get_browser()
    context, page = await _new_stealth_page(browser)
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&num={max_results + 2}"
        await page.goto(search_url, timeout=timeout_ms, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(0.3, 0.8))

        results = await page.evaluate("""
            () => {
                // Google organic results live in #search or #rso
                const container = document.querySelector('#rso') || document.querySelector('#search');
                if (!container) return [];
                const out = [];
                // Each result is usually a div with an <a> and a data-header-feature or class tF2Cxc
                const links = container.querySelectorAll('a[href^="http"]');
                const seen = new Set();
                for (const a of links) {
                    const href = a.getAttribute('href');
                    if (!href || seen.has(href)) continue;
                    // Skip Google internal links
                    if (href.includes('google.com/') || href.includes('accounts.google')) continue;
                    seen.add(href);
                    // Find the nearest heading text
                    const h3 = a.querySelector('h3');
                    const title = h3 ? h3.textContent.trim() : a.textContent.trim().slice(0, 120);
                    if (!title) continue;
                    // Find snippet: next sibling with text
                    let snippet = '';
                    const parent = a.closest('[data-sokoban-container]') || a.closest('.g') || a.parentElement?.parentElement;
                    if (parent) {
                        const spans = parent.querySelectorAll('span');
                        for (const s of spans) {
                            const t = s.textContent.trim();
                            if (t.length > 40 && !t.includes(title.slice(0, 20))) {
                                snippet = t.slice(0, 300);
                                break;
                            }
                        }
                    }
                    out.push({title, url: href, content: snippet});
                }
                return out;
            }
        """)
        return [dict(r, source="google") for r in (results or [])[:max_results]]
    finally:
        await context.close()


# ============================================================
# Engine: Bing HTML
# ============================================================

async def _search_bing(query: str, max_results: int, timeout_ms: int) -> list[dict]:
    """Scrape Bing search results via Playwright."""
    browser = await _get_browser()
    context, page = await _new_stealth_page(browser)
    try:
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results + 2}"
        await page.goto(search_url, timeout=timeout_ms, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(0.3, 0.8))

        results = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('#b_results .b_algo');
                const out = [];
                for (const item of items) {
                    const a = item.querySelector('h2 a');
                    const snippet = item.querySelector('.b_caption p');
                    if (a) {
                        out.push({
                            title: a.textContent.trim(),
                            url: a.getAttribute('href') || '',
                            content: snippet ? snippet.textContent.trim() : '',
                        });
                    }
                }
                return out;
            }
        """)
        return [dict(r, source="bing") for r in (results or [])[:max_results]]
    finally:
        await context.close()


# ============================================================
# Result Merger & Deduplication
# ============================================================

def _url_fingerprint(url: str) -> str:
    """Normalize URL for dedup (strip scheme, www, trailing slash)."""
    parsed = urlparse(url)
    normalized = (parsed.netloc.removeprefix("www.") + parsed.path.rstrip("/")).lower()
    return hashlib.md5(normalized.encode()).hexdigest()


def _merge_results(all_results: list[list[dict]], max_results: int) -> list[dict]:
    """Merge results from multiple engines, preferring higher-ranked entries."""
    seen: dict[str, dict] = {}
    merged = []

    for engine_results in all_results:
        for r in engine_results:
            fp = _url_fingerprint(r.get("url", ""))
            if fp not in seen:
                seen[fp] = r
                merged.append(r)
            else:
                # If this engine has a longer snippet, use it
                existing = seen[fp]
                if len(r.get("content", "")) > len(existing.get("content", "")):
                    existing["content"] = r["content"]
                # Track that multiple engines found this (higher relevance)
                existing.setdefault("engines", 1)
                existing["engines"] = existing.get("engines", 1) + 1

    # Sort: results found by multiple engines first, then original order
    merged.sort(key=lambda r: r.get("engines", 1), reverse=True)
    return merged[:max_results]


# ============================================================
# Content Enrichment (follow links)
# ============================================================

_CONTENT_EXTRACT_JS = """
    () => {
        const remove = ['script','style','noscript','nav','footer','header',
                        '[role="complementary"]','.ads','.advertisement','.cookie-banner'];
        const clone = document.body.cloneNode(true);
        remove.forEach(s => {
            clone.querySelectorAll(s).forEach(el => el.remove());
        });
        for (const sel of ['main','article','[role="main"]','.content','#content']) {
            const el = clone.querySelector(sel);
            if (el && el.innerText.trim().length > 100) {
                return el.innerText.replace(/\\s+/g, ' ').trim().slice(0, 1200);
            }
        }
        return clone.innerText.replace(/\\s+/g, ' ').trim().slice(0, 1200);
    }
"""


async def _enrich_results(
    context, results: list[dict], timeout_ms: int,
) -> list[dict]:
    """Follow result links and append scraped text to the content."""
    enriched = []

    for r in results:
        url = r.get("url", "")
        if not url or not url.startswith("http"):
            enriched.append(r)
            continue

        try:
            page = await context.new_page()
            try:
                await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                await asyncio.sleep(0.5)
                text = await page.evaluate(_CONTENT_EXTRACT_JS)

                if text and len(text) > len(r.get("content", "")):
                    r["content"] = text[:800]
            finally:
                await page.close()
        except Exception as e:
            logger.debug(f"WebSearcher: Failed to enrich {url}: {e}")

        enriched.append(r)

    return enriched


# ============================================================
# Public API
# ============================================================

# Engine registry: name → (function, priority)
SEARCH_ENGINES = {
    "duckduckgo": (_search_duckduckgo, 1),
    "google": (_search_google, 2),
    "bing": (_search_bing, 3),
}


async def web_search(
    query: str,
    max_results: int = 5,
    follow_links: bool = False,
    timeout_ms: int = 15000,
    engines: Optional[list[str]] = None,
    parallel: bool = True,
) -> list[dict]:
    """
    Multi-engine web search with result merging.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        follow_links: If True, follow each result link and scrape content
        timeout_ms: Page load timeout in milliseconds per engine
        engines: List of engine names to use (default: all available).
                 Options: "duckduckgo", "google", "bing"
        parallel: If True, run engines in parallel; else sequential (first success).

    Returns:
        List of dicts: {title, url, content, source}
    """
    active_engines = engines or list(SEARCH_ENGINES.keys())

    if parallel:
        results = await _parallel_search(query, max_results, timeout_ms, active_engines)
    else:
        results = await _sequential_search(query, max_results, timeout_ms, active_engines)

    # Optionally enrich with full page content
    if follow_links and results:
        try:
            browser = await _get_browser()
            context, _ = await _new_stealth_page(browser)
            try:
                results = await _enrich_results(context, results, timeout_ms)
            finally:
                await context.close()
        except Exception as e:
            logger.warning(f"WebSearcher: Enrichment failed: {e}")

    logger.info(f"WebSearcher: '{query[:60]}' → {len(results)} results")
    return results


async def _parallel_search(
    query: str, max_results: int, timeout_ms: int, engines: list[str],
) -> list[dict]:
    """Run all engines in parallel, merge results."""

    async def _run_engine(name: str) -> list[dict]:
        fn, _ = SEARCH_ENGINES.get(name, (None, 99))
        if fn is None:
            return []
        try:
            return await asyncio.wait_for(
                fn(query, max_results, timeout_ms),
                timeout=timeout_ms / 1000 + 5,
            )
        except Exception as e:
            logger.debug(f"WebSearcher: {name} failed: {e}")
            return []

    all_results = await asyncio.gather(*[_run_engine(e) for e in engines])
    return _merge_results(list(all_results), max_results)


async def _sequential_search(
    query: str, max_results: int, timeout_ms: int, engines: list[str],
) -> list[dict]:
    """Try engines sequentially, stop at first success."""
    for name in engines:
        fn, _ = SEARCH_ENGINES.get(name, (None, 99))
        if fn is None:
            continue
        try:
            results = await asyncio.wait_for(
                fn(query, max_results, timeout_ms),
                timeout=timeout_ms / 1000 + 5,
            )
            if results:
                logger.info(f"WebSearcher: {name} returned {len(results)} results")
                return results
        except Exception as e:
            logger.debug(f"WebSearcher: {name} failed: {e}")
            continue
    return []


async def close_browser():
    """Shut down the shared browser instance."""
    global _browser_instance, _playwright_module

    async with _browser_lock:
        if _browser_instance:
            await _browser_instance.close()
            _browser_instance = None
        if _playwright_module:
            await _playwright_module.stop()
            _playwright_module = None
        logger.info("WebSearcher: Browser closed")
