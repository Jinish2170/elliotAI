# VERITAS Masterpiece Upgrade Plan

## Executive Summary

Transform VERITAS from a functional prototype into a **production-grade forensic web auditor** with:
- Consistent, high-accuracy results
- Deep technical analysis (covering darknet-level sites)
- Mature site-type-specific auditing
- Dual-tier verdict system (Technical + Non-Technical)
- Enhanced OSINT capabilities
- Robust lifecycle management

---

## Critical Issues Identified

### 1. Inconsistent Accuracy
**Root Causes:**
- Vision agent prompts not sophisticated enough
- OSINT verification too shallow
- Trust scoring lacks context-aware weighting
- Missing multi-pass verification

**Solution:** Implement confidence triangulation, multi-source verification, and ensemble scoring

### 2. Missing Audit Data
**Root Causes:**
- Evidence capture incomplete
- Lifecycle transitions lose data
- No persistent state across agent phases
- Weak event streaming

**Solution:** Implement complete evidence ledger, state persistence, and comprehensive event model

### 3. Weak Lifecycle Management
**Root Causes:**
- No proper phase gates/quality checkpoints
- No recovery from agent failures
- No budget enforcement per phase
- Missing audit session management

**Solution:** Implement state machine with rollback, quality gates, and session persistence

### 4. Lacks Technical Depth
**Root Causes:**
- Surface-level security checks only
- No advanced threat intelligence
- Missing deep web/darknet analysis
- No sophisticated OSINT

**Solution:** Add threat intelligence feeds, darknet monitoring, and advanced security analysis

---

## PHASE 1: Enhanced Vision Agent

### Goals
- 95%+ dark pattern detection accuracy
- Multi-pass screenshot analysis
- Sophisticated VLM prompt engineering
- Better temporal comparison

### Implementation

#### 1.1 Multi-Pass Analysis Pipeline
```python
# agents/vision.py - Enhanced version

class VisionAgentEnhanced:
    def __init__(self):
        self.passes = [
            "full_page_scan",      # Complete page overview
            "element_interaction", # Interactive elements focus
            "deceptive_patterns",  # Dark pattern specific
            "content_analysis",    # Trustworthiness cues
            "screenshot_temporal"  # Time-based comparison
        ]

    async def analyze_screenshot_multi_pass(self, screenshot_path: str):
        results = []
        for pass_name in self.passes:
            prompt = self._build_pass_prompt(pass_name)
            result = await self.nim_client.analyze_image(screenshot_path, prompt)
            results.append({"pass": pass_name, ...})

        # Enemble confidence averaging
        return self._ensemble_results(results)
```

#### 1.2 Sophisticated VLM Prompts
```python
# config/dark_patterns.py - Enhanced taxonomy

ENHANCED_DARK_PATTERNS = {
    "visual_interference": {
        "vulnerability_scan": """
Scan this screenshot for visual manipulation tactics:
1. Button size hierarchy: Measure Accept vs Decline button dimensions
2. Color contrast analysis: Compare action button colors vs background
3. Visual flow path: Trace what elements draw the eye first
4. Hidden elements: Look for opacity <0.5, negative margins, overflow:hidden
5. Misleading proximity: Analyze spacing between related vs unrelated elements

Return structured JSON with measurements, confidence scores, and visual coordinates.
""",

        "micro_influences": """
Detect subtle behavioral nudges:
1. Default selection states (radio/checkbox pre-selection)
2. Opt-out vs opt-in architecture
3. Progressive disclosure (revealing info gradually)
4. Choice architecture (how options are presented)
5. Cognitive load manipulation (information overload/underload)

Analyze for each detection and provide UX psychology rationale.
"""
    },

    "false_urgency": {
        "temporal_fraud_detection": """
Detect fake urgency and temporal manipulation:
1. Examine any countdown timers or clocks - note exact values and locations
2. Check for changing numbers ("3 left", "15 viewing") that might be dynamic
3. Look for time-based claims (24h only, expires today)
4. Analyze if urgency elements use real-time updates or static content
5. Detect artificial scarcity (limited slots, waiting lists)

Provide: Timer values, detection of reset behavior, authenticity assessment.
""",

        "psychological_pressure": """
Analyze psychological pressure tactics:
1. Loss aversion framing ("don't miss", "last chance")
2. Social proof engineering ("15 people viewing now")
3. Authority leverage (stock photos of "experts", fake testimonials)
4. Commitment consistency (pre-filled forms, saved cart)
5. Choice reduction (hidden alternatives, forced options)

Rate each tactic from 0-10 and explain manipulation mechanism.
"""
    }
}
```

#### 1.3 Better Temporal Comparison
```python
# analysis/temporal_analyzer.py - Enhanced

class TemporalAnalyzerEnhanced:
    async def compare_screenshots(
        self,
        screenshot_a: str,  # t=0
        screenshot_b: str   # t=delay
    ) -> TemporalResult:
        # 1. Computer vision diff
        visual_diff = await self._compute_visual_diff(screenshot_a, screenshot_b)

        # 2. Text extraction and comparison
        text_diff = await self._compare_text_extracts

        # 3. Timer/analytics element tracking
        timer_analysis = await self._track_timer_elements(screenshot_a, screenshot_b)

        # 4. Dynamic content detection
        dynamic_changes = await self._detect_dynamic_content(screenshot_a, screenshot_b)

        # 5. Fraudulent temporal pattern detection
        fraud_patterns = self._detect_temporal_fraud(timer_analysis)

        return TemporalResult(
            visual_changes=visual_diff,
            text_changes=text_diff,
            timer_fraud=fraud_patterns,
            dynamic_content=dynamic_changes,
            confidence=self._compute_confidence(...)
        )
```

