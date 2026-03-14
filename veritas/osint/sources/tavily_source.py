"""Tavily-powered OSINT source for threat intelligence, reputation, and social media checks.

Uses Tavily search API to provide intelligent web search as a fallback
for OSINT categories that lack dedicated API sources (THREAT_INTEL, REPUTATION, SOCIAL).
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from veritas.osint.types import OSINTCategory, OSINTResult, SourceStatus

logger = logging.getLogger("veritas.osint.tavily_source")


# Query templates per category — focused search queries for each OSINT category
_CATEGORY_QUERIES: Dict[OSINTCategory, List[str]] = {
    OSINTCategory.THREAT_INTEL: [
        '"{domain}" malware threat report',
        '"{domain}" security vulnerability CVE',
    ],
    OSINTCategory.REPUTATION: [
        '"{domain}" scam fraud review',
        '"{domain}" trustpilot OR sitejabber OR bbb rating',
    ],
    OSINTCategory.SOCIAL: [
        '"{domain}" company linkedin OR twitter OR crunchbase',
    ],
}


class TavilyReputationSource:
    """Tavily-powered OSINT source for REPUTATION category.

    Searches for domain reputation, reviews, scam reports using the
    Tavily search API with intelligent query construction.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None

    async def query(self, domain: str) -> OSINTResult:
        """Query Tavily for domain reputation intelligence.

        Args:
            domain: Domain to search for

        Returns:
            OSINTResult with reputation data from web search
        """
        return await self._search_category(domain, OSINTCategory.REPUTATION)

    async def _search_category(
        self, domain: str, category: OSINTCategory
    ) -> OSINTResult:
        """Execute Tavily searches for a specific category."""
        clean_domain = urlparse(
            domain if domain.startswith("http") else f"https://{domain}"
        ).netloc or domain

        queries = _CATEGORY_QUERIES.get(category, [])
        all_results: List[Dict[str, Any]] = []
        signals: List[Dict[str, Any]] = []

        try:
            from tavily import AsyncTavilyClient

            if not self._client:
                self._client = AsyncTavilyClient(api_key=self._api_key)

            for query_template in queries:
                query = query_template.format(domain=clean_domain)
                # Per-query retry with exponential backoff + timeout
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        response = await asyncio.wait_for(
                            self._client.search(
                                query=query,
                                max_results=3,
                                search_depth="basic",
                            ),
                            timeout=20.0,
                        )
                        results = response.get("results", [])
                        for r in results:
                            entry = {
                                "title": r.get("title", ""),
                                "url": r.get("url", ""),
                                "snippet": r.get("content", "")[:300],
                                "score": r.get("score", 0.0),
                                "query_used": query,
                            }
                            all_results.append(entry)
                            signal = self._extract_signal(entry, category)
                            if signal:
                                signals.append(signal)
                        break  # success, move to next query
                    except asyncio.TimeoutError:
                        wait = 2 ** attempt
                        logger.warning(f"Tavily timeout for '{query}' (attempt {attempt + 1}/{max_attempts}), retrying in {wait}s")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(wait)
                    except Exception as e:
                        wait = 2 ** attempt
                        logger.warning(f"Tavily query failed for '{query}': {e} (attempt {attempt + 1}/{max_attempts})")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(wait)

            if not all_results:
                return OSINTResult(
                    source=f"tavily_{category.value}",
                    category=category,
                    query_type="web_search",
                    query_value=clean_domain,
                    status=SourceStatus.ERROR,
                    data={},
                    confidence_score=0.0,
                    error_message="No results from Tavily search",
                )

            return OSINTResult(
                source=f"tavily_{category.value}",
                category=category,
                query_type="web_search",
                query_value=clean_domain,
                status=SourceStatus.SUCCESS,
                data={
                    "search_results": all_results,
                    "signals": signals,
                    "total_results": len(all_results),
                    "queries_executed": len(queries),
                },
                confidence_score=min(0.7, 0.3 + 0.1 * len(all_results)),
            )

        except ImportError:
            logger.error("tavily package not installed")
            return OSINTResult(
                source=f"tavily_{category.value}",
                category=category,
                query_type="web_search",
                query_value=clean_domain,
                status=SourceStatus.ERROR,
                data={},
                confidence_score=0.0,
                error_message="tavily package not installed",
            )
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return OSINTResult(
                source=f"tavily_{category.value}",
                category=category,
                query_type="web_search",
                query_value=clean_domain,
                status=SourceStatus.ERROR,
                data={},
                confidence_score=0.0,
                error_message=str(e),
            )

    @staticmethod
    def _extract_signal(
        result: Dict[str, Any], category: OSINTCategory
    ) -> Optional[Dict[str, Any]]:
        """Extract a structured signal from a search result."""
        snippet = (result.get("snippet", "") + " " + result.get("title", "")).lower()
        url = result.get("url", "").lower()

        if category == OSINTCategory.REPUTATION:
            # Detect negative reputation signals
            negative_kw = ["scam", "fraud", "fake", "complaint", "rip off", "warning", "avoid"]
            positive_kw = ["trusted", "legitimate", "reliable", "verified", "recommended"]
            review_sites = ["trustpilot.com", "sitejabber.com", "bbb.org", "glassdoor.com"]

            is_review_site = any(s in url for s in review_sites)
            neg_score = sum(1 for kw in negative_kw if kw in snippet)
            pos_score = sum(1 for kw in positive_kw if kw in snippet)

            if neg_score > 0 or pos_score > 0 or is_review_site:
                return {
                    "type": "reputation",
                    "source_url": result.get("url", ""),
                    "sentiment": "negative" if neg_score > pos_score else "positive" if pos_score > neg_score else "neutral",
                    "is_review_site": is_review_site,
                    "negative_keywords": neg_score,
                    "positive_keywords": pos_score,
                }

        elif category == OSINTCategory.THREAT_INTEL:
            threat_kw = ["malware", "phishing", "exploit", "cve-", "vulnerability", "breach", "compromised"]
            threat_score = sum(1 for kw in threat_kw if kw in snippet)
            if threat_score > 0:
                return {
                    "type": "threat_intel",
                    "source_url": result.get("url", ""),
                    "threat_keywords": threat_score,
                    "snippet": result.get("snippet", "")[:200],
                }

        elif category == OSINTCategory.SOCIAL:
            social_sites = ["linkedin.com", "twitter.com", "x.com", "crunchbase.com", "github.com"]
            is_social = any(s in url for s in social_sites)
            if is_social:
                return {
                    "type": "social_presence",
                    "platform": next((s.split(".")[0] for s in social_sites if s in url), "unknown"),
                    "source_url": result.get("url", ""),
                }

        return None


class TavilyThreatIntelSource(TavilyReputationSource):
    """Tavily-powered OSINT source for THREAT_INTEL category."""

    async def query(self, domain: str) -> OSINTResult:
        return await self._search_category(domain, OSINTCategory.THREAT_INTEL)


class TavilySocialSource(TavilyReputationSource):
    """Tavily-powered OSINT source for SOCIAL category."""

    async def query(self, domain: str) -> OSINTResult:
        return await self._search_category(domain, OSINTCategory.SOCIAL)
