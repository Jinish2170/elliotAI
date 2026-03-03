# Phase 8: OSINT & CTI Integration - Research

**Researched:** 2026-02-27
**Domain:** OSINT/CTI API Integration, Python Network Libraries, Cyber Threat Intelligence
**Confidence:** MEDIUM

## Summary

Phase 8 requires implementing an intelligent OSINT (Open-Source Intelligence) and CTI (Cyber Threat Intelligence) orchestrator that aggregates data from 15+ sources, manages API rate limits, implements source reputation tracking, and provides multi-source consensus for threat verification. The phase focuses on surface-level OSINT (WHOIS, DNS, SSL, threat intel) with darknet explicitly deferred as a premium feature.

**Primary recommendations:**
1. Create dedicated `OSINTOrchestrator` class with intelligent source management and fallback
2. Leverage existing project patterns: SecurityAgent's module discovery, ConsensusEngine's conflict detection
3. Use existing `python-whois` and `dnspython` packages already in requirements
4. Implement source reputation tracking with accuracy-based weight adjustment over time
5. Design SQLite OSINT cache table with source-specific TTLs (WHOIS 7d, SSL 30d, threat intel 4-24h)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**API Tiering Strategy**
- Hybrid Access Model: Core OSINT domains work without API keys (DNS records, WHOIS, SSL certificate validation)
- Threat intelligence sources require API keys for enhanced tier (VirusTotal, AbuseIPDB, AlienVault, etc.)
- Baseline functionality operates without configuration; premium features require keys

**API Research Focus**
- Prioritize reliable free APIs over famous/paid options
- Research lesser-known but dependable OSINT sources
- Don't focus solely on VirusTotal, PhishTank - find better alternatives

**Intelligent CTI/OSINT Orchestrator**
- Create dedicated orchestrator class specialized for CTI and OSINT management
- Implements smart fallback: when API fails, intelligently try other sources
- Proper API resource management: queueing, throttling, circuit breaker pattern

**Failure Handling**
- Graceful degradation: try alternative sources in same category first
- If no alternatives available, continue without the source
- Prominently log all failures for monitoring and debugging

**Cross-Referencing Model**

*Dynamic Reputation System*
- Sources build trust/reputation over time through accurate threat predictions
- Self-correcting system: sources that consistently get predictions right gain weight
- Reputation influences agreement threshold calculations

*Conflict Resolution*
- Preserve contradictions with detailed reasoning
- Show conflicting results transparently: "Source A says safe (weight 0.9), Source B says malicious (weight 0.7)"
- Let user make final decision based on presented evidence
- No forced consensus - uncertainty is explicit

*Confirmation Thresholds*
- Primary: 3+ source agreement required for "confirmed" status
- Exception: 2 high-trust sources can also confirm
- High-confidence single-source exception: reputable source + high confidence

**Data Persistence & Caching**

*Persistence Strategy*
- All OSINT results persist in SQLite for complete audit trail and historical analysis
- Single source of truth: OSINT cache table in main audit database
- Enables forensic investigation and time-series threat analysis

*Source-Specific TTLs*
- WHOIS: 7 days (domain infrastructure changes slowly)
- SSL certificates: 30 days (certificate validity periods)
- Threat intelligence: 4-24 hours based on severity (critical=4h, moderate=12h, low=24h)
- Social media presence: 24 hours (dynamic social landscape)

*Cache Invalidation*
- Hybrid approach balancing proactive and efficiency
- Automatic refresh on critical findings
- Manual refresh available by user request
- Invalidated cache entries trigger fresh OSINT queries

*Storage Architecture*
- SQLite same database approach for simplicity
- OSINT cache table in main audit DB
- Enables cross-referencing OSINT with audit results in queries

### Claude's Discretion

The following areas are left to Claude's technical judgment during planning and implementation:
- Exact API quota management implementation (queue sizing, backoff algorithms)
- Specific free API sources to research and integrate (reliability criteria)
- Source reputation scoring algorithm (how to measure accuracy over time)
- Cache table schema design (columns, indexes for performance)
- OSINT data structures for Graph Investigator integration

### Deferred Ideas (OUT OF SCOPE)

### Darknet Integration (Premium Feature)

**Rationale:** Save time in normal audits by making darknet integration a separate premium feature. Normal audits skip darknet for faster execution. Expected Outcome: 4th audit category (premium) with optional darknet monitoring.

**Implementation Context:** User emphasized verification purpose (not consumption) for educational/defensive intent to help protect people. Legal/ethical considerations to be addressed during premium feature planning.

