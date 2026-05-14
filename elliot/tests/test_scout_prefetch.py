"""
Unit tests for first-pass Scout link prefetch (_select_prefetch_urls).

Prefetch fetches a few priority internal links on the first Scout pass so Vision
and Graph have multi-page evidence before the first Judge call — the root-cause
fix for audits that looped just to gather pages the Judge needed.
"""
from elliot.agents.scout import ScoutResult
from elliot.core.nodes.scout import _select_prefetch_urls


def _result(internal_links):
    return ScoutResult(
        url="https://example.com",
        status="SUCCESS",
        page_metadata={"internal_links": internal_links},
    )


def test_priority_pages_selected_first():
    result = _result(["/blog", "/about", "/news", "/contact"])
    urls = _select_prefetch_urls("https://example.com", result, limit=2)
    assert urls == ["https://example.com/about", "https://example.com/contact"]


def test_backfills_with_other_links_when_few_priority():
    result = _result(["/blog", "/news"])
    urls = _select_prefetch_urls("https://example.com", result, limit=3)
    assert urls == ["https://example.com/blog", "https://example.com/news"]


def test_off_domain_links_excluded():
    result = _result(["https://evil.example/about", "/contact"])
    urls = _select_prefetch_urls("https://example.com", result, limit=5)
    assert urls == ["https://example.com/contact"]


def test_base_url_and_duplicates_excluded():
    result = _result(["/", "/about", "/about", "https://example.com/about/"])
    urls = _select_prefetch_urls("https://example.com", result, limit=5)
    assert urls == ["https://example.com/about"]


def test_limit_zero_disables_prefetch():
    result = _result(["/about", "/contact"])
    assert _select_prefetch_urls("https://example.com", result, limit=0) == []


def test_relative_links_resolved_against_base():
    result = _result(["about", "team/leadership"])
    urls = _select_prefetch_urls("https://example.com/", result, limit=5)
    assert urls == ["https://example.com/about", "https://example.com/team/leadership"]


def test_missing_or_malformed_metadata_is_safe():
    assert _select_prefetch_urls("https://example.com", _result(None), limit=3) == []
    assert _select_prefetch_urls("https://example.com", _result("not-a-list"), limit=3) == []
    assert _select_prefetch_urls("https://example.com", _result([None, 42, ""]), limit=3) == []
