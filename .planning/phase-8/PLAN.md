# Plan: Phase 8 - OSINT & CTI Integration

**Phase ID:** 8
**Milestone:** v2.0 Masterpiece Features
**Depends on:** Phase 6 (Vision Agent Enhancement) - Vision Pass 4 needs cross-reference with OSINT
**Status:** pending
**Created:** 2026-02-23

---

## Context

### Current State (Pre-Phase)

**Graph Investigator (`veritas/agents/graph_investigator.py`):**
- Basic WHOIS, DNS, SSL certificate verification
- Tavily search for entity verification
- Simple domain intel gathering
- No external threat intelligence feeds
- No social media presence verification
- No darknet/market exposure detection
- No multi-source cross-referencing with conflict detection
- No confidence scoring for OSINT results

**External Intelligence:**
- Tavily search API (optional, may not be configured)
- VirusTotal (placeholder, not implemented)
- No rate limiting or API quota management
- No caching for OSINT results
- No offline threat feeds

**Frontend:**
- Basic entity details display (domain, WHOIS, DNS)
- No OSINT source breakdown
- No threat exposure indicators
- No intelligence network visualization

### Goal State (Post-Phase)

**15+ OSINT Intelligence Sources:**
- Domain verification (WHOIS, DNS records)
- SSL certificate analysis (expiration, CA, validity)
- Malicious URL checking (VirusTotal, PhishTank)
- Social media presence verification (Twitter/X, LinkedIn, Facebook, Instagram)
- Company database lookups (Crunchbase, OpenCorporates, Companies House UK)
- Threat intelligence feeds (AbuseIPDB, AlienVault OTX, ThreatConnect)
- Reputation scoring (Web of Trust, URLVoid, Google Safe Browsing)
- Email reputation (email verification, breach database check)
- IP reputation (Spamhaus, Project Honey Pot)
- URL analysis (URLscan.io, Hybri)

**Darknet Analyzer (6 Marketplaces via Threat Feeds):**
- Dark marketplace threat feed integration (no direct Tor access)
- Pattern matching against known darknet listings
- Threat exposure indicators
- Marketplace correlation with site entities

**Enhanced Graph Investigator:**
- Multi-source entity profile building
- Cross-reference findings across sources
- Confidence scoring for OSINT data (0-100%)
- Conflict detection and resolution
- Intelligence network generation (entity relationships)

**CTI Intelligence Gathering:**
- Social engineering intelligence gathering patterns (researcher methodology)
- Multi-source verification with confidence scoring
- Flag conflicting information for human review
- CTI-lite: IOCs detection, threat attribution suggestions, MITRE ATT&CK framework
- Smart intelligence network with contextual reasoning

**Progress Streaming:**
- OSINT progress events per source being queried
- Real-time intelligence discovery notifications
- Batched findings for efficiency
- Rate limit status reporting

---

## Critical Implementation Risks (Must Address)

### 1. API Rate Limiting Risk (CRITICAL)

**Risk:** 15+ sources with strict rate limits → throttling or API key revocation

**Analysis:**
- WHOIS: No rate limit, but can be slow
- VirusTotal: 4 requests/minute (free tier), 30/minute (enterprise)
- PhishTank: No public API, requires manual database download
- Social media APIs: Very strict (Twitter: 450 requests/15min, LinkedIn: ~500/day)
- Domain databases: Varied (OpenCorporates: open, Crunchbase: requires signup)
- Threat feeds: AbuseIPDB: 5 requests/hour (free), AlienVault OTX: 20 requests/day (free)

**Problem if unmitigated:**
```
Audit URL → Query 15 sources → Most throttle → Partial results → Unreliable intel
```

**Mitigation Strategy:**

**A. Tiered Source Strategy (Run in Parallel Groups)**
```python
# veritas/agents/graph_investigator/osint_sources.py (new file)
from enum import Enum
from dataclasses import dataclass

class SourcePriority(Enum):
    """Priority for OSINT sources (execute in tier order)."""
    CRITICAL = 1    # Always run fast, no rate limit
    IMPORTANT = 2   # Run with caching, moderate rate limit
    SUPPLEMENTARY = 3 # Run only if time permits, strict rate limits
    OPTIONAL = 4    # Skip if budget exhausted

class SourceRateLimit:
    """Rate limit configuration for each source."""
    requests_per_minute: int
    requests_per_hour: int
    requires_api_key: bool

# Source configurations
OSINT_SOURCES = {
    # Tier 1: CRITICAL (fast, free, unlimited)
    'whois': {
        'priority': SourcePriority.CRITICAL,
        'rate_limit': SourceRateLimit(requests_per_minute=999, requests_per_hour=999, requires_api_key=False),
        'cache_ttl': 7 * 86400  # 7 days
    },
    'dns': {
        'priority': SourcePriority.CRITICAL,
        'rate_limit': SourceRateLimit(requests_per_minute=999, requests_per_hour=999, requires_api_key=False),
        'cache_ttl': 7 * 86400
    },
    'ssl': {
        'priority': SourcePriority.CRITICAL,
        'rate_limit': SourceRateLimit(requests_per_minute=999, requests_per_hour=999, requires_api_key=False),
        'cache_ttl': 7 * 86400
    },

    # Tier 2: IMPORTANT (some rate limits, requires careful handling)
    'virus_total': {
        'priority': SourcePriority.IMPORTANT,
        'rate_limit': SourceRateLimit(requests_per_minute=4, requests_per_hour=60, requires_api_key=True),
        'cache_ttl': 24 * 86400  # 1 day
    },
    'abuseipdb': {
        'priority': SourcePriority.IMPORTANT,
        'rate_limit': SourceRateLimit(requests_per_minute=5, requests_per_hour=10, requires_api_key=True),
        'cache_ttl': 24 * 86400
    },

    # Tier 3: SUPPLEMENTARY (strict limits, use offline databases)
    'phish_tank': {
        'priority': SourcePriority.SUPPLEMENTARY,
        'rate_limit': SourceRateLimit(requests_per_minute=1, requests_per_hour=60, requires_api_key=False),
        'cache_ttl': 7 * 86400  # Use offline database
    },
    'social_twitter': {
        'priority': SourcePriority.SUPPLEMENTARY,
        'rate_limit': SourceRateLimit(requests_per_minute=30, requests_per_hour=450, requires_api_key=False),
        'cache_ttl': 24 * 86400
    },

    # Tier 4: OPTIONAL (external dependencies, skip if time constrained)
    'linkedin': {
        'priority': SourcePriority.OPTIONAL,
        'rate_limit': SourceRateLimit(requests_per_minute=1, requests_per_hour=24, requires_api_key=True),
        'cache_ttl': 7 * 86400
    },
}

# Group for parallel execution
SOURCE_GROUPS = {
    'tier_1': ['whois', 'dns', 'ssl'],
    'tier_2': ['virus_total', 'abuseipdb', 'urlvoid', 'threat_connect'],
    'tier_3': ['phish_tank', 'social_twitter', 'social_facebook'],
    'tier_4': ['linkedin', 'crunchbase']
}
```

