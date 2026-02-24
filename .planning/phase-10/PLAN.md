# Plan: Phase 10 - Cybersecurity Deep Dive

**Phase ID:** 10
**Milestone:** v2.0 Masterpiece Features
**Depends on:** Phase 9 (Judge System & Orchestrator) - Security findings feedJudge verdict
**Status:** pending
**Created:** 2026-02-23

---

## Context

### Current State (Pre-Phase)

**Security Analysis (`veritas/analysis/`):**
- Existing modules: Security headers, phishing checker, redirect analyzer, DOM analyzer
- Limited enterprise compliance checks (no OWASP Top 10, PCI DSS, GDPR)
- No CVSS scoring for findings
- No grouping by execution tier (fast/medium/deep)
- No darknet threat detection integration
- Security findings not mapped to CWE or CVSS

**Security Agent (`veritas/agents/security_agent.py`):**
- Empty SecurityAgent class (tech debt)
- Security node uses imperative module calls directly
- No agent pattern consistency
- No security results streaming

### Goal State (Post-Phase)

**25+ Enterprise Security Modules with CVSS Scoring:**
- OWASP Top 10 compliance (10 modules)
- PCI DSS compliance checks (5 modules)
- GDPR compliance checks (5 modules)
- TLS/SSL analysis (2 modules)
- Cookie security (2 modules)
- Content Security Policy analysis (1 module)
- Total: 25+ modules covering major compliance frameworks

**Darknet Threat Detection with Integration:**
- Threat feed correlation with security findings
- CVSS scoring for cyber security findings
- Calibration baseline from known-safe sites
- IOC integration from Phase 8

**Grouped Execution Tiers:**
- Fast tier: <5s checks (headers, basic TLS)
- Medium tier: <15s checks (CSP, cookies)
- Deep tier: <30s checks (full DOM analysis, compliance)

**SecurityAgent Pattern:**
- Consistent agent architecture
- Proper results serialization
- Security findings with CWE/CVSS metadata
- Real-time security progress streaming

---

## Implementation Strategy (Condensed)

### 10.1 Create Security Module Structure

**Files:**
- `veritas/analysis/security/owasp_top10.py` (new)
- `veritas/analysis/security/pci_dss.py` (new)
- `veritas/analysis/security/gdpr.py` (new)

**25+ Modules:**

**OWASP Top 10 (2021):**
1. A01: Broken Access Control
2. A02: Cryptographic Failures
3. A03: Injection (extends existing)
4. A04: Insecure Design
5. A05: Security Misconfiguration
6. A06: Vulnerable/Outdated Components
7. A07: Authentication Failures
8. A08: Data Integrity Failures
9. A09: Security Logging Failures
10. A10: SSRF (extends existing)

**PCI DSS:**
11. SSL/TLS Compliance
12. Data Encryption in Transit
13. Secure Authentication
14. Vulnerability Scanning (placeholder)
15. Compliance Documentation

**GDPR:**
16. Cookie Consent
17. Data Privacy Policy
18. Right to Deletion
19. Data Portability
20. Contact Privacy Officer

**Additional:**
21. TLS 1.3 Enforcement
22. HSTS Implementation
23. Secure Cookies (HttpOnly, Secure, SameSite)
24. CSP Analysis
25. X-Frame-Options
26. X-Content-Type-Options

### 10.2 Implement Security Module Base Class

```python
# veritas/analysis/security/base.py (new)
class SecurityModule:
    def __init__(self):
        self.timeout = 10
        self.tier = 'medium'  # 'fast', 'medium', 'deep'

    async def analyze(self, url: str, dom_meta: dict) -> SecurityFinding:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError
```

### 10.3 Create SecurityAgent with Grouped Execution

```python
# veritas/agents/security_agent.py (rewrite)
class SecurityAgent:
    tiers = {
        'fast': [SSLModule, SecurityHeaderAnalyzer],
        'medium': [CSPModule, CookieSecurityModule],
        'deep': [OWASPModule, PCIModule, GDPRModule, DOMSecurityModule]
    }

    async def analyze(self, url: str, scout_result: ScoutResult) -> SecurityResult:
        findings = []

        # Execute fast tier (parallel)
        fast_tasks = [mod().analyze(url) for mod in self.tiers['fast']]
        fast_results = await asyncio.gather(*fast_tasks)
        findings.extend(fast_results)

        # Execute medium tier
        medium_tasks = [mod().analyze(url) for mod in self.tiers['medium']]
        medium_results = await asyncio.gather(*medium_tasks)
        findings.extend(medium_results)

        # Execute deep tier (sequential)
        for mod in self.tiers['deep']:
            deep_result = await mod().analyze(url, scout_result.dom_metadata)
            findings.append(deep_result)

        return SecurityResult(findings=findings)
```