---

## PHASE 2: Powerful OSINT & Graph Agent

### Goals
- Enterprise-level OSINT verification
- Multi-source intelligence gathering
- Darknet/marketplace monitoring
- Deep web analysis support
- 10+ intelligence sources

### Implementation

#### 2.1 Enhanced OSINT Sources
```python
# core/os_intelligence.py - NEW MODULE

class OSIntelligenceEngine:
    """Enhanced OSINT with 15+ intelligence sources"""

    def __init__(self):
        self.sources = {
            # Domain Intelligence
            "whois": self._whois_lookup,
            "dns_records": self._dns_analysis,
            "ssl_certificate": self._ssl_cert_analysis,
            "domain_age": self._domain_age_calculation,
            "domain_history": self._domain_history_lookup,

            # Reputation & Threat Intelligence
            "google_safe_browsing": self._gsb_check,
            "virus_total": self._virus_total_check,
            "phishtank": self._phishtank_check,
            "urlhaus": self._urlhaus_check,
            "abuse_ch": self._abuse_ch_check,

            # Business Verification
            "business_registry": self._business_registry_search,
            "linkedin_verification": self._linkedin_company_check,
            "yelp_google_maps": self._local_business_verification,

            # Social Media & Presence
            "social_media_sherlock": self._social_media_profiles,
            "reputation_analysis": self._reputation_aggregator,

            # Darknet & Deep Web
            "darknet_monitor": self._darknet_marketplace_check,
            "tor_exits": self._tor_exit_node_check,
            "i2p_freifunk": self._alternative_network_check,

            # Technical Fingerprinting
            "server_headers": self._server_fingerprint,
            "web_tech_stack": self._wappalyzer_scan,
            "cdn_analysis": self._cdn_providers,
            "ip_geolocation": self._ip_geo_analysis,
            "asn_analysis": self._asn_lookup,

            # Content Analysis
            "content_hash": self._content_fingerprinting,
            "phishing_signatures": self._phishing_pattern_match,
            "ml_probability": self._ml_threat_score
        }

    async def full_osint_sweep(self, domain: str) -> OSIntReport:
        """Run complete OSINT sweep with parallel execution"""
        results = {}

        # Parallel execution of all sources
        tasks = [source(domain) for source in self.sources.values()]
        source_results = await asyncio.gather(*tasks, return_exceptions=True)

        for source_name, result in zip(self.sources.keys(), source_results):
            results[source_name] = result

        # Intelligence fusion
        fused = self._fuse_intelligence(results)

        # Anomaly detection
        anomalies = self._detect_anomalies(results, fused)

        # Trust assessment
        trust_score = self._compute_osint_trust_score(fused, anomalies)

        return OSIntReport(
            raw_results=results,
            fused_intelligence=fused,
            anomalies=anomalies,
            trust_score=trust_score,
            risk_level=self._classify_risk(trust_score),
            recommendations=self._generate_recommendations(fused, anomalies)
        )
```

#### 2.2 Darknet Analysis Support
```python
# core/darknet_analyzer.py - NEW MODULE

class DarknetAnalyzer:
    """Support for darknet/marketplace monitoring"""

    def __init__(self):
        self.monitored_markets = [
            "AlphaBay", "Dream Market", "Wall Street Market",
            "Empire Market", "Cannazon", "Tochka"
        ]
        self.phishing_kits = self._load_phishing_kits_database()

    async def check_darknet_mentions(self, domain: str) -> DarknetResult:
        """Check if domain is mentioned on darknet marketplaces"""
        results = []

        for marketplace in self.monitored_markets:
            try:
                mentions = await self._scan_marketplace(domain, marketplace)
                if mentions:
                    results.append({
                        "marketplace": marketplace,
                        "mentions": mentions,
                        "listings": await self._extract_listings(mentions),
                        "risk_level": "CRITICAL" if len(mentions) > 0 else "NONE"
                    })
            except Exception as e:
                logger.warning(f"Darknet scan failed for {marketplace}: {e}")

        # Check against phishing kits
        kit_matches = await self._check_phishing_kits(domain)

        return DarknetResult(
            marketplace_mentions=results,
            phishing_kit_matches=kit_matches,
            overall_risk_level=self._compute_darknet_risk(results, kit_matches),
            actionable_intel=self._extract_actionable_intel(results, kit_matches)
        )

    async def check_phishing_kits(self, domain: str) -> PhishingKitResult:
        """Check if domain matches known phishing kits"""
        # Database of known phishing kit signatures
        signatures = await self._load_phishing_kit_signatures()

        matches = []
        for signature in signatures:
            if await self._matches_signature(domain, signature):
                matches.append({
                    "kit_name": signature["name"],
                    "kit_type": signature["type"],
                    "target_brand": signature["target"],
                    "last_seen": signature["last_active"],
                    "known_victims": signature["victim_count"]
                })

        return PhishingKitResult(
            matches=matches,
            risk_level="CRITICAL" if matches else "NONE"
        )
```

