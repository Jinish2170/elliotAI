# Phase 8 - OSINT Future Expansion APIs

**Purpose:** Document verified free APIs for extending OSINT sources from 6 current sources to 15+ sources.

**Current Sources (6 implemented):**
1. DNS (dnspython) - core infrastructure
2. WHOIS (python-whois) - core infrastructure
3. SSL (stdlib ssl) - core infrastructure
4. URLVoid - threat intel (optional API key)
5. AbuseIPDB - threat intel (optional API key)
6. TODO: 1 additional source placeholder

**Required Expansion (9 additional sources):**

---

## Priority 1: Threat Intelligence APIs (3 sources)

### 1. AlienVault OTX (Open Threat Exchange)
**Type:** Threat Intelligence Community Feed
**Free Tier:** Yes - Open community API
**Rate Limit:** Unknown - requires testing
**Purpose:** Malware detection, threat actor tracking
**Documentation:** https://otx.alienvault.com/api/
**Implementation Notes:**
- Endpoint for pulse/indicators lookup
- Returns malware hashes, IPs, domains
- Community-driven threat intelligence

```python
# TODO: veritas/osint/sources/alienvault.py
class AlienVaultSource:
    BASE_URL = "https://otx.alienvault.com/api/v1"
    # Implement indicator lookup for malware/signatures
```

### 2. Spamhaus DROP / Zen
**Type:** Spam/CBOT Detection Lists
**Free Tier:** Yes - Public DNSBL feeds
**Rate Limit:** None (DNS-based queries)
**Purpose:** Botnet, spam, exploit source detection
**Documentation:** https://www.spamhaus.org/drop/
**Implementation Notes:**
- Query DROP lists via DNS
- Check if IP/domain is listed in spam databases

```python
# TODO: veritas/osint/sources/spamhaus.py
class SpamhausSource:
    # DNSBL queries for DROP, Zen lists
```

### 3. Google Safe Browsing (v4 API)
**Type:** URL Reputation / Malware Detection
**Free Tier:** Yes - 10,000 queries/day
**Rate Limit:** 10K/day free
**Purpose:** Malicious URL, phishing site detection
**Documentation:** https://developers.google.com/safe-browsing/v4
**Implementation Notes:**
- Requires API key
- Check URLs against Google's reputation database

```python
# TODO: veritas/osint/sources/gsafebrowsing.py
class GoogleSafeBrowsingSource:
    BASE_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
```

---

## Priority 2: Domain Reputation APIs (2 sources)

### 4. Domain Reputation Checker (VirusTotal Public API)
**Type:** Domain/URL Reputation
**Free Tier:** Yes - 500 requests/day
**Rate Limit:** 500/day
**Purpose:** Multi-engine virus scanning reputation
**Documentation:** https://docs.virustotal.com/reference
**Implementation Notes:**
- Previously avoided due to being "famous", but essential for domain reputation
- Returns detection count across 70+ engines

```python
# TODO: veritas/osint/sources/virustotal.py
class VirusTotalSource:
    BASE_URL = "https://www.virustotal.com/api/v3"
```

### 5. Censys Free API (Limited)
**Type:** Internet Scanning / Infrastructure Analysis
**Free Tier:** Yes - 250 queries/month
**Rate Limit:** 250/month (limited)
**Purpose:** SSL certificate analysis, service discovery
**Documentation:** https://search.censys.io/api
**Implementation Notes:**
- Use sparingly due to low quota
- Excellent for SSL certificate chain analysis

```python
# TODO: veritas/osint/sources/censys.py
class CensysSource:
    BASE_URL = "https://search.censys.io/api/v2"
```

---

## Priority 3: Email/Social Verification (2 sources)

### 6. HaveIBeenPwned API
**Type:** Credential Breach Data
**Free Tier:** Tiered - subscription for domain search
**Rate Limit:** Varies by tier
**Purpose:** Email breach checking
**Documentation:** https://haveibeenpwned.com/API/v3
**Implementation Notes:**
- Check if email/address has been leaked in data breaches
- May require API key for domain-specific searches

```python
# TODO: veritas/osint/sources/haveibeenpwned.py
class HaveIBeenPwnedSource:
    BASE_URL = "https://haveibeenpwned.com/api/v3"
```

### 7. Hunter.io Public API
**Type:** Email Finder / Professional Contact
**Free Tier:** Yes - 25 requests/month
**Rate Limit:** 25/month
**Purpose:** Professional email verification
**Documentation:** https://hunter.io/api/v2
**Implementation Notes:**
- Verify professional email addresses
- Check domain email patterns

```python
# TODO: veritas/osint/sources/hunter.py
class HunterSource:
    BASE_URL = "https://api.hunter.io/v2"
```

---

## Priority 4: Geolocation/IP Analysis (2 sources)

### 8. ipinfo.io Free API
**Type:** IP Geolocation / ASN Analysis
**Free Tier:** Yes - 50,000 requests/month
**Rate Limit:** 50K/month
**Purpose:** IP geolocation, ASN, ISP data
**Documentation:** https://ipinfo.io/developers
**Implementation Notes:**
- Get precise geolocation for IP addresses
- Identify hosting companies, ISPs