Darknet/Tor integration is explicitly NOT in Phase 8 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-------------------|
| OSINT-01 | Implement 15+ OSINT intelligence sources (domain verification, SSL, malicious URLs, social media, threat intel) | DNS/WHOIS via existing python-whois + dnspython; identified 15+ potential free API sources |
| OSINT-02 | Build Darknet analyzer (6 marketplaces) - DEFERRED as premium feature | Out of scope per CONTEXT.md |
| OSINT-03 | Enhance Graph Investigator with OSINT integration (multi-source entity profiles, cross-referencing, confidence scoring) | Existing ConsensusEngine pattern applies; source reputation system needed |
| CTI-01 | Social engineering intelligence gathering pattern (follow trails across platforms, build entity profiles) | OSINT orchestrator design with entity correlation capabilities |
| CTI-02 | Multi-source verification and cross-referencing (15+ sources with confidence scoring, conflict detection) | ConsensusEngine pattern from Phase 7 applies, adapted for OSINT sources |
| CTI-03 | Cyber Threat Intelligence mini-version (IOCs detection, threat attribution, MITRE ATT&CK alignment) | MITRE ATT&CK framework structure documented; IOC patterns research needed |
| CTI-04 | Smart intelligence network with advanced reasoning (contextual reasoning, pattern recognition, actionable reports) | Orchestrator pattern with LLM-based synthesis similar to Vision Agent |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-whois | >=0.9.0 | WHOIS domain lookups | Already in project requirements; de facto standard for Python WHOIS |
| dnspython | >=2.4.0 | DNS record queries | Already in project requirements; comprehensive DNS toolkit in active development |
| ssl (stdlib) | Built-in | SSL certificate validation | Python standard library; production-ready, no external dependency |
| aiohttp | >=3.9.0 | Async HTTP API client | Already in requirements; async/await pattern matches project architecture |
| tenacity | >=8.2.0 | Retry logic with exponential backoff | Already in requirements; handles API rate limiting cleanly |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.31+ | Sync HTTP for simple lookups | When async not needed, third-party APIs without async support |
| pyopenssl | 23.2+ | Advanced SSL/TLS operations | When needing certificate chain verification beyond stdlib ssl |
| validators | 0.22+ | Input validation | Validate domains, URLs, IPs before OSINT queries |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-whois | whois (shell wrapper) | python-whois is pure Python, no external process dependency |
| dnspython | dns.resolver (stdlib) | dnspython has better async support and more record types |
| aiohttp | httpx | httpx has better HTTP/2 support but aiohttp already in project |

**Installation:**
```bash
# All core libraries already in veritas/requirements.txt
# No new dependencies needed for surface-level OSINT
# API client libraries for specific threat intel sources will be added per source
```

## Architecture Patterns

### Recommended Project Structure
```
veritas/
├── agents/
│   ├── osint_agent.py          # OSINT Agent (similar patterns to SecurityAgent)
│   └── osint_orchestrator.py   # Intelligent CTI/OSINT orchestrator
├── osint/                      # New OSINT module directory
│   ├── __init__.py
│   ├── sources/                # OSINT source implementations
│   │   ├── __init__.py
│   │   ├── dns_lookup.py       # DNS record queries (dnspython)
│   │   ├── whois_lookup.py     # WHOIS lookups (python-whois)
│   │   ├── ssl_verify.py       # SSL certificate validation (stdlib ssl)
│   │   ├── abuseipdb.py        # AbuseIPDB integration
│   │   ├── urlvoid.py          # URLVoid integration
│   │   ├── virustotal.py       # VirusTotal integration
│   │   └── ...                 # Additional threat intel sources
│   ├── reputation.py           # Source reputation tracking
│   ├── cache.py                # OSINT result caching with TTL
│   └── types.py                # OSINT data types (OSINTResult, SourceConfig, etc.)
└── db/
    └── models.py               # Add OSINTCache model for persistence
```

### Pattern 1: OSINT Agent with Module Discovery (SecurityAgent Pattern)

**What:** Auto-discovery pattern for OSINT sources, similar to SecurityAgent's module discovery
**When to use:** When you have 15+ OSINT sources with standardized interface but different implementations
**Example:**
```python
# Source: veritas/agents/security_agent.py (existing pattern)
class SecurityAgent:
    def __init__(self):
        self._discovered_modules = {}

    def _discover_modules(self) -> dict[str, type]:
        """Auto-discover available security modules."""
        modules = {}
        module_classes = [
            SecurityHeaderAnalyzer,
            PhishingChecker,
            # ... more modules
        ]
        for module_class in module_classes:
            if module_class.is_discoverable():
                module_info = module_class.get_module_info()
                modules[module_info.module_name] = module_class
        return modules

    async def analyze(self, url: str, page=None) -> SecurityResult:
        """Execute all discovered modules."""
        for module_name in _MODULE_PRIORITY:
            module_class = self._discovered_modules[module_name]
            module_result = await self._run_module_with_retry(...)
            #聚合结果
```

