"""
Link Explorer for Multi-Page Discovery

Discovers and prioritizes navigation links for multi-page exploration.
Categorizes links by location (nav, footer, content) and priority (1=highest).

Usage:
    from veritas.agents.scout_nav.link_explorer import LinkExplorer

    explorer = LinkExplorer("https://example.com")
    links = await explorer.discover_links(page)
    for link in links:
        print(f"{link.url} ({link.location}) - priority {link.priority}")
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from playwright.async_api import Page

from veritas.core.types import LinkInfo

logger = logging.getLogger("veritas.scout.link_explorer")


class LinkExplorer:
    """
    Discovers, filters, and prioritizes links for multi-page exploration.

    Attributes:
        base_url: The base URL for exploration
        base_domain: Domain extracted from base_url
        visited_urls: Set of URLs already visited or discovered
        RELEVANT_KEYWORDS: Keywords that indicate high-priority content links
        MAX_PAGES: Maximum number of pages to visit per exploration
    """

    RELEVANT_KEYWORDS = [
        'about', 'contact', 'privacy', 'terms', 'faq', 'team', 'learn more'
    ]
    MAX_PAGES = 8

    def __init__(self, base_url: str):
        """
        Initialize LinkExplorer with base URL.

        Args:
            base_url: The starting URL for exploration
        """
        self.base_url = base_url
        self.base_domain = self._extract_domain(base_url)
        self.visited_urls: set[str] = set()

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name (e.g., "example.com" from "https://www.example.com/path")
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or parsed.hostname or ""
        except Exception as e:
            logger.warning(f"Failed to extract domain from {url}: {e}")
            return ""

    async def discover_links(self, page: "Page") -> list[LinkInfo]:
        """
        Discover and categorize links from the current page.

        Extracts nav links (priority 1), footer links (priority 2),
        and content links matching RELEVANT_KEYWORDS (priority 3).
        Filters by domain, removes duplicates, and sorts by priority.

        Args:
            page: Playwright Page object to extract links from

        Returns:
            List of LinkInfo objects sorted by priority (lower first)
        """
        # Get links from page using JavaScript
        script = self._get_link_extraction_script()
        try:
            link_data_list = await page.evaluate(script)
        except Exception as e:
            logger.warning(f"Failed to evaluate link extraction script: {e}")
            return []

        # Filter and deduplicate links
        unique_links: dict[str, LinkInfo] = {}
        for link_data in link_data_list:
            link_info = self._filter_link(link_data)
            if link_info and link_info.url not in unique_links:
                unique_links[link_info.url] = link_info

        # Sort by priority
        sorted_links = sorted(
            unique_links.values(),
            key=lambda li: li.priority
        )

        logger.info(
            f"Discovered {len(sorted_links)} links "
            f"(nav={sum(1 for l in sorted_links if l.location == 'nav')}, "
            f"footer={sum(1 for l in sorted_links if l.location == 'footer')}, "
            f"content={sum(1 for l in sorted_links if l.location == 'content')})"
        )

        return sorted_links

    def _get_link_extraction_script(self) -> str:
        """
        Get JavaScript function for extracting and categorizing links.

        Returns:
            JavaScript string that finds nav, footer, and content links
        """
        # Convert keywords list to JS array
        keywords_js = "[" + ", ".join(f"'{kw}'" for kw in self.RELEVANT_KEYWORDS) + "]"

        return f"""
            (() => {{
                const baseDomain = window.location.hostname;
                const relevantKeywords = {keywords_js};

                // Find nav links (priority 1)
                const navLinks = [];
                const navSelectors = [
                    'nav a[href]',
                    'header a[href]',
                    '[role="navigation"] a[href]',
                    '.navigation a[href]',
                    '.navbar a[href]',
                    '.menu a[href]'
                ];

                navSelectors.forEach(selector => {{
                    document.querySelectorAll(selector).forEach(a => {{
                        try {{
                            const url = new URL(a.href);
                            if (url.protocol.startsWith('http')) {{
                                navLinks.push({{
                                    url: a.href,
                                    text: a.textContent?.trim() || '',
                                    location: 'nav',
                                    priority: 1
                                }});
                            }}
                        }} catch(e) {{}}
                    }});
                }});

                // Find footer links (priority 2)
                const footerLinks = [];
                const footerSelectors = [
                    'footer a[href]',
                    '.footer a[href]',
                    '.site-footer a[href]'
                ];

                footerSelectors.forEach(selector => {{
                    document.querySelectorAll(selector).forEach(a => {{
                        try {{
                            const url = new URL(a.href);
                            if (url.protocol.startsWith('http')) {{
                                footerLinks.push({{
                                    url: a.href,
                                    text: a.textContent?.trim() || '',
                                    location: 'footer',
                                    priority: 2
                                }});
                            }}
                        }} catch(e) {{}}
                    }});
                }});

                // Find content links matching relevant keywords (priority 3)
                const contentLinks = [];
                const contentSelectors = [
                    'main a[href]',
                    'article a[href]',
                    '.content a[href]',
                    '.post-content a[href]',
                    '.entry-content a[href]'
                ];

                contentSelectors.forEach(selector => {{
                    document.querySelectorAll(selector).forEach(a => {{
                        try {{
                            const url = new URL(a.href);
                            const text = (a.textContent?.trim() || '').toLowerCase();
                            const href = a.href.toLowerCase();

                            // Check if link matches relevant keywords
                            const matchesKeyword = relevantKeywords.some(kw =>
                                text.includes(kw) || href.includes(kw)
                            );

                            if (url.protocol.startsWith('http') && matchesKeyword) {{
                                contentLinks.push({{
                                    url: a.href,
                                    text: a.textContent?.trim() || '',
                                    location: 'content',
                                    priority: 3
                                }});
                            }}
                        }} catch(e) {{}}
                    }});
                }});

                // Combine all links
                return [...navLinks, ...footerLinks, ...contentLinks];
            }})()
        """

    def _filter_link(self, link_data: dict) -> Optional[LinkInfo]:
        """
        Filter and validate a single link.

        Args:
            link_data: Dictionary with url, text, location, priority

        Returns:
            LinkInfo object if valid, None otherwise
        """
        url = link_data.get("url", "")
        text = link_data.get("text", "")
        location = link_data.get("location", "")
        priority = link_data.get("priority", 99)

        # Validate required fields
        if not url or not location:
            return None

        # Check domain
        if not self._is_same_domain(url):
            return None

        # Skip already visited
        if url in self.visited_urls:
            return None

        # Validate HTTPS/HTTP
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.scheme.startswith(("http", "https")):
                return None
        except Exception:
            return None

        # Mark as visited
        self.visited_urls.add(url)

        return LinkInfo(
            url=url,
            text=text or "",
            location=location,
            priority=priority,
            depth=0
        )

    def _is_same_domain(self, url_str: str) -> bool:
        """
        Check if URL is from the same domain as base_url.

        Handles subdomains correctly: sub.example.com matches example.com.

        Args:
            url_str: URL to check

        Returns:
            True if same domain, False otherwise
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url_str)
            link_domain = parsed.netloc or parsed.hostname or ""

            # Direct match
            if link_domain == self.base_domain:
                return True

            # Subdomain match: sub.example.com ends with .example.com
            if link_domain.endswith(f".{self.base_domain}"):
                return True

            # Handle edge cases: www.example.com == example.com
            if link_domain == f"www.{self.base_domain}":
                return True

            if self.base_domain == f"www.{link_domain}":
                return True

            return False
        except Exception as e:
            logger.debug(f"Domain check failed for {url_str}: {e}")
            return False