#### 2.3 Enhanced Graph Agent
```python
# agents/graph_investigator.py - Enhanced version

class GraphInvestigatorEnhanced:
    def __init__(self):
        self.osint_engine = OSIntelligenceEngine()
        self.darknet_analyzer = DarknetAnalyzer()
        self.graph_engine = KnowledgeGraphEngine()

    async def investigate(self, domain: str, site_type: str) -> GraphInvestigationResult:
        # 1. Deep OSINT sweep
        osint_report = await self.osint_engine.full_osint_sweep(domain)

        # 2. Darknet monitoring
        darknet_result = await self.darknet_analyzer.check_darknet_mentions(domain)

        # 3. Build comprehensive entity graph
        graph = await self._build_entity_graph(
            domain=domain,
            osint_data=osint_report,
            darknet_data=darknet_result,
            site_type=site_type
        )

        # 4. Graph analysis
        anomalies = await self.graph_engine.detect_anomalies(graph)
        suspicious_subgraphs = await self.graph_engine.find_suspicious_clusters(graph)

        # 5. Cross-reference verification
        verification_status = await self._cross_reference_verify(
            graph=graph,
            entity_claims=self._extract_entity_claims(domain),
            external_sources=osint_report
        )

        # 6. Enhanced scoring
        entity_trust_score = self._compute_entity_trust_score(
            graph=graph,
            anomalies=anomalies,
            verification=verification_status,
            darknet_risk=darknet_result.overall_risk_level
        )

        return GraphInvestigationResult(
            osint_report=osint_report,
            darknet_result=darknet_result,
            entity_graph=graph,
            anomalies=anomalies,
            suspicious_clusters=suspicious_subgraphs,
            verification_status=verification_status,
            trust_score=entity_trust_score,
            findings=self._generate_findings(...)
        )
```

---

## PHASE 3: Sophisticated Judge Agent

### Goals
- Dual-tier verdict system (Technical + Non-Technical)
- Context-aware, site-type-specific scoring
- User-customizable criteria
- Sophisticated risk assessment
- Actionable, specific recommendations

### Implementation

#### 3.1 Dual-Tier Verdict System
```python
# agents/judge.py - Enhanced version

class JudgeAgentEnhanced:
    @dataclass
    class VerdictTechnical:
        """For security professionals & technical users"""
        trust_score: int  # 0-100
        risk_level: str
        signal_breakdown: Dict[str, int]
        raw_findings: List[Finding]
        ioc_indicators: List[str]  # Indicators of Compromise
        cwe_mapping: List[str]      # Common Weakness Enumeration
        attack_vectors: List[str]
        cvss_score: float           # Common Vulnerability Scoring System
        technical_metadata: Dict

    @dataclass
    class VerdictNonTechnical:
        """For general users - simplified language"""
        trust_score: int  # 0-100
        risk_level: str
        plain_english_summary: str
        what_this_means: str
        key_findings: List[str]
        what_to_do_here: List[str]
        what_to_avoid: List[str]
        red_flags: List[str]
        green_flags: List[str]

    async def render_verdict(
        self,
        evidence: AuditEvidence,
        user_type: str = "non_technical"  # or "technical", "both"
    ) -> Judgement:
        """Generate dual-tier verdict"""

        # 1. Compute sophisticated trust score
        trust_score = await self._compute_sophisticated_trust_score(evidence)

        # 2. Determine risk level with nuance
        risk_level = self._determine_nuanced_risk_level(trust_score, evidence)

        # 3. Generate technical verdict
        technical_verdict = await self._generate_technical_verdict(
            evidence, trust_score, risk_level
        )

        # 4. Generate non-technical verdict
        non_technical_verdict = await self._generate_non_technical_verdict(
            evidence, trust_score, risk_level
        )

        # 5. Site-type-specific context
        site_context = await self._add_site_type_context(
            evidence.site_type,
            technical_verdict,
            non_technical_verdict
        )

        # 6. User-customizable criteria application
        user_customized = await self._apply_user_criteria(
            evidence,
            [technical_verdict, non_technical_verdict],
            user_type
        )

        return Judgement(
            technical=technical_verdict,
            non_technical=non_technical_verdict,
            site_context=site_context,
            recommendations=await self._generate_recommendations(evidence),
            user_customized=user_customized
        )

    async def _generate_non_technical_verdict(
        self,
        evidence: AuditEvidence,
        trust_score: int,
        risk_level: str
    ) -> VerdictNonTechnical:
        """Simplified language for non-technical users"""

        # Use NIM LLM to generate plain English summary
        summary_prompt = f"""
        Analyze these findings about {evidence.url} and write a 2-sentence summary
        in simple, non-technical language that a 70-year-old grandparent would understand.
        Avoid all jargon. Use analogies if helpful.

        Key findings:
        - Trust score: {trust_score}/100
        - Risk level: {risk_level}
        - Dark patterns found: {len(evidence.dark_patterns)}
        - Security issues: {len(evidence.security_findings)}
        """

        summary = await self.nim_client.generate_text(summary_prompt)

        # What this means in context
        context_prompt = f"""
        Explain what the {trust_score} trust score means in practical terms for
        someone wondering if they should trust this website. What does this score
        say about their safety, privacy, and ability to make informed decisions?
        Keep it simple, actionable, and reassuring or caution-appropriate.
        """

        what_this_means = await self.nim_client.generate_text(context_prompt)

        # Key findings - converted from technical to plain English
        key_findings = await self._plain_english_converter(evidence)

        # Actionable advice
        what_to_do_here = await self._generate_actionable_advice(evidence, risk_level)
        what_to_avoid = await self._generate_avoidance_advice(evidence, risk_level)

        # Red and green flags
        red_flags = self._extract_red_flags(evidence)
        green_flags = self._extract_green_flags(evidence)

        return VerdictNonTechnical(
            trust_score=trust_score,
            risk_level=risk_level,
            plain_english_summary=summary,
            what_this_means=what_this_means,
            key_findings=key_findings,
            what_to_do_here=what_to_do_here,
            what_to_avoid=what_to_avoid,
            red_flags=red_flags,
            green_flags=green_flags
        )

    async def _generate_technical_verdict(
        self,
        evidence: AuditEvidence,
        trust_score: int,
        risk_level: str
    ) -> VerdictTechnical:
        """Detailed verdict for security professionals"""

        # Signal breakdown with context
        signal_breakdown = {
            "visual_intelligence": evidence.vision_score,
            "structural_analysis": evidence.dom_score,
            "temporal_integrity": evidence.temporal_score,
            "entity_verification": evidence.OSINT_score,
            "metadata_validation": evidence.meta_score,
            "security_audit": evidence.security_score
        }

        # IOC indicators
        iocs = self._extract_IOCs(evidence)

        # CWE mapping
        cwes = self._map_to_CWE(evidence.security_findings)

        # Attack vectors
        attack_vectors = self._identify_attack_vectors(evidence)

        # CVSS score
        cvss_score = self._compute_cvss_score(evidence.security_findings)

        # Technical metadata
        tech_metadata = {
            "scan_depth": evidence.pages_analyzed + evidence.screenshots_captured,
            "ai_confidence": evidence.overall_confidence,
            "osint_sources": len(evidence.osint_sources),
            "darknet_risk": evidence.darknet_risk_level,
            "threat_intelligence": evidence.threat_intelligence_score
        }

        return VerdictTechnical(
            trust_score=trust_score,
            risk_level=risk_level,
            signal_breakdown=signal_breakdown,
            raw_findings=evidence.all_findings,
            ioc_indicators=iocs,
            cwe_mapping=cwes,
            attack_vectors=attack_vectors,
            cvss_score=cvss_score,
            technical_metadata=tech_metadata
        )
```