### 10.4 CVSS Integration from Phase 9

```python
# Use CVSSCalculator from Phase 9
# Map security findings to CWE/CVSS
for finding in findings:
    cwe = cwemapper.map_finding_to_cwe(finding.category)
    cvss_score = cvss_calculator.calculate_base_score_from_finding(finding)
    finding.cwe = cwe
    finding.cvss_score = cvss_score
```

### 10.5 Darknet Threat Integration

```python
# Integrate darknet analysis from Phase 8
darknet_intel = DarknetThreatIntel(offline feeds)
darknet_findings = darknet_intel.analyze_exposure(domain, entity_keywords)

# Correlate with security findings
for finding in findings:
    if finding.category in ['sql_injection', 'xss', 'csrf']:
        finding.darknet_exposure = darknet_findings['has_exposure']
```

---

## Dependencies (What Must Complete First)

### Internal (Within Phase 10)
1. **Security Module Base → Specific Modules**: Create base class first, then implement all modules extending it
2. **CVSS Calculator Integration → SecurityAgent**: Integrate CVSS from Phase 9 before SecurityAgent produces results
3. **Darknet Intel → SecurityAgent**: Correlate findings after both are implemented

### External (From Previous Phases)
1. **Phase 7 (Quality Foundation)**: Multi-source validated findings from earlier phases feed security analysis
2. **Phase 8 (OSINT Integration)**: IOC extraction and threat feed data used for darknet correlation
3. **Phase 9 (Judge System)**: CVSSCalculator and CWEMapper used for scoring security findings
4. **Phase 1-5 (v1.0 Core)**: ✅ DONE

### Blocks for Future Phases
1. **Phase 11 (Showcase)**: Security findings with CVSS scores enrich the Agent Theater display

---

## Test Strategy

### Unit Tests

**Test: OWASP A01 Broken Access Control detection**
```python
def test_owasp_a01_no_role_check():
    module = BrokenAccessControlModule()
    dom_meta = {
        'admin_panel': {'exists': True, 'requires_role': False}
    }

    finding = await module.analyze('http://example.com', dom_meta)

    assert finding.category == 'broken_access_control'
    assert finding.severity == 'critical'
```

**Test: PCI DSS SSL compliance**
```python
def test_pci_ssl_requires_1_2_plus():
    module = SSLComplianceModule()
    ssl_info = {'tls_version': '1.0', 'has_ssl': True}

    finding = await module.is_compliant(ssl_info)

    assert not finding.is_compliant
    assert 'TLS 1.2 or higher' in finding.message
```

**Test: GDPR cookie consent**
```python
def test_gdpr_cookie_consent_required():
    module = GDPRModule()
    cookies = [
        {'name': 'analytics', 'consent_banner': False, 'has_consent': False}
    ]

    finding = await module.check_cookie_compliance(cookies)

    assert finding.violation == 'missing_consent_banner'
```

**Test: Security module tier assignment**
```python
def test_module_tier_classification():
    fast_module = SSLModule()
    medium_module = CSPModule()
    deep_module = OWASPModule()

    assert fast_module.tier == 'fast'
    assert fast_module.timeout <= 5

    assert medium_module.tier == 'medium'
    assert medium_module.timeout <= 15

    assert deep_module.tier == 'deep'
    assert deep_module.timeout <= 30
```

---

### Integration Tests

**Test: SecurityAgent executes all modules in tiers**
```python
@pytest.mark.asyncio
async def test_security_agent_tiered_execution():
    agent = SecurityAgent()
    scout_result = ScoutResult(url='http://example.com', dom_metadata={})

    result = await agent.analyze(scout_result.url, scout_result)

    # Should have findings from all tiers
    assert len(result.findings) > 0

    # Fast, medium, deep checks should all run
    categories = [f.category for f in result.findings]
    assert 'ssl_compliance' in categories  # Fast
    assert 'csp_analysis' in categories  # Medium
    assert any('owasp' in c for c in categories)  # Deep
```

