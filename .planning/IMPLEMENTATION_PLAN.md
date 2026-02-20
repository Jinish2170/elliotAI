# VERITAS: Step-by-Step Implementation Plan
**Masterpiece Upgrade - College Final Year Project**

> "Make VERITAS more mature than wrappers, with masterclass content showcase that flexes agent intelligence"

---

## Executive Summary

This plan transforms VERITAS from a functional tool into a sophisticated forensic auditing platform with:
- Multi-pass Vision Agent (95%+ dark pattern detection accuracy)
- Powerful OSINT Graph Investigator (15+ intelligence sources)
- Dual-Tier Judge System (technical + non-technical verdicts)
- Enterprise Security Audit (25+ modules including darknet analysis)
- Masterclass Content Showcase (psychology-driven engagement)

---

## Implementation Roadmap

### WEEK 1-2: Vision Agent Enhancement 🎯
### WEEK 3: OSINT & Graph Power-Up 🔍
### WEEK 4: Judge System Dual-Tier ⚖️
### WEEK 5: Cybersecurity Deep Dive 🛡️
### WEEK 6: Content Showcase & UX 💎

---

## PHASE 1: Enhanced Vision Agent (Week 1-2)

**Goal:** 95%+ accuracy in dark pattern detection with sophisticated multi-pass analysis

### Step 1.1: Create Multi-Pass Pipeline Architecture
**File:** `veritas/agents/vision_enhanced.py`

```python
class EnhancedVisionAgent:
    """5-Pass Analysis System for Comprehensive Visual Deception Detection"""

    def __init__(self, nim_client: NimClient):
        self.nim = nim_client
        self.passes = [
            "full_page_scan",           # Pass 1: Complete page overview
            "element_interaction",     # Pass 2: Interactive elements focus
            "deceptive_patterns",      # Pass 3: Dark pattern specific
            "content_analysis",        # Pass 4: Trustworthiness cues
            "screenshot_temporal"      # Pass 5: Time-based comparison
        ]
        self.vlm_prompts = self._load_sophisticated_prompts()

    async def analyze(self, screenshots: List[str], dom_context: Dict) -> VisionReport:
        """Execute all 5 passes with confidence aggregation"""
        results = []

        for pass_name in self.passes:
            result = await self._run_pass(pass_name, screenshots, dom_context)
            results.append(result)
            # Emit real-time progress event for showcase
            self._emit_progress(pass_name, result.confidence)

        return self._aggregate_results(results)
```

**Tasks:**
- [ ] Create `vision_enhanced.py` base class
- [ ] Define pass execution logic with VLM integration
- [ ] Implement confidence aggregation algorithm
- [ ] Add progress emission for frontend showcase

**Time Estimate:** 4 hours

### Step 1.2: Design Sophisticated VLM Prompts
**File:** `veritas/config/vlm_prompts.py`

```python
VLM_PROMPTS = {
    "full_page_scan": """
You are a forensic web auditor specializing in visual deception detection.

Analyze this webpage screenshot for:
1. **Visual Hierarchy Manipulation**: Patterns that draw attention away from critical information
2. **Color Psychology Exploitation**: Urgency colors (red/orange) overused, trust colors (blue) misused
3. **Layout Traps**: Grid manipulations, deceptive whitespace usage, eye-path obstructions

For each finding, provide:
- Location (coordinates if visible)
- Deception type (5 dark pattern categories)
- Confidence score (0-1)
- Visual evidence description
- Potential user psychological impact

Output format: JSON
""",
    "element_interaction": """
You are analyzing interactive interface elements for manipulation tactics.

Focus on:
1. **Buttons with Deceptive Wording**: "Download" that installs ads, "Close" that subscribes
2. **Radio/Checkbox Pre-selection**: Options auto-checked without consent
3. **Dropdown Default Manipulation**: Most profitable option selected by default
4. **Toggle Switch Deception**: Off state looks like On, ambiguous labeling
5. **Slider/Range Manipulation**: Fake range limits, snap-to-profit values

For each element:
- Element type and visual appearance
- Text content and labeling
- Expected vs actual behavior
- Manipulation technique
- Deception confidence (0-1)

Output format: JSON
""",
    "deceptive_patterns": """
You are a dark pattern forensics investigator.

Identify these 5 dark pattern categories:

1. **Visual Interference**: Popups, overlays, fake system notifications blocking content
2. **False Urgency**: Countdown timers with arbitrary dates, "only X left!", "ending soon!"
3. **Forced Continuity**: Checkbox hell, difficult cancellation, auto-renewal traps
4. **Sneaking**: Hidden fees in checkout, price changes at last step, terms hidden
5. **Social Engineering**: Fake reviews, manufactured scarcity, fake user counts

For each pattern detected:
- Pattern category
- Specific instance description
- Visual location evidence
- Psychological manipulation technique
- Impact on user autonomy
- Confidence score (0-1)

Output format: JSON
""",
    "content_analysis": """
You are analyzing trustworthiness signals in webpage content.

Evaluate:
1. **Professional Language Quality**: Grammar, spelling, capitalization consistency
2. **Domain Authority Cues**: Social proof, certifications, awards displayed
3. **Policy Transparency**: Terms, privacy policy, refund policy visibility
4. **Contact Information Credibility**: Physical addresses, phone numbers, support channels
5. **Content Freshness**: Dates, version numbers, update indicators
6. **Visual Consistency**: Logo usage, branding consistency, design quality

For each signal:
- Signal type and observation
- Trustworthiness score (-1 to +1)
- Evidence location
- Red/green flag classification

Output format: JSON
""",
    "screenshot_temporal": """
You are comparing before/after webpage screenshots for temporal deception.

Analyze changes between screenshots:
1. **Countdown Timer Fraud**: Timer resets or jumps back
2. **Dynamic Price Manipulation**: Prices increase after user interaction
3. **Stock Quantity Changing**: Numbers decrease artificially
4. **Pop-in Elements**: Content appears only after scroll or interaction
5. **Hidden Fee Reveal**: Charges shown only at last step
6. **Visual State Changes**: Colors shift, buttons change appearance

For each temporal manipulation:
- What changed between screenshots
- Timing of the change
- Manipulation technique
- User psychological impact
- Deception confidence (0-1)

Output format: JSON
"""
}
```

**Tasks:**
- [ ] Create `vlm_prompts.py` with 5 sophisticated prompts
- [ ] Test prompts with sample screenshots
- [ ] Refine based on VLM output quality
- [ ] Add prompt versioning for optimization

**Time Estimate:** 6 hours

### Step 1.3: Implement Enhanced Temporal Comparison with CV
**File:** `veritas/analysis/temporal_cv.py`

```python
import cv2
import numpy as np
from typing import Tuple, List

class TemporalComputerVision:
    """Advanced temporal analysis using computer vision"""

    async def compare_screenshots(
        self,
        before_path: str,
        after_path: str
    ) -> TemporalDiff:
        """Compare two screenshots with multiple CV techniques"""

        # Load images
        img1 = cv2.imread(before_path)
        img2 = cv2.imread(after_path)

        # 1. Structural Similarity Index (SSIM)
        ssim_score = self._compute_ssim(img1, img2)

        # 2. Optical Flow for movement detection
        flow_vectors = self._compute_optical_flow(img1, img2)

        # 3. Difference mask for changed regions
        diff_mask = self._compute_difference_mask(img1, img2)

        # 4. Text region changes (OCR-based)
        text_changes = await self._detect_text_changes(img1, img2)

        # 5. Color histogram shifts
        color_shifts = self._compute_histogram_diff(img1, img2)

        return TemporalDiff(
            ssim_score=ssim_score,
            optical_flow=flow_vectors,
            changed_regions=diff_mask,
            text_changes=text_changes,
            color_shifts=color_shifts,
            overall_change_score=self._aggregate_changes(
                ssim_score, flow_vectors, diff_mask,
                text_changes, color_shifts
            )
        )

    async def detect_timer_fraud(
        self,
        video_frames: List[str]
    ) -> List[TimerManipulation]:
        """Detect countdown timer fraud from video frames"""

        manipulations = []

        for i in range(len(video_frames) - 1):
            frame1 = cv2.imread(video_frames[i])
            frame2 = cv2.imread(video_frames[i + 1])

            # Extract timer region (typically top-right or near CTA)
            timer_regions = self._locate_timer_regions(frame2)

            for region in timer_regions:
                # OCR to read timer value
                timer_text1 = self._ocr_timer_value(frame1, region)
                timer_text2 = self._ocr_timer_value(frame2, region)

                # Parse and compare
                time1 = self._parse_timer(timer_text1)
                time2 = self._parse_timer(timer_text2)

                # Detect anomalies
                if time2 > time1:  # Timer went backwards!
                    manipulations.append(
                        TimerManipulation(
                            frame_index=i,
                            region=region,
                            before_value=time1,
                            after_value=time2,
                            anomaly_type="timer_reset",
                            confidence=0.9
                        )
                    )

                # Detect suspiciously slow decrement
                elif time1 - time2 < 1:  # Less than 1 second over many frames
                    manipulations.append(
                        TimerManipulation(
                            frame_index=i,
                            region=region,
                            before_value=time1,
                            after_value=time2,
                            anomaly_type="slow_decrement",
                            confidence=0.7
                        )
                    )

        return manipulations
```