**B. Circuit Breaker Pattern for API Calls**
```python
# veritas/core/osint_client.py (new file)
from dataclasses import dataclass
from typing import Dict, Optional
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class QuotaState:
    """Track API quota usage per source."""
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    last_minute_reset: float = 0
    last_hour_reset: float = 0
    blocked_until: float = 0  # If throttled, unblock after this timestamp

    def can_request(self, rate_limit: SourceRateLimit) -> tuple[bool, Optional[str]]:
        """Check if request is allowed."""
        now = time.time()

        # Check if blocked
        if now < self.blocked_until:
            wait_time = self.blocked_until - now
            return False, f"Rate limited, waiting {wait_time:.1f}s"

        # Check minute limit
        if now - self.last_minute_reset > 60:
            self.requests_this_minute = 0
            self.last_minute_reset = now

        if self.requests_this_minute >= rate_limit.requests_per_minute:
            return False, f"Minute rate limit ({rate_limit.requests_per_minute}) exceeded"

        # Check hour limit
        if now - self.last_hour_reset > 3600:
            self.requests_this_hour = 0
            self.last_hour_reset = now

        if self.requests_this_hour >= rate_limit.requests_per_hour:
            return False, f"Hour rate limit ({rate_limit.requests_per_hour}) exceeded"

        return True, None

    def record_request(self):
        """Record that a request was made."""
        self.requests_this_minute += 1
        self.requests_this_hour += 1

class CircuitBreaker:
    """
    Circuit breaker for OSINT API calls.

    Opens after N consecutive failures, stays open for backoff period.
    """

    FAILURE_THRESHOLD = 3
    BACKOFF_SECONDS = 60  # Wait 60s after opening

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.failures = 0
        self.is_open = False
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    def should_attempt_call(self) -> bool:
        """Check if call should be attempted."""
        if not self.is_open:
            return True

        # Check if backoff period expired
        if time.time() - self.last_failure_time > self.BACKOFF_SECONDS:
            self.is_open = False
            self.state = "half-open"
            self.logger.info(f"Circuit breaker {self.source_name} transitioning to half-open")
            return True

        return False

    def record_success(self):
        """Record successful call."""
        self.failures = 0
        if self.state == "half-open":
            self.is_open = False
            self.state = "closed"
            self.logger.info(f"Circuit breaker {self.source_name} closed (success in half-open state)")

    def record_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.FAILURE_THRESHOLD:
            self.is_open = True
            self.state = "open"
            self.logger.error(f"Circuit breaker {self.source_name} opened after {self.failures} failures")

class OSINTClient:
    """Client for OSINT queries with rate limiting and circuit breakers."""

    def __init__(self):
        self.quota_states: Dict[str, QuotaState] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.cache: Dict[str, tuple] = {}  # {key: (data, expiry_time)}

    async def query_source(
        self,
        source_name: str,
        query: str,
        use_cache: bool = True
    ) -> Optional[dict]:
        """
        Query an OSINT source with rate limiting, caching, and circuit breaking.

        Returns: Data from source or None if throttled/failed
        """
        # Check cache
        cache_key = f"{source_name}:{query}"
        if use_cache and cache_key in self.cache:
            data, expiry = self.cache[cache_key]
            if time.time() < expiry:
                logger.debug(f"Cache hit for {source_name}")
                return data
            else:
                del self.cache[cache_key]

        # Get source config
        if source_name not in OSINT_SOURCES:
            logger.error(f"Unknown OSINT source: {source_name}")
            return None

        source_config = OSINT_SOURCES[source_name]
        rate_limit = source_config['rate_limit']

        # Initialize quota state and circuit breaker
        if source_name not in self.quota_states:
            self.quota_states[source_name] = QuotaState()
        if source_name not in self.circuit_breakers:
            self.circuit_breakers[source_name] = CircuitBreaker(source_name)

        quota = self.quota_states[source_name]
        breaker = self.circuit_breakers[source_name]

        # Check circuit breaker
        if not breaker.should_attempt_call():
            logger.warning(f"Circuit breaker open for {source_name}, skipping")
            return None

        # Check rate limit
        can_request, reason = quota.can_request(rate_limit)
        if not can_request:
            logger.warning(f"Rate limited for {source_name}: {reason}")
            return None

        # Execute query
        try:
            data = await self._execute_query(source_name, query)

            # Record success
            quota.record_request()
            breaker.record_success()

            # Cache result
            cache_ttl = source_config.get('cache_ttl', 0)
            if cache_ttl > 0:
                self.cache[cache_key] = (data, time.time() + cache_ttl)

            return data

        except Exception as e:
            # Record failure
            breaker.record_failure()
            logger.error(f"Query failed for {source_name}: {e}")
            return None

    async def _execute_query(self, source_name: str, query: str) -> dict:
        """Execute actual query for a source."""
        # Dispatch to source-specific implementations
        if source_name == 'whois':
            return await self._query_whois(query)
        elif source_name == 'dns':
            return await self._query_dns(query)
        elif source_name == 'ssl':
            return await self._query_ssl(query)
        elif source_name == 'virus_total':
            return await self._query_virus_total(query)
        elif source_name == 'abuseipdb':
            return await self._query_abuseipdb(query)
        # ... other source implementations
        else:
            raise ValueError(f"Unhandled source: {source_name}")

    async def _query_whois(self, domain: str) -> dict:
        """Query WHOIS for domain."""
        import pythonwhois

        result = pythonwhois.get_whois(domain)

        return {
            'source': 'whois',
            'domain': domain,
            'registrar': result.get('registrar', ['Unknown'])[0],
            'creation_date': result.get('creation_date', [None])[0],
            'expiration_date': result.get('expiration_date', [None])[0],
            'registered': result.get('creation_date', [None])[0] is not None
        }

    async def _query_dns(self, domain: str) -> dict:
        """Query DNS records for domain."""
        import dns.resolver

        records = {}

        try:
            records['A'] = [str(rdata) for rdata in dns.resolver.resolve(domain, 'A')]
        except:
            records['A'] = []

        try:
            records['MX'] = [str(rdata.exchange) for rdata in dns.resolver.resolve(domain, 'MX')]
        except:
            records['MX'] = []

        try:
            records['TXT'] = [rdata.to_text() for rdata in dns.resolver.resolve(domain, 'TXT')]
        except:
            records['TXT'] = []

        return {
            'source': 'dns',
            'domain': domain,
            'has_records': len(records['A']) > 0,
            'mail_servers': records['MX'],
            'text_records': records['TXT'],
            'all_records': records
        }

    async def _query_ssl(self, domain: str) -> dict:
        """Query SSL certificate for domain."""
        import ssl
        import socket

        context = ssl.create_default_context()

        try:
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

                    return {
                        'source': 'ssl',
                        'domain': domain,
                        'has_ssl': True,
                        'cert_issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'cert_subject': dict(x[0] for x in cert.get('subject', [])),
                        'valid_from': cert.get('notBefore'),
                        'valid_until': cert.get('notAfter'),
                        'version': cert.get('version'),
                        'is_valid': ssock.version() is not None
                    }
        except Exception as e:
            return {
                'source': 'ssl',
                'domain': domain,
                'has_ssl': False,
                'error': str(e)
            }

    async def _query_virus_total(self, url: str) -> dict:
        """Query VirusTotal for URL analysis."""
        # Requires API key
        if not VIRUS_TOTAL_API_KEY:
            logger.warning("VirusTotal API key not configured")
            return {'source': 'virus_total', 'error': 'API key required'}

        import httpx

        params = {'apikey': VIRUS_TOTAL_API_KEY, 'resource': url}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://www.virustotal.com/vtapi/v2/url/scan',
                data=params,
                timeout=30
            )

            if response.status_code == 429:
                raise RateLimitError("VirusTotal rate limit exceeded")

            response.raise_for_status()
            result = response.json()

            # Get scan report
            scan_response = await client.get(
                'https://www.virustotal.com/vtapi/v2/url/report',
                params=params,
                timeout=30
            )
            scan_response.raise_for_status()
            scan_data = scan_response.json()

            positives = scan_data.get('positives', 0)
            total = scan_data.get('total', 0)

            return {
                'source': 'virus_total',
                'url': url,
                'malicious': positives > 0,
                'detection_rate': f"{positives}/{total}" if total > 0 else "0/0",
                'scan_id': scan_data.get('scan_id'),
                'response_code': scan_results.get('response_code', 0)
            }

    async def _query_abuseipdb(self, ip_address: str) -> dict:
        """Query AbuseIPDB for reputation."""
        if not ABUSEIPDB_API_KEY:
            logger.warning("AbuseIPDB API key not configured")
            return {'source': 'abuseipdb', 'error': 'API key required'}

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://api abuseipdb.com/api/v2/check',
                headers={'Key': ABUSEIPDB_API_KEY},
                params={'ipAddress': ip_address},
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            return {
                'source': 'abuseipdb',
                'ip_address': ip_address,
                'is_malicious': data.get('data', {}).get('abuseConfidenceScore', 0) >= 25,
                'abuse_confidence_score': data.get('data', {}).get('abuseConfidenceScore', 0),
                'last_reported_at': data.get('data', {}).get('lastReportedAt'),
                'total_reports': data.get('data', {}).get('totalReports', 0)
            }
```