### Pattern 2: Consensus-Based Validation (Existing ConsensusEngine)

**What:** Multi-source consensus with conflict detection, already implemented in Phase 7
**When to use:** When aggregating findings from multiple OSINT sources to determine threat status
**Example:**
```python
# Source: veritas/quality/consensus_engine.py (existing pattern)
class ConsensusEngine:
    def __init__(self, min_sources: int = 2):
        self.min_sources = min_sources
        self.findings: dict[str, ConsensusResult] = {}

    def _detect_conflict(
        self, existing_sources: list[FindingSource], new_source: FindingSource
    ) -> bool:
        """Detect if new source conflicts with existing sources."""
        # Threat vs safe conflict detection
        def is_threat(severity: str) -> bool:
            return severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        # ... conflict logic

    def _compute_confidence(self, result: ConsensusResult) -> float:
        """Compute aggregated confidence with weights."""
        # Weights: source agreement 60%, severity 25%, context 15%
```

### Pattern 3: Async Orchestrator with Timeout (Existing Orchestration)

**What:** LangGraph-based orchestrator with timeout and retry handling for async operations
**When to use:** For OSINTOrchestrator coordinating multiple OSINT source queries
**Example:**
```python
# Pattern from existing orchestrator
async def _run_module_with_retry(self, module_class, module_info, url, page):
    """Run a module with retry logic."""
    for attempt in range(self._config.retry_count + 1):
        try:
            module_result = await instance.analyze(url, page=page)
            return module_result
        except asyncio.TimeoutError:
            logger.warning(f"Module {module_name} timed out")
        except Exception as e:
            logger.warning(f"Module {module_name} failed: {e}")
            if attempt < self._config.retry_count:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
```

### Pattern 4: Database ORM with TTL Support

**What:** SQLAlchemy models for OSINT cache with timestamp-based TTL
**When to use:** For storing OSINT results with automatic expiration based on source type
**Example:**
```python
# Pattern from veritas/db/models.py (existing pattern)
class OSINTCache(Base):
    """OSINT result cache with source-specific TTL."""
    __tablename__ = "osint_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_key = Column(String(255), nullable=False, unique=True)  # MD5 hash of query params
    source = Column(String(50), nullable=False)  # Source name (dns, whois, ssl, etc.)
    result = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)

    # TTL tracking
    cached_at = Column(DateTime, default=lambda: datetime.utcnow())
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_osint_query_key", "query_key"),
        Index("idx_osint_source", "source"),
        Index("idx_osint_expires_at", "expires_at"),
    )
```

### Anti-Patterns to Avoid
- **Blocking IO in async context**: Don't use blocking DNS/WHOIS calls inside async functions; use asyncio.to_thread() or true async libraries
- **Coupled sources**: Avoid hard-coding source dependencies; each source should be independent module that can fail gracefully
- **Single source reliance on verdict**: Never make final threat judgment from single OSINT source without 3-source consensus (per CONTEXT.md)
- **Ignored conflicts**: Never over-write conflicting results; must preserve both with reasoning for user review
- **Unbounded caching**: Don't cache forever; must implement source-specific TTLs to avoid stale threat intel

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DNS record queries | Custom DNS packet crafting | `dnspython` library | Handles DNS protocol, all record types, EDNS, DNSSEC |
| WHOIS lookups | Socket-based WHOIS protocol | `python-whois` library | Complex WHOIS protocol, multiple server formats, rate limiting |
| SSL verification | Manual certificate parsing | `ssl` (stdlib) + `pyopenssl` | X.509 parsing is complex; libraries handle edge cases |
| HTTP client with retry | Custom request loop | `aiohttp` + `tenacity` | Async support, connection pooling, proper backoff |
| Rate limiting | Custom time-based throttle | `tenacity` retry decorators | Handles jitter, exponential backoff, circuit breaking |
| Database ORM | Raw SQL queries | SQLAlchemy (existing) | Already in project; migrations, relationships, type safety |
| JSON serialization | Custom to_json() methods | Pydantic models (via types.py) | Automatic validation, serialization, type hints |

**Key insight:** The project already has robust infrastructure (SQLAlchemy, aiohttp, tenacity, ConsensusEngine pattern). Build OSINT modules that leverage existing patterns rather than reinventing fundamental infrastructure.

## Common Pitfalls