**Tasks:**
- [ ] Create `temporal_cv.py` with CV-based temporal analysis
- [ ] Implement SSIM computation with OpenCV
- [ ] Add optical flow for motion detection
- [ ] Build timer fraud detection from video frames
- [ ] Integrate with existing temporal analyzer

**Time Estimate:** 8 hours

### Step 1.4: Build Progress Showcase Emitter
**File:** `veritas/core/progress_emitter.py`

```python
from dataclasses import dataclass
from typing import Any
from datetime import datetime

@dataclass
class ProgressEvent:
    """Real-time progress event for frontend showcase"""
    agent: str                      # "vision", "graph", "judge"
    stage: str                      # "pass_1", "pass_2", etc.
    stage_name: str                 # "Full Page Scan", "Element Interaction", etc.
    status: str                     # "running", "complete", "error"
    timestamp: datetime
    findings_count: int             # Number of findings in this stage
    confidence: float               # Current confidence score
    details: Dict[str, Any]         # Additional showcase data
    visual_evidence: Optional[str]  # Screenshot path for this stage

class ProgressEmitter:
    """Emits real-time agent progress for psychology-driven showcase"""

    def __init__(self, websocket_manager):
        self.ws = websocket_manager

    async def emit_vision_pass_started(self, pass_name: str):
        """Emit event when vision pass starts"""
        await self.ws.broadcast({
            "type": "vision_pass_started",
            "agent": "vision",
            "pass_name": pass_name,
            "timestamp": datetime.now().isoformat(),
            "showcase": {
                "icon": "🔍",
                "title": f"Starting {pass_name}",
                "description": self._get_pass_description(pass_name),
                "expected_duration": self._estimate_pass_duration(pass_name),
                "animation": "scanning"
            }
        })

    async def emit_vision_pass_complete(self, pass_name: str, findings: List):
        """Emit event when vision pass completes"""
        await self.ws.broadcast({
            "type": "vision_pass_complete",
            "agent": "vision",
            "pass_name": pass_name,
            "timestamp": datetime.now().isoformat(),
            "findings_count": len(findings),
            "confidence": self._compute_pass_confidence(findings),
            "showcase": {
                "icon": "✅",
                "title": f"{pass_name} Complete",
                "highlights": self._extract_showcase_highlights(findings),
                "visual_evidence": self._select_visual_evidence(findings),
                "animation": "success"
            }
        })

    async def emit_finding_detected(self, finding: DarkPatternFinding):
        """Emit individual finding for real-time showcase"""
        await self.ws.broadcast({
            "type": "finding_detected",
            "agent": "vision",
            "timestamp": datetime.now().isoformat(),
            "finding": {
                "type": finding.pattern_type,
                "severity": finding.severity,
                "description": finding.description,
                "location": finding.location,
                "confidence": finding.confidence,
                "visual_preview": finding.screenshot_url
            },
            "showcase": {
                "icon": self._get_finding_icon(finding.pattern_type),
                "title": self._get_finding_title(finding),
                "flash_effect": True,
                "focus_region": finding.location
            }
        })
```

**Tasks:**
- [ ] Create `progress_emitter.py` with event definitions
- [ ] Implement all showcase emit methods
- [ ] Add visual evidence selection logic
- [ ] Integrate with WebSocket manager
- [ ] Design showcase data structures for frontend

**Time Estimate:** 4 hours

**Week 1-2 Total:** 22 hours ~ 3 days

---

## PHASE 2: OSINT & Graph Power-Up (Week 3)

**Goal:** 15+ intelligence sources with darknet monitoring and deep verification

### Step 2.1: Create OSIntelligence Engine
**File:** `veritas/agents/osint_engine.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List, Set
import aiohttp
import asyncio

class OSIntelligenceEngine:
    """15+ Source OSINT Engine for Deep Entity Verification"""

    SOURCES = {
        # Domain Intelligence (3 sources)
        "whois": "Domain registration information",
        "dns_records": "DNS configuration and history",
        "ssl_certificate": "SSL/TLS certificate chain and validity",

        # Threat Intelligence (6 sources)
        "google_safe_browsing": "Google's malicious URL database",
        "virus_total": "VirusTotal URL reputation",
        "phishtank": "Phishing report database",
        "urlhaus": "URLhaus malware URL feed",
        "abuse_ch": "Abuse.ch threat intelligence",
        "cymru_malware": "Team Cymru Malware Hash Registry",

        # Business Verification (3 sources)
        "business_registry": "Official business registration",
        "linkedin_verification": "LinkedIn company verification",
        "yelp_google_maps": "Review platform presence",

        # Enhanced Intelligence (3 sources)
        "darknet_monitor": "Darknet marketplace monitoring",
        "tor_exits": "Tor exit node detection",
        "i2p_freifunk": "I2P/Freifunk network analysis"
    }

    async def investigate_domain(self, domain: str) -> OSINTReport:
        """Run comprehensive OSINT investigation on domain"""

        report = OSINTReport(domain=domain)
        tasks = []

        # Group 1: Fast synchronous checks (timeout: 5s)
        fast_tasks = [
            self._check_whois(domain),
            self._check_ssl(domain),
            self._check_google_safe_browsing(domain)
        ]

        # Group 2: Medium priority checks (timeout: 10s)
        medium_tasks = [
            self._check_virus_total(domain),
            self._check_dns_records(domain),
            self._check_business_registry(domain),
            self._check_linkedin(domain),
            self._check_tor_exits(domain)
        ]

        # Group 3: Deep investigation (timeout: 30s)
        deep_tasks = [
            self._check_phishtank(domain),
            self._check_urlhaus(domain),
            self._check_abuse_ch(domain),
            self._check_yelp_google_maps(domain),
            self._check_darknet_monitor(domain),
            self._check_cymru_malware(domain),
            self._check_i2p_freifunk(domain)
        ]

        # Execute with timeouts and parallelism
        report.fast_checks = await asyncio.gather(*[self._wrap_task(t, 5) for t in fast_tasks], return_exceptions=True)
        report.medium_checks = await asyncio.gather(*[self._wrap_task(t, 10) for t in medium_tasks], return_exceptions=True)
        report.deep_checks = await asyncio.gather(*[self._wrap_task(t, 30) for t in deep_tasks], return_exceptions=True)

        # Aggregate findings
        report.threat_score = self._compute_threat_score(report)
        report.verification_score = self._compute_verification_score(report)
        report.darknet_exposure = self._compute_darknet_exposure(report)

        return report
```

**Tasks:**
- [ ] Create `osint_engine.py` base class
- [ ] Implement all 15+ OSINT check methods
- [ ] Add timeout handling and error recovery
- [ ] Implement threat scoring algorithm
- [ ] Add verification score computation
- [ ] Build darknet exposure metric