**C. Offline Database Fallback for Strict Sources**
```python
# veritas/agents/graph_investigator/offline_feeds.py (new file)
import json
import logging
from pathlib import Path
from typing import Set, List

logger = logging.getLogger(__name__)

class OfflineThreatFeed:
    """Offline threat intelligence database for rate-limited sources."""

    FEEDS_DIR = Path(__file__).parent / 'threat_feeds'

    def __init__(self):
        self.phish_tank_urls: Set[str] = set()
        self.virus_offline_blacklist: Set[str] = set()
        self.malicious_domains: Set[str] = set()
        self._load_offline_feeds()

    def _load_offline_feeds(self):
        """Load offline threat feed databases."""
        # PhishTank (download periodically)
        phish_tank_file = self.FEEDS_DIR / 'phishtank.csv'
        if phish_tank_file.exists():
            self._load_phishtank(phish_tank_file)

        # VirusTotal offline blacklist
        vt_file = self.FEEDS_DIR / 'virustotal_blacklist.json'
        if vt_file.exists():
            self._load_virustotal(vt_file)

        # Malicious domains list
        malicious_file = self.FEEDS_DIR / 'malicious_domains.txt'
        if malicious_file.exists():
            self._load_malicious_domains(malicious_file)

        logger.info(f"Loaded offline threat feeds: {len(self.phish_tank_urls)} PhishTank URLs")

    def _load_phishtank(self, filepath: Path):
        """Load PhishTank CSV database."""
        import csv

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url')
                    if url and row.get('verified', '') == 'yes':
                        self.phish_tank_urls.add(url)
        except Exception as e:
            logger.error(f"Failed to load PhishTank database: {e}")

    def _load_virustotal(self, filepath: Path):
        """Load VirusTotal offline blacklist."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.virus_offline_blacklist.update(data.get('malicious_urls', []))
        except Exception as e:
            logger.error(f"Failed to load VirusTotal database: {e}")

    def _load_malicious_domains(self, filepath: Path):
        """Load malicious domains text file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.malicious_domains.update(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to load malicious domains: {e}")

    def check_url_offline(self, url: str) -> dict:
        """Check URL against offline threat feeds."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc

        findings = []

        if url in self.phish_tank_urls:
            findings.append({
                'feed': 'phishtank',
                'malicious': True,
                'confidence': 90  # High confidence for verified PhishTank
            })

        if url in self.virus_offline_blacklist:
            findings.append({
                'feed': 'virustotal_offline',
                'malicious': True,
                'confidence': 85
            })

        if domain in self.malicious_domains:
            findings.append({
                'feed': 'malicious_domains',
                'malicious': True,
                'confidence': 75
            })

        return {
            'offline_check': True,
            'malicious': any(f['malicious'] for f in findings),
            'findings': findings,
            'confidence': max(f.get('confidence', 0) for f in findings) if findings else 0
        }

    def update_feeds(self):
        """
        Download and update offline threat feeds.

        Call this periodically (e.g., daily or weekly).
        """
        import httpx

        # Download PhishTank
        try:
            phish_tank_url = "https://data.phishtank.com/data/online-valid.csv.bz2"
            # ... decompress and save
        except Exception as e:
            logger.error(f"Failed to update PhishTank: {e}")

        # ... other feed updates
```

**Test Strategy:**
- Unit test rate limiting with mock quota states
- Test circuit breaker opening/closing with failures
- Integration test with 10 sources, verify throttling works

---

### 2. Darknet Analysis Legal Risk (HIGH)

**Risk:** Direct Tor network access to darknet marketplaces is illegal in many jurisdictions

**Problem:**
- Requirement OSINT-02: "Darknet analyzer (6 marketplaces)"
- Direct .onion scraping = potential legal liability
- Many jurisdictions prohibit Tor network access for commercial purposes

**Solution:** Use Threat Feeds Instead of Direct Access

**Strategy:**
- Don't scrape darknet directly
- Subscribe to (or use free) threat intelligence feeds that track darknet activity
- Pattern match domain entities against known darknet listings
- Use offline databases of known dark market domains

