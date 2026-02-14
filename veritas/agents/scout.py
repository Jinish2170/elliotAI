"""
Veritas Agent 1 — The Stealth Scout (Browser Automation)

The "Hands & Legs" of Veritas. Navigates target URLs, captures evidence.

Capabilities:
    - Stealth Playwright browser with anti-detection
    - Temporal screenshot capture (Screenshot_A at t0, Screenshot_B at t+delay)
    - CAPTCHA detection (content scan + iframe URL scan)
    - Comprehensive page metadata extraction (DOM analysis)
    - Mobile + Desktop viewport support
    - Human behavior simulation (scroll, mouse jitter)
    - Async context manager for proper resource cleanup

Patterns merged from:
    - glass-box-portal/backend/main.py → capture_mobile_screenshot()
      (mobile viewport, navigator.webdriver=undefined, networkidle wait)
    - Rag_v5.0.0/rag-core/ingestion/scrapers.py → StealthScraper
      (enhanced stealth JS, user-agent rotation, retry, content extraction)
"""

import asyncio
import logging
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from playwright.async_api import (Browser, BrowserContext, Page, Playwright,
                                  async_playwright)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import settings
from config.site_types import SiteType, classify_site_type

logger = logging.getLogger("veritas.scout")


# ============================================================
# User Agent Pool
# (From RAGv5 scrapers.py pattern — rotated per-context)
# ============================================================

_DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

_MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.62 Mobile/15E148 Safari/604.1",
]


# ============================================================
# CAPTCHA Indicators
# ============================================================

_CAPTCHA_CONTENT_INDICATORS = [
    "captcha", "recaptcha", "hcaptcha", "challenge-platform",
    "cf-turnstile", "arkose", "funcaptcha", "geetest",
    "challenge-form", "captcha-container", "captcha-box",
    "please verify you are a human", "verify you are not a robot",
    "complete the security check",
]

_CAPTCHA_IFRAME_INDICATORS = [
    "recaptcha", "hcaptcha", "captcha", "turnstile",
    "arkoselabs", "funcaptcha", "geetest",
]


# ============================================================
# Stealth JavaScript
# (Merged from glass-box main.py + RAGv5 scrapers.py)
# ============================================================

_STEALTH_SCRIPT = """
// === Navigator overrides ===
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// === Chrome object (makes headless look like real Chrome) ===
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {isInstalled: false, InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'}, RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'}}
};

// === Permissions API override ===
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// === WebGL vendor spoofing ===
const getParameterProxyHandler = {
    apply: function(target, ctx, args) {
        if (args[0] === 37445) return 'Intel Inc.';
        if (args[0] === 37446) return 'Intel Iris OpenGL Engine';
        return Reflect.apply(target, ctx, args);
    }
};
try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            WebGLRenderingContext.prototype.getParameter = new Proxy(
                WebGLRenderingContext.prototype.getParameter,
                getParameterProxyHandler
            );
        }
    }
} catch(e) {}

// === Iframe contentWindow override ===
Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    get: function() { return window; }
});

// === Connection rtt override (headless defaults to 0) ===
if (navigator.connection) {
    Object.defineProperty(navigator.connection, 'rtt', {get: () => 50});
}

// === Screen dimensions (match viewport) ===
Object.defineProperty(screen, 'colorDepth', {get: () => 24});
"""


# ============================================================
# Data Classes
# ============================================================

@dataclass
class PageMetadata:
    """Structured metadata extracted from a web page via JS execution."""
    title: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    og_tags: dict = field(default_factory=dict)
    canonical_url: str = ""
    language: str = ""
    scripts_count: int = 0
    external_scripts: list[str] = field(default_factory=list)
    forms: list[dict] = field(default_factory=list)
    links_internal: list[str] = field(default_factory=list)
    links_external: list[str] = field(default_factory=list)
    images_count: int = 0
    has_ssl: bool = False
    cookies_count: int = 0