#### 3.2 Site-Type-Specific Scoring
```python
# config/site_type_scoring.py - NEW MODULE

SITE_TYPE_SCORING_STRATEGIES = {
    "e_commerce": {
        "weighted_signals": {
            "visual_intelligence": 0.20,  # Deceptive pricing, fake reviews
            "structural_analysis": 0.15,  # Form security, payment flows
            "temporal_integrity": 0.20,  # Fake urgency, countdown fraud
            "entity_verification": 0.25,  # Business registration, reviews
            "metadata_validation": 0.10,  # SSL, domain age
            "security_audit": 0.20        # Payment security, data protection
        },
        "critical_checks": [
            "payment_form_security",
            "review_authenticity",
            "pricing_fraud",
            "subscription_terms",
            "refund_policy",
            "customer_support_verification"
        ],
        "dark_pattern_focus": [
            "drip_pricing",
            "hidden_subscription",
            "fake_countdown",
            "stock_scarcity_manipulation",
            "confirmshaming"
        ],
        "security_focus": [
            "PCI_DSS_compliance",
            "payment_gateway_verification",
            "SSL_certificate_validity",
            "data_encryption",
            "GDPR_compliance"
        ]
    },

    "portfolio": {
        "weighted_signals": {
            "visual_intelligence": 0.15,
            "structural_analysis": 0.10,
            "temporal_integrity": 0.05,
            "entity_verification": 0.35,  # CRITICAL - verify company exists
            "metadata_validation": 0.20,
            "security_audit": 0.15
        },
        "critical_checks": [
            "company_registration",
            "physical_address_verification",
            "team_member_verification",
            "portfolio_authenticity",
            "client testimonials_verification",
            "case_study_verification"
        ],
        "dark_pattern_focus": [
            "fake_projects",
            "inflated_client_list",
            "fake_certifications",
            "misleading_case_studies",
            "stock_team_photos"
        ],
        "security_focus": [
            "SSL_certificate",
            "contact_form_security",
            "data_collection_transparency"
        ]
    },

    "financial_services": {
        "weighted_signals": {
            "visual_intelligence": 0.15,
            "structural_analysis": 0.15,
            "temporal_integrity": 0.10,
            "entity_verification": 0.30,  # CRITICAL - regulatory compliance
            "metadata_validation": 0.15,
            "security_audit": 0.25        # CRITICAL - financial security
        },
        "critical_checks": [
            "regulatory_licensing",      # SEC, FCA, etc.
            "financial_authorization",
            "institution_verification",
            "deposit_protection",
            "regulatory_compliance",
            "audit_trail"
        ],
        "dark_pattern_focus": [
            "misleading_returns",
            "hidden_fees",
            "complicated_terms",
            "fake_authority",
            "pressure_upsell"
        ],
        "security_focus": [
            "2FA_implementation",
            "encryption_standards",
            "PCI_DSS_compliance",
            "regulatory_audit_compliance",
            "fraud_detection_systems"
        ]
    },

    "social_media": {
        "weighted_signals": {
            "visual_intelligence": 0.10,
            "structural_analysis": 0.10,
            "temporal_integrity": 0.05,
            "entity_verification": 0.20,
            "metadata_validation": 0.20,
            "security_audit": 0.15,        # Privacy settings
            "content_authenticity": 0.20   # NEW - fake accounts, bots
        },
        "critical_checks": [
            "account_authenticity",
            "follower_fraud_detection",
            "engagement_authenticity",
            "content_originality",
            "privacy_settings",
            "data_handling_practices"
        ]
    },

    "darknet_marketplace": {
        "weighted_signals": {
            "visual_intelligence": 0.10,
            "structural_analysis": 0.15,
            "temporal_integrity": 0.05,
            "entity_verification": 0.40,  # CRITICAL - almost always anonymous
            "metadata_validation": 0.15,
            "security_audit": 0.15,
            "threat_level": 0.20           # NEW - explicit threat analysis
        },
        "critical_checks": [
            "exit_scam_detection",
            "vendor_verification",
            "escrow_service_check",
            "pgp_key_validity",
            "marketplace_age",
            "reputation_tracking"
        ],
        "threat_indicators": [
            "known_criminal_association",
            "illegal_product_categories",
            "fraud_complaints",
            "exit_scam_patterns",
            "law_enforcement_takedowns"
        ]
    }
}
```