**Time Estimate:** 12 hours

### Step 2.2: Implement Darknet Analyzer
**File:** `veritas/analysis/darknet_analyzer.py`

```python
class DarknetAnalyzer:
    """Monitor 6 major darknet marketplaces for phishing/credential theft"""

    MARKETPLACES = {
        "empire": "Empire Market",
        "alpha": "AlphaBay",
        "darkfox": "DarkFox Market",
        "tor2door": "Tor2Door Market",
        "canada": "Canada HQ",
        "apollon": "Apollon Market"
    }

    THREAT_TYPES = {
        "phishing_kit": "Complete phishing website clones",
        "credential_database": "Username/password dumps",
        "credit_card_dumps": "Stolen credit card information",
        "identity_theft": "Full identity packages",
        "bank_account": "Bank account credentials",
        "crypto_wallet": "Cryptocurrency wallet access"
    }

    async def monitor_domain(self, domain: str) -> DarknetReport:
        """Check if domain appears in darknet marketplaces"""

        report = DarknetReport(domain=domain)
        detected_items = []

        for marketplace_id, marketplace_name in self.MARKETPLACES.items():
            # In production, use actual darknet API endpoints
            # For now, simulate with threat intelligence feeds
            marketplace_hits = await self._search_marketplace(
                marketplace_id, domain
            )

            for hit in marketplace_hits:
                if hit.matches:
                    detected_items.append({
                        "marketplace": marketplace_name,
                        "threat_type": hit.threat_type,
                        "listing_title": hit.title,
                        "price": hit.price,
                        "date_posted": hit.date_posted,
                        "seller_reputation": hit.seller_rating,
                        "description_snippet": hit.description[:200] + "...",
                        "evidence_tokens": extract_domain_tokens(hit.description)
                    })

        report.detected_items = detected_items
        report.darknet_risk_score = self._compute_darknet_risk(detected_items)
        report.threat_level = self._categorize_threat_level(report.darknet_risk_score)

        return report

    def _classify_threat_level(self, risk_score: float) -> str:
        """Categorize darknet threat level"""
        if risk_score >= 0.8:
            return "CRITICAL - Active criminal marketplace listings"
        elif risk_score >= 0.5:
            return "HIGH - Multiple marketplace mentions"
        elif risk_score >= 0.2:
            return "MEDIUM - Isolated marketplace references"
        elif risk_score > 0:
            return "LOW - Indicators of suspicious activity"
        else:
            return "NONE - No darknet exposure detected"
```

**Tasks:**
- [ ] Create `darknet_analyzer.py` base class
- [ ] Define marketplace threat signatures
- [ ] Implement domain token extraction
- [ ] Build threat scoring algorithm
- [ ] Add evidence collection for showcase
- [ ] Create darknet risk classification

**Time Estimate:** 8 hours

### Step 2.3: Enhance Graph Investigator with OSINT Integration
**File:** `veritas/agents/graph_investigator.py` (enhance existing)

```python
class EnhancedGraphInvestigator:
    """Graph-based entity verification with deep OSINT integration"""

    async def build_knowledge_graph(
        self,
        osint_report: OSINTReport,
        darknet_report: DarknetReport,
        entities: List[Entity]
    ) -> KnowledgeGraph:
        """Build comprehensive knowledge graph from all intelligence"""

        graph = nx.MultiDiGraph()

        # Add domain node with OSINT attributes
        graph.add_node(
            "domain",
            node_type="domain",
            **osint_report.to_attributes()
        )

        # Add entity nodes from webpage
        for entity in entities:
            graph.add_node(
                entity.id,
                node_type="entity",
                entity_type=entity.type,
                text=entity.text,
                confidence=entity.confidence
            )

        # Add OSINT source nodes
        for source, data in osint_report.get_source_data().items():
            graph.add_node(
                f"osint_{source}",
                node_type="osint_source",
                source_type=data.get("type"),
                reliability=data.get("reliability", 0.5),
                timestamp=data.get("timestamp")
            )

            # Connect domain to OSINT source
            graph.add_edge(
                "domain",
                f"osint_{source}",
                relationship_type=osint_report.get_relationship(source),
                weight=data.get("confidence", 0.5)
            )

        # Add darknet threat nodes
        for item in darknet_report.detected_items:
            graph.add_node(
                f"darknet_{hash(item['listing_title'])}",
                node_type="darknet_threat",
                threat_type=item["threat_type"],
                marketplace=item["marketplace"],
                price=item["price"],
                seller_reputation=item["seller_reputation"]
            )

            # Connect domain to darknet threat
            graph.add_edge(
                "domain",
                f"darknet_{hash(item['listing_title'])}",
                relationship_type="listed_in",
                weight=0.9  # High confidence if found in marketplace
            )

        # Run centrality and community detection
        betweenness = nx.betweenness_centrality(graph)
        pagerank = nx.pagerank(graph)
        communities = nx.community.greedy_modularity_communities(graph)

        # Add graph metrics to nodes
        for node in graph.nodes():
            graph.nodes[node]["betweenness"] = betweenness.get(node, 0)
            graph.nodes[node]["pagerank"] = pagerank.get(node, 0)
            graph.nodes[node]["community_id"] = self._find_community(node, communities)

        return graph

    async def analyze_graph_paths(self, graph: KnowledgeGraph) -> GraphAnalysis:
        """Analyze suspicious paths and connections in the graph"""

        analysis = GraphAnalysis()

        # Find paths from domain to darknet threats
        darknet_nodes = [
            n for n, attrs in graph.nodes(data=True)
            if attrs.get("node_type") == "darknet_threat"
        ]

        for darknet_node in darknet_nodes:
            try:
                path = nx.shortest_path(
                    graph,
                    source="domain",
                    target=darknet_node
                )
                analysis.suspicious_paths.append({
                    "path": path,
                    "path_length": len(path),
                    "threat_type": graph.nodes[darknet_node]["threat_type"],
                    "marketplace": graph.nodes[darknet_node]["marketplace"],
                    "risk_score": self._compute_path_risk(path, graph)
                })
            except nx.NetworkXNoPath:
                continue

        # Find OSINT source clusters (multiple OSINT sources agreeing)
        osint_nodes = [
            n for n, attrs in graph.nodes(data=True)
            if attrs.get("node_type") == "osint_source"
        ]

        for node in osint_nodes:
            neighbors = list(graph.neighbors(node))
            if len(neighbors) > 1:
                analysis.osint_clusters.append({
                    "source": node,
                    "connected_entities": neighbors,
                    "cluster_strength": sum([
                        graph.edges[(node, n)]["weight"]
                        for n in neighbors
                    ])
                })

        # Compute graph-level metrics
        analysis.graph_sparsity = nx.density(graph)
        analysis.avg_clustering = nx.average_clustering(graph)
        analysis.strongly_connected = nx.is_strongly_connected(graph)

        return analysis
```

**Tasks:**
- [ ] Extend existing `graph_investigator.py`
- [ ] Integrate OSINT engine results
- [ ] Add darknet threat nodes to graph
- [ ] Implement path analysis for darknet connections
- [ ] Build graph centrality metrics
- [ ] Add community detection

**Time Estimate:** 6 hours

**Week 3 Total:** 26 hours ~ 3-4 days

---

## PHASE 3: Dual-Tier Judge System (Week 4)

**Goal:** Sophisticated verdicts for both technical and non-technical users

### Step 3.1: Design Verdict Data Classes
**File:** `veritas/models/verdicts.py`