```python
# TODO: veritas/osint/sources/ipinfo.py
class IpInfoSource:
    BASE_URL = "https://ipinfo.io"
```

### 9. Shodan API (Free Tier)
**Type:** Internet-connected device scanning
**Free Tier:** Yes - 100 requests/month
**Rate Limit:** 100/month
**Purpose:** Infrastructure/Exposure detection
**Documentation:** https://developer.shodan.io/developing/api/
**Implementation Notes:**
- Previous research mentioned paid focus, but has free tier
- Use sparingly for exposed service detection

```python
# TODO: veritas/osint/sources/shodan.py
class ShodanSource:
    BASE_URL = "https://api.shodan.io"
```

---

## Implementation TODOs

### File Structure for Future Sources:
```
veritas/osint/sources/
├── __init__.py
├── dns_lookup.py          # ✅ DONE (08-01)
├── whois_lookup.py        # ✅ DONE (08-01)
├── ssl_verify.py          # ✅ DONE (08-01)
├── urlvoid.py             # ✅ DONE (08-02)
├── abuseipdb.py           # ✅ DONE (08-02)
├── alienvault.py          # TODO: Future expansion
├── spamhaus.py            # TODO: Future expansion
├── gsafebrowsing.py       # TODO: Future expansion
├── virustotal.py          # TODO: Future expansion
├── censys.py              # TODO: Future expansion
├── haveibeenpwned.py      # TODO: Future expansion
├── hunter.py              # TODO: Future expansion
├── ipinfo.py              # TODO: Future expansion
└── shodan.py              # TODO: Future expansion
```

### Registration in OSINTOrchestrator:
Update `veritas/osint/orchestrator.py` `_discover_sources()` method to register new sources:
```python
# Pattern for adding new sources
try:
    from veritas.osint.sources.{api_name} import {ClassName}
    api_key = getattr(settings, "{API_NAME_UPPER}_API_KEY", None)

    if api_key or not requires_api_key:
        self._register_source(
            ClassName(api_key) if requires_api_key else ClassName(),
            SourceConfig(
                enabled=True,
                priority=2,  # IMPORTANT
                requires_api_key=True,
                rate_limit_rpm=LIMIT,
                rate_limit_rph=LIMIT_HOURLY
            )
        )
except ImportError:
    pass
```

### Update SOURCE_TTLS in cache.py:
```python
SOURCE_TTLS = {
    # Existing
    "dns": timedelta(hours=24),
    "whois": timedelta(days=7),
    "ssl": timedelta(days=30),
    "abuseipdb": timedelta(hours=12),
    "urlvoid": timedelta(hours=24),

    # Future expansion
    "alienvault": timedelta(hours=6),
    "spamhaus": timedelta(hours=12),
    "gsafebrowsing": timedelta(hours=6),
    "virustotal": timedelta(hours=4),
    "censys": timedelta(hours=24),
    "haveibeenpwned": timedelta(days=7),
    "hunter": timedelta(hours=24),
    "ipinfo": timedelta(days=7),
    "shodan": timedelta(hours=24),
}
```

### Verification Criteria for Each New Source:
- [ ] Source returns valid OSINTResult with SourceStatus.SUCCESS
- [ ] Async wrapper prevents blocking event loop
- [ ] Error handling with proper logging
- [ ] Rate limiting enforced (RPM/RPH)
- [ ] Cache integration with appropriate TTL
- [ ] Fallback logic for source failures
- [ ] Tests pass for source implementation

---

## Notes

### API Key Configuration:
Add to `config.py`:
```python
# Future OSINT API Keys
ALIENVAULT_API_KEY = env("ALIENVAULT_API_KEY", default=None)
GOOGLE_SAFE_BROWSING_API_KEY = env("GOOGLE_SAFE_BROWSING_API_KEY", default=None)
VIRUSTOTAL_API_KEY = env("VIRUTOTAL_API_KEY", default=None)
CENSYS_API_ID = env("CENSYS_API_ID", default=None)
CENSYS_API_SECRET = env("CENSYS_API_SECRET", default=None)
HAVEIBEENPWNED_API_KEY = env("HAVEIBEENPWNED_API_KEY", default=None)
HUNTER_API_KEY = env("HUNTER_API_KEY", default=None)
IPINFO_API_KEY = env("IPINFO_API_KEY", default=None)
SHODAN_API_KEY = env("SHODAN_API_KEY", default=None)
```

### Prioritization for Implementation:
1. **Phase 8**: Implement 6 core sources (DNS, WHOIS, SSL, URLVoid, AbuseIPDB) ✅
2. **Phase 9**: Add top 3 threat intel APIs (AlienVault, Spamhaus, Google Safe Browsing)
3. **Phase 10**: Add domain reputation APIs (VirusTotal, Censys)
4. **Phase 11+:** Add email/social and geolocation sources as needed

---

*Created: 2026-02-27*
*Purpose: Document verified free API targets for OSINT expansion to 15+ sources*