@dataclass
class ScoutResult:
    """
    Complete result from a Scout investigation.
    Contains all evidence gathered from a single URL visit.
    """
    url: str
    status: str  # SUCCESS | CAPTCHA_BLOCKED | TIMEOUT | ERROR

    # Evidence
    screenshots: list[str] = field(default_factory=list)
    screenshot_timestamps: list[float] = field(default_factory=list)
    screenshot_labels: list[str] = field(default_factory=list)

    # Page info
    page_title: str = ""
    page_metadata: dict = field(default_factory=dict)
    links: list[str] = field(default_factory=list)
    forms_detected: int = 0

    # Detection flags
    captcha_detected: bool = False

    # Diagnostics
    error_message: str = ""
    navigation_time_ms: float = 0
    viewport_used: str = "desktop"
    user_agent_used: str = ""

    # Trust modifiers from scout-level findings
    trust_modifier: float = 0.0
    trust_notes: list[str] = field(default_factory=list)

    # Site type classification
    site_type: str = "company_portfolio"
    site_type_confidence: float = 0.3

    # DOM analysis results (from DOMAnalyzer)
    dom_analysis: dict = field(default_factory=dict)

    # Form validation results (from FormActionValidator)
    form_validation: dict = field(default_factory=dict)


# ============================================================
# The Stealth Scout Agent
# ============================================================

