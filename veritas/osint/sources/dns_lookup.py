"""Async DNS lookup source using dnspython.

Provides DNS record querying with async wrapping to prevent blocking.
Supports multiple record types including A, AAAA, MX, TXT, NS, SOA, CNAME.
"""

from typing import Dict, List, Optional

import dns.resolver
from dns.exception import DNSException

from veritas.osint.types import OSINTCategory, OSINTResult, SourceStatus
import asyncio


class DNSSource:
    """Async DNS lookup source.

    Queries DNS records for domains with blocking operations
    wrapped in thread pool executor to prevent blocking async context.
    """

    # Supported DNS record types
    RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "SOA", "CNAME"]

    async def query(
        self,
        domain: str,
        record_types: Optional[List[str]] = None
    ) -> OSINTResult:
        """Query DNS records for a domain.

        Args:
            domain: Domain name to query
            record_types: List of DNS record types to query (defaults to RECORD_TYPES)

        Returns:
            OSINTResult with DNS records organized by type
        """
        query_type = "dns"
        query_value = domain

        # Default to all record types if not specified
        if record_types is None:
            record_types = self.RECORD_TYPES

        # Run blocking DNS queries in thread pool executor
        try:
            results_dict = await asyncio.to_thread(
                self._query_all_types,
                domain,
                record_types
            )

            # Determine success based on having at least some successful queries
            has_success = any(
                r.get("status") == "success" for r in results_dict.values()
            )
            status = SourceStatus.SUCCESS if has_success else SourceStatus.ERROR

            return OSINTResult(
                source="dns",
                category=OSINTCategory.DNS,
                query_type=query_type,
                query_value=query_value,
                status=status,
                data=results_dict,
                confidence_score=0.95 if has_success else 0.0,
                cached_at=None,
                error_message=None,
            )

        except dns.resolver.NXDOMAIN as e:
            # Non-existent domain - return error with specific message
            return OSINTResult(
                source="dns",
                category=OSINTCategory.DNS,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data={"status": "error", "error": "NXDOMAIN - domain does not exist"},
                confidence_score=0.0,
                cached_at=None,
                error_message=f"NXDOMAIN: {str(e)}",
            )

        except DNSException as e:
            # Other DNS errors
            return OSINTResult(
                source="dns",
                category=OSINTCategory.DNS,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data={"status": "error", "error": str(e)},
                confidence_score=0.0,
                cached_at=None,
                error_message=f"DNS Exception: {str(e)}",
            )

        except Exception as e:
            # Unexpected errors
            return OSINTResult(
                source="dns",
                category=OSINTCategory.DNS,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data={"status": "error", "error": str(e)},
                confidence_score=0.0,
                cached_at=None,
                error_message=f"Unexpected error: {str(e)}",
            )

    def _query_all_types(
        self,
        domain: str,
        record_types: List[str]
    ) -> Dict[str, Dict]:
        """Query all requested DNS record types.

        Args:
            domain: Domain name to query
            record_types: List of DNS record types to query

        Returns:
            Dictionary mapping record type to result dict with status and records
        """
        results = {}
        error_messages = []

        for record_type in record_types:
            try:
                result = self._query_single_type(domain, record_type)
                results[record_type] = result

                if result.get("status") != "success":
                    error_messages.append(
                        f"{record_type}: {result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                error_messages.append(f"{record_type}: {str(e)}")
                results[record_type] = {
                    "status": "error",
                    "records": [],
                    "count": 0,
                    "error": str(e),
                }

        return results

    def _query_single_type(
        self,
        domain: str,
        record_type: str
    ) -> Dict:
        """Query a single DNS record type.

        Args:
            domain: Domain name to query
            record_type: DNS record type (A, AAAA, MX, TXT, etc.)

        Returns:
            Dictionary with status, records list, count, and optional error
        """
        try:
            # Query DNS with no answer allowed (won't raise on empty results)
            answer = dns.resolver.resolve(domain, record_type, raise_on_no_answer=False)

            records = []
            for rdata in answer:
                # Convert DNS record data to text string
                records.append(rdata.to_text())

            return {
                "status": "success" if records else "no_records",
                "records": records,
                "count": len(records),
                "error": None,
            }

        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            # Domain exists but no records of this type, or domain doesn't exist
            # These are considered successful queries with empty results
            return {
                "status": "no_records",
                "records": [],
                "count": 0,
                "error": None,
            }

        except dns.resolver.NoNameservers:
            # No name servers available for this domain
            return {
                "status": "error",
                "records": [],
                "count": 0,
                "error": "No nameservers available",
            }

        except dns.resolver.Timeout:
            return {
                "status": "error",
                "records": [],
                "count": 0,
                "error": "DNS query timeout",
            }

        except DNSException as e:
            return {
                "status": "error",
                "records": [],
                "count": 0,
                "error": str(e),
            }
