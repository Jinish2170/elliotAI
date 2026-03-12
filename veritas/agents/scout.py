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
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from veritas.core.types import ExplorationResult, PageVisit, ScrollResult

from playwright.async_api import (Browser, BrowserContext, Page, Playwright,
                                  async_playwright)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veritas.config import settings
from veritas.config.site_types import SiteType, classify_site_type

logger = logging.getLogger("veritas.scout")

# Import IOC detector for threat intelligence
_IOC_AVAILABLE = False
try:
    # Try to import, but do it lazily to avoid circular imports
    from veritas.osint.ioc_detector import IOCDetector
    _IOC_AVAILABLE = True
except ImportError:
    logger.warning("IOCDetector not available, .onion detection disabled")
    IOCDetector = None
    _IOC_AVAILABLE = False

# Import OnionDetector and TORClient for .onion URL routing
_ONION_DETECTOR_AVAILABLE = False
try:
    from veritas.darknet.onion_detector import OnionDetector as _OnionDetector
    from veritas.darknet.tor_client import TORClient as _TORClient
    _ONION_DETECTOR_AVAILABLE = True
except ImportError:
    logger.warning("OnionDetector/TORClient not available, TOR routing disabled")
    _OnionDetector = None
    _TORClient = None


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

    # IOC (Indicators of Compromise) detection
    ioc_detected: bool = False
    ioc_indicators: list[dict] = field(default_factory=list)  # List of detected IOCs
    onion_detected: bool = False  # True if .onion addresses found
    onion_addresses: list[str] = field(default_factory=list)  # List of .onion addresses

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

    # Scroll orchestration results (from ScrollOrchestrator)
    scroll_result: Optional["ScrollResult"] = None

    # Real page data for downstream agents (Plan 13-01)
    page_content: str = ""              # Full HTML of the page (up to 500KB)
    response_headers: dict = field(default_factory=dict)  # HTTP response headers


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

    def __init__(self, evidence_dir: Optional[Path] = None, progress_emitter: Optional["ProgressEmitter"] = None, use_tor: bool = False):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._evidence_dir = evidence_dir or settings.EVIDENCE_DIR
        self._evidence_dir.mkdir(parents=True, exist_ok=True)
        self.progress_emitter = progress_emitter
        self.use_tor = use_tor
        self._ioc_detector = IOCDetector() if _IOC_AVAILABLE and IOCDetector is not None else None
        self._onion_detector = _OnionDetector() if _ONION_DETECTOR_AVAILABLE and _OnionDetector is not None else None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()

        # Build base launch args
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--window-size=1920,1080",
        ]

        # TOR SOCKS5 proxy support (for darknet_investigation tier)
        if self.use_tor:
            tor_host = getattr(settings, "TOR_SOCKS_HOST", "127.0.0.1")
            tor_port = getattr(settings, "TOR_SOCKS_PORT", 9050)
            try:
                launch_args.append(f"--proxy-server=socks5://{tor_host}:{tor_port}")
                logger.info(f"StealthScout: TOR SOCKS5 proxy enabled ({tor_host}:{tor_port})")
            except Exception as e:
                logger.warning(f"StealthScout: TOR proxy setup failed, continuing without TOR: {e}")

        self._browser = await self._playwright.chromium.launch(
            headless=settings.BROWSER_HEADLESS,
            args=launch_args,
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
        enable_scrolling: bool = True,
        progress_emitter: Optional["ProgressEmitter"] = None,
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
            9. Intelligent scrolling (optional) for lazy-loaded content

        Args:
            url: Target URL to investigate
            temporal_delay: Seconds between Screenshot_A and B (default: from settings)
            viewport: "desktop" or "mobile"
            enable_scrolling: Enable intelligent scroll orchestration (default: True)

        Returns:
            ScoutResult with all screenshots, metadata, and status
        """
        delay = temporal_delay if temporal_delay is not None else settings.TEMPORAL_DELAY
        audit_id = uuid.uuid4().hex[:8]
        user_agent = ""
        scroll_result = None
        emitter = progress_emitter or self.progress_emitter

        # Emit agent start status
        if emitter:
            await emitter.emit_agent_status("Scout", "running", f"Capturing {url}...")

        # Route .onion URLs via TOR instead of browser (Plan 12-04)
        if self._is_onion_url(url):
            logger.info(f"Detected .onion URL — routing capture via TOR: {url}")
            if emitter:
                await emitter.emit_progress("Scout", "tor_routing", 10, "Routing via TOR network...")
            tor_result = await self._capture_via_tor(url)
            if emitter:
                await emitter.emit_agent_status("Scout", "completed")
            return ScoutResult(
                url=url,
                status="SUCCESS" if tor_result.get("status") and not tor_result.get("error") else "ERROR",
                page_metadata={"tor_response": tor_result, "is_onion": True},
                onion_detected=True,
                onion_addresses=[url],
                trust_modifier=-0.3,
                trust_notes=["Target URL is a .onion hidden service — routed via TOR"],
                error_message=tor_result.get("error") or "",
            )

        context = await self._create_stealth_context(viewport)
        page = await context.new_page()

        # Capture HTTP response headers from the main navigation response (Plan 13-01)
        _captured_response_headers: dict = {}

        async def _on_response(response) -> None:
            try:
                if response.url == url or url.rstrip("/") in response.url:
                    _captured_response_headers.update(dict(response.headers))
            except Exception:
                pass

        page.on("response", _on_response)

        try:
            await self._apply_stealth(page)
            user_agent = await page.evaluate("navigator.userAgent")

            # --- Navigate ---
            start_time = time.time()
            nav_success = await self._safe_navigate(page, url)
            nav_time = (time.time() - start_time) * 1000

            if not nav_success:
                if emitter:
                    await emitter.emit_error("nav_error", "Navigation failed after all retry strategies", "Scout", recoverable=True)
                    await emitter.emit_agent_status("Scout", "failed", "Navigation failed")
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
                if emitter:
                    await emitter.emit_error("captcha_blocked", "Site blocked by CAPTCHA", "Scout", recoverable=False)
                    await emitter.emit_agent_status("Scout", "failed", "CAPTCHA blocked")
                    if ss_path:
                        # Emit CAPTCHA screenshot
                        import os
                        if os.path.exists(ss_path):
                            with open(ss_path, "rb") as f:
                                await emitter.emit_screenshot(f.read(), "captcha", "Scout")
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
            if emitter and ss_a:
                import os
                if os.path.exists(ss_a):
                    with open(ss_a, "rb") as f:
                        await emitter.emit_screenshot(f.read(), "t0", "Scout")
                        await emitter.emit_progress("Scout", "screenshot_a", 15, "Initial capture complete")

            # --- Human Simulation ---
            if emitter:
                await emitter.emit_progress("Scout", "human_sim", 20, "Simulating human behavior...")
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
            if emitter and ss_b:
                import os
                if os.path.exists(ss_b):
                    with open(ss_b, "rb") as f:
                        await emitter.emit_screenshot(f.read(), f"t{delay}", "Scout")
                        await emitter.emit_progress("Scout", "screenshot_b", 30, "Temporal capture complete")

            # --- Full-page Screenshot ---
            if emitter:
                await emitter.emit_progress("Scout", "screenshot_full", 40, "Capturing full page...")
            ss_full = await self._take_full_screenshot(page, audit_id)
            ts_full = time.time()
            if emitter and ss_full:
                import os
                if os.path.exists(ss_full):
                    with open(ss_full, "rb") as f:
                        await emitter.emit_screenshot(f.read(), "fullpage", "Scout")
                        await emitter.emit_progress("Scout", "screenshot_full_complete", 50, "Full page capture complete")

            # --- Metadata Extraction ---
            metadata = await self._extract_metadata(page)
            
            # --- IOC Initialization ---
            ioc_detected = False
            ioc_indicators = []
            onion_detected = False
            onion_addresses = []

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
                from veritas.analysis.dom_analyzer import DOMAnalyzer
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
                from veritas.analysis.form_validator import FormActionValidator
                fv = FormActionValidator()
                fv_res = await fv.validate(page, url)
                form_val_result = fv_res.to_dict()
                logger.debug(f"Form validation: {fv_res.total_forms} forms, {fv_res.critical_count} critical")
            except Exception as e:
                logger.warning(f"Form validation failed (non-critical): {e}")

            # --- IOC Detection ---
            # Also capture full page content here (reuse for security analysis, Plan 13-01)
            page_content = ""
            try:
                if self._ioc_detector:
                    ioc_content = await page.content()
                    page_content = ioc_content[:512_000]  # Truncate to 500KB
                    ioc_result = await self._ioc_detector.detect_content(
                        url=url,
                        content=ioc_content,
                        links=metadata.links_external[:50],
                    )
                    ioc_detected = ioc_result.found
                    ioc_indicators = [ind.to_dict() for ind in ioc_result.indicators[:20]]
                    onion_detected = ioc_result.onion_detected
                    onion_addresses = [
                        ind["value"]
                        for ind in ioc_indicators
                        if str(ind.get("type", "")).upper() == "ONION_ADDRESS"
                    ]
                else:
                    # Capture page_content even without IOC detector
                    raw_content = await page.content()
                    page_content = raw_content[:512_000]
            except Exception as e:
                logger.warning(f"IOC detection failed (non-critical): {e}")

            # --- Intelligent Scrolling (Optional) ---
            if enable_scrolling:
                try:
                    if emitter:
                        await emitter.emit_progress("Scout", "scrolling", 60, "Intelligent scrolling...")
                    from veritas.agents.scout_nav.scroll_orchestrator import ScrollOrchestrator
                    from veritas.agents.scout_nav.lazy_load_detector import LazyLoadDetector

                    detector = LazyLoadDetector()
                    orchestrator = ScrollOrchestrator(self._evidence_dir, detector)

                    scroll_start_time = time.time()
                    scroll_result = await orchestrator.scroll_page(page, audit_id)
                    scroll_time = (time.time() - scroll_start_time) * 1000

                    logger.info(
                        f"Scroll complete: {scroll_result.total_cycles} cycles, "
                        f"stabilized={scroll_result.stabilized}, "
                        f"lazy_load={scroll_result.lazy_load_detected}, "
                        f"screenshots={scroll_result.screenshots_captured}, "
                        f"time={scroll_time:.0f}ms"
                    )
                    if emitter and scroll_result and scroll_result.screenshots_captured > 0:
                        # Emit progress for scrolling cycles
                        await emitter.emit_progress(
                            "Scout",
                            "scroll_complete",
                            75,
                            f"Scrolled {scroll_result.total_cycles} cycles, {scroll_result.screenshots_captured} screenshots"
                        )
                except Exception as e:
                    logger.warning(f"Scroll orchestration failed (non-critical): {e}")
                    scroll_result = None

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

            # IOC trust modifiers (onion detection = high risk indicator)
            if onion_detected:
                trust_notes.append(f"Onion (.onion) addresses detected: {len(onion_addresses)} hidden services found")
                trust_mod -= 0.3  # Significant trust reduction for .onion links
                if len(onion_addresses) == 1:
                    trust_notes.append("Single .onion link detected — may indicate darknet connection")
                else:
                    trust_notes.append(f"{len(onion_addresses)} .onion links detected — strong darknet connection signals")
            if ioc_detected and not onion_detected:
                trust_notes.append(f"Security indicators detected: {len(ioc_indicators)} IOCs found")

            logger.info(
                f"Investigation complete: {url} | "
                f"screenshots={len(screenshots)} | "
                f"links_internal={len(metadata.links_internal)} | "
                f"links_external={len(metadata.links_external)} | "
                f"forms={len(metadata.forms)} | "
                f"nav_time={nav_time:.0f}ms"
                f"{' | onions=' + str(len(onion_addresses)) if onion_detected else ''}"
            )

            # Emit completion status
            if emitter:
                await emitter.emit_progress("Scout", "complete", 100, f"Investigation complete: {len(screenshots)} screenshots")
                await emitter.emit_agent_status("Scout", "completed")

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
                ioc_detected=ioc_detected,
                ioc_indicators=ioc_indicators[:20],  # Limit to prevent huge payloads
                onion_detected=onion_detected,
                onion_addresses=onion_addresses,
                navigation_time_ms=nav_time,
                viewport_used=viewport,
                user_agent_used=user_agent,
                trust_modifier=trust_mod,
                trust_notes=trust_notes,
                site_type=site_type.value,
                site_type_confidence=site_type_conf,
                dom_analysis=dom_result,
                form_validation=form_val_result,
                scroll_result=scroll_result,
                page_content=page_content,
                response_headers=_captured_response_headers,
            )

        except Exception as e:
            logger.error(f"Investigation error for {url}: {e}", exc_info=True)
            if emitter:
                await emitter.emit_error("scout_error", str(e), "Scout", recoverable=True)
                await emitter.emit_agent_status("Scout", "failed", str(e))
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
        progress_emitter: Optional["ProgressEmitter"] = None,
        enable_scrolling: bool = True,
    ) -> ScoutResult:
        """
        Enhanced navigation for sub-pages with intelligent scrolling and
        section-aware screenshots. Captures key page regions (hero, pricing,
        testimonials, forms, footer) for later analysis.

        Used when the Judge agent requests investigation of additional pages
        (e.g., /about, /contact, /terms, /cancel).
        """
        audit_id = uuid.uuid4().hex[:8]
        emitter = progress_emitter or self.progress_emitter

        # Emit agent start status
        if emitter:
            await emitter.emit_agent_status("Scout", "running", f"Capturing subpage: {url}")

        context = await self._create_stealth_context(viewport)
        page = await context.new_page()

        # Capture HTTP response headers (Plan 13-01)
        _subpage_response_headers: dict = {}

        async def _on_subpage_response(response) -> None:
            try:
                if response.url == url or url.rstrip("/") in response.url:
                    _subpage_response_headers.update(dict(response.headers))
            except Exception:
                pass

        page.on("response", _on_subpage_response)

        try:
            await self._apply_stealth(page)
            start_time = time.time()
            nav_success = await self._safe_navigate(page, url)
            nav_time = (time.time() - start_time) * 1000

            if not nav_success:
                if emitter:
                    await emitter.emit_error("nav_error", "Navigation failed", "Scout", recoverable=True)
                    await emitter.emit_agent_status("Scout", "failed", "Navigation failed")
                return ScoutResult(url=url, status="TIMEOUT", navigation_time_ms=nav_time)

            if await self._detect_captcha(page):
                if emitter:
                    await emitter.emit_error("captcha_blocked", "Site blocked by CAPTCHA", "Scout", recoverable=False)
                    await emitter.emit_agent_status("Scout", "failed", "CAPTCHA blocked")
                return ScoutResult(
                    url=url, status="CAPTCHA_BLOCKED", captcha_detected=True
                )

            ss = await self._take_screenshot(page, audit_id, "subpage")
            ss_full = await self._take_full_screenshot(page, audit_id)
            metadata = await self._extract_metadata(page)

            # --- Intelligent Scrolling for subpages ---
            scroll_result = None
            section_screenshots = []
            if enable_scrolling:
                try:
                    from veritas.agents.scout_nav.scroll_orchestrator import ScrollOrchestrator
                    from veritas.agents.scout_nav.lazy_load_detector import LazyLoadDetector

                    detector = LazyLoadDetector()
                    orchestrator = ScrollOrchestrator(self._evidence_dir, detector)
                    scroll_result = await orchestrator.scroll_page(page, audit_id)
                    logger.debug(
                        f"Subpage scroll: {scroll_result.total_cycles} cycles, "
                        f"{scroll_result.screenshots_captured} screenshots"
                    )
                except Exception as e:
                    logger.debug(f"Subpage scroll failed (non-critical): {e}")

            # --- Section-aware screenshots ---
            try:
                section_screenshots = await self._capture_section_screenshots(page, audit_id)
            except Exception as e:
                logger.debug(f"Section screenshots failed (non-critical): {e}")

            # IOC Detection for subpages + capture real page_content (Plan 13-01)
            ioc_detected = False
            ioc_indicators = []
            onion_detected = False
            onion_addresses = []
            subpage_content = ""
            try:
                if self._ioc_detector:
                    ioc_content = await page.content()
                    subpage_content = ioc_content[:512_000]
                    ioc_result = await self._ioc_detector.detect_content(
                        url=url,
                        content=ioc_content,
                        links=metadata.links_external[:50],
                    )
                    ioc_detected = ioc_result.found
                    ioc_indicators = [ind.to_dict() for ind in ioc_result.indicators[:10]]
                    onion_detected = ioc_result.onion_detected
                    onion_addresses = [
                        ind["value"]
                        for ind in ioc_indicators
                        if str(ind.get("type", "")).upper() == "ONION_ADDRESS"
                    ]
                else:
                    raw_content = await page.content()
                    subpage_content = raw_content[:512_000]
            except Exception as e:
                logger.warning(f"Subpage IOC detection failed (non-critical): {e}")

            screenshots = [p for p in [ss, ss_full] if p] + section_screenshots

            # Emit screenshots
            if emitter:
                import os
                if ss and os.path.exists(ss):
                    with open(ss, "rb") as f:
                        await emitter.emit_screenshot(f.read(), "subpage", "Scout")
                if ss_full and os.path.exists(ss_full):
                    with open(ss_full, "rb") as f2:
                        await emitter.emit_screenshot(f2.read(), "subpage_full", "Scout")
                await emitter.emit_agent_status("Scout", "completed")
                await emitter.emit_progress("Scout", "subpage_complete", 100, f"Subpage captured: {len(screenshots)} screenshots")

            # Build labels list
            screenshot_labels = ["subpage", "subpage_full"][:min(2, len([p for p in [ss, ss_full] if p]))]
            screenshot_labels += [f"section_{i}" for i in range(len(section_screenshots))]

            return ScoutResult(
                url=url,
                status="SUCCESS",
                screenshots=screenshots,
                screenshot_timestamps=[time.time()] * len(screenshots),
                screenshot_labels=screenshot_labels,
                page_title=metadata.title,
                page_metadata={
                    "forms_count": len(metadata.forms),
                    "forms": metadata.forms,
                    "has_ssl": metadata.has_ssl,
                    "internal_links_count": len(metadata.links_internal),
                    "external_links_count": len(metadata.links_external),
                },
                forms_detected=len(metadata.forms),
                ioc_detected=ioc_detected,
                ioc_indicators=ioc_indicators,
                onion_detected=onion_detected,
                onion_addresses=onion_addresses,
                trust_notes=[f"{len(onion_addresses)} .onion links detected"] if onion_detected else [],
                trust_modifier=-0.3 if onion_detected else 0.0,
                navigation_time_ms=nav_time,
                page_content=subpage_content,
                response_headers=_subpage_response_headers,
                scroll_result=scroll_result,
            )
        except Exception as e:
            if emitter:
                await emitter.emit_error("scout_error", str(e), "Scout", recoverable=True)
                await emitter.emit_agent_status("Scout", "failed", str(e))
            return ScoutResult(url=url, status="ERROR", error_message=str(e))
        finally:
            await page.close()
            await context.close()

    # ================================================================
    # Public: Multi-Page Exploration
    # ================================================================

    async def explore_multi_page(
        self,
        url: str,
        max_pages: int = 8,
        timeout_per_page_ms: int = 15000,
        enable_scrolling: bool = False,
    ) -> "ExplorationResult":
        """
        Explore multiple pages beyond the initial landing page.

        Discovers navigation links (nav, footer, content) and visits
        priority-sorted pages up to max_pages limit.

        Args:
            url: Base URL to start exploration from
            max_pages: Maximum number of additional pages to visit (default 8)
            timeout_per_page_ms: Timeout per navigation in milliseconds (default 15000)
            enable_scrolling: Whether to apply intelligent scrolling (default False)

        Returns:
            ExplorationResult with visited pages, times, and discovered links
        """
        from veritas.core.types import ExplorationResult, PageVisit
        from veritas.agents.scout_nav.link_explorer import LinkExplorer

        context = None
        page = None

        try:
            # Initialize result
            result = ExplorationResult(
                base_url=url,
                pages_visited=[],
                total_pages=0,
                total_time_ms=0,
                breadcrumbs=[],
                links_discovered=[],
            )

            # Create browser context
            context = await self._create_stealth_context(viewport="desktop")
            page = await context.new_page()
            await self._apply_stealth(page)

            # Generate audit_id for screenshot naming
            audit_id = uuid.uuid4().hex[:8]

            # Navigate to base URL first to discover links
            logger.info(f"Navigating to base URL: {url}")
            nav_success = await self._navigate_with_timeout(page, url, settings.SCREENSHOT_TIMEOUT * 1000)

            if not nav_success:
                logger.warning(f"Failed to navigate to base URL: {url}")
                return result

            # Initialize LinkExplorer and discover links
            explorer = LinkExplorer(url)
            discovered_links = await explorer.discover_links(page)

            # Store discovered links in result
            result.links_discovered = discovered_links
            logger.info(f"Discovered {len(discovered_links)} links to explore")

            # Visit up to max_pages links
            links_to_visit = discovered_links[:max_pages]

            for i, link_info in enumerate(links_to_visit):
                page_start_time = time.time()

                # Navigate to subpage
                nav_success = await self._navigate_with_timeout(page, link_info.url, timeout_per_page_ms)
                navigation_time_ms = int((time.time() - page_start_time) * 1000)

                if not nav_success:
                    # Create TIMEOUT PageVisit
                    page_visit = PageVisit(
                        url=link_info.url,
                        status="TIMEOUT",
                        navigation_time_ms=navigation_time_ms,
                    )
                    result.pages_visited.append(page_visit)
                    result.breadcrumbs.append(link_info.url)
                    logger.warning(f"Navigation timeout for: {link_info.url}")
                    continue

                # Capture screenshot
                screenshot_path = await self._take_screenshot(page, audit_id, f"page_{i}")

                # Get page title
                page_title = await self._safe_title(page)

                # Optional: Apply intelligent scrolling
                scroll_result = None
                if enable_scrolling:
                    try:
                        from veritas.agents.scout_nav.scroll_orchestrator import ScrollOrchestrator
                        from veritas.agents.scout_nav.lazy_load_detector import LazyLoadDetector

                        detector = LazyLoadDetector()
                        orchestrator = ScrollOrchestrator(self._evidence_dir, detector)
                        scroll_result = await orchestrator.scroll_page(page, audit_id)
                        logger.debug(f"Scroll results for {link_info.url}: {scroll_result.screenshots_captured} screenshots")
                    except Exception as e:
                        logger.debug(f"Scroll orchestration failed (non-critical) for {link_info.url}: {e}")
                        scroll_result = None

                # Create SUCCESS PageVisit
                page_visit = PageVisit(
                    url=link_info.url,
                    status="SUCCESS",
                    screenshot_path=screenshot_path,
                    page_title=page_title,
                    navigation_time_ms=navigation_time_ms,
                    scroll_result=scroll_result,
                )

                result.pages_visited.append(page_visit)
                result.breadcrumbs.append(link_info.url)

                logger.info(
                    f"Visited page {i + 1}/{max_pages}: {link_info.url} "
                    f"(title={page_title}, time={navigation_time_ms}ms)"
                )

            # Calculate totals
            result.total_pages = len(result.pages_visited)
            result.total_time_ms = sum(pv.navigation_time_ms for pv in result.pages_visited)

            logger.info(
                f"Multi-page exploration complete: {result.total_pages} pages visited, "
                f"{result.total_time_ms}ms total, {len(result.links_discovered)} links discovered"
            )

            return result

        except Exception as e:
            logger.error(f"Multi-page exploration error for {url}: {e}", exc_info=True)
            # Return partial result if available
            return result
        finally:
            if page:
                await page.close()
            if context:
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
        return await self._navigate_with_timeout(page, url, timeout_ms)

    async def _navigate_with_timeout(self, page: Page, url: str, timeout_ms: int) -> bool:
        """
        Navigate with fallback wait strategies using specific timeout.

        Tries strategies in order: networkidle → domcontentloaded → load → commit.
        Returns True on first successful navigation, False if all fail.

        Args:
            page: Playwright Page object
            url: URL to navigate to
            timeout_ms: Timeout in milliseconds

        Returns:
            True if navigation succeeded, False otherwise
        """
        for wait_strategy in ["networkidle", "domcontentloaded", "load", "commit"]:
            try:
                await page.goto(url, wait_until=wait_strategy, timeout=timeout_ms)
                logger.debug(f"Navigation succeeded with wait_until={wait_strategy}")
                return True
            except Exception as e:
                logger.debug(f"Navigation with {wait_strategy} failed: {e}")
                continue

        logger.warning(f"Navigation failed for all strategies: {url}")
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

    async def _capture_section_screenshots(
        self, page: Page, audit_id: str, max_sections: int = 5
    ) -> list[str]:
        """Capture screenshots of important page sections.

        Identifies key regions (pricing, testimonials, forms, trust badges,
        footer) by scanning the DOM for semantic landmarks and captures
        viewport-clipped screenshots of each.

        Args:
            page: Playwright Page object (already navigated)
            audit_id: Unique audit identifier for filenames
            max_sections: Maximum sections to capture

        Returns:
            List of screenshot file paths
        """
        section_paths: List[str] = []
        try:
            # JS to identify important section bounding boxes
            sections = await page.evaluate("""
                () => {
                    const results = [];
                    const vw = window.innerWidth;
                    const vh = window.innerHeight;

                    // Selectors for important sections, ordered by forensic priority
                    const selectors = [
                        { name: 'pricing', sel: '[class*="pricing" i], [id*="pricing" i], [data-section="pricing"]' },
                        { name: 'testimonial', sel: '[class*="testimonial" i], [class*="review" i], [id*="testimonial" i], [id*="review" i]' },
                        { name: 'form', sel: 'form:not([role="search"]), [class*="contact-form" i], [class*="signup" i]' },
                        { name: 'trust', sel: '[class*="trust" i], [class*="partner" i], [class*="client" i], [class*="badge" i]' },
                        { name: 'cta', sel: '[class*="cta" i], [class*="call-to-action" i], [class*="hero" i]' },
                        { name: 'footer', sel: 'footer, [role="contentinfo"]' },
                    ];

                    for (const { name, sel } of selectors) {
                        try {
                            const el = document.querySelector(sel);
                            if (el) {
                                const rect = el.getBoundingClientRect();
                                if (rect.height > 50 && rect.width > 100) {
                                    results.push({
                                        name: name,
                                        y: Math.max(0, rect.top + window.scrollY),
                                        height: Math.min(rect.height, vh * 2),
                                    });
                                }
                            }
                        } catch(e) {}
                    }
                    return results;
                }
            """)

            if not sections:
                return []

            # Capture up to max_sections, deduplicating overlapping regions
            captured_y = set()
            for section in sections[:max_sections]:
                y = int(section["y"])
                # Skip if too close to an already-captured region
                if any(abs(y - cy) < 200 for cy in captured_y):
                    continue
                captured_y.add(y)

                try:
                    # Scroll to section and capture viewport
                    await page.evaluate(f"window.scrollTo(0, {y})")
                    await asyncio.sleep(0.3)
                    label = f"section_{section['name']}"
                    path = await self._take_screenshot(page, audit_id, label)
                    if path:
                        section_paths.append(path)
                except Exception as e:
                    logger.debug(f"Section screenshot '{section['name']}' failed: {e}")

            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")

        except Exception as e:
            logger.debug(f"Section screenshot capture failed: {e}")

        return section_paths

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

    # ================================================================
    # Private: TOR Routing
    # ================================================================

    def _is_onion_url(self, url: str) -> bool:
        """Check if URL is a .onion hidden service using OnionDetector."""
        if self._onion_detector is None:
            return ".onion" in url.lower()
        return self._onion_detector.is_darknet_url(url)

    async def _capture_via_tor(self, url: str) -> dict:
        """Fetch .onion URL content through TOR SOCKS5h proxy."""
        if _TORClient is None:
            logger.warning(f"TORClient unavailable, cannot capture .onion URL: {url}")
            return {"status": None, "text": None, "headers": {}, "error": "TOR not available"}
        try:
            async with _TORClient() as tor:
                tor_available = await tor.check_connection()
                if not tor_available:
                    logger.warning("TOR proxy not running, skipping .onion capture")
                    return {"status": None, "text": None, "headers": {}, "error": "TOR proxy not running"}
                result = await tor.get(url)
                logger.info(f"TOR capture complete for {url}: status={result.get('status')}")
                return result
        except Exception as e:
            logger.warning(f"TOR capture failed for {url}: {e}")
            return {"status": None, "text": None, "headers": {}, "error": str(e)}
