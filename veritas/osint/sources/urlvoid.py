"""URLVoid API client for domain reputation detection.

Queries URLVoid API to check domain detection rate across multiple
antivirus engines and calculate risk level based on detections.
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import aiohttp

from veritas.osint.types import OSINTCategory, OSINTResult, SourceStatus


logger = logging.getLogger("veritas.osint.sources.urlvoid")


class URLVoidSource:
    """URLVoid API client for domain reputation.

    Provides detection counts and risk assessment by querying
    the URLVoid API (free tier: 500 requests/day).
    """

    API_ENDPOINT = "https://www.urlvoid.com/api/1000"

    def __init__(self, api_key: str):
        """Initialize URLVoid source.

        Args:
            api_key: URLVoid API key from https://urlvoid.com/
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.

        Returns:
            aiohttp.ClientSession instance
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            logger.debug("URLVoid: Created new aiohttp session")
        return self.session

    async def query(self, domain: str) -> OSINTResult:
        """Query URLVoid for domain reputation.

        Makes GET request to URLVoid API, parses XML response,
        and returns detection counts with risk assessment.

        Args:
            domain: Domain name to query

        Returns:
            OSINTResult with detection data, risk level, and confidence
        """
        query_type = "reputation"
        query_value = domain

        try:
            session = await self._get_session()

            # Make API request
            params = {
                "host": domain,
                "key": self.api_key
            }

            async with session.get(
                self.API_ENDPOINT,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return OSINTResult(
                        source="urlvoid",
                        category=OSINTCategory.REPUTATION,
                        query_type=query_type,
                        query_value=query_value,
                        status=SourceStatus.ERROR,
                        data=None,
                        confidence_score=0.0,
                        cached_at=None,
                        error_message=f"HTTP {response.status}: {await response.text()}",
                    )

                content = await response.text()

            # Parse XML response
            detections, engines_count = self._parse_xml(content)

            # Calculate metrics
            engine_blacklist_count = engines_count - detections
            is_clean = detections == 0
            risk_level, confidence = self._calculate_risk_level(
                detections,
                engines_count
            )

            result_data = {
                "domain": domain,
                "detections": detections,
                "engines_count": engines_count,
                "engine_blacklist_count": engine_blacklist_count,
                "is_clean": is_clean,
                "risk_level": risk_level,
                "queried_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"URLVoid: {domain} - {detections}/{engines_count} detections, "
                f"risk_level={risk_level}"
            )

            return OSINTResult(
                source="urlvoid",
                category=OSINTCategory.REPUTATION,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.SUCCESS,
                data=result_data,
                confidence_score=confidence,
                cached_at=None,
                error_message=None,
            )

        except aiohttp.ClientTimeout:
            logger.warning(f"URLVoid: Timeout querying {domain}")
            return OSINTResult(
                source="urlvoid",
                category=OSINTCategory.REPUTATION,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.TIMEOUT,
                data=None,
                confidence_score=0.0,
                cached_at=None,
                error_message="Request timeout",
            )

        except Exception as e:
            logger.warning(f"URLVoid: Error querying {domain}: {str(e)}")
            return OSINTResult(
                source="urlvoid",
                category=OSINTCategory.REPUTATION,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data=None,
                confidence_score=0.0,
                cached_at=None,
                error_message=f"Request error: {str(e)}",
            )

    def _parse_xml(self, xml_content: str) -> tuple[int, int]:
        """Parse URLVoid XML response to extract detections and engine count.

        Args:
            xml_content: XML response from URLVoid API

        Returns:
            Tuple of (detections, engines_count)
        """
        try:
            root = ET.fromstring(xml_content)

            # Extract detection count
            detections_elem = root.find(".//detections")
            detections = int(detections_elem.text) if detections_elem is not None else 0

            # Extract engines count
            engines_elem = root.find(".//engines_count")
            engines_count = int(engines_elem.text) if engines_elem is not None else 0

            return detections, engines_count

        except ET.ParseError:
            logger.error("URLVoid: Failed to parse XML response")
            return 0, 0

    def _calculate_risk_level(
        self,
        detections: int,
        engines_count: int
    ) -> tuple[str, float]:
        """Calculate risk level and confidence based on detections.

        Args:
            detections: Number of engines that detected threats
            engines_count: Total number of engines queried

        Returns:
            Tuple of (risk_level, confidence_score)
            risk_level: "clean", "low", "medium", or "high"
            confidence_score: 0.0-1.0 confidence value
        """
        if detections == 0:
            return "clean", 0.7

        # Calculate detection percentage
        if engines_count > 0:
            detection_rate = detections / engines_count
        else:
            detection_rate = 0.0

        # Determine risk level
        if detection_rate >= 0.5:
            risk_level = "high"
            confidence = 1.0
        elif detection_rate >= 0.25:
            risk_level = "medium"
            confidence = 0.9
        elif detection_rate >= 0.05:
            risk_level = "low"
            confidence = 0.8
        else:
            risk_level = "low"
            confidence = 0.7

        return risk_level, confidence

    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("URLVoid: Closed aiohttp session")