---

## PHASE 4: Enhanced Security Audit

### Goals
- 20+ security modules
- OWASP Top 10 coverage
- Advanced vulnerability detection
- Payment industry standards
- GDPR/privacy compliance

### Implementation

#### 4.1 Comprehensive Security Audit
```python
# analysis/security_audit_comprehensive.py - NEW

class ComprehensiveSecurityAudit:
    """Enterprise-grade security assessment"""

    MODULES = {
        # Headers & Infrastructure
        "security_headers": SecurityHeadersAnalysis,
        "csp_analysis": ContentSecurityPolicyAnalyzer,
        "hsts_compliance": HSTSComplianceChecker,
        "x_frame_options": ClickjackingProtectionChecker,
        "cors_analysis": CORSConfigurationAnalyzer,

        # Input Validation & Injection
        "sql_injection": SQLInjectionScanner,
        "xss_detection": XSSDetector,
        "csrf_protection": CSRFProtectionChecker,
        "command_injection": CommandInjectionScanner,
        "ssrf_vulnerability": SSRFScanner,

        # Authentication & Session
        "auth_mechanisms": AuthenticationAnalyzer,
        "session_security": SessionSecurityAnalyzer,
        "brute_force_protection": BruteForceProtectionChecker,
        "password_policy": PasswordPolicyAnalyzer,

        # Data Protection & Privacy
        "tls_ssl_analysis": TLSSSLAnalyzer,
        "data_transmission": DataTransmissionSecurityAnalyzer,
        "data_storage": DataStorageSecurityAnalyzer,
        "privacy_policy": PrivacyPolicyAnalyzer,
        "cookie_security": CookieSecurityAnalyzer,

        # Payment & Financial
        "pci_dss_compliance": PCIDSSComplianceChecker,
        "payment_gateway": PaymentGatewayAnalyzer,
        "credit_card_handling": CreditCardSecurityAnalyzer,

        # Advanced Threat Intelligence
        "threat_feed_correlation": ThreatFeedCorrelator,
        "malicious_patterns": MaliciousPatternDetector,
        "botnet_indicators": BotnetIndicatorScanner,
        "cryptojacking": CryptoJackingDetector,
        "skimmer_detection": PaymentSkimmerScanner,

        # Business Logic
        "business_logic_flaws": BusinessLogicAnalyzer,
        "privilege_escalation": PrivilegeEscalationScanner,
        "rate_limiting": RateLimitingAnalyzer,
        "error_handling": ErrorHandlingAnalyzer
    }

    async def comprehensive_audit(self, url: str) -> SecurityAuditReport:
        """Run all 25+ security modules"""

        results = {}

        # Run all modules in parallel where possible
        for module_name, module_class in self.MODULES.items():
            try:
                module = module_class()
                result = await module.analyze(url)
                results[module_name] = result
            except Exception as e:
                logger.error(f"Security module {module_name} failed: {e}")
                results[module_name] = {"error": str(e), "severity": "unknown"}

        # Aggregate results
        critical_issues = []
        high_issues = []
        medium_issues = []
        low_issues = []

        for module_name, result in results.items():
            severity = result.get("severity", "low")
            issues = result.get("findings", [])

            for issue in issues:
                categorized_issue = {
                    "module": module_name,
                    **issue
                }

                if severity == "critical":
                    critical_issues.append(categorized_issue)
                elif severity == "high":
                    high_issues.append(categorized_issue)
                elif severity == "medium":
                    medium_issues.append(categorized_issue)
                else:
                    low_issues.append(categorized_issue)

        # CVSS scoring
        cvss_score = await self._compute_cvss_score(results)

        # OWASP Top 10 mapping
        owasp_mapping = await self._map_to_owasp_top10(results)

        # Compliance checks
        compliance = {
            "gdpr": await self._check_gdpr_compliance(results),
            "pci_dss": await self._check_pci_dss_compliance(results),
            "soc2": await self._check_soc2_compliance(results),
            "iso_27001": await self._check_iso27001_compliance(results)
        }

        # Overall security score
        security_score = self._compute_security_score(results, cvss_score)

        return SecurityAuditReport(
            module_results=results,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            cvss_score=cvss_score,
            owasp_mapping=owasp_mapping,
            compliance=compliance,
            security_score=security_score,
            recommendations=await self._generate_recommendations(results),
            executive_summary=await self._generate_executive_summary(results)
        )
```

---