class StealthScout:
    """
    Agent 1: Stealth web browser for forensic screenshot capture.

    Usage:
        async with StealthScout() as scout:
            result = await scout.investigate("https://example.com")
            print(result.status, result.screenshots)
    """

    def __init__(self, evidence_dir: Optional[Path] = None):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._evidence_dir = evidence_dir or settings.EVIDENCE_DIR
        self._evidence_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.BROWSER_HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )
        logger.info("StealthScout browser launched")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("StealthScout browser closed")

    # ================================================================
    # Public: Full Investigation
    # ================================================================

    async def investigate(
        self,
        url: str,
        temporal_delay: Optional[int] = None,
        viewport: str = "desktop",
    ) -> ScoutResult:
        """
        Full forensic investigation of a URL:
            1. Navigate with stealth browser
            2. Check for CAPTCHA
            3. Take Screenshot_A (t0) — viewport shot
            4. Simulate human behavior (scroll, mouse jitter)
            5. Wait temporal_delay seconds
            6. Take Screenshot_B (t+delay) — viewport shot (for timer comparison)
            7. Take full-page screenshot
            8. Extract comprehensive page metadata

        Args:
            url: Target URL to investigate
            temporal_delay: Seconds between Screenshot_A and B (default: from settings)
            viewport: "desktop" or "mobile"

        Returns:
            ScoutResult with all screenshots, metadata, and status
        """
        delay = temporal_delay if temporal_delay is not None else settings.TEMPORAL_DELAY
        audit_id = uuid.uuid4().hex[:8]
        user_agent = ""

        context = await self._create_stealth_context(viewport)
        page = await context.new_page()

        try:
            await self._apply_stealth(page)
            user_agent = await page.evaluate("navigator.userAgent")

            # --- Navigate ---
            start_time = time.time()
            nav_success = await self._safe_navigate(page, url)
            nav_time = (time.time() - start_time) * 1000

            if not nav_success:
                return ScoutResult(
                    url=url,
                    status="TIMEOUT",
                    error_message="Navigation failed after all retry strategies",
                    navigation_time_ms=nav_time,
                    viewport_used=viewport,
                    user_agent_used=user_agent,
                )

            # --- CAPTCHA Check ---
            if await self._detect_captcha(page):
                ss_path = await self._take_screenshot(page, audit_id, "captcha")
                title = await self._safe_title(page)
                logger.info(f"CAPTCHA detected on {url}")
                return ScoutResult(
                    url=url,
                    status="CAPTCHA_BLOCKED",
                    screenshots=[ss_path] if ss_path else [],
                    screenshot_timestamps=[time.time()] if ss_path else [],
                    screenshot_labels=["captcha"] if ss_path else [],
                    captcha_detected=True,
                    page_title=title,
                    navigation_time_ms=nav_time,
                    viewport_used=viewport,
                    user_agent_used=user_agent,
                    trust_modifier=0.0,
                    trust_notes=["CAPTCHA present — this is a neutral/positive security indicator"],
                )

            # --- Screenshot A (t0) ---
            ss_a = await self._take_screenshot(page, audit_id, "t0")
            ts_a = time.time()
            logger.debug(f"Screenshot A captured for {url}")

            # --- Human Simulation ---
            await self._simulate_human(page)

            # --- Temporal Wait ---
            logger.debug(f"Temporal wait: {delay}s for timer detection")
            await asyncio.sleep(delay)

            # --- Screenshot B (t + delay) ---
            # Scroll back to top first to get the same viewport region
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)
            ss_b = await self._take_screenshot(page, audit_id, f"t{delay}")
            ts_b = time.time()
            logger.debug(f"Screenshot B captured for {url}")

            # --- Full-page Screenshot ---
            ss_full = await self._take_full_screenshot(page, audit_id)
            ts_full = time.time()

            # --- Metadata Extraction ---
            metadata = await self._extract_metadata(page)

            # --- Site Type Classification ---
            has_price = any(
                kw in (metadata.description + " " + " ".join(metadata.keywords)).lower()
                for kw in ["price", "buy", "cart", "shop", "checkout", "$", "€", "£"]
            )
            has_pw = any(f.get("hasPassword") for f in metadata.forms)
            has_cc = any(f.get("hasCreditCard") for f in metadata.forms)
            site_type, site_type_conf = classify_site_type(
                url=url,
                title=metadata.title,
                description=metadata.description,
                keywords=" ".join(metadata.keywords) if metadata.keywords else "",
                has_ssl=metadata.has_ssl,
                has_password_form=has_pw,
                has_cc_form=has_cc,
                has_price_elements=has_price,
                scripts_count=metadata.scripts_count,
                external_links_count=len(metadata.links_external),
                forms_count=len(metadata.forms),
                cookies_count=metadata.cookies_count,
            )
            logger.info(f"Site type classified: {site_type.value} (conf={site_type_conf:.0%})")

            # --- DOM Analysis (zero-AI structural checks) ---
            dom_result = {}
            try:
                from analysis.dom_analyzer import DOMAnalyzer
                dom_analyzer = DOMAnalyzer()
                dom_result = await dom_analyzer.analyze(page)
                if not isinstance(dom_result, dict):
                    dom_result = dom_result.__dict__ if hasattr(dom_result, '__dict__') else {}
                logger.debug(f"DOM analysis complete: {len(dom_result.get('findings', []))} findings")
            except Exception as e:
                logger.warning(f"DOM analysis failed (non-critical): {e}")

            # --- Form Validation ---
            form_val_result = {}
            try:
                from analysis.form_validator import FormActionValidator
                fv = FormActionValidator()
                fv_res = await fv.validate(page, url)
                form_val_result = fv_res.to_dict()
                logger.debug(f"Form validation: {fv_res.total_forms} forms, {fv_res.critical_count} critical")
            except Exception as e:
                logger.warning(f"Form validation failed (non-critical): {e}")

            # --- Assemble Result ---
            screenshots = [p for p in [ss_a, ss_b, ss_full] if p]
            timestamps = []
            labels = []
            if ss_a:
                timestamps.append(ts_a)
                labels.append("t0")
            if ss_b:
                timestamps.append(ts_b)
                labels.append(f"t{delay}")
            if ss_full:
                timestamps.append(ts_full)
                labels.append("fullpage")

            # Scout-level trust signals
            trust_notes = []
            trust_mod = 0.0
            if not metadata.has_ssl:
                trust_notes.append("No SSL/HTTPS detected")
                trust_mod -= 0.1
            if len(metadata.forms) > 0:
                password_forms = [f for f in metadata.forms if f.get("hasPassword")]
                if password_forms and not metadata.has_ssl:
                    trust_notes.append("Password form detected WITHOUT SSL — critical risk")
                    trust_mod -= 0.2

            logger.info(
                f"Investigation complete: {url} | "
                f"screenshots={len(screenshots)} | "
                f"links_internal={len(metadata.links_internal)} | "
                f"links_external={len(metadata.links_external)} | "
                f"forms={len(metadata.forms)} | "
                f"nav_time={nav_time:.0f}ms"
            )

            return ScoutResult(
                url=url,
                status="SUCCESS",
                screenshots=screenshots,
                screenshot_timestamps=timestamps,
                screenshot_labels=labels,
                page_title=metadata.title,
                page_metadata={
                    "description": metadata.description,
                    "keywords": metadata.keywords,
                    "og_tags": metadata.og_tags,
                    "canonical_url": metadata.canonical_url,
                    "language": metadata.language,
                    "scripts_count": metadata.scripts_count,
                    "external_scripts": metadata.external_scripts[:20],
                    "forms": metadata.forms,
                    "forms_count": len(metadata.forms),
                    "internal_links_count": len(metadata.links_internal),
                    "external_links_count": len(metadata.links_external),
                    "images_count": metadata.images_count,
                    "has_ssl": metadata.has_ssl,
                    "cookies_count": metadata.cookies_count,
                },
                links=metadata.links_external[:50],
                forms_detected=len(metadata.forms),
                captcha_detected=False,
                navigation_time_ms=nav_time,
                viewport_used=viewport,
                user_agent_used=user_agent,
                trust_modifier=trust_mod,
                trust_notes=trust_notes,
                site_type=site_type.value,
                site_type_confidence=site_type_conf,
                dom_analysis=dom_result,
                form_validation=form_val_result,
            )

        except Exception as e:
            logger.error(f"Investigation error for {url}: {e}", exc_info=True)
            return ScoutResult(
                url=url,
                status="ERROR",
                error_message=str(e),
                viewport_used=viewport,
                user_agent_used=user_agent,
            )
        finally:
            await page.close()
            await context.close()

    # ================================================================
    # Public: Lightweight Sub-page Navigation
    # ================================================================

    async def navigate_subpage(
        self,
        url: str,
        viewport: str = "desktop",
    ) -> ScoutResult:
        """
        Lightweight navigation for sub-pages (no temporal screenshots).
        Used when the Judge agent requests investigation of additional pages
        (e.g., /about, /contact, /terms, /cancel).
        """
        audit_id = uuid.uuid4().hex[:8]
        context = await self._create_stealth_context(viewport)
        page = await context.new_page()

        try:
            await self._apply_stealth(page)
            start_time = time.time()
            nav_success = await self._safe_navigate(page, url)
            nav_time = (time.time() - start_time) * 1000

            if not nav_success:
                return ScoutResult(url=url, status="TIMEOUT", navigation_time_ms=nav_time)

            if await self._detect_captcha(page):
                return ScoutResult(
                    url=url, status="CAPTCHA_BLOCKED", captcha_detected=True
                )

            ss = await self._take_screenshot(page, audit_id, "subpage")
            ss_full = await self._take_full_screenshot(page, audit_id)
            metadata = await self._extract_metadata(page)

            screenshots = [p for p in [ss, ss_full] if p]

            return ScoutResult(
                url=url,
                status="SUCCESS",
                screenshots=screenshots,
                screenshot_timestamps=[time.time()] * len(screenshots),
                screenshot_labels=["subpage", "subpage_full"][:len(screenshots)],
                page_title=metadata.title,
                page_metadata={
                    "forms_count": len(metadata.forms),
                    "forms": metadata.forms,
                    "has_ssl": metadata.has_ssl,
                    "internal_links_count": len(metadata.links_internal),
                    "external_links_count": len(metadata.links_external),
                },
                forms_detected=len(metadata.forms),
                navigation_time_ms=nav_time,
            )
        except Exception as e:
            return ScoutResult(url=url, status="ERROR", error_message=str(e))
        finally:
            await page.close()
            await context.close()

    # ================================================================
    # Private: Browser Context Setup
    # ================================================================

    async def _create_stealth_context(self, viewport: str = "desktop") -> BrowserContext:
        """Create a browser context with randomized stealth settings."""
        if viewport == "mobile":
            ua = random.choice(_MOBILE_USER_AGENTS)
            vp = {
                "width": settings.MOBILE_VIEWPORT_WIDTH,
                "height": settings.MOBILE_VIEWPORT_HEIGHT,
            }
        else:
            ua = random.choice(_DESKTOP_USER_AGENTS)
            # Slight randomization to avoid viewport fingerprinting
            vp = {
                "width": settings.BROWSER_VIEWPORT_WIDTH + random.randint(-20, 20),
                "height": settings.BROWSER_VIEWPORT_HEIGHT + random.randint(-20, 20),
            }

        context = await self._browser.new_context(
            viewport=vp,
            user_agent=ua,
            locale="en-US",
            timezone_id="America/New_York",
            has_touch=viewport == "mobile",
            is_mobile=viewport == "mobile",
            java_script_enabled=True,
            ignore_https_errors=True,
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            },
        )
        return context

    async def _apply_stealth(self, page: Page):
        """Inject stealth JavaScript patches into the page."""
        await page.add_init_script(_STEALTH_SCRIPT)

    # ================================================================
    # Private: Navigation
    # ================================================================

    async def _safe_navigate(self, page: Page, url: str) -> bool:
        """
        Navigate with fallback wait strategies.
        Tries: networkidle → domcontentloaded → load → commit
        """
        timeout_ms = settings.SCREENSHOT_TIMEOUT * 1000

        for wait_strategy in ["networkidle", "domcontentloaded", "load", "commit"]:
            try:
                await page.goto(url, wait_until=wait_strategy, timeout=timeout_ms)
                logger.debug(f"Navigation succeeded with wait_until={wait_strategy}")
                return True
            except Exception as e:
                logger.debug(f"Navigation with {wait_strategy} failed: {e}")
                continue

        return False

    async def _safe_title(self, page: Page) -> str:
        """Safely get page title."""
        try:
            return await page.title()
        except Exception:
            return ""

    # ================================================================
    # Private: Screenshot Capture
    # ================================================================

    async def _take_screenshot(
        self, page: Page, audit_id: str, label: str
    ) -> Optional[str]:
        """Capture a viewport-sized screenshot."""
        try:
            filename = f"{audit_id}_{label}.jpg"
            filepath = self._evidence_dir / filename
            await page.screenshot(
                path=str(filepath),
                type="jpeg",
                quality=85,
                full_page=False,
            )
            return str(filepath)
        except Exception as e:
            logger.warning(f"Screenshot failed ({label}): {e}")
            return None

    async def _take_full_screenshot(
        self, page: Page, audit_id: str
    ) -> Optional[str]:
        """Capture a full-page (scrolled) screenshot."""
        try:
            filename = f"{audit_id}_fullpage.jpg"
            filepath = self._evidence_dir / filename
            await page.screenshot(
                path=str(filepath),
                type="jpeg",
                quality=80,
                full_page=True,
            )
            return str(filepath)
        except Exception as e:
            logger.warning(f"Full-page screenshot failed: {e}")
            return None

    # ================================================================
    # Private: CAPTCHA Detection
    # ================================================================

    async def _detect_captcha(self, page: Page) -> bool:
        """
        Detect if the page has a CAPTCHA challenge.
        Two-phase check: page content scan + iframe URL scan.
        """
        try:
            # Phase 1: Content scan
            content = (await page.content()).lower()
            for indicator in _CAPTCHA_CONTENT_INDICATORS:
                if indicator in content:
                    return True

            # Phase 2: Iframe URL scan
            for frame in page.frames:
                frame_url = frame.url.lower()
                for indicator in _CAPTCHA_IFRAME_INDICATORS:
                    if indicator in frame_url:
                        return True

            return False
        except Exception:
            return False

    # ================================================================
    # Private: Metadata Extraction
    # (Pattern from RAGv5 scrapers.py → _extract_with_js)
    # ================================================================

    async def _extract_metadata(self, page: Page) -> PageMetadata:
        """Extract comprehensive page metadata via JavaScript execution."""
        try:
            meta = await page.evaluate("""
                () => {
                    const getMeta = (name) => {
                        const el = document.querySelector(
                            `meta[name="${name}"], meta[property="${name}"]`
                        );
                        return el ? el.getAttribute('content') : '';
                    };

                    // OG tags
                    const ogTags = {};
                    document.querySelectorAll('meta[property^="og:"]').forEach(el => {
                        ogTags[el.getAttribute('property')] = el.getAttribute('content');
                    });

                    // Links — split internal vs external
                    const hostname = window.location.hostname;
                    const internalLinks = new Set();
                    const externalLinks = new Set();
                    document.querySelectorAll('a[href]').forEach(a => {
                        try {
                            const url = new URL(a.href);
                            if (url.protocol.startsWith('http')) {
                                if (url.hostname === hostname || url.hostname.endsWith('.' + hostname)) {
                                    internalLinks.add(url.href);
                                } else {
                                    externalLinks.add(url.href);
                                }
                            }
                        } catch(e) {}
                    });

                    // Forms — detect password fields, email fields, action URLs
                    const forms = [];
                    document.querySelectorAll('form').forEach(f => {
                        const inputs = f.querySelectorAll('input, select, textarea');
                        const inputTypes = Array.from(inputs).map(i => i.type || 'text');
                        forms.push({
                            action: f.action || '',
                            method: (f.method || 'GET').toUpperCase(),
                            inputCount: inputs.length,
                            inputTypes: inputTypes,
                            hasPassword: inputTypes.includes('password'),
                            hasEmail: inputTypes.includes('email'),
                            hasCreditCard: Array.from(inputs).some(i =>
                                (i.name + i.id + i.placeholder).toLowerCase().match(
                                    /card|credit|ccnum|cvc|cvv|expir/
                                )
                            ),
                        });
                    });

                    // External scripts
                    const scripts = [];
                    document.querySelectorAll('script[src]').forEach(s => {
                        scripts.push(s.src);
                    });

                    return {
                        title: document.title || '',
                        description: getMeta('description'),
                        keywords: (getMeta('keywords') || '').split(',').map(k => k.trim()).filter(Boolean),
                        ogTags,
                        canonicalUrl: (document.querySelector('link[rel="canonical"]') || {}).href || '',
                        language: document.documentElement.lang || '',
                        scriptsCount: document.querySelectorAll('script').length,
                        externalScripts: scripts,
                        forms,
                        internalLinks: [...internalLinks],
                        externalLinks: [...externalLinks],
                        imagesCount: document.querySelectorAll('img').length,
                        hasSSL: window.location.protocol === 'https:',
                    };
                }
            """)

            # Get cookies
            cookies = await page.context.cookies()

            return PageMetadata(
                title=meta.get("title", ""),
                description=meta.get("description", ""),
                keywords=meta.get("keywords", []),
                og_tags=meta.get("ogTags", {}),
                canonical_url=meta.get("canonicalUrl", ""),
                language=meta.get("language", ""),
                scripts_count=meta.get("scriptsCount", 0),
                external_scripts=meta.get("externalScripts", []),
                forms=meta.get("forms", []),
                links_internal=meta.get("internalLinks", []),
                links_external=meta.get("externalLinks", []),
                images_count=meta.get("imagesCount", 0),
                has_ssl=meta.get("hasSSL", False),
                cookies_count=len(cookies),
            )
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
            return PageMetadata()

    # ================================================================
    # Private: Human Simulation
    # ================================================================

    async def _simulate_human(self, page: Page):
        """
        Simulate realistic human behavior to defeat behavioral analysis:
        - Random scroll patterns
        - Mouse movement with natural jitter
        - Random pauses between actions
        """
        try:
            viewport = page.viewport_size

            # Phase 1: Gradual scroll down
            scroll_steps = random.randint(2, 4)
            for i in range(scroll_steps):
                scroll_amount = random.randint(150, 500)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await asyncio.sleep(random.uniform(0.3, 1.2))

            # Phase 2: Mouse movement with natural curves
            if viewport:
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, max(200, viewport["width"] - 100))
                    y = random.randint(100, max(200, viewport["height"] - 100))
                    steps = random.randint(5, 20)
                    await page.mouse.move(x, y, steps=steps)
                    await asyncio.sleep(random.uniform(0.05, 0.4))

            # Phase 3: Brief pause (reading simulation)
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Phase 4: Scroll back to top for Screenshot_B
            await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            await asyncio.sleep(0.5)

        except Exception as e:
            # Non-critical — continue even if simulation fails
            logger.debug(f"Human simulation error (non-critical): {e}")