**Implementation:**
```python
# veritas/agents/graph_investigator/darknet_intel.py (new file)
import logging
from typing import List, Dict, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class DarknetThreatFeed:
    """
    Darknet intelligence from threat feeds (no direct Tor access).

    Uses offline databases of known dark marketplace domains and patterns.
    """

    # Known dark marketplace TLDs and patterns (never access directly)
    DARKNET_TLDS = {
        '.onion',  # Tor hidden services
        '.i2p',    # I2P network
    }

    # Known dark marketplace patterns (from threat feeds)
    MARKETPLACE_PATTERNS = {
        'alpha', 'dream', 'wall_street', 'berlusconi', 'monopoly',
        'cannazon', 'darknet', 'onion_market', 'darkmarket'
    }

    def __init__(self, offline_feed: OfflineThreatFeed):
        self.offline_feed = offline_feed
        self.known_market_domains: Set[str] = set()
        self._load_market_domain_database()

    def _load_market_domain_database(self):
        """Load database of known dark marketplace domains (from threat feeds)."""
        market_file = self.offline_feed.FEEDS_DIR / 'darknet_markets.txt'

        if market_file.exists():
            with open(market_file, 'r', encoding='utf-8') as f:
                self.known_market_domains.update(line.strip() for line in f if line.strip())

            logger.info(f"Loaded {len(self.known_market_domains)} known dark marketplace domains")

    def analyze_darknet_exposure(self, domain: str, entity_keywords: List[str]) -> dict:
        """
        Analyze domain for darknet exposure via threat feeds.

        NEVER connects to Tor network directly.

        Args:
            domain: Domain being analyzed
            entity_keywords: Keywords from site (company names, brands, products)

        Returns:
            {
                'has_darknet_exposure': bool,
                'marketplace_matches': List[str],
                'entity_in_darknet': bool,
                'confidence': float
            }
        """
        findings = {
            'has_darknet_exposure': False,
            'marketplace_matches': [],
            'entity_in_darknet': False,
            'confidence': 0.0
        }

        # Check 1: Is domain itself a known marketplace?
        if domain in self.known_market_domains:
            findings['has_darknet_exposure'] = True
            findings['marketplace_matches'].append(domain)
            findings['confidence'] = 100

        # Check 2: Does domain use darknet TLD? (should not happen for .com/.org but check anyway)
        from urllib.parse import urlparse
        parsed = urlparse(f"https://{domain}")  # Parse to get TLD
        if any(parsed.netloc.endswith(tld) for tld in self.DARKNET_TLDS):
            findings['has_darknet_exposure'] = True
            findings['marketplace_matches'].append(f"Darknet TLD detected: {parsed.netloc}")
            findings['confidence'] = 95

        # Check 3: Are site entities mentioned in threat feeds?
        # This requires threat feed databases that track marketplace listings
        entity_threat_matches = self._check_entities_in_threat_feeds(entity_keywords)
        if entity_threat_matches:
            findings['has_darknet_exposure'] = True
            findings['entity_in_darknet'] = True
            findings['marketplace_matches'].extend(entity_threat_matches)
            findings['confidence'] = 70

        return findings

    def _check_entities_in_threat_feeds(self, keywords: List[str]) -> List[str]:
        """
        Check if site entities appear in darknet threat feeds.

        Returns: List of threat feed matches
        """
        matches = []

        # This would query threat intelligence databases that track dark marketplace listings
        # For now, we check offline keyword databases

        # Load threat feed keyword databases
        market_keywords_file = self.offline_feed.FEEDS_DIR / 'darknet_keywords.txt'
        if not market_keywords_file.exists():
            return matches

        with open(market_keywords_file, 'r', encoding='utf-8') as f:
            market_keywords = set(line.strip().lower() for line in f)

        # Check if site keywords match darknet keywords
        for keyword in keywords:
            if keyword.lower() in market_keywords:
                matches.append(f"Entity '{keyword}' found in darknet threat feeds")

        return matches

    def get_darknet_intel_summary(self) -> dict:
        """
        Get summary of darknet intelligence.

        For frontend display.
        """
        return {
            'total_known_markets': len(self.known_market_domains),
            'market_sources': ['ThreatFox', 'CyberChef Dark DB', 'Malvertising DB'],
            'legal_compliance': 'Uses threat feeds only, no direct Tor access',
            'last_updated': self._get_feed_timestamp()
        }

    def _get_feed_timestamp(self) -> str:
        """Get timestamp of last feed update."""
        market_file = self.offline_feed.FEEDS_DIR / 'darknet_markets.txt'

        if market_file.exists():
            import time
            return time.strftime('%Y-%m-%d', time.gmtime(market_file.stat().st_mtime))

        return 'Unknown'
```

**Test Strategy:**
- Verify no Tor connections are made (use mock network)
- Test domain matching against known market list
- Test keyword matching against threat feed database

---

### 3. Cross-Source Conflict Detection Complexity (MEDIUM)

**Risk:** Multiple sources disagree → how to resolve?

**Example Conflicts:**
- VirusTotal: "Malicious (3/56 scanners detect)"
- URLVoid: "Clean (domain reputation 0/0)"
- Web of Trust: "Excellent reputation (95/100)"

**Gap:** Which source to trust? How to combine conflicting signals?

**Solution:** Source Trust Scoring + Confidence Weighted Aggregation

**Implementation:**
```python
# veritas/agents/graph_investigator/conflict_resolver.py (new file)
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class SourceTrustLevel(Enum):
    """Trust level for OSINT sources."""
    HIGH = 1       # Authoritative, well-maintained (VirusTotal, AbuseIPDB)
    MEDIUM = 2     # Community-driven, potentially noisy (URLVoid, Web of Trust)
    LOW = 3        # Reputation-based, may be outdated (domain reputation lists)
    UNKNOWN = 4    # Unknown or unverified sources

@dataclass
class SourceTrustWeight:
    """Trust weight and confidence for OSINT source."""
    source: str
    trust_level: SourceTrustLevel
    base_weight: float  # 0-1, higher = more trusted
    confidence_bias: float  # Boost confidence when source reports malicious

# Source trust configuration (based on community consensus)
SOURCE_TRUST_WEIGHTS = {
    # HIGH trust (authoritative)
    'virus_total': SourceTrustWeight('virus_total', SourceTrustLevel.HIGH, 0.9, 1.2),
    'abuseipdb': SourceTrustWeight('abuseipdb', SourceTrustLevel.HIGH, 0.85, 1.1),
    'phishtank': SourceTrustWeight('phishtank', SourceTrustLevel.HIGH, 0.9, 1.3),

    # MEDIUM trust (community-driven)
    'urlvoid': SourceTrustWeight('urlvoid', SourceTrustLevel.MEDIUM, 0.6, 1.0),
    'web_of_trust': SourceTrustWeight('web_of_trust', SourceTrustLevel.MEDIUM, 0.55, 0.9),
    'urlscan_io': SourceTrustWeight('urlscan_io', SourceTrustLevel.MEDIUM, 0.7, 1.1),

    # LOW trust (reputation lists)
    'domain_reputation': SourceTrustWeight('domain_reputation', SourceTrustLevel.LOW, 0.4, 0.8),

    # Technical sources (not reputation, but factual)
    'whois': SourceTrustWeight('whois', SourceTrustLevel.HIGH, 1.0, 1.0),  # Factual
    'dns': SourceTrustWeight('dns', SourceTrustLevel.HIGH, 1.0, 1.0),      # Factual
    'ssl': SourceTrustWeight('ssl', SourceTrustLevel.HIGH, 1.0, 1.0),      # Factual
}

class ConflictResolver:
    """
    Resolves conflicts between OSINT sources using trust scoring.

    Implements QUAL-01: Multi-source verification with conflict detection.
    """

    def __init__(self):
        self.source_weights = SOURCE_TRUST_WEIGHTS

    def resolve_conflicts(self, osint_results: Dict[str, dict]) -> dict:
        """
        Resolve conflicts between OSINT sources.

        Args:
            osint_results: {source_name: result_data}

        Returns:
            {
                'overall_malicious': bool,
                'confidence': float,
                'conflicting_sources': List[str],
                'trust_breakdown': dict,
                'resolution_notes': List[str]
            }
        """
        # Classify results by malignancy
        malicious_sources = [s for s, r in osint_results.items() if r.get('malicious', False)]
        clean_sources = [s for s, r in osint_results.items() if not r.get('malicious', False)]

        # Calculate weighted confidence
        weighted_malicious_score = 0.0
        weighted_clean_score = 0.0

        for source, result in osint_results.items():
            if source not in self.source_weights:
                logger.warning(f"Unknown source {source}, using default trust")
                trust_weight = SourceTrustWeight(source, SourceTrustLevel.UNKNOWN, 0.5, 1.0)
            else:
                trust_weight = self.source_weights[source]

            # Get source's reported confidence (if available)
            source_confidence = result.get('confidence', 0.5)

            # Apply trust weight and confidence bias
            if result.get('malicious', False):
                contribution = trust_weight.base_weight * source_confidence * trust_weight.confidence_bias
                weighted_malicious_score += contribution
            else:
                contribution = trust_weight.base_weight * source_confidence
                weighted_clean_score += contribution

        # Normalize scores
        total_score = weighted_malicious_score + weighted_clean_score
        if total_score > 0:
            malicious_ratio = weighted_malicious_score / total_score
        else:
            malicious_ratio = 0.0

        # Determine final verdict
        overall_malicious = malicious_ratio >= 0.5
        confidence = malicious_ratio * 100 if overall_malicious else (1 - malicious_ratio) * 100

        # Detect conflicts
        conflicting = []
        if malicious_sources and clean_sources:
            conflicting = [
                (malicious_sources[0] if malicious_sources else '?', clean_sources[0] if clean_sources else '?')
            ]

        resolution_notes = self._generate_resolution_notes(
            malicious_sources,
            clean_sources,
            malicious_ratio,
            conflicting
        )

        return {
            'overall_malicious': overall_malicious,
            'confidence': round(confidence, 1),
            'conflicting_sources': conflicting,
            'trust_breakdown': {
                'malicious_count': len(malicious_sources),
                'clean_count': len(clean_sources),
                'weighted_malicious_score': round(weighted_malicious_score, 3),
                'weighted_clean_score': round(weighted_clean_score, 3),
                'malicious_ratio': round(malicious_ratio, 3)
            },
            'resolution_notes': resolution_notes
        }

    def _generate_resolution_notes(
        self,
        malicious_sources: List[str],
        clean_sources: List[str],
        malicious_ratio: float,
        conflicting: List[tuple]
    ) -> List[str]:
        """Generate human-readable resolution notes."""
        notes = []

        if not conflicting:
            notes.append("All sources in agreement")
        else:
            notes.append("⚠️ Conflicting reports from sources:")

            # Compare highest-trust malicious vs highest-trust clean
            if malicious_sources:
                best_malicious = max(malicious_sources, key=lambda s: self.source_weights.get(s, 0.5))
                notes.append(f"  - Malicious (trusted): {best_malicious}")

            if clean_sources:
                best_clean = max(clean_sources, key=lambda s: self.source_weights.get(s, 0.5))
                notes.append(f"  - Clean (trusted): {best_clean}")

            # Explain resolution
            if malicious_ratio >= 0.5:
                notes.append(f"Resolution: Trusted malicious sources outweigh clean sources ({malicious_ratio:.0%})")
            else:
                notes.append(f"Resolution: Trusted clean sources outweigh malicious sources ({malicious_ratio:.0%})")

        # Add notes about source quality
        high_trust_malicious = [s for s in malicious_sources if self.source_weights.get(s, SourceTrustLevel.UNKNOWN) == SourceTrustLevel.HIGH]
        if high_trust_malicious:
            notes.append(f"High-trust sources reporting malicious: {', '.join(high_trust_malicious)}")

        return notes
```