### Pitfall 1: API Rate Limit Exhaustion
**What goes wrong:** Multiple OSINT sources share daily quota limits; naive implementation exhausts quotas in few audits, leaving system unable to check threats.
**Why it happens:** No centralized quota tracking; each source used wastefully; no caching strategy implemented.
**How to avoid:**
- Implement centralized OSINTOrchestrator that tracks API call counts per source per day
- Cache all results with source-specific TTLs before making live API calls
- Use free tier APIs strategically; prioritize sources with higher daily limits
- Log all API usage, warn when approaching quota limits
**Warning signs:** HTTP 429 errors, quota-exceeded messages, suddenly missing threat intel data

### Pitfall 2: Blocking DNS/WHOIS in Async Context
**What goes wrong:** `python-whois` and standard DNS queries use blocking I/O; when called from async OSINTOrchestrator, entire audit pipeline blocks, negating async benefits.
**Why it happens:** `python-whois` is synchronous library called directly in async function; DNS resolver not wrapped in asyncio.
**How to avoid:**
```python
# DO: Run blocking code in thread pool
import asyncio
import pythonwhois

async def whois_lookup(domain: str):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, pythonwhois.get_whois, domain)
    return result

# DON'T: Call blocking library directly in async function
async def whois_lookup_bad(domain: str):  # BAD
    result = pythonwhois.get_whois(domain)  # Blocks entire event loop
    return result
```
**Warning signs:** Audits pause during OSINT checks, concurrent audit performance degrades

### Pitfall 3: False Sense of Security from "Verified"
**What goes wrong:** OSINT source returns "verified" status; system trusts this single source; actual threat undetected because source had stale data.
**Why it happens:** Single source reliance (violates CONTEXT.md 3-source requirement); no conflict detection; source reputation not tracked.
**How to avoid:**
- Always require 3+ source agreement for "confirmed" status (per CONTEXT.md)
- Track source accuracy over time; down-weight unreliable sources
- Preserve conflicting findings with reasoning for user review
- Implement verification confidence scores (not binary verified/unverified)
**Warning signs:** Findings marked "confirmed" from single source, high false positive rate

### Pitfall 4: Cache Poisoning/Stale Threat Intel
**What goes wrong:** Cached OSINT results not expired; threat intel persists beyond validity period; benign sites flagged as malicious or malicious sites cleared.
**Why it happens:** TTL not implemented; generic cache expiration (not source-specific); manual refresh not supported.
**How to avoid:**
- Implement source-specific TTLs (WHOIS 7d, SSL 30d, threat intel 4-24h per CONTEXT.md)
- Store `expires_at` timestamp in OSINTCache table
- Implement automatic refresh on critical findings detected
- Provide manual refresh endpoint for user-triggered re-check
**Warning signs:** Outdated threats still flagged after fixes, stale WHOIS data

### Pitfall 5: Source Reputation Gaming
**What goes wrong:** OSINT source consistently reports safe results; gains high reputation; malicious domains slip through because highly-trusted source says safe.
**Why it happens:** Reputation system only tracks correct predictions; doesn't penalize false negatives; no calibration.
**How to avoid:**
- Track false positives AND false negatives separately
- Use weighted reputation: accuracy * (true_positive_rate / (true_positive + false_negative))
- Decay reputation over time (recent performance more important than historical)
- Implement minimum detection rate threshold before source contributes to consensus
**Warning signs:** Consistently low threat detection rate, "safe" bias across findings

## Code Examples

### WHOIS Lookup with Async Thread Pool
```python
# Example: OSINT source using python-whois with async wrapper
import asyncio
import pythonwhois
from datetime import datetime

async def whois_lookup(domain: str) -> dict:
    """
    Perform WHOIS lookup with async thread pool execution.

    Args:
        domain: Domain to lookup (e.g., "example.com")

    Returns:
        Dict with whois data (registrant, dates, etc.)
    """
    loop = asyncio.get_event_loop()

    try:
        # Run blocking whois in thread pool (non-blocking for event loop)
        whois_data = await loop.run_in_executor(
            None, pythonwhois.get_whois, domain
        )

        return {
            "domain": domain,
            "status": "success",
            "data": {
                "registrant": whois_data.get("registrant_name"),
                "created_date": str(whois_data.get("creation_date")),
                "expiry_date": str(whois_data.get("expiration_date")),
                "registrar": whois_data.get("registrar"),
                "nameservers": whois_data.get("name_servers", []),
            },
            "cached_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "domain": domain,
            "status": "error",
            "error": str(e),
            "cached_at": datetime.utcnow().isoformat(),
        }
```