```python
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

class RiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"

@dataclass
class VerdictTechnical:
    """Technical verdict for security professionals and auditors"""

    # Core scoring
    trust_score: int              # 0-100
    risk_level: RiskLevel
    percentile_rank: float        # Compare against similar websites

    # Detailed breakdown
    signal_breakdown: Dict[str, int]  # Each signal's contribution to score
    raw_findings: List[Dict[str, Any]]

    # Security indicators
    ioc_indicators: List[str]         # Indicators of Compromise
    cwe_mapping: List[str]            # CWE vulnerabilities found
    attack_vectors: List[str]         # Potential attack vectors
    cvss_score: float                 # CVSS 3.1 score (0-10)
    cvss_vector: str                  # CVSS vector string

    # OSINT verification
    osint_sources_verified: int       # Number of OSINT sources confirming
    osint_sources_failed: int         # Number of OSINT sources flagging
    darknet_exposure: Dict[str, Any]  # Darknet marketplace findings

    # Technical metadata
    technical_metadata: Dict
    scan_timestamp: str
    scan_duration_seconds: float
    technologies_detected: List[str]  # Tech stack fingerprinting

    # Quality metrics
    confidence_interval: tuple        # 95% confidence interval for score
    data_completeness: float          # 0-1, how complete the audit was
    anomalies_detected: List[str]     # Unexpected behaviors

@dataclass
class VerdictNonTechnical:
    """Non-technical verdict for general users"""

    # Core scoring (same as technical)
    trust_score: int
    risk_level: RiskLevel

    # Plain English summary
    plain_english_summary: str        # 2-3 sentences explaining the verdict
    what_this_means: str             # Detailed explanation in simple terms

    # Key findings (top 5 most impactful)
    key_findings: List[str]          # Most important discoveries

    # Actionable advice
    what_to_do_here: List[str]       # What user can do on this site
    what_to_avoid: List[str]         # What to watch out for
    red_flags: List[str]             # Things that are concerning
    green_flags: List[str]           # Things that are reassuring

    # Comparative context
    how_does_this_compare: str       # Compared to other similar sites
    industry_benchmark: str          # How this compares to industry average

    # Risk explanation
    your_personal_risk: str          # What this means for the user
    worst_case_scenario: str         # What could go wrong
    best_case_scenario: str          # What to expect if things go well

    # Recommendations
    recommendation: str              # Main recommendation (use/avoid/caution)
    if_you_decide_to_use: str        # Safety tips if proceeding
    alternatives: List[str]          # Better alternatives if available

    # Visual cues
    color_code: str                  # Red/Yellow/Green for UI display
    icon_emoji: str                  # 🚫/⚠️/✅

@dataclass
class DualVerdict:
    """Combined verdict system for all user types"""

    url: str
    audit_id: str
    timestamp: str

    technical: VerdictTechnical
    non_technical: VerdictNonTechnical

    # Cross-reference
    summary: str                     # Executive summary for both audiences
    quick_action: str                # Single recommended action
```

**Tasks:**
- [ ] Create `verdicts.py` with all data classes
- [ ] Define RiskLevel enum and mapping
- [ ] Add validation logic for verdict consistency
- [ ] Create conversion methods between tiers

**Time Estimate:** 4 hours

### Step 3.2: Implement Site-Type-Specific Scoring
**File:** `veritas/config/site_strategies.py`

```python
class ECommerceStrategy:
    """Scoring strategy for e-commerce websites"""

    PRIORITY_SIGNALS = {
        "payment_security": 0.15,      # PCI DSS compliance, secure checkout
        "price_transparency": 0.12,    # No hidden fees, clear pricing
        "review_authenticity": 0.10,   # Real reviews, not fake
        "return_policy": 0.08,         # Clear return/refund policy
        "customer_support": 0.07,      # Support accessibility
        "inventory_accuracy": 0.07,    # Accurate stock levels
        "shipping_transparency": 0.07, # Clear shipping info
    }

    DARK_PATTERN_SENSITIVITY = {
        "false_urgency": 2.0,          # Double penalty for fake countdowns
        "sneaking": 2.5,               # Triple penalty for hidden fees
        "forced_continuity": 3.0,      # Maximum penalty for auto-charge traps
        "visual_interference": 1.5,
        "social_engineering": 2.0
    }

    CRITICAL_CHECKS = {
        "ssl_certificate": "Must have valid TLS/SSL",
        "pci_dss_badge": "PCI DSS compliance indicator",
        "secure_checkout": "HTTPS checkout with lock icon",
        "clear_pricing": "No hidden charges at checkout",
        "contact_info": "Physical address and phone number"
    }

    @classmethod
    def get_verdict_template(cls, score: int) -> VerdictNonTechnical:
        """Generate non-technical verdict template for e-commerce"""
        if score >= 80:
            return VerdictNonTechnical(
                trust_score=score,
                risk_level=RiskLevel.SAFE,
                plain_english_summary="This appears to be a trustworthy e-commerce site with good security practices.",
                what_this_means="The site uses secure payment processing, has clear pricing, and provides good customer support options.",
                key_findings=[
                    "Secure checkout with valid SSL certificate",
                    "Transparent pricing with no hidden fees",
                    "Responsive customer support available"
                ],
                recommendation="Proceed with confidence when making purchases.",
                if_you_decide_to_use="Review return policy before buying, use credit card for purchase protection.",
                alternatives=[]
            )
        elif score >= 60:
            return VerdictNonTechnical(
                trust_score=score,
                risk_level=RiskLevel.MEDIUM,
                plain_english_summary="This e-commerce site is generally safe but has some areas that need attention.",
                what_this_means="While the site appears legitimate, there are some concerns around transparency or security practices.",
                key_findings=[
                    some_critical_and_some_positive_findings
                ],
                recommendation="Proceed with caution.",
                if_you_decide_to_use="Read terms carefully, use credit card not debit, save screenshots of your order.",
                alternatives=["Consider well-known platforms like Amazon, eBay"]
            )
        # ... more score ranges

class PortfolioStrategy:
    """Scoring strategy for company portfolio/showcase websites"""

    PRIORITY_SIGNALS = {
        "company_verification": 0.15,   # Business registration, LinkedIn presence
        "contact_authenticity": 0.12,   # Real contact information
        "consistency": 0.10,            # Brand/story consistency across platforms
        "professional_quality": 0.08,   # Design and content quality
    }
    # ...

class DarknetStrategy:
    """Scoring strategy for darknet marketplace analysis"""

    PRIORITY_SIGNALS = {
        "exit_node_clean": 0.20,       # Not a known malicious exit node
        "tor_network_valid": 0.15,     # Proper Tor network configuration
        "marketplace_reputation": 0.15,
        "vendor_verification": 0.10,
    }

    DARK_PATTERN_SENSITIVITY = {
        # Sensitivity boosted for darknet context
        "exit_node_malicious": 5.0,    # Massive penalty if malicious exit node detected
        "phishing_kit": 5.0,           # Maximum penalty if phishing kit found
    }
    # ...

# Site type detection
class SiteTypeDetector:
    """Detect website type from URL and content"""
    SITE_TYPES = {
        "e_commerce": ECommerceStrategy,
        "portfolio": PortfolioStrategy,
        "financial_services": FinancialServicesStrategy,
        "social_media": SocialMediaStrategy,
        "darknet_marketplace": DarknetStrategy,
        # ... 11 total strategies
    }
```

**Tasks:**
- [ ] Create all 11 site-type strategy classes
- [ ] Define priority signals for each type
- [ ] Implement dark pattern sensitivity multipliers
- [ ] Create critical checks per site type
- [ ] Build verdict templates for different score ranges
- [ ] Implement site type detection logic

**Time Estimate:** 12 hours

### Step 3.3: Build Judge Agent with Dual-Tier Generation
**File:** `veritas/agents/judge_dual.py`

