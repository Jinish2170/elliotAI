"""OSINT result caching with source-specific TTLs.

Provides caching layer for OSINT queries using SQLite backend.
Each source type has its own TTL configuration to balance
freshness with API rate limit conservation.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from veritas.osint.types import OSINTCategory, OSINTResult


class OSINTCache:
    """OSINT result cache with source-specific TTLs.

    Manages caching of OSINT query results with time-based expiration.
    Each source category has a configured TTL to optimize freshness
    while minimizing redundant API calls.
    """

    # Source-specific TTLs
    SOURCE_TTLS = {
        "dns": timedelta(hours=24),      # DNS records change infrequently, 24h cache
        "whois": timedelta(days=7),      # WHOIS data rarely changes, 7-day cache
        "ssl": timedelta(days=30),       # SSL certs valid 90+ days, 30-day cache
        "abuseipdb": timedelta(hours=12), # Threat intel changes faster, 12h cache
        "urlvoid": timedelta(hours=24),   # Reputation data, 24h cache
        "social": timedelta(hours=24),    # Social media data, 24h cache
    }

    # Default TTL for unknown sources
    DEFAULT_TTL = timedelta(hours=24)

    @staticmethod
    def generate_cache_key(
        source: str,
        category: OSINTCategory,
        query_type: str,
        **query_params: Any
    ) -> str:
        """Generate a deterministic cache key for a query.

        Args:
            source: OSINT source name (e.g., "dns", "whois", "ssl")
            category: Category of the OSINT query
            query_type: Type of query
            **query_params: Additional query parameters

        Returns:
            MD5 hash string representing the cache key
        """
        # Normalize all params to lowercase strings
        normalized_params = {
            k: str(v).lower() if v is not None else ""
            for k, v in query_params.items()
        }

        # Create cache key compound string
        key_parts = {
            "source": source.lower(),
            "category": category.value,
            "query_type": query_type.lower(),
            "params": normalized_params,
        }

        # Sort keys alphabetically for consistent hashing
        key_json = json.dumps(key_parts, sort_keys=True)

        # Generate MD5 hash
        hash_obj = hashlib.md5(key_json.encode('utf-8'))
        return hash_obj.hexdigest()

    @staticmethod
    def get_cached_result(
        session,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if not expired.

        Args:
            session: SQLAlchemy database session
            cache_key: Cache key to lookup

        Returns:
            Dictionary with cached result data, or None if not found/expired
        """
        # Dynamic import to avoid circular dependency
        from veritas.db.models import OSINTCache

        try:
            cached = (
                session.query(OSINTCache)
                .filter(OSINTCache.query_key == cache_key)
                .filter(OSINTCache.expires_at > datetime.utcnow())
                .first()
            )

            if cached:
                return {
                    "source": cached.source,
                    "result": cached.result,
                    "confidence_score": cached.confidence_score,
                    "cached_at": cached.cached_at,
                    "expires_at": cached.expires_at,
                    "from_cache": True,
                }

            return None

        except Exception as e:
            # Log error but don't fail - just return None to force fresh query
            # In production, this would be logged
            return None

    @staticmethod
    def cache_result(
        session,
        cache_key: str,
        result: OSINTResult,
        source_override: Optional[str] = None
    ) -> None:
        """Store OSINT result in cache with calculated expiration.

        Args:
            session: SQLAlchemy database session
            cache_key: Cache key to store result under
            result: OSINTResult to cache
            source_override: Optional override for source name (used by orchestrators)
        """
        # Dynamic import to avoid circular dependency
        from veritas.db.models import OSINTCache

        source_name = source_override or result.source

        # Get TTL for this source, default to 24h
        ttl = OSINTCache.SOURCE_TTLS.get(source_name, OSINTCache.DEFAULT_TTL)
        expires_at = datetime.utcnow() + ttl

        try:
            # Delete any existing entry with the same cache key
            session.query(OSINTCache).filter(
                OSINTCache.query_key == cache_key
            ).delete()

            # Create new cache entry
            cache_entry = OSINTCache(
                query_key=cache_key,
                source=result.source,
                category=result.category.value,
                result=result.data or {},
                confidence_score=result.confidence_score,
                cached_at=datetime.utcnow(),
                expires_at=expires_at,
            )

            session.add(cache_entry)
            session.commit()

        except Exception as e:
            # Log error but don't fail - cache miss is acceptable
            # In production, this would be logged
            session.rollback()