**Test Strategy:**
- Unit test conflict resolution with 2 conflicting sources
- Test weight calculation with different trust levels
- Verify correct source prioritization (HIGH trust beats MEDIUM trust)

---

## Dependencies (What Must Complete First)

### Internal (Within Phase 8)
1. **OSINTClient → ConflictResolver**: Gather all OSINT results first, then resolve conflicts
2. **CircuitBreaker → Rate limiting**: Circuit breaker opens before rate limit hits
3. **OfflineThreatFeed → ThreatIntel**: Offline feeds need to be loaded before darknet analysis

### External (From Previous Phases)
1. **Phase 1-5 (v1.0 Core)**: ✅ DONE
2. **Phase 6 (Vision Agent Enhancement)**: Vision Pass 4 cross-reference will consume OSINT data
3. **Phase 7 (Quality Foundation)**: Multi-source validation will include OSINT as a "source"

### Blocks for Future Phases
1. **Phase 9 (Judge System)**: Judge uses OSINT findings for technical verdict data
2. **Phase 10 (Cybersecurity)**: Darknet threat detection integrates with security modules
3. **Phase 11 (Showcase)**: Intel network visualization needs OSINT entity relationships

---

## Task Breakdown (With File Locations)

### 8.1 Implement OSINTClient with Rate Limiting

**Files:**
- `veritas/core/osint_client.py` (new file)
- `veritas/config/settings.py` (add API key settings)

**Tasks:**
```python
# veritas/core/osint/client.py (new file)
"""OSINT client with rate limiting, caching, and circuit breakers."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

@dataclass
class QuotaState:
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    last_minute_reset: float = 0.0
    last_hour_reset: float = 0.0
    blocked_until: float = 0.0

class OSINTClient:
    """Client for OSINT queries with rate limiting and caching."""

    SOURCE_CONFIGS = {
        'whois': {'rpm': 999, 'rph': 999, 'cache_ttl': 7*86400},
        'dns': {'rpm': 999, 'rph': 999, 'cache_ttl': 7*86400},
        'ssl': {'rpm': 999, 'rph': 999, 'cache_ttl': 7*86400},
        'virustotal': {'rpm': 4, 'rph': 60, 'cache_ttl': 24*86400},
        'abuseipdb': {'rpm': 5, 'rph': 10, 'cache_ttl': 24*86400},
        'phishtank': {'rpm': 1, 'rph': 60, 'cache_ttl': 7*86400},
    }

    SOURCE_GROUPS = {
        'tier_1': ['whois', 'dns', 'ssl'],
        'tier_2': ['virustotal', 'abuseipdb', 'urlvoid'],
        'tier_3': ['phishtank'],
    }

    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.quota_states: Dict[str, QuotaState] = {}
        self.cache: Dict[str, Tuple[dict, float]] = {}
        self.offline_feeds: OfflineThreatFeed = OfflineThreatFeed()

    async def query_all_sources(self, url: str) -> Dict[str, dict]:
        """Query all OSINT sources for URL (prioritized)."""
        results = {}

        # Extract domain
        domain = urlparse(url).netloc

        # Query tier 1 (fast, no rate limits) in parallel
        tier_1_tasks = [
            self.query_source(src, domain) for src in ['whois', 'dns', 'ssl']
        ]
        tier_1_results = await asyncio.gather(*tier_1_tasks, return_exceptions=True)

        for i, src in enumerate(['whois', 'dns', 'ssl']):
            if not isinstance(tier_1_results[i], Exception):
                results[src] = tier_1_results[i]

        # Query tier 2 (rate limited) with delays
        await asyncio.sleep(1)  # Rate limit buffer
        results.update(await self._query_tier(url))

        # Query tier 3 (strict limits, optional)
        if self._should_query_tier_3():
            await asyncio.sleep(0.5)
            results.update(await self._query_tier_3(url))

        return results

    async def query_source(self, source: str, query: str) -> Optional[dict]:
        """Query single source with circuit breaking."""
        # Check cache
        cache_key = f"{source}:{query}"
        if cache_key in self.cache:
            data, expiry = self.cache[cache_key]
            if time.time() < expiry:
                return data

        # Check quota
        if source not in self.quota_states:
            self.quota_states[source] = QuotaState()
        quota = self.quota_states[source]

        config = self.SOURCE_CONFIGS.get(source, {})
        if quota.requests_this_minute >= config.get('rpm', 999):
            logger.warning(f"Rate limited {source}")
            return None

        # Execute query
        try:
            result = await self._execute_source_query(source, query)

            # Update quota
            quota.requests_this_minute += 1

            # Cache
            ttl = config.get('cache_ttl', 0)
            if ttl > 0:
                self.cache[cache_key] = (result, time.time() + ttl)

            return result

        except Exception as e:
            logger.error(f"{source} query failed: {e}")
            return None

    async def _execute_source_query(self, source: str, query: str) -> dict:
        """Dispatch to source-specific implementation."""
        if source == 'whois':
            return await self._whois(query)
        elif source == 'dns':
            return await self._dns(query)
        elif source == 'ssl':
            return await self._ssl(query)
        elif source == 'virustotal':
            return await self._virustotal(query)
        elif source == 'abuseipdb':
            return await self._abuseipdb(query)
        elif source == 'phishtank':
            return await self._phishtank_offline(query)
        else:
            raise ValueError(f"Unknown source: {source}")

    async def _whois(self, domain: str) -> dict:
        import pythonwhois
        result = pythonwhois.get_whois(domain)
        return {
            'source': 'whois',
            'domain': domain,
            'registrar': result.get('registrar', ['Unknown'])[0],
            'created': str(result.get('creation_date', [None])[0]),
            'expires': str(result.get('expiration_date', [None])[0]),
        }

    # ... other source implementations (dns, ssl, virustotal, etc.)
```