```python
class DualJudgeAgent:
    """Sophisticated judge generating both technical and non-technical verdicts"""

    async def judge(
        self,
        vision_report: VisionReport,
        osint_report: OSINTReport,
        darknet_report: DarknetReport,
        security_report: SecurityReport,
        site_type: str
    ) -> DualVerdict:
        """Generate comprehensive dual-tier verdict"""

        # Select appropriate strategy
        strategy = self._get_strategy(site_type)

        # Compute trust scores with site-type-specific weighting
        weighted_score = strategy.compute_trust_score({
            "vision": vision_report,
            "osint": osint_report,
            "darknet": darknet_report,
            "security": security_report
        })

        # Generate technical verdict
        technical = VerdictTechnical(
            trust_score=weighted_score.final_score,
            risk_level=self._map_score_to_risk(weighted_score.final_score),
            percentile_rank=weighted_score.percentile,

            signal_breakdown=weighted_score.signal_breakdown,
            raw_findings=vision_report.findings + security_report.vulnerabilities,

            ioc_indicators=self._extract_iocs(osint_report),
            cwe_mapping=self._map_cwes(security_report),
            attack_vectors=self._identify_attack_vectors({
                vision_report, osint_report, darknet_report, security_report
            }),
            cvss_score=self._compute_cvss(security_report),
            cvss_vector=self._generate_cvss_vector(security_report),

            osint_sources_verified=osint_report.verification_count,
            osint_sources_failed=osint_report.threat_count,
            darknet_exposure=darknet_report.to_dict(),

            technical_metadata={
                "scan_metadata": {...},
                "fingerprinting": security_report.tech_stack
            },
            scan_timestamp=datetime.now().isoformat(),
            scan_duration_seconds=self._compute_duration(start_time),
            technologies_detected=security_report.tech_stack,

            confidence_interval=self._compute_confidence_interval({
                vision_report, osint_report, darknet_report, security_report
            }),
            data_completeness=self._compute_completeness({
                vision_report, osint_report, darknet_report, security_report
            }),
            anomalies_detected=self._detect_anomalies({
                vision_report, osint_report, darknet_report, security_report
            })
        )

        # Generate non-technical verdict
        non_technical = strategy.generate_verdict_template(
            weighted_score.final_score
        )

        # Augment with specific findings
        non_technical.key_findings = self._top_five_most_impactful({
            vision_report, osint_report, darknet_report, security_report
        })
        non_technical.red_flags = self._extract_red_flags({
            vision_report, osint_report, darknet_report, security_report
        })
        non_technical.green_flags = self._extract_green_flags({
            vision_report, osint_report, darknet_report, security_report
        })
        non_technical.industry_benchmark = await self._compare_to_industry(
            site_type, weighted_score.final_score
        )

        # Executive summary connecting both tiers
        summary = f"""
        Technical Assessment: Score of {weighted_score.final_score}/100 indicates {technical.risk_level.value} risk level
        with {len(technical.raw_findings)} findings across {len(technical.cvse_mapping)} security categories.

        User Guidance: {non_technical.plain_english_summary}

        Recommendation: {non_technical.recommendation}
        """.strip()

        return DualVerdict(
            url=vision_report.url,
            audit_id=vision_report.audit_id,
            timestamp=datetime.now().isoformat(),
            technical=technical,
            non_technical=non_technical,
            summary=summary,
            quick_action=non_technical.recommendation
        )
```

**Tasks:**
- [ ] Create `judge_dual.py` base class
- [ ] Implement trust score computation with weighting
- [ ] Build technical verdict generation
- [ ] Build non-technical verdict generation
- [ ] Add executive summary generation
- [ ] Implement industry benchmarking

**Time Estimate:** 8 hours

**Week 4 Total:** 24 hours ~ 3 days

---

## PHASE 4: Cybersecurity Deep Dive (Week 5)

**Goal:** 25+ security modules including darknet-level threat detection

### Step 4.1: Implement Enterprise Security Modules
**File:** `veritas/analysis/security_enterprise.py`

```python
class ComprehensiveSecurityAudit:
    """25+ Module Enterprise Security Audit"""

    MODULES = {
        # OWASP Top 10 (10 modules)
        "injection_detection": InjectionDetector,
        "broken_authentication": BrokenAuthDetector,
        "sensitive_data_exposure": SensitiveDataDetector,
        "xml_external_entities": XXEDetector,
        "broken_access_control": AccessControlDetector,
        "security_misconfiguration": MisconfigurationDetector,
        "cross_site_scripting": XSSDetector,
        "insecure_deserialization": DeserializationDetector,
        "vulnerable_components": ComponentsDetector,
        "insufficient_logging": LoggingDetector,

        # Authentication & Session Security (4 modules)
        "auth_mechanisms": AuthMechanismsDetector,
        "session_security": SessionSecurityDetector,
        "brute_force_protection": BruteForceDetector,
        "password_policy": PasswordPolicyDetector,

        # Data Protection (4 modules)
        "tls_ssl_analysis": TLSAnalyzer,
        "data_transmission": DataTransmissionAnalyzer,
        "data_storage": DataStorageAnalyzer,
        "privacy_policy": PrivacyPolicyAnalyzer,

        # PCI DSS Compliance (3 modules)
        "pci_dss_compliance": PCIComplianceChecker,
        "payment_gateway": PaymentGatewayAnalyzer,
        "credit_card_handling": CreditCardHandlerAnalyzer,

        # Advanced Threat Detection (4 modules)
        "threat_feed_correlation": ThreatFeedCorrelator,
        "malicious_patterns": MaliciousPatternDetector,
        "botnet_indicators": BotnetIndicatorDetector,
        "cryptojacking": CryptojackingDetector,

        # Additional Critical Modules (4 modules)
        "skimmer_detection": CardSkimmerDetector,
        "business_logic_flaws": BusinessLogicDetector,
        "privilege_escalation": PrivilegeEscalationDetector,
        "rate_limiting": RateLimitingDetector
    }

    async def run_comprehensive_scan(self, url: str) -> SecurityReport:
        """Run all 25+ security modules"""

        report = SecurityReport(url=url)

        # Phase 1: Fast synchronous scans (5s timeout each)
        fast_modules = [
            "security_headers", "security_misconfiguration",
            "tls_ssl_analysis", "broken_access_control"
        ]
        for module_name in fast_modules:
            result = await self._run_module(module_name, url, timeout=5)
            report.add_module_result(module_name, result)

        # Phase 2: Medium priority scans (10s timeout each)
        medium_modules = [
            "injection_detection", "xss_detection",
            "csrf_protection", "auth_mechanisms"
        ]
        for module_name in medium_modules:
            result = await self._run_module(module_name, url, timeout=10)
            report.add_module_result(module_name, result)

        # Phase 3: Deep security scans (30s timeout each)
        deep_modules = [
            "threat_feed_correlation", "malicious_patterns",
            "botnet_indicators", "skimmer_detection"
        ]
        for module_name in deep_modules:
            result = await self._run_module(module_name, url, timeout=30)
            report.add_module_result(module_name, result)

        # Compute aggregate security score
        report.security_score = self._compute_security_score(report)
        report.owasp_violations = self._map_owasp_violations(report)
        report.pci_dss_compliance = self._check_pci_dss_compliance(report)
        report.gdpr_compliance = self._check_gdpr_compliance(report)

        return report
```

**Tasks:**
- [ ] Create `security_enterprise.py` base class
- [ ] Implement 25+ security detector modules
- [ ] Add OWASP Top 10 mapping
- [ ] Implement PCI DSS compliance checker
- [ ] Add GDPR compliance checking
- [ ] Build threat feed correlation

**Time Estimate:** 16 hours

### Step 4.2: Build Darknet-Level Threat Detection
**File:** `veritas/analysis/threat_advanced.py`

