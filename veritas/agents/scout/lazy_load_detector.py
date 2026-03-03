"""
LazyLoadDetector - DOM mutation tracking for lazy-load detection.

Monitors DOM changes using MutationObserver to detect lazy-loaded content
during intelligent page scrolling.
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger("veritas.agents.scout.lazy_load_detector")


MUTATION_OBSERVER_SCRIPT = """
// MutationObserver-based lazy load detector
// Tracks DOM additions between checkpoints during scrolling

(function() {
    if (window.__lazyLoadDetector) {
        return; // Already injected
    }

    window.__lazyLoadDetector = {
        mutations: [],
        lastScrollHeight: document.documentElement.scrollHeight || document.body.scrollHeight,

        bufferMutations: function(records) {
            window.__lazyLoadDetector.mutations.push(...records);
        },

        reset: function() {
            window.__lazyLoadDetector.mutations = [];
            window.__lazyLoadDetector.lastScrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
        },

        hasMutations: function() {
            return window.__lazyLoadDetector.mutations.length > 0;
        },

        getScrollHeight: function() {
            return document.documentElement.scrollHeight || document.body.scrollHeight;
        },

        scrollHeightChanged: function() {
            const currentHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
            return currentHeight !== window.__lazyLoadDetector.lastScrollHeight;
        },

        hasNewContent: function() {
            const hasMuts = window.__lazyLoadDetector.mutations.length > 0;
            const heightChanged = document.documentElement.scrollHeight !== window.__lazyLoadDetector.lastScrollHeight;
            const bothSignals = hasMuts && heightChanged;

            return {
                hasMutations: hasMuts,
                scrollHeightChanged: heightChanged,
                bothSignals: bothSignals
            };
        }
    };

    // Set up MutationObserver to track DOM changes
    const observer = new MutationObserver(window.__lazyLoadDetector.bufferMutations);
    observer.observe(document.body, {
        childList: true,    // Track added/removed child elements
        subtree: true,      // Track all descendants
        attributes: false,
        characterData: false
    });

    // Store observer reference for cleanup
    window.__lazyLoadDetector._observer = observer;
})();
"""


class LazyLoadDetector:
    """
    Tracks DOM mutations for lazy-load detection during page scrolling.

    Uses MutationObserver to detect content additions between scroll checkpoints.
    Helps distinguish static pages from lazy-loading pages for scroll termination.
    """

    def __init__(self):
        """Initialize LazyLoadDetector."""
        self._injected = False

    async def inject(self, page: Page) -> None:
        """
        Inject MutationObserver script into the page.

        Args:
            page: Playwright Page object
        """
        try:
            await page.evaluate(MUTATION_OBSERVER_SCRIPT)
            self._injected = True
            logger.debug("LazyLoadDetector MutationObserver injected")
        except Exception as e:
            logger.warning(f"Failed to inject LazyLoadDetector: {e}")
            raise

    async def has_new_content(self, page: Page) -> dict:
        """
        Check for new content since last checkpoint.

        Returns dict with three signals:
        - hasMutations: True if DOM changes detected
        - scrollHeightChanged: True if page height changed
        - bothSignals: True if BOTH mutations AND height change (strong signal)

        Args:
            page: Playwright Page object

        Returns:
            dict with keys: hasMutations, scrollHeightChanged, bothSignals
        """
        if not self._injected:
            raise RuntimeError("LazyLoadDetector not injected - call inject() first")

        try:
            result = await page.evaluate("""
                () => window.__lazyLoadDetector.hasNewContent()
            """)
            return result
        except Exception as e:
            logger.error(f"has_new_content() check failed: {e}")
            # Return safe default on error
            return {"hasMutations": False, "scrollHeightChanged": False, "bothSignals": False}

    async def reset(self, page: Page) -> None:
        """
        Reset mutation buffer and scroll height for next checkpoint.

        Args:
            page: Playwright Page object
        """
        if not self._injected:
            raise RuntimeError("LazyLoadDetector not injected - call inject() first")

        try:
            await page.evaluate("""
                () => window.__lazyLoadDetector.reset()
            """)
            logger.debug("LazyLoadDetector mutation buffer reset")
        except Exception as e:
            logger.warning(f"Failed to reset LazyLoadDetector: {e}")

    async def disconnect(self, page: Page) -> None:
        """
        Disconnect MutationObserver to prevent memory leaks.

        Args:
            page: Playwright Page object
        """
        if not self._injected:
            return

        try:
            await page.evaluate("""
                () => {
                    if (window.__lazyLoadDetector && window.__lazyLoadDetector._observer) {
                        window.__lazyLoadDetector._observer.disconnect();
                    }
                }
            """)
            logger.debug("LazyLoadDetector disconnected")
        except Exception as e:
            logger.warning(f"Failed to disconnect LazyLoadDetector: {e}")
        finally:
            self._injected = False
