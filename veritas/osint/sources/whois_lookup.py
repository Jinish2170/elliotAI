"""Async WHOIS lookup source using python-whois.

Provides domain WHOIS information with async wrapping to prevent blocking.
Extracts and normalizes WHOIS fields including registrar, dates, and nameservers.
"""

from datetime import datetime
from typing import Dict, Optional

import whois

from veritas.osint.types import OSINTCategory, OSINTResult, SourceStatus
import asyncio


class WHOISSource:
    """Async WHOIS lookup source.

    Queries WHOIS data for domains with blocking operations
    wrapped in thread pool executor to prevent blocking async context.
    Normalizes WHOIS fields for consistent consumption.
    """

    async def query(self, domain: str) -> OSINTResult:
        """Query WHOIS data for a domain.

        Args:
            domain: Domain name to query

        Returns:
            OSINTResult with normalized WHOIS data including domain age,
            registrar, creation/expiry dates, and nameservers.
        """
        query_type = "whois"
        query_value = domain

        # Run blocking WHOIS query in thread pool executor
        try:
            whois_result = await asyncio.to_thread(
                whois.whois,
                domain
            )

            # whois.whois() returns None for invalid domains or errors
            if whois_result is None:
                return OSINTResult(
                    source="whois",
                    category=OSINTCategory.WHOIS,
                    query_type=query_type,
                    query_value=query_value,
                    status=SourceStatus.ERROR,
                    data=None,
                    confidence_score=0.0,
                    cached_at=None,
                    error_message="No WHOIS data returned (invalid domain or not registered)",
                )

            # Normalize WHOIS fields
            normalized = self._normalize_whois_data(domain, whois_result)

            # Calculate age-based confidence
            age_days = normalized.get("age_days", -1)
            confidence = 0.9 if age_days > 0 else 0.5

            return OSINTResult(
                source="whois",
                category=OSINTCategory.WHOIS,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.SUCCESS,
                data=normalized,
                confidence_score=confidence,
                cached_at=None,
                error_message=None,
            )

        except Exception as e:
            return OSINTResult(
                source="whois",
                category=OSINTCategory.WHOIS,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data=None,
                confidence_score=0.0,
                cached_at=None,
                error_message=f"WHOIS error: {str(e)}",
            )

    def _normalize_whois_data(
        self,
        domain: str,
        whois_result: any
    ) -> Dict:
        """Normalize WHOIS data to consistent format.

        Args:
            domain: Domain name being queried
            whois_result: WHOIS result object from python-whois

        Returns:
            Normalized dictionary with standardized field names
        """
        normalized = {
            "domain": domain,
            "registrant": None,
            "created_date": None,
            "expiry_date": None,
            "age_days": -1,
            "registrar": None,
            "nameservers": None,
            "registrant_country": None,
            "registrant_org": None,
        }

        # Extract registrant name
        registrant = getattr(whois_result, "registrant_name", None)
        if not registrant:
            registrant = getattr(whois_result, "name", None)
        normalized["registrant"] = self._extract_first_value(registrant)

        # Extract registrar
        registrar = getattr(whois_result, "registrar", None)
        if not registrar:
            registrar = getattr(whois_result, "sponsoring_registrar", None)
        normalized["registrar"] = self._extract_first_value(registrar)

        # Extract nameservers
        nameservers = getattr(whois_result, "name_servers", None)
        if nameservers:
            if isinstance(nameservers, list):
                # Filter out None values
                normalized["nameservers"] = [ns for ns in nameservers if ns]
            else:
                normalized["nameservers"] = [nameservers]

        # Extract and normalize dates
        created_date = getattr(whois_result, "creation_date", None)
        normalized["created_date"] = self._extract_first_date_value(created_date)

        expiry_date = getattr(whois_result, "expiration_date", None)
        normalized["expiry_date"] = self._extract_first_date_value(expiry_date)

        # Calculate domain age
        if created_date and isinstance(created_date, datetime):
            age_days = (datetime.utcnow() - created_date).days
            normalized["age_days"] = max(0, age_days)

        # Extract registrant organization
        registrant_org = getattr(whois_result, "registrant_org", None)
        normalized["registrant_org"] = self._extract_first_value(registrant_org)

        # Extract registrant country
        registrant_country = getattr(whois_result, "registrant_country", None)
        normalized["registrant_country"] = self._extract_first_value(registrant_country)

        return normalized

    def _extract_first_value(
        self,
        value: any
    ) -> Optional[str]:
        """Extract first value from potentially nested field.

        Args:
            value: Value from WHOIS data (may be None, string, or list)

        Returns:
            First non-None value as string, or None
        """
        if value is None:
            return None

        if isinstance(value, list):
            # Take first non-None item from list
            for item in value:
                if item:
                    return str(item)
            return None

        return str(value)

    def _extract_first_date_value(
        self,
        value: any
    ) -> Optional[str]:
        """Extract first date value and format as ISO string.

        Args:
            value: Value from WHOIS data (may be None, datetime, or list of datetimes)

        Returns:
            ISO formatted date string, or None
        """
        if value is None:
            return None

        if isinstance(value, list):
            # Take first valid datetime from list
            for item in value:
                if item:
                    if isinstance(item, datetime):
                        return item.isoformat()
            return None

        if isinstance(value, datetime):
            return value.isoformat()

        return None
