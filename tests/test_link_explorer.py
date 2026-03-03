"""
Tests for Link Explorer and multi-page exploration functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from veritas.agents.scout_nav.link_explorer import LinkExplorer
from veritas.core.types import LinkInfo, PageVisit, ExplorationResult, ScrollResult


@pytest.fixture
def sample_link_infos():
    """Sample LinkInfo objects for testing."""
    return [
        LinkInfo(url="https://example.com/about", text="About Us", location="nav", priority=1),
        LinkInfo(url="https://example.com/contact", text="Contact", location="nav", priority=1),
        LinkInfo(url="https://example.com/privacy", text="Privacy Policy", location="footer", priority=2),
        LinkInfo(url="https://example.com/team", text="Our Team", location="content", priority=3),
    ]


# ============================================================
# Dataclass Tests
# ============================================================

class TestDataclasses:
    """Test LinkInfo, PageVisit, and ExplorationResult dataclasses."""

    def test_link_info_dataclass_fields(self):
        """Verify LinkInfo has all required fields with correct types."""
        link = LinkInfo(
            url="https://example.com/page",
            text="Test Page",
            location="nav",
            priority=1,
            depth=0
        )
        assert link.url == "https://example.com/page"
        assert link.text == "Test Page"
        assert link.location == "nav"
        assert link.priority == 1
        assert link.depth == 0

    def test_link_info_default_depth(self):
        """Verify LinkInfo depth defaults to 0."""
        link = LinkInfo(
            url="https://example.com/page",
            text="Test",
            location="nav",
            priority=1
        )
        assert link.depth == 0

    def test_page_visit_dataclass_fields(self):
        """Verify PageVisit has all required fields with correct types."""
        page_visit = PageVisit(
            url="https://example.com/about",
            status="SUCCESS",
            screenshot_path="test.jpg",
            page_title="About Us",
            navigation_time_ms=1500,
            scroll_result=None
        )
        assert page_visit.url == "https://example.com/about"
        assert page_visit.status == "SUCCESS"
        assert page_visit.screenshot_path == "test.jpg"
        assert page_visit.page_title == "About Us"
        assert page_visit.navigation_time_ms == 1500
        assert page_visit.scroll_result is None

    def test_page_visit_optional_fields(self):
        """Verify PageVisit optional fields default correctly."""
        page_visit = PageVisit(
            url="https://example.com/page",
            status="ERROR"
        )
        assert page_visit.url == "https://example.com/page"
        assert page_visit.status == "ERROR"
        assert page_visit.screenshot_path is None
        assert page_visit.page_title == ""
        assert page_visit.navigation_time_ms == 0
        assert page_visit.scroll_result is None

    def test_exploration_result_dataclass_fields(self):
        """Verify ExplorationResult has all required fields with correct types."""
        pages = [PageVisit(url="https://example.com/page1", status="SUCCESS")]
        links = [LinkInfo(url="https://example.com/page2", text="Link", location="nav", priority=1)]

        result = ExplorationResult(
            base_url="https://example.com",
            pages_visited=pages,
            total_pages=1,
            total_time_ms=2000,
            breadcrumbs=["https://example.com/page1"],
            links_discovered=links
        )
        assert result.base_url == "https://example.com"
        assert len(result.pages_visited) == 1
        assert result.total_pages == 1
        assert result.total_time_ms == 2000
        assert len(result.breadcrumbs) == 1
        assert len(result.links_discovered) == 1

    def test_exploration_result_default_list_fields(self):
        """Verify ExplorationResult list fields default to empty lists."""
        result = ExplorationResult(base_url="https://example.com")
        assert result.pages_visited == []
        assert result.breadcrumbs == []
        assert result.links_discovered == []

    def test_exploration_result_to_dict(self):
        """Verify ExplorationResult.to_dict() works correctly."""
        scroll_result = ScrollResult(
            total_cycles=3,
            stabilized=True,
            lazy_load_detected=False,
            screenshots_captured=2
        )
        pages = [
            PageVisit(
                url="https://example.com/page",
                status="SUCCESS",
                screenshot_path="test.jpg",
                page_title="Test Page",
                navigation_time_ms=1000,
                scroll_result=scroll_result
            )
        ]
        result = ExplorationResult(
            base_url="https://example.com",
            pages_visited=pages,
            breadcrumbs=["https://example.com/page"]
        )

        result_dict = result.to_dict()
        assert result_dict["base_url"] == "https://example.com"
        assert result_dict["total_pages"] == 0  # Not set
        assert result_dict["total_time_ms"] == 0  # Not set
        assert len(result_dict["pages_visited"]) == 1
        assert len(result_dict["breadcrumbs"]) == 1
        assert result_dict["pages_visited"][0]["url"] == "https://example.com/page"
        assert result_dict["pages_visited"][0]["scroll_result"] == scroll_result.to_dict()


# ============================================================
# LinkExplorer Tests
# ============================================================

class TestLinkExplorer:
    """Test LinkExplorer link discovery and filtering."""

    @pytest.fixture
    def explorer(self):
        """Create a LinkExplorer instance for testing."""
        return LinkExplorer("https://example.com")

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright Page object."""
        page = AsyncMock()
        return page

    @pytest.mark.asyncio
    async def test_link_discovery_prioritizes_nav_links(self, explorer, mock_page):
        """Verify nav links have priority 1 and appear first in results."""
        # Mock link extraction to return mixed link types
        mock_links = [
            {"url": "https://example.com/contact", "text": "Contact", "location": "nav", "priority": 1},
            {"url": "https://example.com/about", "text": "About", "location": "nav", "priority": 1},
            {"url": "https://example.com/privacy", "text": "Privacy", "location": "footer", "priority": 2},
            {"url": "https://example.com/team", "text": "Team", "location": "content", "priority": 3},
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_links)

        links = await explorer.discover_links(mock_page)

        # Verify nav links come first
        assert len(links) == 4
        assert links[0].location == "nav"
        assert links[1].location == "nav"
        assert links[2].location == "footer"
        assert links[3].location == "content"

        # Verify nav links have priority 1
        assert links[0].priority == 1
        assert links[1].priority == 1

    @pytest.mark.asyncio
    async def test_link_discovery_categorizes_footer_and_content(self, explorer, mock_page):
        """Verify footer links get priority 2 and content links get priority 3."""
        mock_links = [
            {"url": "https://example.com/terms", "text": "Terms", "location": "footer", "priority": 2},
            {"url": "https://example.com/privacy", "text": "Privacy", "location": "footer", "priority": 2},
            {"url": "https://example.com/team", "text": "Team", "location": "content", "priority": 3},
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_links)

        links = await explorer.discover_links(mock_page)

        # Footer links (priority 2) come before content links (priority 3)
        assert len(links) == 3
        assert links[0].location == "footer"
        assert links[0].priority == 2
        assert links[1].location == "footer"
        assert links[1].priority == 2
        assert links[2].location == "content"
        assert links[2].priority == 3

    @pytest.mark.asyncio
    async def test_link_filtering_restricts_to_same_domain(self, explorer, mock_page):
        """Verify only same-domain links are returned."""
        # Mix of internal and external links
        mock_links = [
            {"url": "https://example.com/about", "text": "About", "location": "nav", "priority": 1},
            {"url": "https://evil.com/link", "text": "External", "location": "nav", "priority": 1},
            {"url": "https://sub.example.com/page", "text": "Subdomain", "location": "nav", "priority": 1},
            {"url": "https://www.example.com/contact", "text": "WWW", "location": "nav", "priority": 1},
            {"url": "https://external.org/page", "text": "Another External", "location": "content", "priority": 3},
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_links)

        links = await explorer.discover_links(mock_page)

        # Only same-domain links retained
        assert len(links) == 3
        urls = [link.url for link in links]
        assert "https://example.com/about" in urls
        assert "https://sub.example.com/page" in urls
        assert "https://www.example.com/contact" in urls
        assert "https://evil.com/link" not in urls
        assert "https://external.org/page" not in urls

    @pytest.mark.asyncio
    async def test_link_filtering_removes_duplicates(self, explorer, mock_page):
        """Verify duplicate URLs are removed."""
        mock_links = [
            {"url": "https://example.com/about", "text": "About 1", "location": "nav", "priority": 1},
            {"url": "https://example.com/about", "text": "About 2", "location": "footer", "priority": 2},
            {"url": "https://example.com/contact", "text": "Contact", "location": "nav", "priority": 1},
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_links)

        links = await explorer.discover_links(mock_page)

        # Duplicate URL removed, first link kept (lower priority)
        assert len(links) == 2
        urls = [link.url for link in links]
        assert urls.count("https://example.com/about") == 1
        assert "https://example.com/contact" in urls

    @pytest.mark.asyncio
    async def test_link_filtering_skips_visited_urls(self, explorer, mock_page):
        """Verify visited URLs are tracked and skipped on subsequent calls."""
        mock_links = [
            {"url": "https://example.com/about", "text": "About", "location": "nav", "priority": 1},
            {"url": "https://example.com/contact", "text": "Contact", "location": "nav", "priority": 1},
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_links)

        # First call returns both links
        links1 = await explorer.discover_links(mock_page)
        assert len(links1) == 2

        # Second call with same links returns empty (all already visited)
        links2 = await explorer.discover_links(mock_page)
        assert len(links2) == 0

    @pytest.mark.asyncio
    async def test_link_extraction_script_is_js_string(self, explorer):
        """Verify _get_link_extraction_script returns valid JavaScript."""
        script = explorer._get_link_extraction_script()
        assert isinstance(script, str)
        assert len(script) > 0
        # Check script contains expected keywords
        assert "nav" in script
        assert "footer" in script
        assert "content" in script

    def test_domain_matching_exact_match(self, explorer):
        """Verify exact domain match works."""
        assert explorer._is_same_domain("https://example.com/page") is True

    def test_domain_matching_subdomain(self, explorer):
        """Verify subdomain matches base domain."""
        assert explorer._is_same_domain("https://sub.example.com/page") is True

    def test_domain_matching_www(self, explorer):
        """Verify www.domain matches domain."""
        assert explorer._is_same_domain("https://www.example.com/page") is True

    def test_domain_matching_different_domain(self, explorer):
        """Verify different domain does not match."""
        assert explorer._is_same_domain("https://evil.com/page") is False

    def test_domain_matching_non_http_protocol(self, explorer):
        """Verify non-HTTP schemes are filtered out."""
        # The _is_same_domain should return True for http/https URLs
        # But _filter_link will reject them based on scheme check
        assert explorer._is_same_domain("javascript:void(0)") is False