---

### 8.2 Implement OfflineThreatFeed

**File:**
- `veritas/core/osint/offline_feeds.py` (new file)

**Tasks:**
```python
# veritas/core/osint/offline_feeds.py (new file)
"""Offline threat intelligence databases for rate-limited OSINT sources."""

import csv
import json
from pathlib import Path
from typing import Set, List, Dict
import logging

logger = logging.getLogger(__name__)

class OfflineThreatFeed:
    """Offline threat intelligence databases."""

    FEEDS_DIR = Path(__file__).parent.parent / 'data' / 'threat_feeds'

    def __init__(self):
        self.phish_tank_urls: Set[str] = set()
        self.malicious_domains: Set[str] = set()
        self.darknet_markets: Set[str] = set()
        self.darknet_keywords: Set[str] = set()
        self._load_feeds()

    def _load_feeds(self):
        """Load all offline threat feed databases."""
        self.FEEDS_DIR.mkdir(parents=True, exist_ok=True)

        self._load_phishtank()
        self._load_malicious_domains()
        self._load_darknet_data()

        logger.info(f"Loaded offline feeds: {len(self.phish_tank_urls)} PhishTank, {len(self.malicious_domains)} malicious")

    def _load_phishtank(self):
        """Load PhishTank database."""
        phish_file = self.FEEDS_DIR / 'phishtank.csv'

        if not phish_file.exists():
            logger.info("PhishTank database not found, will need to download")
            return

        with open(phish_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('verified', '') == 'yes':
                    self.phish_tank_urls.add(row.get('url', ''))

    def _load_malicious_domains(self):
        """Load malicious domains database."""
        mal_file = self.FEEDS_DIR / 'malicious_domains.txt'

        if not mal_file.exists():
            return

        with open(mal_file, 'r', encoding='utf-8') as f:
            self.malicious_domains.update(line.strip() for line in f if line.strip())

    def _load_darknet_data(self):
        """Load dark marketplace and keyword databases."""
        market_file = self.FEEDS_DIR / 'darknet_markets.txt'
        keyword_file = self.FEEDS_DIR / 'darknet_keywords.txt'

        if market_file.exists():
            with open(market_file, 'r', encoding='utf-8') as f:
                self.darknet_markets.update(line.strip() for line in f)

        if keyword_file.exists():
            with open(keyword_file, 'r', encoding='utf-8') as f:
                self.darknet_keywords.update(line.strip().lower() for line in f)

    def check_url(self, url: str) -> Dict:
        """Check URL against offline threat feeds."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc

        findings = []

        if url in self.phish_tank_urls:
            findings.append(('phishtank', 90, 'Verified phishing URL'))

        if domain in self.malicious_domains:
            findings.append(('malicious_domains', 75, 'Domain in malicious database'))

        return {
            'url': url,
            'threat_detected': len(findings) > 0,
            'findings': findings,
            'confidence': max(f[1] for f in findings) if findings else 0
        }
```

---

### 8.3 Implement Darknet Threat Feed Integration

**File:**
- `veritas/agents/graph_investigator/darknet_intel.py` (new file)

**Tasks:**
```python
# veritas/agents/graph_investigator/darknet_intel.py (new file)
"""Darknet intelligence via threat feeds (no direct Tor access)."""

import logging
from typing import List, Dict, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class DarknetThreatIntel:
    """Darknet intelligence using threat feeds only (legal compliance)."""

    MARKETPLACE_PATTERNS = [
        'alpha', 'dream', 'wall_street', 'berlusconi', 'cannazon',
        'monopoly', 'darknet', 'onion_market'
    ]

    def __init__(self, offline_feed: OfflineThreatFeed):
        self.offline_feed = offline_feed
        self.known_markets = self._load_market_database()

    def _load_market_database(self) -> Set[str]:
        """Load known dark marketplace domains from threat feeds."""
        market_file = self.offline_feed.FEEDS_DIR / 'darknet_markets.txt'
        if not market_file.exists():
            return set()

        with open(market_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())

    def analyze_exposure(self, domain: str, entity_keywords: List[str]) -> dict:
        """Analyze darknet exposure using threat feeds (no Tor access)."""
        findings = {
            'has_exposure': False,
            'marketplace_matches': [],
            'entity_matches': [],
            'confidence': 0.0,
            'legal_note': 'Uses threat feeds only, no direct Tor access'
        }

        # Check domain against known markets
        if domain in self.known_markets:
            findings['has_exposure'] = True
            findings['marketplace_matches'].append(f"Domain in known marketplace list")
            findings['confidence'] = 100

        # Check entity keywords against threat feed databases
        for keyword in entity_keywords:
            if keyword.lower() in self.offline_feed.darknet_keywords:
                findings['has_exposure'] = True
                findings['entity_matches'].append(f"Entity '{keyword}' appears in darknet threat data")
                findings['confidence'] = max(findings['confidence'], 70)

        return findings
```

---

### 8.4 Implement ConflictResolver for Cross-Source Validation

**File:**
- `veritas/agents/graph_investigator/conflict_resolver.py` (new file)