## PHASE 5: Mature Lifecycle Management

### Goals
- Robust state machine with quality gates
- Recovery from agent failures
- Budget enforcement per phase
- Session persistence and resumption
- Audit metadata tracking

### Implementation

#### 5.1 Enhanced Orchestrator with Quality Gates
```python
# core/orchestrator_enhanced.py - NEW

class OrchestratorEnhanced:
    """Production-grade audit orchestration"""

    def __init__(self):
        self.state = AuditSession()
        self.audit_metadata = AuditMetadata()
        self.recovery_manager = RecoveryManager()
        self.quality_gates = QualityGateManager()

    async def orchestrate_audit(
        self,
        url: str,
        site_type: str,
        audit_tier: str,
        user_preferences: AuditPreferences
    ) -> AuditResult:
        """Main audit orchestration with quality gates"""

        # Initialize audit session
        await self._initialize_session(url, site_type, audit_tier, user_preferences)

        # Phase 1: Scout Agent
        await self.quality_gates.pre_phase_gate("scout")
        scout_result = await self._execute_phase_scout()
        await self.quality_gates.post_phase_gate("scout", scout_result)
        self.state.save_checkpoint("scout_complete")

        # Phase 2: Security Agent
        await self.quality_gates.pre_phase_gate("security")
        security_result = await self._execute_phase_security()
        await self.quality_gates.post_phase_gate("security", security_result)
        self.state.save_checkpoint("security_complete")

        # Phase 3: Vision Agent (Multi-pass)
        await self.quality_gates.pre_phase_gate("vision")
        vision_result = await self._execute_phase_vision_enhanced()
        await self.quality_gates.post_phase_gate("vision", vision_result)
        self.state.save_checkpoint("vision_complete")

        # Phase 4: Graph/OSINT Agent
        await self.quality_gates.pre_phase_gate("graph")
        graph_result = await self._execute_phase_graph_enhanced()
        await self.quality_gates.post_phase_gate("graph", graph_result)
        self.state.save_checkpoint("graph_complete")

        # Phase 5: Judge Agent (Dual-tier)
        await self.quality_gates.pre_phase_gate("judge")
        verdict = await self._execute_phase_judge_enhanced()
        await self.quality_gates.post_phase_gate("judge", verdict)

        # Final quality gate
        await self.quality_gates.final_quality_gate(self.state)

        # Generate comprehensive report
        report = await self._generate_comprehensive_report()

        # Save audit metadata
        await self._save_audit_metadata()

        return AuditResult(
            verdict=verdict,
            report=report,
            metadata=self.audit_metadata,
            session_id=self.state.session_id
        )

    async def _execute_phase_scout(self) -> ScoutResult:
        """Execute scout phase with budget enforcement and recovery"""
        max_retries = 3
        budget = AgentBudget(
            max_pages=self._get_pages_budget(),
            max_screenshots=self._get_screenshot_budget(),
            timeout=timedelta(minutes=5)
        )

        for attempt in range(max_retries):
            try:
                scout = ScoutAgentEnhanced()
                result = await scout.investigate(
                    url=self.state.url,
                    site_type=self.state.site_type,
                    budget=budget
                )

                # Validate result
                if not await self.quality_gates.validate_scout_result(result):
                    raise QualityGateException("Scout validation failed")

                self.state.scout_result = result
                return result

            except Exception as e:
                logger.warning(f"Scout attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    # Try recovery strategy
                    recovery_result = await self.recovery_manager.recover_scout()
                    if recovery_result.success:
                        self.state.scout_result = recovery_result.data
                        return recovery_result.data
                else:
                    # Final failure - use degraded fallback
                    fallback_result = await self.recovery_manager.scout_fallback()
                    self.state.scout_result = fallback_result
                    return fallback_result
```

#### 5.2 Quality Gate Manager
```python
# core/quality_gate_manager.py - NEW

class QualityGateManager:
    """Enforces quality standards at each audit phase"""

    QUALITY_STANDARDS = {
        "scout": {
            "min_pages": 1,
            "min_screenshots": 2,
            "required_data": ["url", "dom", "ssl", "meta"],
            "max_errors": 1
        },
        "security": {
            "min_modules_pass": 15,
            "critical_issues_max": 0,
            "required_modules": ["security_headers", "ssl_analysis"],
            "confidence_threshold": 0.7
        },
        "vision": {
            "min_confidence": 0.6,
            "min_findings": 0,
            "required_passes": 3,  # out of 5 multi-passes
            "coverage_threshold": 0.8
        },
        "graph": {
            "min_osint_sources": 5,
            "entity_verification_pass": True,
            "required_intelligence": ["whois", "dns", "ssl"],
            "confidence_threshold": 0.65
        },
        "judge": {
            "trust_score_computed": True,
            "verdict_complete": True,
            "both_tiers_ready": True,
            "recommendations": True
        }
    }

    async def pre_phase_gate(self, phase: str):
        """Validate prerequisites before phase starts"""
        self.current_phase = phase
        self.phase_start_time = datetime.now()

        # Log phase start
        logger.info(f"Quality Gate: Starting phase '{phase}'")
        self.state.log_event("phase_start", {"phase": phase})

        # Check resource availability
        await self._check_resources()

        # Validate state transition
        await self._validate_state_transition(phase)

    async def post_phase_gate(self, phase: str, result: Any):
        """Validate phase meets quality standards"""

        standards = self.QUALITY_STANDARDS.get(phase, {})

        # Validate against standards
        issues = await self._validate_against_standards(result, standards)

        if issues:
            logger.warning(f"Quality issues in phase '{phase}': {issues}")
            self.state.log_event("quality_issue", {
                "phase": phase,
                "issues": issues
            })

            # Attempt quality improvements
            improved = await self._attempt_quality_improvements(result, issues)
            if improved:
                issues = await self._validate_against_standards(improved, standards)

        # Final validation
        if not issues or await self._accept_with_degradation(issues):
            self.state.phase_results[phase] = result or improved
            await self._close_phase(phase)
        else:
            raise QualityGateException(
                f"Phase '{phase}' failed quality validation: {issues}"
            )

    async def final_quality_gate(self, state: AuditSession):
        """Final validation before report generation"""

        # Check all phases passed
        failed_phases = [
            phase for phase in ["scout", "security", "vision", "graph", "judge"]
            if phase not in state.phase_results
        ]

        if failed_phases:
            raise QualityGateException(
                f"Failed phases: {failed_phases}"
            )

        # Validate data completeness
        completeness = await self._check_data_completeness(state)
        if completeness < 0.8:  # At least 80% completeness
            logger.warning(f"Data completeness below threshold: {completeness}")

        # Validate consistency
        consistency = await self._check_data_consistency(state)
        if not consistency:
            logger.warning("Data inconsistencies detected")

        # Validate timestamp ordering
        await self._validate_timestamp_ordering(state)

        # Final audit metadata
        state.final_metadata = await self._compile_final_metadata(state)
```

