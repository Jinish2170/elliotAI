"""AbuseIPDB API client for IP address threat intelligence.

Queries AbuseIPDB API to check IP address abuse reports,
confidence scores, and usage type classification.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

import aiohttp

from veritas.osint.types import OSINTCategory, OSINTResult, SourceStatus


logger = logging.getLogger("veritas.osint.sources.abuseipdb")


class AbuseIPDBSource:
    """AbuseIPDB API client for IP address threat intelligence.

    Provides abuse confidence scores, report counts, and usage type
    classification by querying the AbuseIPDB API (free tier: 1000 requests/day).
    """

    API_ENDPOINT = "https://api.abuseipdb.com/api/v2/check"

    # IPv4 regex pattern for IP detection
    IPv4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    def __init__(self, api_key: str):
        """Initialize AbuseIPDB source.

        Args:
            api_key: AbuseIPDB API key from https://abuseipdb.com/
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.

        Returns:
            aiohttp.ClientSession instance
        """
        if self.session is None or self.session.closed:
            headers = {"Key": self.api_key}
            self.session = aiohttp.ClientSession(headers=headers)
            logger.debug("AbuseIPDB: Created new aiohttp session with Key header")
        return self.session

    async def check_ip(self, ip_address: str) -> OSINTResult:
        """Check IP address abuse reports.

        Makes GET request to AbuseIPDB check endpoint and returns
        abuse confidence, report counts, and classification.

        Args:
            ip_address: IPv4 address to check

        Returns:
            OSINTResult with abuse confidence, report counts, and metadata
        """
        query_type = "abuse_check"
        query_value = ip_address

        try:
            session = await self._get_session()

            # Make API request
            params = {
                "ipAddress": ip_address,
                "maxAgeInDays": 90,
                "verbose": ""
            }

            async with session.get(
                self.API_ENDPOINT,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return OSINTResult(
                        source="abuseipdb",
                        category=OSINTCategory.THREAT_INTEL,
                        query_type=query_type,
                        query_value=query_value,
                        status=SourceStatus.ERROR,
                        data=None,
                        confidence_score=0.0,
                        cached_at=None,
                        error_message=f"HTTP {response.status}: {await response.text()}",
                    )

                content = await response.json()

            # Check for API errors in response
            if content.get("errors"):
                error_list = content["errors"]
                error_msg = ", ".join(
                    f"{err.get('detail', str(err))}" for err in error_list
                )
                logger.warning(f"AbuseIPDB: API error for {ip_address}: {error_msg}")
                return OSINTResult(
                    source="abuseipdb",
                    category=OSINTCategory.THREAT_INTEL,
                    query_type=query_type,
                    query_value=query_value,
                    status=SourceStatus.ERROR,
                    data=None,
                    confidence_score=0.0,
                    cached_at=None,
                    error_message=error_msg,
                )

            # Extract data from response
            data = content.get("data", {})

            abuse_confidence_score = data.get("abuseConfidenceScore", 0)
            total_reports = data.get("totalReports", 0)
            is_whitelisted = data.get("isWhitelisted", False)
            country = data.get("countryCode")

            # Parse last report timestamp
            last_reported_at = None
            last_report_data = data.get("lastReportedAt")
            if last_reported_at:
                try:
                    last_reported_at = last_report_data.strftime("%Y-%m-%dT%H:%M:%SZ")
                except (AttributeError, ValueError):
                    last_reported_at = None

            # Get usage type (first reported type)
            usage_type = None
            reports = data.get("reports", [])
            if reports:
                usage_type = reports[0].get("usageType")

            result_data = {
                "ip_address": ip_address,
                "abuse_confidence_score": abuse_confidence_score,
                "total_reports": total_reports,
                "last_reported_at": last_reported_at,
                "is_whitelisted": is_whitelisted,
                "country": country,
                "usage_type": usage_type,
                "queried_at": datetime.utcnow().isoformat(),
            }

            # Confidence score from API is 0-100, normalize to 0.0-1.0
            confidence = abuse_confidence_score / 100.0

            logger.info(
                f"AbuseIPDB: {ip_address} - abuse_confidence={abuse_confidence_score}%, "
                f"reports={total_reports}"
            )

            return OSINTResult(
                source="abuseipdb",
                category=OSINTCategory.THREAT_INTEL,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.SUCCESS,
                data=result_data,
                confidence_score=confidence,
                cached_at=None,
                error_message=None,
            )

        except aiohttp.ClientTimeout:
            logger.warning(f"AbuseIPDB: Timeout checking {ip_address}")
            return OSINTResult(
                source="abuseipdb",
                category=OSINTCategory.THREAT_INTEL,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.TIMEOUT,
                data=None,
                confidence_score=0.0,
                cached_at=None,
                error_message="Request timeout",
            )

        except Exception as e:
            logger.warning(f"AbuseIPDB: Error checking {ip_address}: {str(e)}")
            return OSINTResult(
                source="abuseipdb",
                category=OSINTCategory.THREAT_INTEL,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data=None,
                confidence_score=0.0,
                cached_at=None,
                error_message=f"Request error: {str(e)}",
            )

    def _is_ipv4(self, value: str) -> bool:
        """Check if value is a valid IPv4 address.

        Args:
            value: String to check

        Returns:
            True if value matches IPv4 pattern
        """
        return bool(self.IPv4_PATTERN.match(value))

    async def query(self, domain_or_ip: str) -> OSINTResult:
        """Query domain or IP address.

        Detects IPv4 address pattern and delegates to check_ip().
        For domains, returns error result (IP resolution not implemented).

        Args:
            domain_or_ip: Domain name or IPv4 address to query

        Returns:
            OSINTResult with threat intelligence data
        """
        query_type = "query"
        query_value = domain_or_ip

        # Detect IPv4 address
        if self._is_ipv4(domain_or_ip):
            return await self.check_ip(domain_or_ip)

        # Domain - return error (IP resolution not implemented)
        logger.info(f"AbuseIPDB: Domain '{domain_or_ip}' not supported (IP-only)")
        return OSINTResult(
            source="abuseipdb",
            category=OSINTCategory.THREAT_INTEL,
            query_type=query_type,
            query_value=query_value,
            status=SourceStatus.ERROR,
            data=None,
            confidence_score=0.0,
            cached_at=None,
            error_message="Domain resolution not implemented (IP addresses only)",
        )

    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("AbuseIPDB: Closed aiohttp session")
