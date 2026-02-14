"""
Veritas — Custom Playwright-Based Web Search Engine

Replaces the Tavily dependency with a direct DuckDuckGo HTML scraper.
Uses Playwright stealth browser (same anti-detection as Scout) to:
    1. Submit search queries to DuckDuckGo
    2. Parse result titles, URLs, and snippets
    3. Optionally follow top results to scrape full content

Returns results in the same format as the old Tavily integration:
    [{"title": str, "url": str, "content": str}, ...]

Inspired by: Rag_v5.0.0/rag-core/ingestion/scrapers.py (DynamicWebLoader)
"""

import asyncio
import logging
import random
import re
from typing import Optional
from urllib.parse import quote_plus, urlparse

logger = logging.getLogger("veritas.web_searcher")

# Lazy browser import — only initialized when first search runs
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


async def web_search(
    query: str,
    max_results: int = 3,
    follow_links: bool = False,
    timeout_ms: int = 15000,
) -> list[dict]:
    """
    Search DuckDuckGo and return results.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        follow_links: If True, follow each result link and scrape content
        timeout_ms: Page load timeout in milliseconds

    Returns:
        List of dicts with keys: title, url, content
    """
    results = []

    try:
        browser = await _get_browser()
        context, page = await _new_stealth_page(browser)

        try:
            # Use DuckDuckGo HTML-only version (no JS required, lighter)
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            await page.goto(search_url, timeout=timeout_ms, wait_until="domcontentloaded")

            # Small random delay to be polite
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Parse DuckDuckGo HTML results
            results = await page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.result');
                    const results = [];
                    for (const item of items) {
                        const titleEl = item.querySelector('.result__title .result__a');
                        const snippetEl = item.querySelector('.result__snippet');
                        const urlEl = item.querySelector('.result__url');

                        if (titleEl) {
                            let href = titleEl.getAttribute('href') || '';
                            // DuckDuckGo wraps URLs in redirects, extract the actual URL
                            const uddgMatch = href.match(/[?&]uddg=([^&]+)/);
                            if (uddgMatch) {
                                href = decodeURIComponent(uddgMatch[1]);
                            }

                            results.push({
                                title: titleEl.textContent.trim(),
                                url: href,
                                content: snippetEl ? snippetEl.textContent.trim() : '',
                            });
                        }
                    }
                    return results;
                }
            """)

            results = results[:max_results]

            # Optionally follow links to get richer content
            if follow_links and results:
                results = await _enrich_results(context, results, timeout_ms)

        finally:
            await context.close()

    except Exception as e:
        logger.warning(f"WebSearcher: Search failed for '{query}': {e}")

    logger.info(f"WebSearcher: '{query}' → {len(results)} results")
    return results


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

                text = await page.evaluate("""
                    () => {
                        const remove = ['script','style','noscript','nav','footer','header',
                                        '[role="complementary"]','.ads','.advertisement'];
                        const clone = document.body.cloneNode(true);
                        remove.forEach(s => {
                            clone.querySelectorAll(s).forEach(el => el.remove());
                        });

                        // Try main content areas first
                        for (const sel of ['main','article','[role="main"]','.content','#content']) {
                            const el = clone.querySelector(sel);
                            if (el && el.innerText.trim().length > 100) {
                                return el.innerText.replace(/\\s+/g, ' ').trim().slice(0, 800);
                            }
                        }
                        return clone.innerText.replace(/\\s+/g, ' ').trim().slice(0, 800);
                    }
                """)

                if text and len(text) > len(r.get("content", "")):
                    r["content"] = text[:500]

            finally:
                await page.close()

        except Exception as e:
            logger.debug(f"WebSearcher: Failed to enrich {url}: {e}")

        enriched.append(r)

    return enriched


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