---

## PHASE 6: Site-Type-Specific Auditing

### Goals
- Adaptive analysis based on website type
- Specialized criteria for each site category
- Context-aware scoring and recommendations
- Type-specific dark pattern detection

### Implementation

#### 6.1 Site Type Classifier & Adapter
```python
# analysis/site_type_adapter.py - NEW

class SiteTypeAdapter:
    """Adapts audit strategy based on website type"""

    SITE_TYPES = {
        "e_commerce": ECommerceAdapter,
        "portfolio": PortfolioAdapter,
        "financial_services": FinancialServicesAdapter,
        "social_media": SocialMediaAdapter,
        "news_media": NewsMediaAdapter,
        "blog_content": BlogContentAdapter,
        "marketplace": MarketplaceAdapter,
        "saas_platform": SaaSPlatformAdapter,
        "government": GovernmentAdapter,
        "educational": EducationalAdapter,
        "darknet_marketplace": DarknetMarketplaceAdapter
    }

    async def classify_site(self, url: str, preliminary_scan: dict) -> SiteTypeInfo:
        """Classify website type with confidence"""

        # Multi-factor classification
        classification_signals = {
            "url_pattern": self._analyze_url_pattern(url),
            "meta_tags": self._analyze_meta_tags(preliminary_scan),
            "page_structure": self._analyze_page_structure(preliminary_scan),
            "content_signals": self._analyze_content(preliminary_scan),
            "technical_indicators": self._analyze_technical_indicators(preliminary_scan),
            "ml_classification": await self._ml_classification(preliminary_scan)
        }

        # Ensemble classification
        site_type, confidence = self._ensemble_classification(classification_signals)

        # Subtype detection (e.g., "e_commerce" → "e_commerce:digital_products")
        subtype = await self._detect_subtype(site_type, preliminary_scan)

        # Industry detection (e.g., "technology", "fashion", "finance")
        industry = await self._detect_industry(preliminary_scan)

        return SiteTypeInfo(
            primary_type=site_type,
            subtype=subtype,
            industry=industry,
            confidence=confidence,
            signals=classification_signals,
            audit_strategy=self.SITE_TYPES[site_type]
        )

    async def adapt_audit(self, site_type_info: SiteTypeInfo) -> AuditStrategy:
        """Generate site-type-specific audit strategy"""

        adapter_class = site_type_info.audit_strategy
        adapter = adapter_class()

        return await adapter.generate_strategy(site_type_info)
```