```python
class AdvancedThreatAnalyzer:
    """Darknet-level threat intelligence and detection"""

    THREAT_INTELLIGENCE_FEEDS = {
        "cybercrime_forums": "Cybercrime forum monitoring",
        "leak_databases": "Credential leak databases",
        "ransomware_tracking": "Ransomware operation tracking",
        "apt_groups": "Advanced Persistent Threat group tracking",
        "c2_servers": "Command & Control server monitoring"
    }

    async def analyze_threat_surface(self, domain: str) -> ThreatSurfaceReport:
        """Analyze darknet-level threat indicators"""

        report = ThreatSurfaceReport(domain=domain)

        # 1. Phishing Kit Detection
        report.phishing_kits = await self._detect_phishing_kits(domain)

        # 2. Credential Leakage Check
        report.credential_leaks = await self._check_credential_leaks(domain)

        # 3. Ransomware Operation Association
        report.ransomware_associations = await self._check_ransomware(domain)

        # 4. APT Group Indicators
        report.apt_indicators = await self._check_apt_groups(domain)

        # 5. Botnet Association
        report.botnet_indicators = await self._check_botnets(domain)

        # 6. Cryptojacking Indicators
        report.cryptojacking_indicators = await self._check_cryptojacking(domain)

        # 7. Card Skimmer Check
        report.skimmer_indicators = await self._check_card_skimmers(domain)

        # Compute threat surface score
        report.threat_score = self._compute_threat_score(report)
        report.threat_level = self._categorize_threat_level(report.threat_score)

        return report

    async def _detect_phishing_kits(self, domain: str) -> List[PhishingKit]:
        """Detect if this is a known phishing kit instance"""

        # Hash webpage and compare to known phishing kit hashes
        page_hash = await self._compute_page_hash(domain)

        known_kits = await self._query_phishing_kit_database(page_hash)

        return [
            PhishingKit(
                kit_name=kit.name,
                kit_version=kit.version,
                operator=kit.operator,
                first_seen=kit.first_seen,
                recent_campagins=kit.campaign_count
            )
            for kit in known_kits
        ]
```

**Tasks:**
- [ ] Create `threat_advanced.py` base class
- [ ] Implement phishing kit detection
- [ ] Add credential leakage checking
- [ ] Build ransomware operation tracking
- [ ] Implement APT Group indicator detection
- [ ] Add botnet association checking
- [ ] Build cryptojacking and skimmer detection

**Time Estimate:** 12 hours

**Week 5 Total:** 28 hours ~ 3-4 days

---

## PHASE 5: Masterclass Content Showcase (Week 6)

**Goal:** Psychology-driven engagement with gradual screenshot reveals, running logs, and agent task flexing

### Step 5.1: Design Psychology-Driven Content Flow
**File:** `frontend/content/showcase_philosophy.md`

```markdown
# Showcasing Philosophy: From Ordinary to Masterclass

## Core Principles

### 1. Gradual Reveal, Not Information Dump
**Bad:** Show all findings at once
**Good:** Reveal findings as agents discover them

**Psychology:** Creates curiosity, builds engagement, mimics real investigation

### 2. Agent Persona & Personality
**Bad:** Generic "System is scanning..."
**Good:** "Vision Agent: Analyzing deceptive color psychology in pricing section"

**Psychology:** Human-like interaction creates emotional investment

### 3. Visual Evidence First, Explanation Second
**Bad:** Text description first
**Good:** Screenshot appears with highlight region, then analysis

**Psychology:** Show-don't-tell is more memorable

### 4. Progress Theater
**Bad:** Simple progress bar
**Good:** Agent status cards with animated icons, confidence gauges, finding previews

**Psychology:** Reward anticipation with visible progress

### 5. Find Something to Celebrate
**Bad:** Only show problems
**Good:** Celebrate green flags: "No hidden fees detected! 🎉"

**Psychology:** Positive reinforcement builds trust
```

**Tasks:**
- [ ] Create `showcase_philosophy.md` document
- [ ] Define psychology principles with examples
- [ ] Create anti-patterns and best practices
- [ ] Add user journey mapping

**Time Estimate:** 2 hours

### Step 5.2: Implement Real-Time Agent Showcase Components
**File:** `frontend/components/AgentTheater.tsx`

```tsx
"use client"

import { motion, AnimatePresence } from "framer-motion"
import { Eye, Shield, Globe, Gavel, Loader, CheckCircle2, AlertTriangle } from "lucide-react"

interface AgentCardProps {
    agent: "vision" | "graph" | "judge"
    status: "waiting" | "running" | "complete" | "error"
    currentStage?: string
    confidence?: number
    findingsCount?: number
    previewFinding?: DarkPatternFinding
}

export function AgentCard({ agent, status, currentStage, confidence, findingsCount, previewFinding }: AgentCardProps) {
    const agentConfig = {
        vision: {
            icon: Eye,
            name: "Vision",
            color: "from-blue-500 to-cyan-500",
            description: "Visual deception detection"
        },
        graph: {
            icon: Globe,
            name: "Graph",
            color: "from-purple-500 to-pink-500",
            description: "Entity verification"
        },
        judge: {
            icon: Gavel,
            color: "from-amber-500 to-orange-500",
            description: "Trust verdict"
        }
    }

    const config = agentConfig[agent]
    const Icon = config.icon

    return (
        <motion.div
            className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            {/* Agent Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <motion.div
                        className={`p-3 rounded-xl bg-gradient-to-br ${config.color}`}
                        animate={status === "running" ? { scale: [1, 1.1, 1] } : {}}
                        transition={{ duration: 0.5 }}
                    >
                        <Icon className="w-6 h-6 text-white" />
                    </motion.div>
                    <div>
                        <h3 className="text-xl font-bold text-white">{config.name} Agent</h3>
                        <p className="text-sm text-slate-400">{config.description}</p>
                    </div>
                </div>

                {/* Status Badge */}
                <motion.div
                    className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    {status === "running" && (
                        <>
                            <Loader className="w-4 h-4 animate-spin text-blue-400" />
                            <span className="text-blue-400">Analyzing</span>
                        </>
                    )}
                    {status === "complete" && (
                        <>
                            <CheckCircle2 className="w-4 h-4 text-green-400" />
                            <span className="text-green-400">Complete</span>
                        </>
                    )}
                    {status === "error" && (
                        <>
                            <AlertTriangle className="w-4 h-4 text-red-400" />
                            <span className="text-red-400">Error</span>
                        </>
                    )}
                </motion.div>
            </div>

            {/* Current Stage */}
            <AnimatePresence>
                {status === "running" && currentStage && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-4"
                    >
                        <div className="text-sm text-slate-300 mb-2">{currentStage}</div>

                        {/* Confidence Gauge */}
                        {confidence !== undefined && (
                            <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
                                <motion.div
                                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 to-cyan-500"
                                    initial={{ width: "0%" }}
                                    animate={{ width: `${confidence * 100}%` }}
                                    transition={{ duration: 0.3 }}
                                />
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Preview Finding */}
            <AnimatePresence>
                {previewFinding && status !== "waiting" && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="mt-4 p-4 bg-slate-800/50 rounded-xl border border-slate-600"
                    >
                        <div className="flex items-start gap-3">
                            <div className="flex-1">
                                <div className="text-xs font-semibold text-slate-400 mb-1">
                                    {previewFinding.pattern_type}
                                </div>
                                <div className="text-sm text-slate-200">
                                    {previewFinding.description}
                                </div>
                            </div>
                            {previewFinding.visual_preview && (
                                <motion.div
                                    className="w-16 h-12 rounded-lg overflow-hidden bg-slate-700"
                                    whileHover={{ scale: 1.05 }}
                                >
                                    {/* Thumbnail of screenshot */}
                                </motion.div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}

export function AgentTheater() {
    const [agents, setAgents] = useState({
        vision: { status: "running", stage: "Full Page Scan", confidence: 0.7, findings: 3 },
        graph: { status: "waiting" },
        judge: { status: "waiting" }
    })

    return (
        <div className="grid grid-cols-3 gap-6">
            {(["vision", "graph", "judge"] as const).map(agent => (
                <AgentCard
                    key={agent}
                    agent={agent}
                    status={agents[agent].status}
                    currentStage={agents[agent].stage}
                    confidence={agents[agent].confidence}
                    findingsCount={agents[agent].findings}
                    previewFinding={agents[agent].previewFinding}
                />
            ))}
        </div>
    )
}
```

**Tasks:**
- [ ] Create `AgentTheater.tsx` component
- [ ] Add animated status transitions
- [ ] Implement confidence gauge visualization
- [ ] Build preview finding card
- [ ] Add visual preview thumbnails
- [ ] Integrate with WebSocket events

**Time Estimate:** 8 hours