**Tasks:**
```python
# veritas/agents/graph_investigator/conflict_resolver.py (new file)
"""Resolves conflicts between OSINT sources using trust scoring."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class SourceTrustLevel(Enum):
    HIGH = 1    # VirusTotal, AbuseIPDB, PhishTank
    MEDIUM = 2  # URLVoid, WOT, URLscan
    LOW = 3     # Reputation lists

@dataclass
class SourceWeight:
    trust: SourceTrustLevel
    weight: float
    bias: float

# Source trust configuration
SOURCE_WEIGHTS = {
    'virustotal': SourceWeight(SourceTrustLevel.HIGH, 0.9, 1.2),
    'abuseipdb': SourceWeight(SourceTrustLevel.HIGH, 0.85, 1.1),
    'phishtank': SourceWeight(SourceTrustLevel.HIGH, 0.9, 1.3),
    'urlvoid': SourceWeight(SourceTrustLevel.MEDIUM, 0.6, 1.0),
    'wot': SourceWeight(SourceTrustLevel.MEDIUM, 0.55, 0.9),
    'domain_rep': SourceWeight(SourceTrustLevel.LOW, 0.4, 0.8),
}

class ConflictResolver:
    """Resolves conflicts between OSINT sources."""

    def resolve(self, results: Dict[str, dict]) -> dict:
        """Resolve conflicts across all OSINT results."""
        malicious = [s for s, r in results.items() if r.get('malicious', False)]
        clean = [s for s, r in results.items() if not r.get('malicious', False)]

        # Calculate weighted scores
        mal_score = self._weighted_score(malicious, results, True)
        clean_score = self._weighted_score(clean, results, False)

        total = mal_score + clean_score
        mal_ratio = mal_score / total if total > 0 else 0.0

        return {
            'malicious': mal_ratio >= 0.5,
            'confidence': mal_ratio * 100 if mal_ratio >= 0.5 else (1 - mal_ratio) * 100,
            'conflict': bool(malicious and clean),
            'sources': {'malicious': len(malicious), 'clean': len(clean)},
            'resolution': self._explain_resolution(malicious, clean, mal_ratio)
        }

    def _weighted_score(self, sources: List[str], results: Dict, malicious: bool) -> float:
        """Calculate weighted confidence score."""
        score = 0.0
        for s in sources:
            if s not in SOURCE_WEIGHTS:
                continue

            w = SOURCE_WEIGHTS[s]
            conf = results[s].get('confidence', 0.5)

            if malicious:
                score += w.weight * conf * w.bias
            else:
                score += w.weight * conf

        return score

    def _explain_resolution(self, mal: List[str], clean: List[str], ratio: float) -> List[str]:
        """Generate human-readable resolution explanation."""
        notes = []

        if not mal or not clean:
            notes.append("All sources agree")
        else:
            notes.append("⚠️ Conflicting reports detected:")
            best_mal = max(mal, key=lambda s: SOURCE_WEIGHTS.get(s, SourceWeight(SourceTrustLevel.MEDIUM, 0.5, 1.0)).weight)
            best_clean = max(clean, key=lambda s: SOURCE_WEIGHTS.get(s, SourceWeight(SourceTrustLevel.MEDIUM, 0.5, 1.0)).weight)
            notes.append(f"  Malicious (trusted): {best_mal}")
            notes.append(f"  Clean (trusted): {best_clean}")
            notes.append(f"Resolution: Weighted average favors {'malicious' if ratio >= 0.5 else 'clean'} ({ratio:.0%})")

        return notes
```

---

### 8.5 Integrate into Enhanced Graph Investigator

**File:**
- `veritas/agents/graph_investigator.py` (rewrite)

**Tasks:**
```python
class GraphInvestigator:
    """Enhanced Graph Investigator with OSINT and CTI."""

    def __init__(self, nim_client: NIMClient):
        self.nim_client = nim_client
        self.osint_client = OSINTClient(api_keys=OSINT_API_KEYS)
        self.offline_feeds = OfflineThreatFeed()
        self.darknet_intel = DarknetThreatIntel(self.offline_feeds)
        self.conflict_resolver = ConflictResolver()

    async def investigate(self, url: str, scout_result: ScoutResult = None) -> GraphResult:
        """Investigate entity with full OSINT and CTI analysis."""

        # Extract domain
        domain = urlparse(url).netloc

        # Query OSINT sources
        osint_results = await self.osint_client.query_all_sources(url)

        # Check offline threat feeds
        offline_threat = self.offline_feeds.check_url(url)
        osint_results['offline_feeds'] = offline_threat

        # Darknet threat analysis (via threat feeds)
        entity_keywords = self._extract_entity_keywords(scout_result)
        darknet_analysis = self.darknet_intel.analyze_exposure(domain, entity_keywords)

        # Resolve conflicts
        conflict_resolution = self.conflict_resolver.resolve(osint_results)

        # Build entity profile
        entity_profile = self._build_entity_profile(
            domain=domain,
            osint_results=osint_results,
            darknet_analysis=darknet_analysis,
            conflict_resolution=conflict_resolution
        )

        return GraphResult(
            domain=domain,
            verifications=self._extract_verifications(osint_results),
            entity_profile=entity_profile,
            darknet_exposure=darknet_analysis,
            conflict_resolution=conflict_resolution,
            intel_sources=list(osint_results.keys())
        )
```

---

## Test Strategy

### Unit Tests

**Test: Rate limiting respects source limits**
```python
@pytest.mark.asyncio
async def test_osint_client_rate_limiting():
    client = OSINTClient()

    # Query 5 times (exceeds VirusTotal's 4/min)
    results = []
    for i in range(5):
        result = await client.query_source('virustotal', 'http://test.com')
        results.append(result)

    # 5th request should be None (rate limited)
    assert results[4] is None
```

**Test: Conflict resolver priorities high-trust sources**
```python
def test_conflict_resolver_trust_levels():
    resolver = ConflictResolver()

    results = {
        'virustotal': {'malicious': True, 'confidence': 0.7},  # HIGH trust
        'urlvoid': {'malicious': False, 'confidence': 0.8},     # MEDIUM trust
    }

    resolution = resolver.resolve(results)

    # High-trust malicious should win
    assert resolution['malicious'] == True
    assert 'High-trust sources' in str(resolution['resolution'])
```

---

### Performance Tests

**Test: OSINT client respects source limits**
```python
@pytest.mark.asyncio
async def test_rate_limiting_enforcement():
    client = OSINTClient(api_keys={'virustotal': 'test_key'})

    # Query 5 times (exceeds VirusTotal's 4/min)
    results = []
    for i in range(5):
        result = await client.query_source('virustotal', 'http://test.com')
        results.append(result)

    # 5th request should be None (rate limited)
    assert results[4] is None
```

**Test: Circuit breaker opening/closing under load**
```python
@pytest.mark.asyncio
async def test_circuit_breaker_behavior():
    client = OSINTClient()

    # Trigger 5 consecutive failures to hit threshold
    for i in range(5):
        await client.query_source('virustotal', 'http://test.com',
                                           mock_fail=True)

    # Circuit breaker should be open after 3rd failure
    assert client.circuit_breakers['virustotal'].is_open == True

    # Reset breaker would allow 1 request after cooldown
    client.circuit_breakers['virustotal'].reset()
    result = await client.query_source('virustotal', 'http://test.com')
    assert result is not None  # Should succeed after reset
```

**Test: Offline feeds fallback efficiency**
```python
def test_offline_threat_feeds_provides_fallback():
    feeds = OfflineThreatFeed()
    feeds._load_phishtank()
    feeds._load_malicious_domains()

    # Verify fallback works - query non-existent URL
    result = feeds.check_url('http://unknown-site.com')

    # Should still return some result even without API calls
    assert isinstance(result, dict)
```