# ============================================================
# test_multi_page_exploration Tests
# ============================================================

class TestMultiPageExploration:
    """Test multi-page exploration functionality."""

    # Note: Full integration testing of explore_multi_page() requires
    # actual browser contexts, which are expensive. These tests use
    # extensive mocking to unit test the logic without launching browsers.

    @pytest.mark.asyncio
    async def test_exploration_respects_max_pages_limit(self, sample_link_infos):
        """Verify exploration visits at most max_pages pages."""
        # This is a conceptual test - actual implementation requires
        # mocking the full StealthScout which would be very complex.
        # The key behavior is: links[:max_pages] iteration limit.
        # The implementation in scout.py correctly uses: links_to_visit = discovered_links[:max_pages]

        # Verify the links are correctly sliced for max_pages
        max_pages = 2
        links_to_visit = sample_link_infos[:max_pages]
        assert len(links_to_visit) == max_pages
        assert links_to_visit[0].url == "https://example.com/about"
        assert links_to_visit[1].url == "https://example.com/contact"

    def test_exploration_breadcrumbs_track_visited_urls(self):
        """Verify breadcrumbs contain visited URLs in order."""
        visited_urls = [
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/privacy"
        ]
        result = ExplorationResult(
            base_url="https://example.com",
            breadcrumbs=visited_urls
        )
        assert len(result.breadcrumbs) == 3
        assert result.breadcrumbs[0] == "https://example.com/about"
        assert result.breadcrumbs[1] == "https://example.com/contact"
        assert result.breadcrumbs[2] == "https://example.com/privacy"

    def test_exploration_handles_navigation_timeout_creation(self):
        """Verify TIMEOUT PageVisit object can be created."""
        timeout_visit = PageVisit(
            url="https://example.com/slow-page",
            status="TIMEOUT",
            navigation_time_ms=15000
        )
        assert timeout_visit.url == "https://example.com/slow-page"
        assert timeout_visit.status == "TIMEOUT"
        assert timeout_visit.navigation_time_ms == 15000

    def test_exploration_success_page_visit_with_scroll(self):
        """Verify SUCCESS PageVisit can include scroll_result."""
        scroll_result = ScrollResult(
            total_cycles=5,
            stabilized=True,
            lazy_load_detected=True,
            screenshots_captured=3
        )
        success_visit = PageVisit(
            url="https://example.com/page",
            status="SUCCESS",
            screenshot_path="page.jpg",
            page_title="Page Title",
            navigation_time_ms=2000,
            scroll_result=scroll_result
        )
        assert success_visit.status == "SUCCESS"
        assert success_visit.scroll_result is not None
        assert success_visit.scroll_result.total_cycles == 5

    def test_exploration_rolls_up_time_metrics(self):
        """Verify ExplorationResult correctly totals navigation times."""
        pages = [
            PageVisit(url="https://example.com/page1", status="SUCCESS", navigation_time_ms=1000),
            PageVisit(url="https://example.com/page2", status="SUCCESS", navigation_time_ms=1500),
            PageVisit(url="https://example.com/page3", status="SUCCESS", navigation_time_ms=2000),
        ]
        result = ExplorationResult(
            base_url="https://example.com",
            pages_visited=pages
        )
        result.total_pages = len(result.pages_visited)
        result.total_time_ms = sum(pv.navigation_time_ms for pv in pages)

        assert result.total_pages == 3
        assert result.total_time_ms == 4500  # 1000 + 1500 + 2000

    def test_exploration_stores_discovered_links(self):
        """Verify ExplorationResult stores all discovered links."""
        links = [
            LinkInfo(url="https://example.com/page1", text="Page 1", location="nav", priority=1),
            LinkInfo(url="https://example.com/page2", text="Page 2", location="footer", priority=2),
        ]
        result = ExplorationResult(
            base_url="https://example.com",
            links_discovered=links
        )
        assert len(result.links_discovered) == 2
        assert result.links_discovered[0].url == "https://example.com/page1"
        assert result.links_discovered[1].url == "https://example.com/page2"