#### 6.2 Example: E-Commerce Adapter
```python
# analysis/adapters/ecommerce_adapter.py - NEW

class ECommerceAdapter(BaseAdapter):
    """Specialized adapter for e-commerce sites"""

    async def generate_strategy(self, site_type_info: SiteTypeInfo) -> AuditStrategy:
        strategy = AuditStrategy()

        # Adjust scout parameters for e-commerce
        strategy.scout_config = {
            "target_pages": [
                "homepage",
                "product_page",
                "cart",
                "checkout",
                "terms",
                "refund_policy",
                "shipping_info"
            ],
            "max_depth": 3,
            "follow_product_links": True,
            "follow_category_links": True,
            "capture_pricing": True,
            "capture_product_metadata": True
        }

        # Vision agent focus for e-commerce
        strategy.vision_passes = [
            {
                "name": "deceptive_pricing",
                "focus": "price comparisons, hidden fees, drip pricing",
                "prompt_template": ECommercePrompts.pricing_deception
            },
            {
                "name": "review_authenticity",
                "focus": "fake reviews, stock photos, unverifiable testimonials",
                "prompt_template": ECommercePrompts.review_analysis
            },
            {
                "name": "subscription_traps",
                "focus": "pre-selected boxes, forced continuity, hidden auto-renewal",
                "prompt_template": ECommercePrompts.subscription_detection
            },
            {
                "name": "urgency_manipulation",
                "focus": "fake countdowns, stock scarcity, time pressure",
                "prompt_template": ECommercePrompts.urgency_analysis
            },
            {
                "name": "checkout_flow",
                "focus": "hidden charges at checkout, surprise upcharges",
                "prompt_template": ECommercePrompts.checkout_analysis
            }
        ]

        # Security audit with e-commerce focus
        strategy.security_modules = {
            "priority": [
                "payment_gateway_security",
                "ssl_certificate",
                "payment_form_security",
                "data_encryption",
                "gdpr_compliance"
            ],
            "required": [
                "pci_dss_compliance",
                "https_enforcement",
                "card_data_protection"
            ]
        }

        # OSINT with e-commerce specific checks
        strategy.osint_focus = {
            "business_verification": True,
            "review_platform_crosscheck": True,  # Check Trustpilot, etc.
            "complaint_databases": True,        # BBB, FTC complaints
            "price_comparison_crosscheck": True # Check if prices are real
        }

        # Trust scoring weights (e-commerce specific)
        strategy.scoring_weights = SITE_TYPE_SCORING_STRATEGIES["e_commerce"]

        # E-commerce specific critical checks
        strategy.critical_checks = [
            PaymentSecurityCriticalCheck(),
            PriceAuthenticityCheck(),
            ReviewAuthenticityCheck(),
            SubscriptionTermsCheck(),
            RefundPolicyAnalysis(),
            CustomerSupportVerification()
        ]

        # E-commerce specific dark patterns
        strategy.dark_pattern_focus = ECommerceDarkPatterns.PATTERNS

        # E-commerce specific recommendations
        strategy.recommendation_generators = [
            ECommerceRecommendationGenerator(),
            PaymentSafetyRecommendationGenerator()
        ]

        return strategy
```

---

## PHASE 7: Complete Evidence Capture

### Goals
- Comprehensive evidence ledger
- No data loss across phases
- Persistent evidence storage
- Evidence integrity verification

### Implementation

#### 7.1 Complete Evidence Ledger
```python
# core/evidence_ledger.py - NEW

class EvidenceLedger:
    """Complete evidence tracking and storage"""

    def __init__(self):
        self.evidence_uuid = str(uuid.uuid4())
        self.evidence_store = LanceDBEvidenceStore()
        self.evidence_hasher = EvidenceHasher()

    async def capture_all_evidence(self, audit_session: AuditSession) -> EvidenceReport:
        """Capture and hash all evidence from audit"""

        ledger = EvidenceLedgerEntry(
            evidence_uuid=self.evidence_uuid,
            audit_id=audit_session.session_id,
            timestamp=datetime.now(),
            url=audit_session.url
        )

        # Capture scout evidence
        ledger.scout_evidence = await self._capture_scout_evidence(audit_session)

        # Capture security evidence
        ledger.security_evidence = await self._capture_security_evidence(audit_session)

        # Capture vision evidence
        ledger.vision_evidence = await self._capture_vision_evidence(audit_session)

        # Capture graph/OSINT evidence
        ledger.graph_evidence = await self._capture_graph_evidence(audit_session)

        # Capture judge evidence
        ledger.judge_evidence = await self._capture_judge_evidence(audit_session)

        # Compute evidence integrity hash
        ledger.integrity_hash = await self.evidence_hasher.hash_ledger(ledger)

        # Store in LanceDB
        await self.evidence_store.store(ledger)

        # Verify integrity
        integrity_verified = await self._verify_integrity(ledger)

        return EvidenceReport(
            ledger=ledger,
            integrity_verified=integrity_verified,
            evidence_summary=self._generate_summary(ledger)
        )
```

---

## Implementation Priority & Timeline

### Week 1: Enhanced Vision Agent
- Multi-pass analysis pipeline
- Sophisticated VLM prompts
- Better temporal comparison
- **Deliverable:** 95%+ dark pattern detection

### Week 2: Powerful OSINT
- 15+ intelligence sources
- Darknet analysis support
- Enhanced graph agent
- **Deliverable:** Enterprise-level OSINT verification

### Week 3: Sophisticated Judge
- Dual-tier verdict system
- Context-aware scoring
- User-customizable criteria
- **Deliverable:** Technical + Non-Technical verdicts

### Week 4: Enhanced Security
- 25+ security modules
- OWASP Top 10 coverage
- GDPR/PCI compliance
- **Deliverable:** Enterprise security audit

### Week 5: Lifecycle & Site Types
- Quality gates implementation
- Site-type adapters
- Mature state machine
- **Deliverable:** Robust audit orchestration

### Week 6: Evidence & Integration
- Complete evidence ledger
- End-to-end testing
- Performance optimization
- **Deliverable:** Production-ready system

---

## Success Metrics

### Accuracy
- Dark pattern detection: 95%+
- Security vulnerability detection: 90%+
- OSINT verification accuracy: 95%+
- Overall trust score accuracy: 85%+

### Coverage
- Security modules: 25+
- OSINT sources: 15+
- Site types supported: 10+
- Dark pattern subtypes: 30+

### Performance
- Standard audit: <3 minutes
- Deep forensic: <5 minutes
- Quick scan: <60 seconds
- API uptime: 99%+

---

## Next Steps

1. **Confirm requirements alignment**
2. **Approve implementation plan**
3. **Begin Phase 1 implementation**
4. **Establish testing methodology**
5. **Create master's thesis documentation**

---

*Ready to transform VERITAS into a masterpiece? Let me know if this plan aligns with your vision and we'll start building!*
