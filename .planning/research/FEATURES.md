# Feature Landscape: VERITAS v2.0 Masterpiece Features

**Domain:** Forensic Web Auditing Platform Enhancement
**Researched:** 2026-02-23

---

## Table Stakes

Features users expect in a forensic web auditing platform. Missing = product feels incomplete.

| Feature | Category | Why Expected | Complexity | Notes |
|---------|----------|--------------|------------|-------|
| Real-time audit progress showcase | Showcase | Users need visibility into analysis status | Low | Already planned - Agent Theater components |
| Screenshot visualization with highlights | Showcase | Visual evidence is core to forensic analysis | Medium | Screenshot carousel with highlight overlays |
| Domain verification (whois, DNS) | OSINT | Basic entity verification expected | Low | Already have python-whois, dnspython |
| SSL certificate validation | OSINT | Security baseline requirement | Low | cryptography library needed |
| Malicious URL checking (VirusTotal) | OSINT | Threat intelligence expected | Medium | API integration req |
| SQL injection detection | Security | OWASP Top 10 requirement | High | Use sqlparse for pattern detection |
| XSS detection | Security | OWASP Top 10 requirement | Medium | beautifulsoup4 + regex |
| Security headers analysis | Security | Standard security audit component | Low | requests library |
| Dark pattern detection | Vision | Core product differentiation | High | VLM + CV approach |
| Dual-tier verdict (technical + non-technical) | Judge | Serve both professionals and general users | Medium | Use existing pydantic + LangChain |

---

## Differentiators

Features that set VERITAS apart from competitors. Not expected but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 5-pass Vision Agent pipeline | Sophisticated multi-modal analysis catches 95%+ dark patterns | High | Passes: full scan, elements, deception, content, temporal |
| 15+ OSINT intelligence sources | Deep entity verification beats single-source tools | Medium | Combines domain intel, threat intel, business verification |
| Darknet exposure monitoring | Unique threat surface analysis rarely available | High | Threat feed approach recommended |
| 11 site-type-specific strategies | Context-aware scoring outperforms generic tools | Medium | E-commerce, financial services, darknet, etc. |
| Computer vision temporal analysis | Detects dynamic scams (timer fraud, price changes) | High | OpenCV SSIM, optical flow |
| Psychology-driven agent persona showcase | Engaging presentation makes audit memorable | Medium | Agent task flexing, personality |
| Gradual screenshot reveal | Creates suspense, mimics real investigation | Low | Screenshot carousel with auto-play |
| 25+ enterprise security modules | Comprehensive audit exceeds typical scanners | Medium | OWASP, PCI DSS, GDPR compliance |
| Knowledge graph visualization | Shows entity relationships for deep insights | Medium | NetworkX already available |

---

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Port scanning (NMAP) | Requires sudo/root privileges, not applicable to web apps | Stick to HTTP/HTTPS security analysis |
| Paid API integrations (Shodan, Censys) | Budget constraints, free alternatives sufficient | Use whois, DNS, VirusTotal free tier |
| Full automated exploitation | Ethical/legal concerns; thesis scope = reporting | Report findings, no exploitation |
| Tor/onion service scraping | Legal risk; dark web access creates liability | Use threat feeds from security vendors |
| Social media login automation | Privacy concerns, out of scope for forensic audit | Business verification APIs only |
| 3D visualization | Unnecessary for 2D web screenshots | 2D carousel with highlight overlays |
| Real-time threat alerting | Monitoring infrastructure beyond thesis scope | Batch audit results only |
| Multi-user authentication system | Out of scope per PROJECT.md | Single-server deployment only |
| Blockchain/crypto analysis | Outside scope of web auditing | Focus on web-based scams (not blockchain) |

---

## Feature Dependencies

Vision Agent -> Screenshot Carousel (needs visual evidence)
Vision Agent -> Progress Emitter (needs pass completion events)
OSINT Engine -> Knowledge Graph (needs OSINT data nodes)
OSINT Darknet -> Advanced Threat Analyzer (needs darknet findings)
Security Modules -> Judge Verdict (needs vulnerability list)
Judge Dual-Tier -> Agent Theater (needs verdict for showcase)
Progress Emitter -> Agent Theater (consumes websocket events)
Agent Theater -> Running Log (consumes log events)
Screenshot Carousel -> Progress Emitter (needs screenshot URLs)

---

## MVP Recommendation

For VERITAS v2.0 masterpiece features (6-week timeline):

Phase 1 Priority (Vision - Week 1-2):
1. 5-pass Vision Agent with VLM integration
2. Temporal CV analysis (OpenCV SSIM, optical flow)
3. Progress emitter for real-time showcase
4. Basic Agent Theater component

Phase 2 Priority (OSINT - Week 3):
1. 5+ OSINT sources (domain intel, threat intel)
2. Darknet threat feed integration
3. Enhanced Graph Investigator with OSINT nodes

Phase 3 Priority (Judge - Week 4):
1. Dual-tier verdict data classes
2. 3-5 site-type strategies (e-commerce, financial, portfolio)
3. Non-technical verdict templates

Phase 4 Priority (Security - Week 5):
1. 10+ OWASP security modules
2. CVSS scoring integration
3. Darknet threat detection (threat feed correlation)

Phase 5 Priority (Showcase - Week 6):
1. Complete Agent Theater with all agents
2. Screenshot carousel with highlight overlays
3. Running log with task flexing
4. Full integration of all showcase components

Defer:
- Full 15 OSINT sources -> Start with 5, add incrementally
- Full 11 site-type strategies -> Start with 3-5 most common
- Full 25 security modules -> Start with 10 OWASP Top 10
- Darknet marketplace direct scraping -> Use threat feeds only

---

## Sources

- VERITAS IMPLEMENTATION_PLAN.md (feature requirements detailed)
- VERITAS PROJECT.md (existing capabilities confirmed)
- OWASP Top 10 2021 (security module categories)
- CVSS (Common Vulnerability Scoring System v3.1)
