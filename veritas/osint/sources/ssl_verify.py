"""Async SSL certificate validation source.

Provides SSL/TLS certificate information with async wrapping to prevent blocking.
Extracts certificate details including issuer, validity periods, and subject.
"""

import socket
import ssl
from datetime import datetime
from typing import Dict, List, Optional

from veritas.osint.types import OSINTCategory, OSINTResult, SourceStatus
import asyncio


class SSLSource:
    """Async SSL certificate validation source.

    Retrieves SSL/TLS certificates for hosts with blocking operations
    wrapped in thread pool executor to prevent blocking async context.
    Provides certificate details, validity checking, and issuer information.
    """

    async def query(
        self,
        hostname: str,
        port: int = 443
    ) -> OSINTResult:
        """Query SSL certificate for a hostname.

        Args:
            hostname: Hostname to query (domain or IP)
            port: Port to connect on (default 443 for HTTPS)

        Returns:
            OSINTResult with certificate details, issuer, validity dates,
            expiry information, and confidence score.
        """
        query_type = "certificate"
        query_value = f"{hostname}:{port}"

        # Run blocking SSL operations in thread pool executor
        try:
            cert_data = await asyncio.to_thread(
                self._get_certificate,
                hostname,
                port
            )

            certificate = cert_data.get("certificate")
            if not certificate:
                return OSINTResult(
                    source="ssl",
                    category=OSINTCategory.SSL,
                    query_type=query_type,
                    query_value=query_value,
                    status=SourceStatus.ERROR,
                    data=None,
                    confidence_score=0.0,
                    cached_at=None,
                    error_message=cert_data.get("error", "Unknown error"),
                )

            # Parse certificate fields
            parsed = self._parse_certificate(certificate, hostname)

            return OSINTResult(
                source="ssl",
                category=OSINTCategory.SSL,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.SUCCESS,
                data=parsed,
                confidence_score=parsed["confidence_score"],
                cached_at=None,
                error_message=None,
            )

        except Exception as e:
            return OSINTResult(
                source="ssl",
                category=OSINTCategory.SSL,
                query_type=query_type,
                query_value=query_value,
                status=SourceStatus.ERROR,
                data=None,
                confidence_score=0.0,
                cached_at=None,
                error_message=f"SSL error: {str(e)}",
            )

    def _get_certificate(
        self,
        hostname: str,
        port: int
    ) -> Dict:
        """Get SSL certificate from remote host.

        Args:
            hostname: Hostname to connect to
            port: Port to connect on

        Returns:
            Dictionary with certificate and any error message
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        try:
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return {"certificate": cert, "error": None}

        except ssl.SSLError as e:
            return {"certificate": None, "error": f"SSL error: {str(e)}"}

        except socket.timeout:
            return {"certificate": None, "error": "Connection timeout"}

        except socket.gaierror as e:
            return {"certificate": None, "error": f"DNS resolution failed: {str(e)}"}

        except ConnectionRefusedError:
            return {"certificate": None, "error": "Connection refused"}

        except OSError as e:
            return {"certificate": None, "error": f"Connection error: {str(e)}"}

    def _parse_certificate(
        self,
        cert: Dict,
        hostname: str
    ) -> Dict:
        """Parse SSL certificate into standardized format.

        Args:
            cert: Certificate dictionary from getpeercert()
            hostname: Original hostname queried

        Returns:
            Dictionary with parsed certificate fields
        """
        parsed = {
            "hostname": hostname,
            "subject": None,
            "issuer": None,
            "issued_at": None,
            "expires_at": None,
            "days_until_expiry": None,
            "subject_alt_names": None,
            "version": None,
            "serial_number": None,
            "is_valid": False,
            "is_expiring_soon": False,
            "issuer_org": None,
            "confidence_score": 0.5,
        }

        # Parse subject
        subject_dict = self._parse_x509_name(cert.get("subject", {}))
        if subject_dict:
            parsed["subject"] = subject_dict

        # Parse issuer
        issuer_dict = self._parse_x509_name(cert.get("issuer", {}))
        if issuer_dict:
            parsed["issuer"] = issuer_dict
            parsed["issuer_org"] = issuer_dict.get("organizationName")

        # Parse validity dates
        not_before = cert.get("notBefore")
        not_after = cert.get("notAfter")

        if not_before:
            parsed["issued_at"] = self._parse_cert_date(not_before)
        if not_after:
            parsed["expires_at"] = self._parse_cert_date(not_after)

        # Calculate expiry metrics
        if parsed["issued_at"] and parsed["expires_at"]:
            not_valid_after = self._parse_cert_date_to_datetime(not_after)
            if not_valid_after:
                days_until_expiry = (not_valid_after - datetime.utcnow()).days
                parsed["days_until_expiry"] = days_until_expiry
                parsed["is_valid"] = days_until_expiry > 0
                parsed["is_expiring_soon"] = 0 < days_until_expiry < 30

                # Confidence based on remaining validity
                parsed["confidence_score"] = 0.9 if days_until_expiry > 30 else 0.5

        # Parse subject alternative names (may be list of tuples or strings)
        alt_names = cert.get("subjectAltName", [])
        if alt_names:
            alt_names_list = []
            for name in alt_names:
                # Handle tuple format: ('DNS', 'example.com')
                if isinstance(name, tuple) and len(name) == 2:
                    if name[0] == "DNS":
                        alt_names_list.append(name[1])
                # Handle string format: "DNS:example.com"
                elif isinstance(name, str) and name.startswith("DNS:"):
                    split = name.split(":", 1)
                    if len(split) == 2:
                        alt_names_list.append(split[1])
            parsed["subject_alt_names"] = alt_names_list if alt_names_list else None

        # Other certificate fields
        parsed["version"] = cert.get("version")
        parsed["serial_number"] = cert.get("serialNumber")

        return parsed

    def _parse_x509_name(
        self,
        name_list: List[tuple]
    ) -> Optional[Dict]:
        """Parse X.509 name into dictionary.

        Args:
            name_list: List of tuples like [('commonName', 'example.com'), ...]

        Returns:
            Dictionary with name attributes
        """
        if not name_list:
            return None

        result = {}
        for field in name_list:
            if isinstance(field, tuple) and len(field) == 2:
                key, value = field
                if key in result:
                    # Append if multiple values for same key
                    if isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value

        return result

    def _parse_cert_date(self, date_str: str) -> Optional[str]:
        """Parse certificate date string to ISO format.

        Args:
            date_str: Date string from certificate (e.g., "May 15 12:00:00 2024 GMT")

        Returns:
            ISO formatted date string, or None
        """
        dt = self._parse_cert_date_to_datetime(date_str)
        return dt.isoformat() if dt else None

    def _parse_cert_date_to_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse certificate date string to datetime.

        Args:
            date_str: Date string from certificate (e.g., "May 15 12:00:00 2024 GMT")

        Returns:
            datetime object, or None
        """
        # Try common X.509 date formats
        formats = [
            "%b %d %H:%M:%S %Y GMT",  # Sep 30 12:00:00 2023 GMT
            "%b %d %H:%M:%S %Y %Z",   # Sep 30 12:00:00 2023 GMT (with timezone)
            "%Y-%m-%dT%H:%M:%SZ",     # ISO format
            "%Y-%m-%d %H:%M:%S",      # Simple format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue

        return None
