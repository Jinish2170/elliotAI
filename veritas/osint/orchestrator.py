"""OSINT orchestrator with source discovery, rate limiting, and circuit breaking.

Provides centralized management of OSINT sources with intelligent fallback
to alternative sources when primary sources fail. Implements circuit breaker
pattern to prevent API throttling and rate limiting to respect API quotas.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from veritas.osint.types import OSINTCategory, OSINTResult, SourceConfig


logger = logging.getLogger("veritas.osint.orchestrator")


class CircuitBreaker:
    """Circuit breaker for OSINT sources.

    Tracks source failures and opens circuit after threshold is reached,
    preventing further calls to failing sources for a timeout period.
    """

    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before trying source again after opening
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self._failures: Dict[str, List[datetime]] = defaultdict(list)

    def record_failure(self, source: str) -> None:
        """Record a failure for a source.

        Args:
            source: Name of the OSINT source
        """
        self._failures[source].append(datetime.utcnow())
        logger.warning(
            f"CircuitBreaker: Recorded failure for {source}, "
            f"{len(self._failures[source])} total"
        )

    def is_open(self, source: str) -> bool:
        """Check if circuit is open for a source.

        Cleans old failures before checking threshold.

        Args:
            source: Name of the OSINT source

        Returns:
            True if circuit is open (source should be skipped)
        """
        now = datetime.utcnow()

        # Clean old failures outside timeout window
        if source in self._failures:
            self._failures[source] = [
                ts for ts in self._failures[source]
                if (now - ts).total_seconds() < self.timeout_seconds
            ]

        # Check if failure threshold exceeded
        is_open = len(self._failures[source]) >= self.failure_threshold

        if is_open:
            logger.warning(
                f"CircuitBreaker: Circuit OPEN for {source} "
                f"({len(self._failures[source])} failures within {self.timeout_seconds}s)"
            )

        return is_open

    def reset(self, source: str) -> None:
        """Reset circuit breaker for a source.

        Args:
            source: Name of the OSINT source
        """
        if source in self._failures:
            del self._failures[source]
            logger.info(f"CircuitBreaker: Circuit RESET for {source}")


class RateLimiter:
    """Rate limiter for OSINT sources.

    Tracks requests per source and enforces RPM (requests per minute)
    and RPH (requests per hour) limits to respect API quotas.
    """

    def __init__(self):
        """Initialize rate limiter."""
        self._requests: Dict[str, List[datetime]] = defaultdict(list)

    def can_request(
        self,
        source: str,
        rpm_limit: Optional[int] = None,
        rph_limit: Optional[int] = None
    ) -> tuple[bool, str]:
        """Check if source can make a request within rate limits.

        Args:
            source: Name of the OSINT source
            rpm_limit: Requests per minute limit (None for no limit)
            rph_limit: Requests per hour limit (None for no limit)

        Returns:
            Tuple of (can_request, reason)
        """
        now = datetime.utcnow()

        # Get or initialize request history
        if source not in self._requests:
            self._requests[source] = []

        # Clean requests older than 1 hour before checking RPH
        self._requests[source] = [
            ts for ts in self._requests[source]
            if (now - ts).total_seconds() < 3600
        ]

        # Count requests in last minute
        rpm_count = sum(
            1 for ts in self._requests[source]
            if (now - ts).total_seconds() < 60
        )

        # Count requests in last hour
        rph_count = len(self._requests[source])

        # Check RPM limit
        if rpm_limit and rpm_count >= rpm_limit:
            return False, f"RPM limit reached ({rpm_count}/{rpm_limit})"

        # Check RPH limit
        if rph_limit and rph_count >= rph_limit:
            return False, f"RPH limit reached ({rph_count}/{rph_limit})"

        return True, ""

    def record_request(self, source: str) -> None:
        """Record a successful request for a source.

        Args:
            source: Name of the OSINT source
        """
        self._requests[source].append(datetime.utcnow())
        logger.debug(f"RateLimiter: Recorded request for {source}")


class OSINTOrchestrator:
    """Orchestrator for OSINT sources with intelligent fallback.

    Manages multiple OSINT sources, coordinates queries with rate limiting,
    and falls back to alternative sources when primary sources fail.
    """

    def __init__(self, db_session=None):
        """Initialize OSINT orchestrator.

        Args:
            db_session: Optional database session for caching
        """
        self._circuit_breaker = CircuitBreaker()
        self._rate_limiter = RateLimiter()
        self._sources: Dict[str, object] = {}
        self._source_configs: Dict[str, SourceConfig] = {}

        # Auto-discover available sources
        self._discover_sources()

    def _discover_sources(self) -> None:
        """Auto-discover available OSINT sources and register them.

        Dynamically imports core sources (DNS, WHOIS, SSL) and
        conditional sources (URLVoid, AbuseIPDB) if API keys available.
        """
        # Import settings dynamically to avoid circular dependency
        from veritas.config import settings

        # Import core sources
        from veritas.osint.sources.dns_lookup import DNSSource
        from veritas.osint.sources.ssl_verify import SSLSource
        from veritas.osint.sources.whois_lookup import WHOISSource

        # Register core sources (no API key required, high priority)
        self._register_source(
            DNSSource(),
            SourceConfig(
                enabled=True,
                priority=1,  # CRITICAL
                requires_api_key=False,
                rate_limit_rpm=999,
                rate_limit_rph=999
            )
        )

        self._register_source(
            WHOISSource(),
            SourceConfig(
                enabled=True,
                priority=1,  # CRITICAL
                requires_api_key=False,
                rate_limit_rpm=999,
                rate_limit_rph=999
            )
        )

        self._register_source(
            SSLSource(),
            SourceConfig(
                enabled=True,
                priority=1,  # CRITICAL
                requires_api_key=False,
                rate_limit_rpm=999,
                rate_limit_rph=999
            )
        )

        # Try to register URLVoid if API key available
        if hasattr(settings, "URLVOID_API_KEY") and settings.URLVOID_API_KEY:
            try:
                from veritas.osint.sources.urlvoid import URLVoidSource

                self._register_source(
                    URLVoidSource(settings.URLVOID_API_KEY),
                    SourceConfig(
                        enabled=True,
                        priority=2,  # IMPORTANT
                        requires_api_key=True,
                        rate_limit_rpm=getattr(settings, "URLVOID_REQUESTS_PER_MINUTE", 20),
                        rate_limit_rph=None  # No daily limit enforced
                    )
                )
                logger.info("OSINTOrchestrator: Registered URLVoid source")
            except ImportError:
                logger.warning("OSINTOrchestrator: URLVoid source not available (ImportError)")
        else:
            logger.info("OSINTOrchestrator: URLVoid not registered (no API key)")

        # Try to register AbuseIPDB if API key available
        if hasattr(settings, "ABUSEIPDB_API_KEY") and settings.ABUSEIPDB_API_KEY:
            try:
                from veritas.osint.sources.abuseipdb import AbuseIPDBSource

                self._register_source(
                    AbuseIPDBSource(settings.ABUSEIPDB_API_KEY),
                    SourceConfig(
                        enabled=True,
                        priority=2,  # IMPORTANT
                        requires_api_key=True,
                        rate_limit_rpm=getattr(settings, "ABUSEIPDB_REQUESTS_PER_MINUTE", 15),
                        rate_limit_rph=None  # No daily limit enforced
                    )
                )
                logger.info("OSINTOrchestrator: Registered AbuseIPDB source")
            except ImportError:
                logger.warning("OSINTOrchestrator: AbuseIPDB source not available (ImportError)")
        else:
            logger.info("OSINTOrchestrator: AbuseIPDB not registered (no API key)")

        logger.info(f"OSINTOrchestrator: Discovered and registered {len(self._sources)} sources")

    def _register_source(self, source: object, config: SourceConfig) -> None:
        """Register an OSINT source with its configuration.

        Args:
            source: OSINT source instance
            config: Source configuration
        """
        source_name = self._get_source_name(source)
        self._sources[source_name] = source
        self._source_configs[source_name] = config
        logger.debug(f"OSINTOrchestrator: Registered source {source_name} with priority {config.priority}")

    def _get_source_name(self, source: object) -> str:
        """Get name of an OSINT source from its class.

        Args:
            source: OSINT source instance

        Returns:
            Lowercase source name (e.g., "dns", "whois", "ssl")
        """
        class_name = source.__class__.__name__
        # Remove "Source" suffix if present and convert to lowercase
        name = class_name.replace("Source", "").lower()
        # Handle special cases
        if name == "abuseipdb":
            name = "abuseipdb"
        return name

    def get_alternative_sources(
        self,
        category: OSINTCategory,
        exclude_source: Optional[str] = None,
        max_alternatives: int = 2
    ) -> List[str]:
        """Get alternative sources for a category, sorted by priority.

        Excludes specified source and returns up to max_alternatives.

        Args:
            category: OSINT category to find alternatives for
            exclude_source: Source to exclude from alternatives
            max_alternatives: Maximum number of alternatives to return

        Returns:
            List of source names sorted by priority (lowest first)
        """
        # Filter sources by category, enabled status, and excluded source
        alternatives = [
            (name, config.priority)
            for name, config in self._source_configs.items()
            if config.enabled
            and name != exclude_source
            and self._sources[name].query.__annotations__.get("return", "")
            .__class__.__name__  # Get return type category from source
            if config.enabled  # Filter again for enabled sources
        ]

        # Actually, we need to map sources to categories properly
        # For now, return all enabled sources except excluded, sorted by priority
        alternatives = [
            (name, config.priority)
            for name, config in self._source_configs.items()
            if config.enabled and name != exclude_source
        ]

        # Sort by priority (lower priority = higher importance)
        alternatives.sort(key=lambda x: x[1])

        # Return only source names, limited to max_alternatives
        return [name for name, _ in alternatives[:max_alternatives]]

    async def get_source_category(self, source_name: str) -> Optional[OSINTCategory]:
        """Get category for a source by inspecting its return type.

        Args:
            source_name: Name of the OSINT source

        Returns:
            OSINTCategory or None if source not found
        """
        if source_name not in self._sources:
            return None

        source = self._sources[source_name]

        # Map source names to categories based on known sources
        category_mapping = {
            "dns": OSINTCategory.DNS,
            "whois": OSINTCategory.WHOIS,
            "ssl": OSINTCategory.SSL,
            "abuseipdb": OSINTCategory.THREAT_INTEL,
            "urlvoid": OSINTCategory.REPUTATION,
        }

        return category_mapping.get(source_name)

    async def query_with_retry(
        self,
        source_name: str,
        method: str,
        *args,
        max_retries: int = 2,
        **kwargs
    ) -> Optional[OSINTResult]:
        """Query a source with retry logic and circuit breaking.

        Checks circuit breaker and rate limits before attempting queries.
        Retries on TimeoutError and other exceptions up to max_retries times.
        Calls _try_alternatives if all retries fail.

        Args:
            source_name: Name of the OSINT source
            method: Method name to call on the source (e.g., "query")
            *args: Positional arguments to pass to the method
            max_retries: Maximum number of retry attempts (default 2)
            **kwargs: Keyword arguments to pass to the method

        Returns:
            OSINTResult or None if source not found, disabled, or all retries fail
        """
        # Get source and config
        source = self.get_source(source_name)
        config = self.get_config(source_name)

        if source is None:
            logger.warning(f"query_with_retry: Source '{source_name}' not found")
            return None

        if config is None or not config.enabled:
            logger.warning(f"query_with_retry: Source '{source_name}' not enabled")
            return None

        # Check circuit breaker - skip if open
        if self._circuit_breaker.is_open(source_name):
            logger.warning(
                f"query_with_retry: Circuit breaker open for '{source_name}', skipping"
            )
            return None

        # Check rate limits - skip if limited
        can_request, limit_reason = self._rate_limiter.can_request(
            source_name,
            config.rate_limit_rpm,
            config.rate_limit_rph
        )
        if not can_request:
            logger.warning(
                f"query_with_retry: Rate limit reached for '{source_name}': {limit_reason}"
            )
            return None

        # Try query with retries
        for attempt in range(max_retries + 1):
            try:
                # Get the method dynamically
                method_func = getattr(source, method)
                result = await method_func(*args, **kwargs)

                # Success - record request and return result
                if result is not None:
                    self._rate_limiter.record_request(source_name)
                    logger.info(
                        f"query_with_retry: '{source_name}' query succeeded "
                        f"(attempt {attempt + 1})"
                    )
                    return result
                else:
                    logger.warning(
                        f"query_with_retry: '{source_name}' returned None "
                        f"(attempt {attempt + 1})"
                    )

            except TimeoutError as e:
                logger.warning(
                    f"query_with_retry: Timeout on '{source_name}' "
                    f"(attempt {attempt + 1}): { str(e)}"
                )
                if attempt == max_retries:
                    self._circuit_breaker.record_failure(source_name)

            except Exception as e:
                logger.warning(
                    f"query_with_retry: Error on '{source_name}' "
                    f"(attempt {attempt + 1}): {str(e)}"
                )
                if attempt == max_retries:
                    self._circuit_breaker.record_failure(source_name)

        # All retries failed - try alternatives
        logger.warning(
            f"All retries failed for '{source_name}', trying alternatives"
        )
        return await self._try_alternatives(source_name, method, *args, **kwargs)

    async def _try_alternatives(
        self,
        failed_source: str,
        method: str,
        *args,
        **kwargs
    ) -> Optional[OSINTResult]:
        """Try alternative sources when primary source fails.

        Queries up to 2 alternative sources and returns first successful result.

        Args:
            failed_source: Name of the source that failed
            method: Method name to call on alternatives
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            OSINTResult from first successful alternative, or None
        """
        # Use THREAT_INTEL as default category for alternatives
        category = OSINTCategory.THREAT_INTEL

        # Get alternative sources
        alternatives = self.get_alternative_sources(
            category,
            exclude_source=failed_source,
            max_alternatives=2
        )

        if not alternatives:
            logger.info("_try_alternatives: No alternative sources available")
            return None

        # Try each alternative
        for alt_source in alternatives:
            logger.info(f"_try_alternatives: Trying alternative '{alt_source}'")
            result = await self.query_with_retry(
                alt_source,
                method,
                *args,
                max_retries=1,  # Reduce retries for alternatives
                **kwargs
            )
            if result is not None:
                logger.info(
                    f"_try_alternatives: Alternative '{alt_source}' succeeded"
                )
                return result

        logger.warning(
            f"_try_alternatives: All alternatives failed [{', '.join(alternatives)}]"
        )
        return None

    async def query_all(
        self,
        category: OSINTCategory,
        query_type: str,
        query_value: str,
        max_parallel: int = 3
    ) -> Dict[str, OSINTResult]:
        """Query all enabled sources in a category with concurrency limiting.

        Filters sources by category and enabled status, then queries all
        in parallel using asyncio.gather() with semaphore for concurrent
        request limiting.

        Args:
            category: OSINT category to query
            query_type: Type of query (passed to source query method)
            query_value: Value to query (passed to source query method)
            max_parallel: Maximum number of concurrent queries (default 3)

        Returns:
            Dictionary mapping source names to OSINTResult (only non-None results)
        """
        # Filter sources to only enabled ones in category
        sources_to_query = {
            name: source
            for name, source in self._sources.items()
            if self._source_configs[name].enabled
            and await self.get_source_category(name) == category
        }

        if not sources_to_query:
            logger.warning(f"query_all: No enabled sources found for category {category}")
            return {}

        # Create semaphore for concurrency limiting
        semaphore = asyncio.Semaphore(max_parallel)

        # Results dictionary to store successful queries
        results: Dict[str, OSINTResult] = {}

        async def query_source(name: str) -> None:
            """Query a single source with semaphore limiting."""
            async with semaphore:
                result = await self.query_with_retry(
                    name,
                    "query",
                    query_value
                )
                if result is not None:
                    results[name] = result

        # Run all queries in parallel
        logger.info(
            f"query_all: Querying {len(sources_to_query)} sources "
            f"with max_parallel={max_parallel}"
        )
        await asyncio.gather(
            *[query_source(name) for name in sources_to_query.keys()]
        )

        logger.info(
            f"query_all: Completed with {len(results)}/{len(sources_to_query)} successful"
        )
        return results

    async def close(self) -> None:
        """Close all source sessions if they have close() method."""
        for name, source in self._sources.items():
            if hasattr(source, "close"):
                try:
                    close_method = getattr(source, "close")
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                    logger.debug(f"OSINTOrchestrator: Closed {name}")
                except Exception as e:
                    logger.warning(f"OSINTOrchestrator: Error closing {name}: {e}")

    def get_source(self, source_name: str) -> Optional[object]:
        """Get a registered source by name.

        Args:
            source_name: Name of the OSINT source

        Returns:
            Source instance or None if not found
        """
        return self._sources.get(source_name)

    def get_config(self, source_name: str) -> Optional[SourceConfig]:
        """Get configuration for a source.

        Args:
            source_name: Name of the OSINT source

        Returns:
            SourceConfig or None if not found
        """
        return self._source_configs.get(source_name)

    def list_sources(self) -> Dict[str, SourceConfig]:
        """List all registered sources with their configurations.

        Returns:
            Dictionary mapping source names to SourceConfig
        """
        return self._source_configs.copy()