### Step 5.3: Build Screenshot Carousel with Gradual Reveal
**File:** `frontend/components/ScreenshotCarousel.tsx`

```tsx
"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useState, useEffect } from "react"
import { ChevronLeft, ChevronRight, ZoomIn, XCircle } from "lucide-react"

interface ScreenshotSlide {
    id: string
    imageUrl: string
    stage: string                    // "pass_1", "pass_2", etc.
    stageName: string                // "Full Page Scan", etc.
    highlights: Array<{
        region: { x, y, width, height }
        description: string
        findingType: string
        severity: "high" | "medium" | "low"
    }>
    timestamp: string
}

export function ScreenshotCarousel({ slides }: { slides: ScreenshotSlide[] }) {
    const [currentIndex, setCurrentIndex] = useState(0)
    const [isPlaying, setIsPlaying] = useState(true)

    // Auto-play through slides
    useEffect(() => {
        if (!isPlaying) return

        const interval = setInterval(() => {
            setCurrentIndex(prev => (prev + 1) % slides.length)
        }, 3000) // New slide every 3 seconds

        return () => clearInterval(interval)
    }, [isPlaying, slides.length])

    const currentSlide = slides[currentIndex]

    return (
        <div className="relative">
            {/* Screenshot Container */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-700">
                {/* Base Screenshot */}
                <motion.img
                    src={currentSlide.imageUrl}
                    alt={currentSlide.stageName}
                    className="w-full h-auto"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                />

                {/* Highlight Overlays */}
                <AnimatePresence>
                    {currentSlide.highlights.map((highlight, idx) => (
                        <motion.div
                            key={idx}
                            className="absolute border-2 animate-pulse"
                            style={{
                                left: `${highlight.region.x}%`,
                                top: `${highlight.region.y}%`,
                                width: `${highlight.region.width}%`,
                                height: `${highlight.region.height}%`,
                                borderColor: highlight.severity === "high" ? "#ef4444" :
                                            highlight.severity === "medium" ? "#f59e0b" :
                                            "#22c55e"
                            }}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.2 }}
                        >
                            {/* Finding label attached to highlight */}
                            <motion.div
                                className="absolute -top-8 left-0 px-3 py-1 bg-slate-900/90 text-white text-xs font-medium rounded whitespace-nowrap"
                                initial={{ y: 10, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                            >
                                {highlight.findingType}: {highlight.description}
                            </motion.div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Stage Banner */}
                <motion.div
                    className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-900 via-slate-900/80 to-transparent p-4"
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                >
                    <div className="text-sm text-slate-400">Analysis Pass</div>
                    <div className="text-xl font-bold text-white">{currentSlide.stageName}</div>
                </motion.div>

                {/* Controls */}
                <div className="absolute top-4 right-4 flex gap-2">
                    <motion.button
                        onClick={() => setIsPlaying(!isPlaying)}
                        className="p-2 bg-slate-900/50 rounded-lg text-white hover:bg-slate-900/70"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                    >
                        {isPlaying ? <XCircle className="w-5 h-5" /> : <ZoomIn className="w-5 h-5" />}
                    </motion.button>
                </div>

                {/* Navigation Arrows */}
                {slides.length > 1 && (
                    <>
                        <motion.button
                            onClick={() => setCurrentIndex(prev => (prev - 1 + slides.length) % slides.length)}
                            className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-slate-900/50 rounded-lg text-white hover:bg-slate-900/70"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            <ChevronLeft className="w-6 h-6" />
                        </motion.button>
                        <motion.button
                            onClick={() => setCurrentIndex(prev => (prev + 1) % slides.length)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-slate-900/50 rounded-lg text-white hover:bg-slate-900/70"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            <ChevronRight className="w-6 h-6" />
                        </motion.button>
                    </>
                )}
            </div>

            {/* Progress Dots */}
            {slides.length > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                    {slides.map((_, idx) => (
                        <motion.button
                            key={idx}
                            onClick={() => setCurrentIndex(idx)}
                            className={`w-2 h-2 rounded-full ${idx === currentIndex ? "bg-blue-500" : "bg-slate-600"}`}
                            whileHover={{ scale: 1.2 }}
                            whileTap={{ scale: 0.8 }}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}
```

**Tasks:**
- [ ] Create `ScreenshotCarousel.tsx` component
- [ ] Implement auto-play with manual controls
- [ ] Build highlight overlay system
- [ ] Add stage banner transitions
- [ ] Create progress dot navigation
- [ ] Add zoom/pan for detailed view

**Time Estimate:** 6 hours

### Step 5.4: Build Running Log with Agent Task Flexing
**File:** `frontend/components/RunningLog.tsx`

```tsx
"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useState, useEffect, useRef } from "react"
import { Terminal, Check, X, Clock, Zap } from "lucide-react"

interface LogEntry {
    id: string
    timestamp: string
    agent: "vision" | "graph" | "judge"
    type: "task_start" | "task_progress" | "task_complete" | "finding" | "error"
    message: string
    details?: object
    duration?: number
}

export function RunningLog() {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [isPaused, setIsPaused] = useState(false)
    const logRef = useRef<HTMLDivElement>(null)

    // Auto-scroll to bottom
    useEffect(() => {
        if (logRef.current && !isPaused) {
            logRef.current.scrollTop = logRef.current.scrollHeight
        }
    }, [logs, isPaused])

    // WebSocket listener would add logs here
    useEffect(() => {
        const ws = new WebSocket("ws://localhost:8000/api/audit/stream/audit-id")

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)

            if (data.type === "task_start") {
                setLogs(prev => [...prev, {
                    id: crypto.randomUUID(),
                    timestamp: new Date().toISOString(),
                    agent: data.agent,
                    type: "task_start",
                    message: data.message,
                    details: data.details
                }])
            }

            if (data.type === "finding_detected") {
                setLogs(prev => [...prev, {
                    id: crypto.randomUUID(),
                    timestamp: new Date().toISOString(),
                    agent: data.agent,
                    type: "finding",
                    message: `🎯 ${data.finding.description}`,
                    details: data.finding
                }])
            }
            // ... handle other event types
        }

        return () => ws.close()
    }, [])

    return (
        <div className="bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden">
            {/* Log Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
                <div className="flex items-center gap-3">
                    <Terminal className="w-5 h-5 text-blue-400" />
                    <h3 className="text-lg font-semibold text-white">Live Audit Log</h3>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                        <Clock className="w-4 h-4" />
                        <span>{logs.length} events</span>
                    </div>
                    <button
                        onClick={() => setIsPaused(!isPaused)}
                        className="text-sm text-blue-400 hover:text-blue-300"
                    >
                        {isPaused ? "▶ Resume" : "⏸ Pause"}
                    </button>
                </div>
            </div>

            {/* Log Entries */}
            <div
                ref={logRef}
                className="h-96 overflow-y-auto px-6 py-4 space-y-3 font-mono text-sm"
            >
                <AnimatePresence mode="popLayout">
                    {logs.map((log) => (
                        <motion.div
                            key={log.id}
                            layout
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className={`p-3 rounded-lg border ${
                                log.type === "error" ? "bg-red-900/20 border-red-800" :
                                log.type === "finding" ? "bg-amber-900/20 border-amber-800" :
                                "bg-slate-800/50 border-slate-700"
                            }`}
                        >
                            <div className="flex items-start gap-3">
                                {/* Icon */}
                                <div className="mt-0.5">
                                    {log.type === "task_start" && (
                                        <Zap className="w-4 h-4 text-blue-400" />
                                    )}
                                    {log.type === "task_complete" && (
                                        <Check className="w-4 h-4 text-green-400" />
                                    )}
                                    {log.type === "finding" && (
                                        <Zap className="w-4 h-4 text-amber-400" />
                                    )}
                                    {log.type === "error" && (
                                        <X className="w-4 h-4 text-red-400" />
                                    )}
                                </div>

                                {/* Content */}
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-xs font-semibold text-slate-400 uppercase">
                                            {log.agent}
                                        </span>
                                        <span className="text-xs text-slate-500">
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                        </span>
                                        {log.duration && (
                                            <span className="text-xs text-slate-500">
                                                {log.duration}ms
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-slate-200">
                                        {log.message}
                                    </div>

                                    {/* Optional details */}
                                    {log.details && log.type === "finding" && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: "auto" }}
                                            className="mt-2 pt-2 border-t border-slate-600"
                                        >
                                            <div className="text-xs text-slate-400">
                                                Type: {log.details.type}<br />
                                                Confidence: {(log.details.confidence * 100).toFixed(0)}%
                                            </div>
                                        </motion.div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    )
}
```