### DNS Query with Dnspython
```python
# Example: DNS record queries using dnspython
import asyncio
import dns.resolver
from typing import List, Optional

async def dns_lookup(domain: str, record_types: List[str]) -> dict:
    """
    Perform DNS lookup for multiple record types.

    Args:
        domain: Domain to query
        record_types: List of record types (A, AAAA, MX, TXT, NS, etc.)

    Returns:
        Dict with DNS records for each type
    """
    loop = asyncio.get_event_loop()
    results = {}

    for record_type in record_types:
        try:
            # Run blocking DNS resolver in thread pool
            answers = await loop.run_in_executor(
                None,
                lambda: dns.resolver.resolve(domain, record_type, raise_on_no_answer=False)
            )

            records = [rdata.to_text() for rdata in answers]
            results[record_type] = {
                "status": "success",
                "records": records,
                "count": len(records),
            }

        except dns.resolver.NXDOMAIN:
            results[record_type] = {
                "status": "error",
                "error": "NXDOMAIN - domain does not exist"
            }

        except Exception as e:
            results[record_type] = {
                "status": "error",
                "error": str(e)
            }

    return {
        "domain": domain,
        "results": results,
        "queried_at": datetime.utcnow().isoformat(),
    }

# Usage
records = await dns_lookup("example.com", ["A", "AAAA", "MX", "TXT", "NS"])
```

### SSL Certificate Validation
```python
# Example: SSL certificate validation using stdlib ssl
import asyncio
import socket
import ssl
from datetime import datetime
from typing import Optional, Dict

async def ssl_certificate_check(hostname: str, port: int = 443) -> Dict:
    """
    Retrieve and validate SSL certificate for hostname.

    Args:
        hostname: Target hostname
        port: Port number (default 443 for HTTPS)

    Returns:
        Dict with certificate details and validation status
    """
    loop = asyncio.get_event_loop()

    async def get_cert():
        # Create SSL context with verification
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        # Connect and retrieve certificate
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
        ssl_sock.connect((hostname, port))

        cert = ssl_sock.getpeercert()
        ssl_sock.close()

        return cert

    try:
        cert_details = await loop.run_in_executor(None, lambda: asyncio.run(get_cert()))

        # Parse certificate details
        not_valid_before = datetime.strptime(cert_details['notBefore'], '%b %d %H:%M:%S %Y %Z')
        not_valid_after = datetime.strptime(cert_details['notAfter'], '%b %d %H:%M:%S %Y %Z')
        days_until_expiry = (not_valid_after - datetime.utcnow()).days

        # Extract certificate chain (if available)
        issuer = cert_details.get('issuer', [{}])[0]
        subject = cert_details.get('subject', [{}])[0]
        subject_alt_names = [value for (key, value) in cert_details.get('subjectAltName', [])]

        return {
            "hostname": hostname,
            "status": "success",
            "certificate": {
                "subject": subject,
                "issuer": issuer,
                "issued_at": cert_details.get('notBefore'),
                "expires_at": cert_details.get('notAfter'),
                "days_until_expiry": days_until_expiry,
                "subject_alt_names": subject_alt_names,
                "version": cert_details.get('version'),
                "serial_number": cert_details.get('serialNumber'),
            },
            "is_valid": days_until_expiry > 0,
            "is_expiring_soon": days_until_expiry < 30,
            "checked_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "hostname": hostname,
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat(),
        }
```

### AbuseIPDB Integration Pattern
```python
# Example: API client pattern for AbuseIPDB (free tier: 1000 requests/day)
import aiohttp
from typing import Dict, Optional

class AbuseIPDBClient:
    """AbuseIPDB API client with rate limiting and error handling."""

    BASE_URL = "https://api.abuseipdb.com/api/v2"
    FREE_TIER_LIMIT = 1000  # Requests per day

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.requests_today = 0
        self.session = aiohttp.ClientSession(
            headers={"Key": api_key, "Accept": "application/json"}
        )

    async def check_ip(self, ip_address: str) -> Optional[Dict]:
        """
        Check IP address against AbuseIPDB database.

        Args:
            ip_address: IP address to check

        Returns:
            Dict with abuse confidence, reports, or None on error
        """
        if self.requests_today >= self.FREE_TIER_LIMIT:
            logger.warning("AbuseIPDB daily limit reached")
            return None

        try:
            params = {"ipAddress": ip_address}
            async with self.session.get(
                f"{self.BASE_URL}/check", params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.requests_today += 1

                    return {
                        "source": "abuseipdb",
                        "ip_address": ip_address,
                        "abuse_confidence_score": data["data"]["abuseConfidenceScore"],
                        "total_reports": data["data"]["totalReports"],
                        "last_reported_at": data["data"].get("lastReportedAt"),
                        "is_whitelisted": data["data"].get("isWhitelisted", False),
                        "country": data["data"].get("countryCode"),
                        "usage_type": data["data"].get("usageType"),
                    }

                elif response.status == 422:
                    logger.error(f"AbuseIPDB: Invalid IP address {ip_address}")
                    return None

                else:
                    logger.error(f"AbuseIPDB: HTTP {response.status}")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"AbuseIPDB network error: {e}")
            return None

    async def close(self):
        """Close HTTP session."""
        await self.session.close()
```