**Test: Performance test for offline feed loading**
```python
import time
import tempfile
from pathlib import Path

@pytest.mark.asyncio
async def test_offline_threat_feed_performance():
    """Measure time to load/benchmark offline threat feeds."""
    # Create temporary test data
    with tempfile.TemporaryDirectory() as temp_dir:
        feeds_dir = Path(temp_dir)

        # Create test PhishTank file with 1000 URLs
        phish_file = feeds_dir / 'phishtank.csv'
        with open(phish_file, 'w') as f:
            f.write('url,submitted_by,verified\n')
            for i in range(1000):
                f.write(f'http://phishing{i}.com,user{i},yes\n')

        # Create test malicious domains file with 500 entries
        mal_file = feeds_dir / 'malicious_domains.txt'
        with open(mal_file, 'w') as f:
            for i in range(500):
                f.write(f'malicious{i}.com\n')

        # Load feeds and measure time
        feeds = OfflineThreatFeed(feeds_dir=feeds_dir)

        start = time.time()
        feeds._load_feeds()
        load_time = time.time() - start

        # Should load within 1 second for this dataset size
        assert load_time < 1.0, f"Feed loading took {load_time:.2f}s, expected < 1s"

        # Verify all entries loaded
        assert len(feeds.phish_tank_urls) == 1000
        assert len(feeds.malicious_domains) == 500

        # Test lookup performance - should be < 1ms
        start = time.time()
        result = feeds.check_url('http://phishing500.com')
        lookup_time = time.time() - start

        assert lookup_time < 0.001, f"Feed lookup took {lookup_time*1000:.2f}ms, expected < 1ms"
        assert result['threat_detected'] == True
```

**Test: Integration test for parallel OSINT queries**
```python
@pytest.mark.asyncio
async def test_parallel_osint_queries_complete_within_constraints():
    """Verify 10+ concurrent queries complete within time constraints."""
    client = OSINTClient(api_keys={'virustotal': 'test_key', 'abuseipdb': 'test_key'})

    # Create 12 concurrent queries (mix of tier 1, 2, 3 sources)
    urls = [f"http://test{i}.com" for i in range(12)]
    queries = []

    # Mix of tier 1 (unlimited), tier 2 (rate limited), tier 3 (optional)
    for url in urls:
        queries.append(client.query_source('whois', url))      # Tier 1
        queries.append(client.query_source('dns', url))        # Tier 1
        queries.append(client.query_source('ssl', url))        # Tier 1
        queries.append(client.query_source('virustotal', url)) # Tier 2
        queries.append(client.query_source('abuseipdb', url))  # Tier 2

    # Execute all queries concurrently
    start = time.time()
    results = await asyncio.gather(*queries, return_exceptions=True)
    elapsed = time.time() - start

    # Parallel execution should complete faster than sequential
    # Sequential would be ~5 seconds per URL * 12 = 60 seconds
    # Parallel should be ~15-20 seconds (limited by rate limits)
    assert elapsed < 25.0, f"Parallel queries took {elapsed:.2f}s, expected < 25s"

    # Verify tier 1 (unlimited) sources all complete
    tier_1_results = results[::5]  # Every 5th result is whois
    tier_1_complete = sum(1 for r in tier_1_results if not isinstance(r, Exception) and r is not None)
    assert tier_1_complete == 12, f"Only {tier_1_complete}/12 tier 1 queries completed"

    # Verify tier 2 (rate limited) sources respect limits (some may be None)
    tier_2_results = [r for i, r in enumerate(results) if i % 5 in [3, 4]]
    tier_2_complete = sum(1 for r in tier_2_results if r is not None)
    assert tier_2_complete >= 6, f"Only {tier_2_complete}/24 tier 2 queries completed (expected at least 6)"
```

**Test: Circuit breaker behavior under load (stress test)**
```python
@pytest.mark.asyncio
async def test_circuit_breaker_stress_multiple_concurrent_failures():
    """Stress test circuit breaker with multiple concurrent failures."""
    client = OSINTClient(api_keys={'virustotal': 'test_key'})

    # Mock a failing source
    original_query = client._execute_query
    fail_count = [0]
    target_failures = 20

    async def failing_query(source: str, query: str) -> dict:
        fail_count[0] += 1
        if fail_count[0] <= target_failures:
            raise Exception("Simulated failure")
        return await original_query(source, query)

    client._execute_query = failing_query

    # Launch 25 concurrent requests (more than failure threshold)
    tasks = [
        client.query_source('virustotal', f'http://test{i}.com')
        for i in range(25)
    ]

    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start

    # Count successful vs failed results
    successful = sum(1 for r in results if not isinstance(r, Exception) and r is not None)
    failed = len(results) - successful

    # Circuit breaker should have opened, preventing some requests
    # We expect most failures, with circuit breaker stopping execution
    assert failed >= 20, f"Circuit breaker should have stopped requests: {failed} failures"

    # Verify circuit breaker state
    assert 'virustotal' in client.circuit_breakers
    breaker = client.circuit_breakers['virustotal']
    assert breaker.is_open or breaker.state == "open", "Circuit breaker should be open"

    # Verify the operation completed quickly (breaker stops early)
    assert elapsed < 5.0, f"Stress test took {elapsed:.2f}s, expected < 5s due to breaker"

    # Test recovery - wait for backoff period and verify reset
    await asyncio.sleep(breaker.BACKOFF_SECONDS + 1)

    # Reset breaker and verify one request succeeds
    fail_count[0] = target_failures + 1  # Stop failing
    result = await client.query_source('virustotal', 'http://test-recovery.com')
    assert not isinstance(result, Exception), "Recovery request should succeed"
```

---

### Integration Tests

**Test: Full OSINT analysis with 10 sources**
```python
@pytest.mark.asyncio
async def test_full_osint_analysis():
    investigator = GraphInvestigator(mock_nim_client)

    result = await investigator.investigate("http://test-site.com")

    assert result.domain is not None
    assert len(result.intel_sources) >= 5
    assert result.conflict_resolution is not None
    assert result.darknet_exposure is not None
```

---

## Success Criteria (When Phase 8 Is Done)

### Must Have (Blocker if Missing)
1. ✅ OSINTClient queries 15+ sources with rate limiting
2. ✅ Offline threat feeds provide fallback for rate-limited sources
3. ✅ Circuit breaker prevents repeated failures
4. ✅ Darknet intelligence via threat feeds (no Tor access)
5. ✅ Conflict resolver prioritizes high-trust sources
6. ✅ Entity profile built from multiple OSINT sources

### Should Have (Warning if Missing)
1. ✅ Cache reduces repeat queries by >70%
2. ✅ Tiered execution prioritizes fast sources
3. ✅ Offline feeds auto-downloaded periodically
4. ✅ Confidence weighted by source trust level
5. ✅ conflicting findings clearly flagged for review

### Nice to Have (Optional)
1. ✅ Threat attribution suggestions based on patterns
2. ✅ MITRE ATT&CK framework integration
3. ✅ Intelligence network visualization (entity relationships)
4. ✅ Real-time threat feed updates during audit

---

## Requirements Covered

| Requirement | Status | Notes |
|-------------|--------|-------|
| OSINT-01 | 📝 Covered | 15+ sources with rate limiting |
| OSINT-02 | 📝 Covered | Darknet via threat feeds |
| OSINT-03 | 📝 Covered | Enhanced Graph with multi-source |
| CTI-01 | 📝 Covered | Researcher methodology emulation |
| CTI-02 | 📝 Covered | Multi-source verification with conflict detection |
| CTI-03 | 📝 Covered | CTI-lite (IOCs, ATT&CK) |
| CTI-04 | 📝 Covered | Smart intelligence network with reasoning |

---

*Plan created: 2026-02-23*
*Next phase: Phase 9 (Judge System & Orchestrator)*