**Tasks:**
- [ ] Create `RunningLog.tsx` component
- [ ] Implement WebSocket listener for real-time logs
- [ ] Add log entry animations
- [ ] Build auto-scroll with pause capability
- [ ] Create log filtering and search
- [ ] Add export log functionality

**Time Estimate:** 6 hours

### Step 5.5: Build Agent Task Flexing Showcase
**File:** `frontend/components/TaskFlexShowcase.tsx`

```tsx
"use client"

import { motion, useSpring, useTransform } from "framer-motion"
import { BarChart3, Cpu, Database, Shield, Globe, Brain } from "lucide-react"

interface AgentPerformance {
    agent: string
    tasksCompleted: number
    tasksTotal: number
    accuracy: number          // 0-100
    processingTime: number    // milliseconds
    findingRate: number       // findings per second
}

export function TaskFlexShowcase({ performance }: { performance: AgentPerformance[] }) {
    return (
        <div className="space-y-6">
            <div className="text-center">
                <h2 className="text-3xl font-bold text-white mb-2">
                    Agent Performance Showcase
                </h2>
                <p className="text-slate-400">
                    Watch our AI agents analyze websites with advanced intelligence
                </p>
            </div>

            <div className="grid gap-6">
                {performance.map((agent) => (
                    <motion.div
                        key={agent.agent}
                        className="bg-slate-900 rounded-2xl border border-slate-700 p-6"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: performance.indexOf(agent) * 0.1 }}
                    >
                        {/* Agent Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <motion.div
                                    className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500"
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                                >
                                    <Brain className="w-6 h-6 text-white" />
                                </motion.div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">{agent.agent}</h3>
                                    <div className="text-sm text-slate-400">
                                        {agent.tasksCompleted}/{agent.tasksTotal} tasks
                                    </div>
                                </div>
                            </div>

                            {/* Accuracy Badge */}
                            <div className="text-right">
                                <div className="text-3xl font-bold text-green-400">
                                    {agent.accuracy}%
                                </div>
                                <div className="text-xs text-slate-400">Accuracy</div>
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="mb-6">
                            <div className="relative h-3 bg-slate-800 rounded-full overflow-hidden">
                                <motion.div
                                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 to-cyan-500"
                                    initial={{ width: "0%" }}
                                    animate={{ width: `${(agent.tasksCompleted / agent.tasksTotal) * 100}%` }}
                                    transition={{ duration: 1, delay: 0.5 }}
                                />
                            </div>
                        </div>

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-3 gap-4">
                            <MetricCard
                                icon={Cpu}
                                label="Processing Speed"
                                value={`${agent.processingTime}ms`}
                                color="blue"
                            />
                            <MetricCard
                                icon={BarChart3}
                                label="Finding Rate"
                                value={`${agent.findingRate.toFixed(2)}/s`}
                                color="purple"
                            />
                            <MetricCard
                                icon={Database}
                                label="Knowledge Base"
                                value="15+ OSINT Sources"
                                color="green"
                            />
                        </div>

                        {/* Flexing Statement */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.8 }}
                            className="mt-6 p-4 bg-gradient-to-r from-blue-900/20 to-cyan-900/20 rounded-xl border border-blue-800"
                        >
                            <div className="flex items-start gap-3">
                                <Brain className="w-5 h-5 text-blue-400 mt-0.5" />
                                <div>
                                    <div className="font-semibold text-blue-300 mb-1">
                                        Intelligence Showcase
                                    </div>
                                    <div className="text-sm text-slate-300">
                                        {getFlexStatement(agent.agent, agent.accuracy, agent.findingRate)}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}

function MetricCard({ icon: Icon, label, value, color }: any) {
    const colorClasses = {
        blue: "from-blue-500/20 to-blue-600/20 border-blue-800 text-blue-400",
        purple: "from-purple-500/20 to-purple-600/20 border-purple-800 text-purple-400",
        green: "from-green-500/20 to-green-600/20 border-green-800 text-green-400"
    }

    return (
        <div className={`p-4 rounded-xl border bg-gradient-to-br ${colorClasses[color]}`}>
            <Icon className="w-5 h-5 mb-2" />
            <div className="text-2xl font-bold">{value}</div>
            <div className="text-xs opacity-80">{label}</div>
        </div>
    )
}

function getFlexStatement(agent: string, accuracy: number, findingRate: number): string {
    const statements = {
        vision: `Analyzed ${12} distinct visual deception techniques using NVIDIA VLM with ${accuracy}% accuracy. Found ${findingRate.toFixed(1)} dark patterns per second through sophisticated multi-pass analysis.`,
        graph: `Queried ${15} OSINT intelligence sources including darknet marketplaces, verified ${8} entities, and built ${42}-node knowledge graph with ${accuracy}% verification accuracy.`,
        judge: `Evaluated ${25} security modules against OWASP Top 10, PCI DSS, and GDPR compliance. Generated dual-tier verdict with ${accuracy}% confidence in ${findingRate.toFixed(1)} seconds.`
    }

    return statements[agent] || ""
}
```

**Tasks:**
- [ ] Create `TaskFlexShowcase.tsx` component
- [ ] Build agent performance cards
- [ ] Implement animated progress bars
- [ ] Add metric cards with icons
- [ ] Create flexing statements generator
- [ ] Add real-time updates from backend

**Time Estimate:** 6 hours

**Week 6 Total:** 28 hours ~ 3-4 days

---

## SUMMARY

### Total Implementation Timeline: 6 Weeks

| Week | Focus | Key Deliverables | Hours |
|------|-------|-----------------|-------|
| 1-2 | Vision Agent | 5-pass pipeline, VLM prompts, CV temporal analysis, progress showcase | 22h ~ 3 days |
| 3 | OSINT & Graph | 15+ OSINT sources, darknet analyzer, graph integration | 26h ~ 3-4 days |
| 4 | Judge System | Dual-tier verdicts, 11 site-type strategies, judge agent | 24h ~ 3 days |
| 5 | Cybersecurity | 25+ security modules, darknet threat detection | 28h ~ 3-4 days |
| 6 | Content Showcase | Agent theater, screenshot carousel, running log, task flexing | 28h ~ 3-4 days |

**Total:** ~128 hours of focused implementation (~3-4 weeks full-time or 6 weeks part-time)

---

## Success Metrics

### Technical Metrics
- ✅ 95%+ dark pattern detection accuracy (Vision)
- ✅ 90%+ security vulnerability detection (Security)
- ✅ 25+ security modules implemented
- ✅ 15+ OSINT intelligence sources
- ✅ 11 website type strategies
- ✅ Dual-tier verdict system for all audiences

### User Experience Metrics
- ✅ Real-time agent progress showcase
- ✅ Screenshot carousel with gradual reveal
- ✅ Running log with agent task flexing
- ✅ Psychology-driven content flow
- ✅ No information dump

### Project Goals
- ✅ More mature than "wrappers"
- ✅ Suitable for master's thesis defense
- ✅ Sophisticated OSINT verification
- ✅ Darknet-level analysis coverage
- ✅ Context-specific auditing by website type
- ✅ Masterclass content showcase

---

## Ready to Start?

**Phase 1 Week 1-2:** Vision Agent Enhancement
- Multi-pass pipeline
- Sophisticated VLM prompts
- Computer vision temporal analysis
- Progress showcase emitter

Let's make VERITAS a masterpiece! 🚀🎓✨