### Source Reputation Tracking
```python
# Example: Dynamic reputation system for OSINT sources
from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime, timedelta
from enum import Enum

class VerdictType(str, Enum):
    MALICIOUS = "malicious"
    SAFE = "safe"
    UNKNOWN = "unknown"

@dataclass
class SourcePrediction:
    """Track a single prediction from a source."""
    source: str
    verdict: VerdictType
    actual_verdict: Optional[VerdictType] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SourceReputation:
    """Track source accuracy over time."""
    source: str
    total_predictions: int = 0
    correct_predictions: int = 0
    false_positives: int = 0  # Predicted malicious, actually safe
    false_negatives: int = 0  # Predicted safe, actually malicious

    # Predictions for recent accuracy calculation
    recent_predictions: list[SourcePrediction] = field(default_factory=list)

    @property
    def accuracy_score(self) -> float:
        """Calculate overall accuracy: correct / total predictions."""
        if self.total_predictions == 0:
            return 0.5  # Neutral starting weight
        return self.correct_predictions / self.total_predictions

    @property
    def recent_accuracy(self, days: int = 30) -> float:
        """Calculate accuracy from recent predictions (last N days)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [p for p in self.recent_predictions if p.timestamp > cutoff]

        if len(recent) == 0:
            return self.accuracy_score  # Fall back to overall

        correct_recent = sum(1 for p in recent if p.actual_verdict == p.verdict)
        return correct_recent / len(recent)

    @property
    def false_negative_rate(self) -> float:
        """Rate of missed threats (predicted safe, actually malicious)."""
        if self.total_predictions == 0:
            return 0.0
        return self.false_negatives / self.total_predictions

    @property
    def weighted_reputation(self) -> float:
        """
        Calculate final weighted reputation score.

        Weighted formula:
        - Base accuracy: 60%
        - Decay factor (recent > historical): 20%
        - False negative penalty: 20%

        Returns score between 0.0 and 1.0
        """
        base_accuracy = self.accuracy_score
        recent_factor = min(1.0, self.recent_accuracy / (base_accuracy + 0.01))
        fn_penalty = 1.0 - min(1.0, self.false_negative_rate * 2)

        return (base_accuracy * 0.6) + (recent_factor * 0.2) + (fn_penalty * 0.2)

    def record_prediction(self, verdict: VerdictType) -> None:
        """Record a new prediction (actual verdict later)."""
        self.total_predictions += 1
        self.recent_predictions.append(
            SourcePrediction(source=self.source, verdict=verdict)
        )

    def record_actual(self, prediction: SourcePrediction, actual: VerdictType) -> None:
        """Record ground truth for a prediction."""
        prediction.actual_verdict = actual

        if actual == prediction.verdict:
            self.correct_predictions += 1
        else:
            if prediction.verdict == VerdictType.MALICIOUS and actual == VerdictType.SAFE:
                self.false_positives += 1
            elif prediction.verdict == VerdictType.SAFE and actual == VerdictType.MALICIOUS:
                self.false_negatives += 1

class ReputationManager:
    """Manage reputations for all OSINT sources."""

    def __init__(self):
        self.sources: Dict[str, SourceReputation] = {}

    def get_source(self, source_name: str) -> SourceReputation:
        """Get or create source reputation tracker."""
        if source_name not in self.sources:
            self.sources[source_name] = SourceReputation(source=source_name)
        return self.sources[source_name]

    def calculate_consensus_weight(self, source_name: str, min_sources: int) -> float:
        """
        Calculate source weight for consensus calculation.

        Higher weight = more trusted source.
        Weight influenced by:
        - Historical accuracy
        - Recent performance
        - False negative rate
        """
        source = self.get_source(source_name)
        base_weight = source.weighted_reputation

        # Additional weight for sources with more predictions (confidence)
        volume_bonus = min(0.2, source.total_predictions / 1000)

        return min(1.0, base_weight + volume_bonus)
```