**Test: CVSS scoring integration from Phase 9**
```python
@pytest.mark.asyncio
async def test_security_findings_have_cvss_scores():
    agent = SecurityAgent()
    cvss_calculator = CVSSCalculator()  # From Phase 9

    result = await agent.analyze('http://example.com', ScoutResult(url='http://example.com'))

    # Critical findings should have high CVSS scores
    for finding in result.findings:
        if finding.severity == 'critical':
            assert finding.cvss_score >= 8.0
            assert finding.cwe is not None
```

**Test: Darknet threat correlation**
```python
@pytest.mark.asyncio
async def test_darknet_threat_correlation():
    darknet_intel = DarknetThreatIntel(offline_feeds=True)
    security_agent = SecurityAgent()

    # URL flagged in darknet feeds
    url = 'http://known-malicious-domain.com'
    result = await security_agent.analyze(url, ScoutResult(url=url))

    # Findings should be elevated due to darknet exposure
    critical_findings = [f for f in result.findings if f.severity == 'critical']
    assert len(critical_findings) > 0
```

---

### Performance Tests

**Test: Fast tier modules complete in <5 seconds**
```python
@pytest.mark.asyncio
async def test_fast_tier_speed():
    agent = SecurityAgent()

    start = time.time()
    fast_results = []
    for mod in agent.tiers['fast']:
        result = await mod().analyze('http://example.com', {})
        fast_results.append(result)
    elapsed = time.time() - start

    assert elapsed < 5.0
    assert len(fast_results) >= 2  # SSL + headers
```

**Test: Medium tier modules complete in <15 seconds**
```python
@pytest.mark.asyncio
async def test_medium_tier_speed():
    agent = SecurityAgent()

    start = time.time()
    medium_results = []
    for mod in agent.tiers['medium']:
        result = await mod().analyze('http://example.com', {})
        medium_results.append(result)
    elapsed = time.time() - start

    assert elapsed < 15.0
    assert len(medium_results) >= 2  # CSP + cookies
```

**Test: All 25+ modules complete in <60 seconds**
```python
@pytest.mark.asyncio
async def test_all_modules_parallel_execution():
    agent = SecurityAgent()

    start = time.time()
    full_result = await agent.analyze('http://example.com', ScoutResult(url='http://example.com', dom_metadata={}))
    elapsed = time.time() - start

    # Should complete entire security audit in <60 seconds
    assert elapsed < 60.0
    assert len(full_result.findings) >= 10  # Multiple findings expected
```

**Test: Calibration - known-safe sites get low CVSS scores**
```python
@pytest.mark.asyncio
async def test_calibration_baseline():
    agent = SecurityAgent()

    # Known safe domains (google.com, github.com)
    safe_sites = ['https://www.google.com', 'https://github.com']

    for url in safe_sites:
        result = await agent.analyze(url, ScoutResult(url=url))

        # Should have CVSS scores < 4.0 (non-critical)
        high_cvss = [f for f in result.findings if f.cvss_score >= 8.0]
        assert len(high_cvss) == 0  # No critical findings on safe sites
```

---

## Success Criteria (When Phase 10 Is Done)

### Must Have
1. ✅ 25+ security modules implemented
2. ✅ OWASP Top 10 coverage (A01-A10)
3. ✅ PCI DSS basic checks
4. ✅ GDPR basic checks
5. ✅ CVSS scores for security findings
6. ✅ Darknet threat correlation

### Should Have
1. ✅ Grouped execution tiers (fast/medium/deep)
2. ✅ SecurityAgent pattern consistency
3. ✅ Real-time security progress streaming
4. ✅ Calibration baseline testing

---

## Requirements Covered

| Requirement | Status | Notes |
|-------------|--------|-------|
| SEC-01 | 📝 Covered | 25+ modules, OWASP/PCI/GDPR |
| SEC-02 | 📝 Covered | Darknet threat detection with CVSS |

---

*Plan created: 2026-02-23*
*Next phase: Phase 11 (Agent Theater & Content Showcase)*