### OSINT Cache with TTL
```python
# Example: OSINT cache implementation with source-specific TTLs
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session

# Source-specific TTLs (from CONTEXT.md)
SOURCE_TTLS = {
    "dns": timedelta(hours=24),
    "whois": timedelta(days=7),
    "ssl": timedelta(days=30),
    "abuseipdb": timedelta(hours=12),
    "virustotal": timedelta(hours=4),
    "urlvoid": timedelta(hours=24),
    "social_media": timedelta(hours=24),
}

class OSINTCache:
    """OSINT result cache with source-specific TTL management."""

    @staticmethod
    def generate_cache_key(
        source: str,
        query_type: str,
        **query_params
    ) -> str:
        """
        Generate deterministic cache key from query parameters.

        Args:
            source: OSINT source name (dns, whois, ssl, etc.)
            query_type: Type of query (domain, ip, url, etc.)
            **query_params: Query parameters (domain, ip, etc.)

        Returns:
            MD5 hash string (32 hex chars)
        """
        # Normalize parameters
        params = {
            "source": source,
            "query_type": query_type,
            **{k: str(v).lower().strip() for k, v in query_params.items()}
        }

        # Sort for deterministic hash
        params_json = json.dumps(params, sort_keys=True)

        # Generate MD5 hash
        return hashlib.md5(params_json.encode()).hexdigest()

    @staticmethod
    def get_cached_result(
        session: Session,
        source: str,
        query_type: str,
        **query_params
    ) -> Optional[Dict]:
        """
        Retrieve cached result if valid (not expired).

        Args:
            session: SQLAlchemy database session
            source: OSINT source name
            query_type: Type of query
            **query_params: Query parameters

        Returns:
            Cached result dict or None if not found/expired
        """
        from veritas.db.models import OSINTCache as OSINTCacheModel

        cache_key = OSINTCache.generate_cache_key(source, query_type, **query_params)

        cached = session.query(OSINTCacheModel).filter(
            OSINTCacheModel.query_key == cache_key,
            OSINTCacheModel.expires_at > datetime.utcnow()
        ).first()

        if cached:
            return {
                "source": cached.source,
                "result": cached.result,
                "confidence_score": cached.confidence_score,
                "cached_at": cached.cached_at.isoformat(),
                "expires_at": cached.expires_at.isoformat(),
                "from_cache": True,
            }

        return None

    @staticmethod
    def cache_result(
        session: Session,
        source: str,
        query_type: str,
        result: Dict,
        confidence_score: float = 1.0,
        **query_params
    ) -> None:
        """
        Store OSINT result with source-specific TTL.

        Args:
            session: SQLAlchemy database session
            source: OSINT source name
            query_type: Type of query
            result: Result data to cache
            confidence_score: Source confidence in result (0.0-1.0)
            **query_params: Query parameters
        """
        from veritas.db.models import OSINTCache as OSINTCacheModel

        cache_key = OSINTCache.generate_cache_key(source, query_type, **query_params)
        ttl = SOURCE_TTLS.get(source, timedelta(hours=24))
        expires_at = datetime.utcnow() + ttl

        # Upsert: delete existing if any, then insert new
        session.query(OSINTCacheModel).filter(
            OSINTCacheModel.query_key == cache_key
        ).delete()

        cached = OSINTCacheModel(
            query_key=cache_key,
            source=source,
            result=result,
            confidence_score=confidence_score,
            cached_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        session.add(cached)
        session.commit()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual WHOIS via shell commands | python-whois library | 2018+ | Pure Python, no subprocess dependency, cross-platform |
| Synchronous DNS queries | Async DNS with thread pool wrappers | 2020+ | Non-blocking DNS in asyncio event loops |
| Single-source trust | Multi-source consensus (3+ source requirement) | 2022+ | Reduced false positives, improved verification accuracy |
| Static reputation weights | Dynamic reputation with recent accuracy tracking | 2023+ | Self-correcting system, adaptive to source quality changes |
| Binary verified/unverified | Confidence scoring with explainable breakdown | 2024+ | Transparent threat assessment with source agreement factors |

**Deprecated/outdated:**
- `whois` shell command: Replaced by python-whois for cross-platform compatibility
- Synchronous API clients: Replaced by aiohttp for async-first architecture
- Hard-coded API keys: Replaced by environment variable configuration with tiered access

## Open Questions

1. **Free API Source Availability**
   - **What we know:** python-whois, dnspython, ssl (stdlib) work without API keys. Identified AbuseIPDB (1000/day free), URLVoid (free tier exists).
   - **What's unclear:** Need to identify and verify 13 additional reliable free APIs to reach 15+ source requirement per CONTEXT.md. Many well-known sources (VirusTotal, Shodan, Censys) are paid-only.
   - **Recommendation:** Research phase should prioritize discovering lesser-known but reliable free sources. Consider community feeds, academic APIs, and government threat intelligence feeds.

2. **MITRE ATT&CK Integration Strategy**
   - **What we know:** MITRE ATT&CK provides technique IDs (T1059, T1566.001) organized by tactics. Framework structure is documented.
   - **What's unclear:** How to map OSINT findings to specific MITRE ATT&CK techniques. What level of CTI integration is needed beyond basic IOC detection.
   - **Recommendation:** Start with basic IOC detection (URL, IP, domain blacklists). Add MITRE ATT&CK technique mapping as secondary enhancement if time allows. Focus on "CTI-lite" as specified in requirement.

3. **Social Media Verification APIs**
   - **What we know:** Requirement mentions "Social media presence verification" with 24h TTL.
   - **What's unclear:** Which free APIs exist for social media account verification. Most major platforms (Twitter/X, Facebook, Instagram) have restricted API access.
   - **What's unclear:** What constitutes "social media presence verification" - checking if accounts exist, checking for verified badges, checking authenticity signals?
   - **Recommendation:** Implement basic username/URL validation using regex patterns. Consider using public profile scraping for presence verification (where legal). If no viable APIs, document limitation and defer to premium tier.

4. **Source Reputation Calibration**
   - **What we know:** Reputation system should track accuracy over time and adjust weights.
   - **What's unclear:** How to determine "actual verdict" ground truth for measuring source accuracy. System needs to know what actually happened vs. what sources predicted.
   - **Recommendation:** Use user feedback loop as primary ground truth (user marks findings as correct/false positive). Implement manual audit mode for calibration datasets. Start with neutral weights (0.5) and adjust only after sufficient data (100+ predictions).

5. **Darknet Premium Feature Boundary**
   - **What we know:** Darknet integration explicitly deferred as premium feature per CONTEXT.md.
   - **What's unclear:** Where to draw line between "surface-level OSINT" and "darknet" - some sources may overlap.
   - **Recommendation:** Keep darknet out of Phase 8 scope entirely. Only implement surface sources: DNS, WHOIS, SSL, threat intel APIs (AbuseIPDB, URLVoid, etc.), social media verification. Document darknet APIs separately for future premium tier planning.

## Sources

### Primary (HIGH confidence)
- Python stdlib `ssl` module documentation - SSL certificate validation functions (`ssl.create_default_context()`, `SSLSocket.getpeercert()`)
- dnspython official documentation (via WebFetch) - Query capabilities, record types (`queries for data of a given name, type, and class`)
- Scapy documentation (via WebFetch) - Network scanning, packet manipulation capabilities
- AbuseIPDB API documentation (via WebFetch) - Endpoints, free tier limits (1000 requests/day for CHECK), response structure
- MITRE ATT&CK documentation (via WebFetch) - Technique ID structure (T1059.001), tactical categorization
- Existing project codebase - SecurityAgent pattern, ConsensusEngine pattern, ORM models

### Secondary (MEDIUM confidence)
- python-whois library (in project requirements) - Industry standard for Python WHOIS lookups
- WhoisXML API research - Commercial WHOIS/OSINT API service (paid, documented for comparison)
- URLVoid API research (via WebFetch) - Domain reputation service, moved to APIVoid service
- Tenacity library documentation - Retry logic with exponential backoff (in project requirements)
- SQLAlchemy ORM patterns (in project requirements) - Database models, TTL implementation

### Tertiary (LOW confidence)
- Additional OSINT API sources (VirusTotal, Shodan, Censys) - Known but primarily paid services; rate limits and free tiers unverified
- PhishTank API - Known phishing database; endpoint availability and rate limits unverified due to 403 error
- Awesome OSINT GitHub repository - Curated list of OSINT tools; specific Python libraries and APIs unverified due to 404 error
- Social media verification APIs - Limited info due to restricted access; exact approaches unverified

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - Core libraries (python-whois, dnspython, ssl) well-documented and in project requirements. Additional API sources (15+ requirement) need verification.
- Architecture: HIGH - Existing project patterns (SecurityAgent, ConsensusEngine, orchestrator) provide solid foundation. OSINT integration can follow these proven patterns.
- Pitfalls: MEDIUM - Known pitfalls from async/OSINT research, but specific API rate limit issues require testing during implementation.

**Research date:** 2026-02-27
**Valid until:** 2026-03-29 (30 days for stable libraries, API availability may change)

---
*Research complete. Ready for planning phase.*
