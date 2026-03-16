"""
Veritas Agent 3 — The Cross-Examiner (Graph Reasoning)

The "Detective" of Veritas. Verifies entities extracted from the website
against real-world data sources and builds a knowledge graph of findings.

Pipeline:
    1. Extract entities from Scout's page metadata + Vision's text findings
    2. Run WHOIS lookup on domain
    3. Run DNS checks
    4. Search entities via web search (Tavily API or custom Playwright scraper)
    5. Build NetworkX knowledge graph with 4 node types + 4 edge types
    6. Detect inconsistencies (contradictions between claims and evidence)
    7. Return GraphResult with graph, findings, and graph-based score

Node Types: WebsiteNode, EntityNode, ClaimNode, EvidenceNode
Edge Types: CLAIMS, VERIFIED_BY, CONTRADICTS, LINKS_TO
"""

import asyncio
import json
import logging
import re
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import networkx as nx

from veritas.config import settings
from veritas.core.nim_client import NIMClient
from veritas.osint.orchestrator import OSINTOrchestrator
from veritas.osint.reputation import ReputationManager, VerdictType
from veritas.osint.cti import CThreatIntelligence
from veritas.quality.consensus_engine import ConsensusEngine

logger = logging.getLogger("veritas.graph")


# ============================================================
# Data Structures
# ============================================================

@dataclass
class EntityClaim:
    """An entity claimed by the website."""
    entity_type: str   # "company", "person", "address", "phone", "email", "founding_date"
    entity_value: str  # The actual claimed value
    source_page: str   # URL where this claim was found
    context: str = ""  # Surrounding text for the claim


@dataclass
class VerificationResult:
    """Result of verifying a single claim against external sources."""
    claim: EntityClaim
    status: str            # "confirmed", "denied", "contradicted", "unverifiable"
    evidence_source: str   # Where the answer came from
    evidence_detail: str   # What was found
    confidence: float      # 0.0 to 1.0


@dataclass
class DomainIntel:
    """Intelligence gathered about the domain itself."""
    domain: str
    registrar: str = ""
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    age_days: int = -1
    registrant_country: str = ""
    registrant_org: str = ""
    name_servers: list[str] = field(default_factory=list)
    ip_address: str = ""
    ip_country: str = ""
    ssl_issuer: str = ""
    is_privacy_protected: bool = False
    raw_whois: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class GraphInconsistency:
    """A detected inconsistency between a claim and evidence."""
    claim_text: str
    evidence_text: str
    inconsistency_type: str  # "address_mismatch", "person_not_found", "age_suspicious", etc.
    severity: str            # "low", "medium", "high", "critical"
    confidence: float
    explanation: str


@dataclass
class GraphResult:
    """Complete result from the Graph investigation."""
    # Domain intelligence
    domain_intel: Optional[DomainIntel] = None

    # Entity verification
    claims_extracted: list[EntityClaim] = field(default_factory=list)
    verifications: list[VerificationResult] = field(default_factory=list)
    inconsistencies: list[GraphInconsistency] = field(default_factory=list)

    # Knowledge graph
    graph: Optional[nx.DiGraph] = None
    graph_node_count: int = 0
    graph_edge_count: int = 0

    # Scores (0.0 to 1.0 — higher = more trustworthy)
    graph_score: float = 0.5
    meta_score: float = 0.5     # Domain age + SSL + WHOIS signals

    # MetaAnalyzer results (MX, SPF, DMARC, deep SSL)
    meta_analysis: dict = field(default_factory=dict)

    # IP Geolocation
    ip_geolocation: dict = field(default_factory=dict)

    # Stats
    tavily_searches: int = 0
    errors: list[str] = field(default_factory=list)

    # OSINT/CTI fields
    osint_sources: dict = field(default_factory=dict)
    osint_consensus: dict = field(default_factory=dict)
    osint_indicators: list = field(default_factory=list)
    cti_techniques: list = field(default_factory=list)
    threat_attribution: dict = field(default_factory=dict)
    threat_level: str = "none"
    osint_confidence: float = 0.0

    @property
    def domain_age_days(self) -> int:
        return self.domain_intel.age_days if self.domain_intel else -1

    @property
    def has_ssl(self) -> bool:
        if self.domain_intel:
            return bool(self.domain_intel.ssl_issuer)
        return False

    @property
    def osint_score(self) -> float:
        """Calculate OSINT-based trust score (0-1, higher = more trustworthy)."""
        if self.osint_consensus:
            status = self.osint_consensus.get("consensus_status", "")
            verdict = self.osint_consensus.get("verdict", "")

            if status == "confirmed":
                return 0.9 if verdict == "safe" else 0.3
            elif status == "conflicted":
                return 0.5  # Neutral on conflicts
            elif status == "likely":
                return 0.8 if verdict == "safe" else 0.4

        return 0.5  # Neutral if no OSINT data

    @property
    def has_threat_indicators(self) -> bool:
        """Check if there are threat indicators."""
        return self.threat_level in ["critical", "high", "medium"]


# ============================================================
# Graph Investigator Agent
# ============================================================

class GraphInvestigator:
    """
    Agent 3: Cross-references website claims against real-world data.

    Usage:
        agent = GraphInvestigator()
        result = await agent.investigate(
            url="https://suspicious-bank.com",
            page_metadata={...},   # From Scout
            page_text="...",       # Extracted text from page
        )

        print(f"Graph score: {result.graph_score}")
        print(f"Domain age: {result.domain_age_days} days")
        print(f"Inconsistencies: {len(result.inconsistencies)}")
    """

    def __init__(self, nim_client: Optional[NIMClient] = None, db_session=None):
        self._nim = nim_client or NIMClient()
        self._db_session = db_session
        self._tavily_client = None
        self._search_count = 0
        self._whois_timeout_s = max(1, int(getattr(settings, "GRAPH_WHOIS_TIMEOUT_S", 12)))
        self._dns_timeout_s = max(1, int(getattr(settings, "GRAPH_DNS_TIMEOUT_S", 6)))
        self._ssl_timeout_s = max(1, int(getattr(settings, "GRAPH_SSL_TIMEOUT_S", 6)))
        self._meta_timeout_s = max(1, int(getattr(settings, "GRAPH_META_TIMEOUT_S", 12)))
        self._verify_timeout_s = max(1, int(getattr(settings, "GRAPH_VERIFY_TIMEOUT_S", 20)))
        self._search_timeout_s = max(1, int(getattr(settings, "GRAPH_SEARCH_TIMEOUT_S", 15)))
        self._verify_concurrency = max(1, int(getattr(settings, "GRAPH_VERIFY_CONCURRENCY", 3)))
        self._search_follow_links = bool(getattr(settings, "GRAPH_SEARCH_FOLLOW_LINKS", False))

        # Initialize OSINT/CTI components (db_session optional for caching)
        self._osint_orchestrator = OSINTOrchestrator(self._db_session)
        self._reputation_manager = ReputationManager()
        self._consensus_engine = ConsensusEngine(min_sources=2)

        # CThreatIntelligence doesn't require db session
        self._cti = CThreatIntelligence()

    # ================================================================
    # Public: Full Investigation
    # ================================================================

    async def investigate(
        self,
        url: str,
        page_metadata: dict,
        page_text: str = "",
        external_links: Optional[list[str]] = None,
        site_type: str = "",
        form_validation: Optional[dict] = None,
        page_html: Optional[str] = None,
        progress_callback: Optional[Any] = None,
    ) -> GraphResult:
        """
        Full graph-based investigation of a URL.

        Runs ALL phases regardless of audit tier — the Graph Investigator
        always performs a thorough investigation with WHOIS, DNS, SSL,
        entity extraction, web-search verification, OSINT, CTI, and
        inconsistency detection.

        Args:
            url: Target URL
            page_metadata: Metadata dict from Scout
            page_text: Extracted text content from the page
            external_links: External links found on the page
            site_type: Site type classification
            form_validation: Form validation results
            page_html: HTML content of the page for OSINT/CTI analysis
            progress_callback: Optional async callable(step: str, detail: str)
                               for real-time investigation progress.

        Returns:
            GraphResult with knowledge graph, verifications, and scores
        """
        result = GraphResult()
        graph = nx.DiGraph()
        _progress = progress_callback or (lambda step, detail: None)

        # Extract domain from URL
        domain = self._extract_domain(url)
        logger.info(f"[GRAPH] Starting full investigation for {domain}")

        # -----------------------------------------------------------
        # Phase 1: Domain Intelligence + MetaAnalyzer + IP Geo
        #          (WHOIS, DNS, SSL, MX, SPF, DMARC — all in parallel)
        # -----------------------------------------------------------
        _progress("domain_intel", f"Running WHOIS + DNS + SSL + MetaAnalyzer for {domain}...")
        domain_intel, meta_dict, ip_geo = await self._parallel_domain_intel(domain, url)
        result.domain_intel = domain_intel
        if meta_dict:
            result.meta_analysis = meta_dict
        if ip_geo:
            result.ip_geolocation = ip_geo
            if ip_geo.get("country"):
                domain_intel.ip_country = ip_geo["country"]
        _progress("domain_intel_done", f"Domain age: {domain_intel.age_days}d, SSL: {domain_intel.ssl_issuer or 'none'}, IP: {domain_intel.ip_address}")

        # Add website node to graph
        graph.add_node(
            url,
            node_type="WebsiteNode",
            domain=domain,
            ip=domain_intel.ip_address,
            ssl_issuer=domain_intel.ssl_issuer,
            domain_age_days=domain_intel.age_days,
            creation_date=str(domain_intel.creation_date) if domain_intel.creation_date else "",
        )
        if domain_intel.ip_country:
            graph.nodes[url]["ip_country"] = domain_intel.ip_country

        # -----------------------------------------------------------
        # Phase 2: Entity Extraction
        # -----------------------------------------------------------
        _progress("entity_extraction", f"Extracting entities from metadata + page text ({len(page_text)} chars)...")
        claims = await self._extract_entities(url, page_metadata, page_text)
        result.claims_extracted = claims
        _progress("entity_extraction_done", f"Extracted {len(claims)} entity claims")

        for claim in claims:
            # Add entity node
            entity_id = f"entity:{claim.entity_type}:{claim.entity_value[:50]}"
            graph.add_node(
                entity_id,
                node_type="EntityNode",
                entity_type=claim.entity_type,
                value=claim.entity_value,
            )
            # Add CLAIMS edge
            graph.add_edge(
                url, entity_id,
                edge_type="CLAIMS",
                claim_type=claim.entity_type,
                context=claim.context[:200],
            )

        # -----------------------------------------------------------
        # Phase 3: Entity Verification via Web Search
        # -----------------------------------------------------------
        verifiable = [c for c in claims if c.entity_type in
                      {"person", "company", "address", "phone", "partnership", "award"}]
        _progress("entity_verification", f"Verifying {len(verifiable)} entities via web search...")
        verifications = await self._verify_entities(claims, domain)
        result.verifications = verifications
        confirmed = sum(1 for v in verifications if v.status == "confirmed")
        denied = sum(1 for v in verifications if v.status in ("denied", "contradicted"))
        _progress("entity_verification_done", f"Verified: {confirmed} confirmed, {denied} contradicted, {len(verifications)-confirmed-denied} unverifiable")

        for v in verifications:
            # Add evidence node
            evidence_id = f"evidence:{v.claim.entity_type}:{v.status}:{self._search_count}"
            graph.add_node(
                evidence_id,
                node_type="EvidenceNode",
                source=v.evidence_source,
                detail=v.evidence_detail[:200],
                verification_status=v.status,
            )

            # Add VERIFIED_BY edge from entity to evidence
            entity_id = f"entity:{v.claim.entity_type}:{v.claim.entity_value[:50]}"
            if entity_id in graph:
                graph.add_edge(
                    entity_id, evidence_id,
                    edge_type="VERIFIED_BY",
                    status=v.status,
                    confidence=v.confidence,
                )

            # If contradicted, add CONTRADICTS edge
            if v.status in ("denied", "contradicted"):
                claim_id = f"claim:{v.claim.entity_value[:50]}"
                graph.add_node(
                    claim_id,
                    node_type="ClaimNode",
                    claim_text=v.claim.entity_value,
                    source_page=v.claim.source_page,
                )
                graph.add_edge(
                    evidence_id, claim_id,
                    edge_type="CONTRADICTS",
                    detail=v.evidence_detail[:200],
                )

        # -----------------------------------------------------------
        # Phase 4: External Link Analysis + Social Engineering Detection
        # -----------------------------------------------------------
        _progress("link_analysis", f"Analyzing {len(external_links or [])} external links...")
        se_link_findings: list[GraphInconsistency] = []
        if external_links:
            se_link_findings = self._analyze_social_engineering_links(external_links, domain)

            for ext_url in external_links[:10]:  # Limit to avoid graph bloat
                ext_domain = self._extract_domain(ext_url)
                if ext_domain and ext_domain != domain:
                    ext_id = f"site:{ext_domain}"
                    if ext_id not in graph:
                        graph.add_node(ext_id, node_type="WebsiteNode", domain=ext_domain)
                    graph.add_edge(url, ext_id, edge_type="LINKS_TO", link_type="outbound")

        # -----------------------------------------------------------
        # Phase 4b: MetaAnalyzer + IP geo already ran in Phase 1
        #           (parallel _parallel_domain_intel handles both)
        # -----------------------------------------------------------

        # -----------------------------------------------------------
        # Phase 4d: OSINT Investigation
        # -----------------------------------------------------------
        _progress("osint", f"Running OSINT investigation (DNS, WHOIS, SSL, Threat Intel)...")
        osint_results = {}
        if self._osint_orchestrator:
            hostname = self._extract_domain(url)
            ip_address = domain_intel.ip_address if domain_intel else ""
            osint_results = await self._run_osint_investigation(domain, hostname, ip_address)

            if osint_results:
                result.osint_sources = osint_results
                result.osint_consensus = osint_results.get("_consensus", {})

                # Enhance DomainIntel with OSINT data
                if result.domain_intel and "whois" in osint_results:
                    whois_data = osint_results["whois"].get("data", {})
                    result.domain_intel.age_days = whois_data.get(
                        "age_days", result.domain_intel.age_days
                    )
                    result.domain_intel.registrar = whois_data.get(
                        "registrar", result.domain_intel.registrar
                    )

        if osint_results:
            src_count = len([k for k in osint_results if k != "_consensus"])
            consensus = osint_results.get("_consensus", {}).get("consensus_status", "none")
            _progress("osint_done", f"OSINT: {src_count} sources queried, consensus={consensus}")
        else:
            _progress("osint_done", "OSINT: no results (orchestrator unavailable or all sources failed)")

        # -----------------------------------------------------------
        # Phase 4e: CTI-Lite Analysis
        # -----------------------------------------------------------
        _progress("cti", "Running Cyber Threat Intelligence analysis...")
        if page_html and self._cti and osint_results:
            try:
                cti_result = await self._cti.analyze_threats(
                    url, page_html, page_text, page_metadata, osint_results
                )

                result.osint_indicators = cti_result.get("indicators", [])
                result.cti_techniques = cti_result.get("mitre_techniques", [])
                result.threat_attribution = cti_result.get("attribution", {})
                result.threat_level = cti_result.get("threat_level", "none")
                result.osint_confidence = cti_result.get("confidence", 0.0)
            except Exception as e:
                logger.warning(f"CTI analysis failed: {e}")
                result.errors.append(f"CTI analysis failed: {e}")

        # Derive osint_confidence from consensus agreement when CTI
        # didn't provide one (common — CTI is optional / may fail).
        if result.osint_confidence == 0.0 and result.osint_consensus:
            agreement = result.osint_consensus.get("agreement_count", 0)
            total = result.osint_consensus.get("total_sources", 0)
            if total > 0:
                result.osint_confidence = round(agreement / total, 3)

        _progress("cti_done", f"CTI: threat_level={result.threat_level}, techniques={len(result.cti_techniques)}, indicators={len(result.osint_indicators)}")

        # -----------------------------------------------------------
        # Phase 5: Inconsistency Detection
        # -----------------------------------------------------------
        _progress("inconsistency", "Detecting inconsistencies between claims and evidence...")
        inconsistencies = self._detect_inconsistencies(
            domain_intel, verifications, claims, site_type,
            form_validation=form_validation, ip_geo=result.ip_geolocation,
        )
        # Merge social engineering link findings
        inconsistencies.extend(se_link_findings)
        result.inconsistencies = inconsistencies

        # -----------------------------------------------------------
        # Phase 5b: Add OSINT Nodes to Graph
        # -----------------------------------------------------------
        if osint_results:
            self._add_osint_nodes_to_graph(graph, domain, osint_results, result)

        _progress("inconsistency_done", f"Found {len(inconsistencies)} inconsistencies")

        # -----------------------------------------------------------
        # Phase 6: Compute Scores
        # -----------------------------------------------------------
        _progress("scoring", "Computing enhanced graph trust score...")
        result.graph = graph
        result.graph_node_count = graph.number_of_nodes()
        result.graph_edge_count = graph.number_of_edges()
        result.meta_score = self._compute_meta_score(domain_intel)
        result.graph_score = self._calculate_enhanced_graph_score(result, graph)
        result.tavily_searches = self._search_count

        summary = (
            f"Graph investigation complete for {domain} | "
            f"claims={len(claims)} | verifications={len(verifications)} | "
            f"inconsistencies={len(inconsistencies)} | "
            f"graph_score={result.graph_score:.2f} | meta_score={result.meta_score:.2f} | "
            f"nodes={result.graph_node_count} | edges={result.graph_edge_count}"
        )
        logger.info(f"[GRAPH] {summary}")
        _progress("complete", summary)

        return result

    # ================================================================
    # Private: Domain Intelligence
    # ================================================================

    async def _parallel_domain_intel(self, domain: str, url: str) -> tuple:
        """
        Run WHOIS+DNS+SSL, MetaAnalyzer, and IP geo ALL in parallel.

        Returns (DomainIntel, meta_dict or None, ip_geo or None).
        Runs Phase 1 + MetaAnalyzer concurrently for efficiency without
        sacrificing any data quality.
        """
        from veritas.analysis.meta_analyzer import MetaAnalyzer

        async def _domain_intel_task():
            return await self._gather_domain_intel(domain)

        async def _meta_task():
            try:
                meta_az = MetaAnalyzer()
                meta_result = await self._run_with_timeout(
                    meta_az.analyze(domain),
                    timeout_s=self._meta_timeout_s,
                    step=f"meta-analysis:{domain}",
                )
                return meta_az.to_dict(meta_result), meta_result
            except Exception as e:
                logger.warning(f"MetaAnalyzer failed (parallel): {e}")
                return None, None

        # Run domain intel and MetaAnalyzer in parallel
        (domain_intel, (meta_dict, meta_result)) = await asyncio.gather(
            _domain_intel_task(), _meta_task(),
        )

        # Backfill domain_intel from MetaAnalyzer where direct lookups missed data
        if meta_result:
            if not domain_intel.ssl_issuer and meta_result.ssl_info.is_valid:
                domain_intel.ssl_issuer = meta_result.ssl_info.issuer
            if domain_intel.age_days < 0 and meta_result.domain_age.age_days >= 0:
                domain_intel.age_days = meta_result.domain_age.age_days
                domain_intel.creation_date = meta_result.domain_age.creation_date

        # IP geolocation (fast, ~2s)
        ip_geo = {}
        if domain_intel.ip_address:
            ip_geo = await self._ip_geolocation(domain_intel.ip_address)

        logger.info(
            f"[GRAPH] Domain intel for {domain}: "
            f"age={domain_intel.age_days}d, ssl={'yes' if domain_intel.ssl_issuer else 'no'}, "
            f"ip={domain_intel.ip_address}, meta={'ok' if meta_dict else 'failed'}"
        )

        return domain_intel, meta_dict, ip_geo

    async def _gather_domain_intel(self, domain: str) -> DomainIntel:
        """Gather WHOIS + DNS + SSL intelligence about the domain in parallel."""
        intel = DomainIntel(domain=domain)

        # Run WHOIS, DNS, and SSL lookups in parallel to save time
        async def _whois_task():
            try:
                return await self._run_blocking(
                    self._whois_lookup_sync,
                    timeout_s=self._whois_timeout_s,
                    step=f"whois:{domain}",
                    domain=domain,
                )
            except TimeoutError as e:
                logger.warning(f"WHOIS lookup timed out for {domain}: {e}")
                intel.errors.append(f"WHOIS timeout after {self._whois_timeout_s}s")
                return None
            except Exception as e:
                logger.warning(f"WHOIS lookup failed for {domain}: {e}")
                intel.errors.append(f"WHOIS failed: {str(e)}")
                return None

        async def _dns_task():
            try:
                return await self._run_blocking(
                    self._dns_lookup_sync,
                    timeout_s=self._dns_timeout_s,
                    step=f"dns:{domain}",
                    domain=domain,
                )
            except TimeoutError:
                logger.warning(f"DNS lookup timed out for {domain}")
                intel.errors.append(f"DNS timeout after {self._dns_timeout_s}s")
                return None
            except (socket.gaierror, Exception) as e:
                logger.warning(f"DNS lookup failed for {domain}: {e}")
                intel.errors.append(f"DNS failed: {str(e)}")
                return None

        async def _ssl_task():
            try:
                return await self._run_blocking(
                    self._ssl_issuer_lookup_sync,
                    timeout_s=self._ssl_timeout_s,
                    step=f"ssl:{domain}",
                    domain=domain,
                    ssl_timeout_s=self._ssl_timeout_s,
                )
            except TimeoutError:
                logger.debug(f"SSL lookup timed out for {domain}")
                return None
            except Exception:
                return None  # No SSL or unreachable

        whois_result, dns_result, ssl_result = await asyncio.gather(
            _whois_task(), _dns_task(), _ssl_task(),
        )

        # Process WHOIS result
        if whois_result is not None:
            w = whois_result
            intel.registrar = str(w.registrar or "")
            intel.registrant_org = str(w.org or "")
            intel.registrant_country = str(w.country or "")
            intel.raw_whois = str(w.text or "")[:2000]

            if w.creation_date:
                cd = w.creation_date
                if isinstance(cd, list):
                    cd = cd[0]
                if isinstance(cd, datetime):
                    intel.creation_date = cd
                    cd_utc = cd if cd.tzinfo else cd.replace(tzinfo=timezone.utc)
                    intel.age_days = (datetime.now(timezone.utc) - cd_utc).days

            if w.expiration_date:
                ed = w.expiration_date
                if isinstance(ed, list):
                    ed = ed[0]
                if isinstance(ed, datetime):
                    intel.expiration_date = ed

            if w.name_servers:
                ns = w.name_servers
                if isinstance(ns, list):
                    intel.name_servers = [str(n) for n in ns]
                else:
                    intel.name_servers = [str(ns)]

            privacy_keywords = ["privacy", "proxy", "redacted", "whoisguard", "domains by proxy"]
            whois_text_lower = intel.raw_whois.lower()
            intel.is_privacy_protected = any(kw in whois_text_lower for kw in privacy_keywords)

        # Process DNS result
        if dns_result is not None:
            intel.ip_address = dns_result

        # Process SSL result
        if ssl_result is not None:
            intel.ssl_issuer = ssl_result

        return intel

    async def _run_osint_investigation(
        self, domain: str, hostname: str, ip_address: str
    ) -> dict:
        """
        Run OSINT investigation using OSINTOrchestrator.

        Coordinated queries to DNS, WHOIS, SSL, threat intel sources.
        Returns dict with source results and consensus.
        """
        if not self._osint_orchestrator:
            logger.warning("OSINT orchestrator not available (no db session)")
            return {}

        from veritas.osint.types import OSINTCategory

        results = {}

        # Query DNS if domain provided
        if domain:
            try:
                dns_result = await self._osint_orchestrator.query_with_retry(
                    "dns", "query", domain
                )
                if dns_result.status.value == "success":
                    results["dns"] = dns_result.to_dict()
            except Exception as e:
                logger.warning(f"DNS OSINT query failed: {e}")

        # Query WHOIS if domain provided
        if domain:
            try:
                whois_result = await self._osint_orchestrator.query_with_retry(
                    "whois", "query", domain
                )
                if whois_result.status.value == "success":
                    results["whois"] = whois_result.to_dict()
            except Exception as e:
                logger.warning(f"WHOIS OSINT query failed: {e}")

        # Query SSL if hostname provided
        if hostname:
            try:
                ssl_result = await self._osint_orchestrator.query_with_retry(
                    "ssl", "query", hostname
                )
                if ssl_result.status.value == "success":
                    results["ssl"] = ssl_result.to_dict()
            except Exception as e:
                logger.warning(f"SSL OSINT query failed: {e}")

        # Query threat intel sources if available
        if domain and results:
            try:
                from veritas.osint.types import OSINTResult

                # Get available threat intel sources
                threat_results = await self._osint_orchestrator.query_all(
                    OSINTCategory.THREAT_INTEL, "domain", domain, max_parallel=2
                )

                # Add successful results
                for source_name, result in threat_results.items():
                    if isinstance(result, OSINTResult) and result.status.value == "success":
                        results[source_name] = result.to_dict()
            except Exception as e:
                logger.warning(f"Threat intel OSINT query failed: {e}")

        # Compute consensus if results exist
        if results and self._consensus_engine:
            try:
                # Convert results dicts back to OSINTResult objects for consensus
                from veritas.osint.types import OSINTResult, SourceStatus, OSINTCategory

                osint_objects = {}
                for source_name, result_dict in results.items():
                    try:
                        # Reconstruct OSINTResult from dict
                        osint_objects[source_name] = OSINTResult(
                            source=source_name,
                            category=OSINTCategory(result_dict.get("category", "dns")),
                            query_type=result_dict.get("query_type", "query"),
                            query_value=result_dict.get("query_value", domain),
                            status=SourceStatus(result_dict.get("status", "success")),
                            data=result_dict.get("data"),
                            confidence_score=result_dict.get("confidence_score", 0.0),
                        )
                    except Exception:
                        # Skip if reconstruction fails
                        continue

                if osint_objects:
                    consensus = self._consensus_engine.compute_osint_consensus(
                        osint_objects, min_sources=2
                    )
                    results["_consensus"] = consensus
            except Exception as e:
                logger.warning(f"Consensus computation failed: {e}")

        return results

    # ================================================================
    # Private: Entity Extraction
    # ================================================================

    async def _extract_entities(
        self,
        url: str,
        page_metadata: dict,
        page_text: str,
    ) -> list[EntityClaim]:
        """
        Extract verifiable entity claims from page metadata and text.
        Uses NIM LLM for intelligent extraction from unstructured text.
        """
        claims = []

        # --- Structured extraction from metadata ---
        title = page_metadata.get("description", "")
        if title:
            claims.append(EntityClaim(
                entity_type="description",
                entity_value=title,
                source_page=url,
                context="Meta description tag",
            ))

        og_tags = page_metadata.get("og_tags", {})
        if og_tags.get("og:site_name"):
            claims.append(EntityClaim(
                entity_type="company",
                entity_value=og_tags["og:site_name"],
                source_page=url,
                context="OpenGraph site_name tag",
            ))

        # --- LLM-powered extraction from text ---
        if page_text and len(page_text.strip()) > 50:
            extracted = await self._llm_extract_entities(url, page_text[:3000])
            claims.extend(extracted)

        # Deduplicate claims by (entity_type, normalized entity_value)
        seen = set()
        unique_claims = []
        for c in claims:
            key = (c.entity_type, c.entity_value.strip().lower())
            if key not in seen:
                seen.add(key)
                unique_claims.append(c)
        return unique_claims

    async def _llm_extract_entities(
        self, url: str, text: str,
    ) -> list[EntityClaim]:
        """Use NIM LLM to extract verifiable entities from page text."""
        # Truncate text to reduce token waste
        text_trimmed = text[:3000] if len(text) > 3000 else text

        prompt = (
            "Extract verifiable real-world entities from this website text.\n"
            "EXTRACT ONLY:\n"
            "- Company names (registered business names, not product names)\n"
            "- Person names with titles (CEO, founder, director)\n"
            "- Physical addresses (street, city, country)\n"
            "- Phone numbers, email addresses\n"
            "- Founding dates or years\n"
            "- Partnership/award/certification claims (specific names only)\n\n"
            "DO NOT extract: generic descriptions, marketing slogans, product features, "
            "industry terms, or obvious truths.\n"
            "Return 0-10 entities maximum. Quality over quantity.\n\n"
            "Respond ONLY in JSON:\n"
            '{"entities": [\n'
            '  {"type": "company|person|address|phone|email|founding_date|partnership|award|certification",\n'
            '   "value": "exact claimed value",\n'
            '   "context": "10-word surrounding context"}\n'
            "]}\n\n"
            f"Website text:\n{text_trimmed}"
        )

        result = await self._nim.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are a forensic entity extraction specialist for website trust audits. "
                "Extract ONLY specific, verifiable claims that can be cross-referenced against "
                "company registries, LinkedIn, or public records. "
                "Never extract marketing language, generic terms, or obvious truths. "
                "If the text contains no verifiable entities, return {\"entities\": []}."
            ),
            max_tokens=768,
            temperature=0.0,
        )

        claims = []
        try:
            response_text = result.get("response", "")
            data = self._extract_json(response_text)
            if data and "entities" in data:
                for entity in data["entities"]:
                    if isinstance(entity, dict) and entity.get("type") and entity.get("value"):
                        claims.append(EntityClaim(
                            entity_type=entity["type"],
                            entity_value=entity["value"],
                            source_page=url,
                            context=entity.get("context", ""),
                        ))
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")

        if not claims:
            import re
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text_trimmed)
            for e in set(emails):
                claims.append(EntityClaim(entity_type="email", entity_value=e, source_page=url, context="Extracted via regex"))
            phones = re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text_trimmed)
            for p in set(phones):
                claims.append(EntityClaim(entity_type="phone", entity_value=p, source_page=url, context="Extracted via regex"))
            corps = re.findall(r'[A-Z][a-zA-Z0-9-]*\s+(?:LLC|Inc\.|Ltd\.|Corporation|Corp\.)', text_trimmed)
            for c in set(corps):
                claims.append(EntityClaim(entity_type="company", entity_value=c, source_page=url, context="Extracted via regex"))

        return claims

    # ================================================================
    # Private: Entity Verification
    # ================================================================

    async def _verify_entities(
        self, claims: list[EntityClaim], domain: str,
    ) -> list[VerificationResult]:
        """
        Verify entity claims against external sources via Tavily search.
        Prioritizes high-value claims (people, addresses, companies).
        """
        verifications = []

        # Priority order: people > companies > addresses > others
        priority_order = ["person", "company", "address", "phone", "email",
                          "founding_date", "partnership", "award", "certification"]

        sorted_claims = sorted(
            claims,
            key=lambda c: priority_order.index(c.entity_type)
            if c.entity_type in priority_order else 99,
        )

        # Limit to top N claims to conserve API budget — tier-based
        max_verifications = getattr(settings, 'max_verifications', 5)
        verifiable_types = {"person", "company", "address", "phone", "partnership", "award"}
        to_verify = [
            c for c in sorted_claims if c.entity_type in verifiable_types
        ][:max_verifications]

        if not to_verify:
            return verifications

        semaphore = asyncio.Semaphore(self._verify_concurrency)

        async def _verify_with_limits(claim: EntityClaim) -> VerificationResult:
            async with semaphore:
                try:
                    return await self._run_with_timeout(
                        self._verify_single_claim(claim, domain),
                        timeout_s=self._verify_timeout_s,
                        step=f"verify:{claim.entity_type}",
                    )
                except TimeoutError:
                    logger.warning(
                        f"Verification timeout for {claim.entity_type}={claim.entity_value[:64]}"
                    )
                    return VerificationResult(
                        claim=claim,
                        status="unverifiable",
                        evidence_source="Timeout",
                        evidence_detail=f"Verification timed out after {self._verify_timeout_s}s",
                        confidence=0.2,
                    )
                except Exception as e:
                    logger.warning(
                        f"Verification failed for {claim.entity_type}={claim.entity_value[:64]}: {e}"
                    )
                    return VerificationResult(
                        claim=claim,
                        status="unverifiable",
                        evidence_source="Error",
                        evidence_detail=str(e),
                        confidence=0.1,
                    )

        verifications = await asyncio.gather(*[_verify_with_limits(claim) for claim in to_verify])

        return verifications

    async def _verify_single_claim(
        self, claim: EntityClaim, domain: str,
    ) -> VerificationResult:
        """Verify a single entity claim via Tavily web search."""
        # Build search query based on claim type
        query = self._build_search_query(claim, domain)

        try:
            search_results = await self._tavily_search(query)
            self._search_count += 1

            if not search_results:
                return VerificationResult(
                    claim=claim,
                    status="unverifiable",
                    evidence_source="Web Search",
                    evidence_detail="No relevant search results found",
                    confidence=0.3,
                )

            # Use NIM LLM to interpret the search results
            verdict = await self._llm_verify(claim, search_results, domain)
            return verdict

        except Exception as e:
            logger.warning(f"Verification failed for {claim.entity_type}={claim.entity_value}: {e}")
            return VerificationResult(
                claim=claim,
                status="unverifiable",
                evidence_source="Error",
                evidence_detail=str(e),
                confidence=0.1,
            )

    def _build_search_query(self, claim: EntityClaim, domain: str) -> str:
        """Build a targeted search query for entity verification."""
        queries = {
            "person": f'"{claim.entity_value}" {domain} CEO OR founder OR director',
            "company": f'"{claim.entity_value}" company registration OR incorporation',
            "address": f'"{claim.entity_value}" business OR office OR "{domain}"',
            "phone": f'"{claim.entity_value}" business phone',
            "partnership": f'"{claim.entity_value}" partnership OR collaboration {domain}',
            "award": f'"{claim.entity_value}" award OR recognition',
        }
        return queries.get(claim.entity_type, f'"{claim.entity_value}" {domain}')

    async def _tavily_search(self, query: str) -> list[dict]:
        """Execute a web search — prefers Tavily if configured, else uses custom Playwright scraper."""
        # Try Tavily first if API key is set
        if settings.TAVILY_API_KEY:
            try:
                from tavily import AsyncTavilyClient

                if not self._tavily_client:
                    self._tavily_client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

                response = await self._run_with_timeout(
                    self._tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3,
                    ),
                    timeout_s=self._search_timeout_s,
                    step="tavily-search",
                )

                results = response.get("results", [])
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:500],
                    }
                    for r in results
                ]

            except Exception as e:
                logger.warning(f"Tavily search failed, falling back to custom scraper: {e}")

        # Fallback: multi-engine custom search (DuckDuckGo + Google + Bing)
        try:
            from veritas.core.web_searcher import web_search
            return await self._run_with_timeout(
                web_search(
                    query=query,
                    max_results=5,
                    follow_links=self._search_follow_links,
                    timeout_ms=self._search_timeout_s * 1000,
                    parallel=True,
                ),
                timeout_s=self._search_timeout_s + 10,
                step="multi-engine-search",
            )
        except Exception as e:
            logger.warning(f"Multi-engine web search also failed: {e}")
            return []

    async def _llm_verify(
        self, claim: EntityClaim, search_results: list[dict], domain: str,
    ) -> VerificationResult:
        """Use NIM LLM to interpret search results against a claim."""
        results_text = "\n".join(
            f"- [{r['title']}]({r['url']}): {r['content'][:300]}"
            for r in search_results[:5]
        )

        prompt = (
            f"Website {domain} claims: {claim.entity_type} = \"{claim.entity_value}\"\n"
            f"Context: \"{claim.context[:150]}\"\n\n"
            f"Search evidence:\n{results_text}\n\n"
            "Verdict? Respond in JSON:\n"
            '{"status": "confirmed|denied|contradicted|unverifiable",\n'
            ' "confidence": 0.0-1.0,\n'
            ' "explanation": "one sentence"}'
        )

        result = await self._nim.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are a forensic OSINT analyst. Compare the website claim against "
                "search evidence with strict rules:\n\n"
                "VERDICT RULES:\n"
                "- 'confirmed': A credible source (gov registry, LinkedIn, press) explicitly "
                " confirms the claim with matching details.\n"
                "- 'contradicted': Search evidence contains SPECIFIC CONFLICTING FACTS "
                " (e.g., different founding year, different address, explicit denial).\n"
                "- 'denied': An official authority explicitly refutes the claim.\n"
                "- 'unverifiable': DEFAULT. Use when search results don't mention the "
                " entity, contain only irrelevant results, or information is simply absent.\n\n"
                "CRITICAL: Absence of evidence is NOT contradiction. Small/regional companies "
                "often have minimal online presence. If you cannot find the entity, "
                "the verdict is 'unverifiable', NEVER 'contradicted'."
            ),
            max_tokens=200,
            temperature=0.0,
        )

        try:
            data = self._extract_json(result.get("response", ""))
            if data:
                status = data.get("status", "unverifiable")
                explanation = data.get("explanation", "").lower()
                confidence = float(data.get("confidence", 0.5))

                # Guardrail: downgrade false "contradicted" verdicts.
                # If the explanation signals absence rather than
                # actual conflicting evidence, treat as unverifiable.
                if status == "contradicted":
                    absence_phrases = [
                        "no results", "not found", "no evidence",
                        "could not find", "no mention", "no record",
                        "no information", "unable to find", "lack of",
                        "no credible", "no relevant", "does not appear",
                        "couldn't find", "no specific", "no matching",
                        "no direct", "limited online", "no data",
                    ]
                    if any(phrase in explanation for phrase in absence_phrases):
                        logger.info(
                            f"Downgraded 'contradicted' → 'unverifiable' for "
                            f"{claim.entity_type}={claim.entity_value[:40]} "
                            f"(reason: absence, not contradiction)"
                        )
                        status = "unverifiable"
                        confidence = min(confidence, 0.4)

                return VerificationResult(
                    claim=claim,
                    status=status,
                    evidence_source="Web Search + NIM LLM",
                    evidence_detail=data.get("explanation", ""),
                    confidence=confidence,
                )
        except Exception:
            pass

        return VerificationResult(
            claim=claim,
            status="unverifiable",
            evidence_source="NIM LLM (unparseable)",
            evidence_detail=result.get("response", "")[:200],
            confidence=0.3,
        )

    # ================================================================
    # Private: Inconsistency Detection
    # ================================================================

    def _detect_inconsistencies(
        self,
        domain_intel: DomainIntel,
        verifications: list[VerificationResult],
        claims: list[EntityClaim],
        site_type: str = "",
        form_validation: Optional[dict] = None,
        ip_geo: Optional[dict] = None,
    ) -> list[GraphInconsistency]:
        """Detect logical inconsistencies between claims and evidence."""
        inconsistencies = []

        # Rule 1: New domain claiming to be established
        if domain_intel.age_days >= 0 and domain_intel.age_days < 30:
            # Check if site claims to be established/old
            for claim in claims:
                if claim.entity_type == "founding_date":
                    try:
                        year_match = re.search(r'(19|20)\d{2}', claim.entity_value)
                        if year_match:
                            claimed_year = int(year_match.group())
                            if claimed_year < 2024:
                                inconsistencies.append(GraphInconsistency(
                                    claim_text=f"Claims founded in {claimed_year}",
                                    evidence_text=f"Domain registered {domain_intel.age_days} days ago",
                                    inconsistency_type="age_suspicious",
                                    severity="critical",
                                    confidence=0.9,
                                    explanation=(
                                        f"Website claims to have been founded in {claimed_year} "
                                        f"but the domain is only {domain_intel.age_days} days old"
                                    ),
                                ))
                    except (ValueError, AttributeError):
                        pass

        # Rule 2: Very new domain (< 7 days)
        if 0 <= domain_intel.age_days < 7:
            inconsistencies.append(GraphInconsistency(
                claim_text="Website exists",
                evidence_text=f"Domain registered {domain_intel.age_days} day(s) ago",
                inconsistency_type="very_new_domain",
                severity="high",
                confidence=0.85,
                explanation="Domain is extremely new — high risk for scam/fraud sites",
            ))

        # Rule 3: Privacy-protected WHOIS on a "legitimate business"
        if domain_intel.is_privacy_protected:
            company_claims = [c for c in claims if c.entity_type == "company"]
            if company_claims:
                inconsistencies.append(GraphInconsistency(
                    claim_text=f"Claims to be '{company_claims[0].entity_value}'",
                    evidence_text="WHOIS data is privacy-protected",
                    inconsistency_type="hidden_registrant",
                    severity="medium",
                    confidence=0.5,
                    explanation=(
                        "Legitimate businesses typically don't hide their WHOIS data. "
                        "Privacy protection is normal for personal sites but unusual for "
                        "businesses claiming transparency."
                    ),
                ))

        # Rule 4: Denied/contradicted verifications
        for v in verifications:
            if v.status in ("denied", "contradicted") and v.confidence > 0.5:
                inconsistencies.append(GraphInconsistency(
                    claim_text=f"{v.claim.entity_type}: {v.claim.entity_value}",
                    evidence_text=v.evidence_detail,
                    inconsistency_type=f"{v.claim.entity_type}_mismatch",
                    severity="high" if v.confidence > 0.7 else "medium",
                    confidence=v.confidence,
                    explanation=(
                        f"The website claims {v.claim.entity_type}='{v.claim.entity_value}' "
                        f"but external evidence {v.status} this: {v.evidence_detail}"
                    ),
                ))

        # Rule 5: SSL issuer mismatch — free / suspicious cert on financial site
        if site_type in ("financial", "saas_subscription", "ecommerce"):
            ssl_issuer = (domain_intel.ssl_issuer or "").lower()
            free_issuers = ["let's encrypt", "letsencrypt", "zerossl", "buypass"]
            if not domain_intel.ssl_issuer:
                inconsistencies.append(GraphInconsistency(
                    claim_text=f"Site type: {site_type}",
                    evidence_text="No SSL certificate detected",
                    inconsistency_type="ssl_missing_critical",
                    severity="critical",
                    confidence=0.95,
                    explanation=f"A {site_type} site MUST have SSL — none detected",
                ))
            elif any(fi in ssl_issuer for fi in free_issuers):
                inconsistencies.append(GraphInconsistency(
                    claim_text=f"Site type: {site_type}",
                    evidence_text=f"SSL issuer: {domain_intel.ssl_issuer}",
                    inconsistency_type="ssl_free_cert",
                    severity="medium",
                    confidence=0.6,
                    explanation=(
                        f"A {site_type} site uses a free SSL cert ({domain_intel.ssl_issuer}). "
                        f"Legitimate financial/payment sites typically use EV or OV certificates."
                    ),
                ))

        # Rule 6: IP geolocation vs claimed country mismatch
        if ip_geo and ip_geo.get("country"):
            ip_country = ip_geo["country"].lower()
            # Check if any address claim mentions a different country
            for claim in claims:
                if claim.entity_type == "address":
                    claimed_lower = claim.entity_value.lower()
                    # Rough check: if address mentions a specific country but IP is different
                    country_names = [
                        "united states", "usa", "uk", "united kingdom", "canada",
                        "australia", "germany", "france", "india", "japan",
                    ]
                    for cn in country_names:
                        if cn in claimed_lower and cn not in ip_country:
                            inconsistencies.append(GraphInconsistency(
                                claim_text=f"Address claims: {claim.entity_value[:80]}",
                                evidence_text=f"Server IP located in: {ip_geo.get('country', '?')} ({ip_geo.get('city', '?')})",
                                inconsistency_type="geolocation_mismatch",
                                severity="medium",
                                confidence=0.55,
                                explanation=(
                                    f"Website claims address in '{cn}' but server "
                                    f"is hosted in {ip_geo.get('country', '?')}"
                                ),
                            ))
                            break

        # Rule 7: Cross-domain sensitive forms (from FormActionValidator)
        if form_validation:
            crit_forms = form_validation.get("critical_count", 0)
            if crit_forms > 0:
                inconsistencies.append(GraphInconsistency(
                    claim_text="Website has forms sending data to external domains",
                    evidence_text=f"{crit_forms} critical form issue(s) detected",
                    inconsistency_type="cross_domain_forms",
                    severity="critical" if crit_forms > 1 else "high",
                    confidence=0.85,
                    explanation=(
                        f"Found {crit_forms} form(s) posting sensitive data (passwords/credit cards) "
                        f"to third-party domains — potential credential harvesting."
                    ),
                ))

        # Rule 8: Bulletproof hosting detection (IP in known hosting abuse countries)
        if ip_geo:
            hosting_provider = ip_geo.get("org", "").lower()
            bulletproof_keywords = [
                "dataclub", "hostkey", "llc bullet", "ecatel", "quasi",
                "hostwinds", "maxided", "media land", "king servers",
            ]
            if any(bp in hosting_provider for bp in bulletproof_keywords):
                inconsistencies.append(GraphInconsistency(
                    claim_text="Hosting provider",
                    evidence_text=f"Hosted by: {ip_geo.get('org', '?')}",
                    inconsistency_type="bulletproof_hosting",
                    severity="critical",
                    confidence=0.80,
                    explanation=(
                        f"IP is hosted by '{ip_geo.get('org', '?')}', which is associated "
                        f"with bulletproof hosting — commonly used by malicious actors."
                    ),
                ))

        # Rule 9: Multiple domains sharing same IP (if resolvable)
        # Lightweight check: just flag if IP is a known shared hosting range
        if domain_intel.ip_address:
            ip = domain_intel.ip_address
            # Common shared hosting indicator: hosting on popular CDN is fine
            cdn_ips = ["104.16.", "104.17.", "104.18.", "172.67.", "13.107."]
            is_cdn = any(ip.startswith(prefix) for prefix in cdn_ips)
            if not is_cdn and not domain_intel.ssl_issuer:
                # Non-CDN + no SSL = higher risk
                inconsistencies.append(GraphInconsistency(
                    claim_text="Website infrastructure",
                    evidence_text=f"IP: {ip}, no CDN, no SSL",
                    inconsistency_type="bare_hosting_no_ssl",
                    severity="high",
                    confidence=0.7,
                    explanation=(
                        "Site is hosted on a bare IP without CDN protection or SSL — "
                        "legitimate businesses typically use CDN and HTTPS."
                    ),
                ))

        return inconsistencies

    # ================================================================
    # Private: Social Engineering Link Analysis
    # ================================================================

    def _analyze_social_engineering_links(
        self, links: list[str], domain: str,
    ) -> list[GraphInconsistency]:
        """
        Analyze external links for social engineering red flags.

        Detects:
        - Urgency/fear parameters in URLs (e.g., ?action=verify&urgent=true)
        - Affiliate chain redirects (multiple redirect hops)
        - URL shorteners hiding destinations
        - Lookalike/typosquat domains
        - Payment links disguised as legitimate redirects
        """
        findings: list[GraphInconsistency] = []
        from urllib.parse import urlparse, parse_qs

        # Known URL shorteners
        shorteners = {
            "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
            "is.gd", "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at",
        }
        # Urgency/phishing URL parameters
        urgency_params = {
            "urgent", "verify", "suspend", "locked", "alert", "action",
            "confirm", "secure", "update", "expire", "deadline", "limited",
        }
        # Payment/financial domains (legitimate → suspicious if unexpected)
        payment_domains = {
            "paypal.com", "stripe.com", "square.com", "venmo.com",
            "cashapp.com", "zelle.com", "wise.com",
        }

        shortener_count = 0
        urgency_link_count = 0
        affiliate_chain_count = 0

        for link in links[:30]:  # Limit scan
            try:
                parsed = urlparse(link)
                link_domain = (parsed.hostname or "").lower()
                params = parse_qs(parsed.query)
                path = parsed.path.lower()

                # 1. URL shorteners hiding destinations
                if link_domain in shorteners:
                    shortener_count += 1

                # 2. Urgency parameters in URLs
                param_keys = {k.lower() for k in params.keys()}
                found_urgency = param_keys & urgency_params
                if found_urgency:
                    urgency_link_count += 1

                # 3. Affiliate/tracking chains (long redirect paths)
                redirect_indicators = ["redirect", "goto", "forward", "click", "track", "out"]
                if any(ri in path for ri in redirect_indicators) and len(path) > 20:
                    affiliate_chain_count += 1

                # 4. Payment domain links from non-financial site
                if link_domain in payment_domains:
                    # Direct payment links are suspicious on non-checkout pages
                    findings.append(GraphInconsistency(
                        claim_text=f"Link to payment service: {link_domain}",
                        evidence_text=f"External link to {link[:100]}",
                        inconsistency_type="suspicious_payment_link",
                        severity="medium",
                        confidence=0.6,
                        explanation=(
                            f"Page links directly to {link_domain}, which could be "
                            f"a phishing redirect disguised as a payment flow."
                        ),
                    ))

                # 5. Lookalike domain detection
                domain_base = domain.split(".")[0].lower()
                link_base = link_domain.split(".")[0].lower() if link_domain else ""
                if (link_base and link_base != domain_base
                        and self._is_lookalike(domain_base, link_base)):
                    findings.append(GraphInconsistency(
                        claim_text=f"Link to lookalike domain: {link_domain}",
                        evidence_text=f"Main domain is {domain}, link goes to {link_domain}",
                        inconsistency_type="lookalike_domain",
                        severity="high",
                        confidence=0.75,
                        explanation=(
                            f"External link to '{link_domain}' closely resembles "
                            f"the main domain '{domain}' — possible typosquatting/phishing."
                        ),
                    ))

            except Exception:
                continue

        # Aggregate findings for shorteners and urgency links
        if shortener_count >= 3:
            findings.append(GraphInconsistency(
                claim_text="Multiple URL-shortened links",
                evidence_text=f"{shortener_count} links use URL shorteners",
                inconsistency_type="excessive_shorteners",
                severity="medium",
                confidence=0.65,
                explanation=(
                    f"Page has {shortener_count} URL-shortened links hiding their "
                    f"true destinations — common social engineering tactic."
                ),
            ))

        if urgency_link_count >= 2:
            findings.append(GraphInconsistency(
                claim_text="Links with urgency/fear parameters",
                evidence_text=f"{urgency_link_count} links contain urgency parameters",
                inconsistency_type="urgency_links",
                severity="high",
                confidence=0.7,
                explanation=(
                    f"Found {urgency_link_count} links with urgency-related URL parameters "
                    f"(verify, suspend, urgent) — social engineering pressure tactic."
                ),
            ))

        if affiliate_chain_count >= 3:
            findings.append(GraphInconsistency(
                claim_text="Redirect/tracking chains in links",
                evidence_text=f"{affiliate_chain_count} links contain redirect paths",
                inconsistency_type="affiliate_chains",
                severity="medium",
                confidence=0.6,
                explanation=(
                    f"Found {affiliate_chain_count} links with redirect/tracking paths — "
                    f"may be obscuring true link destinations."
                ),
            ))

        return findings

    @staticmethod
    def _is_lookalike(base: str, candidate: str) -> bool:
        """Check if candidate is a lookalike/typosquat of base domain name."""
        if len(base) < 4 or len(candidate) < 4:
            return False
        # Levenshtein distance ≤ 2 for similar-length strings
        if abs(len(base) - len(candidate)) > 3:
            return False
        # Simple character-level similarity
        common = sum(1 for a, b in zip(base, candidate) if a == b)
        similarity = common / max(len(base), len(candidate))
        return similarity >= 0.7 and base != candidate

    # ================================================================
    # Private: OSINT Graph Nodes
    # ================================================================

    def _add_osint_nodes_to_graph(
        self, graph: nx.DiGraph, domain: str, osint_results: dict, result: GraphResult
    ) -> None:
        """Add OSINT findings as nodes in the knowledge graph."""
        # Create Website node reference
        website_id = f"Website_{domain}"

        # Ensure Website node has OSINT sources attribute
        if website_id in graph:
            graph.nodes[website_id]["osint_sources"] = list(osint_results.keys())
        else:
            # Create Website node if not exists
            graph.add_node(
                website_id,
                node_type="WebsiteNode",
                domain=domain,
                osint_sources=list(osint_results.keys()),
            )

        # Add OSINT source nodes
        for source_name in osint_results.keys():
            if source_name == "_consensus":
                continue

            source_data = osint_results[source_name]

            # Create OSINTSource node
            source_id = f"OSINTSource_{source_name}"
            graph.add_node(
                source_id,
                node_type="OSINTSourceNode",
                source=source_name,
                category=source_data.get("category", "unknown"),
                confidence=source_data.get("confidence_score", 0.0),
                status=source_data.get("status", "unknown"),
            )

            # Add VERIFIED_BY edge from Website to OSINTSource
            graph.add_edge(website_id, source_id, edge_type="VERIFIED_BY")

        # Add Consensus node if available
        if "_consensus" in osint_results:
            consensus = osint_results["_consensus"]
            consensus_id = f"OSINTConsensus_{domain}"

            graph.add_node(
                consensus_id,
                node_type="ConsensusNode",
                status=consensus.get("consensus_status", ""),
                verdict=consensus.get("verdict", ""),
                agreement_count=consensus.get("agreement_count", 0),
                has_conflict=consensus.get("has_conflict", False),
            )

            # Add CONTRIBUTES_TO edges from OSINTSources to Consensus
            for source_name in osint_results.keys():
                if source_name == "_consensus":
                    continue
                source_id = f"OSINTSource_{source_name}"
                graph.add_edge(source_id, consensus_id, edge_type="CONTRIBUTES_TO")

        # Add IOC nodes
        for indicator in result.osint_indicators:
            if not isinstance(indicator, dict):
                continue

            ioc_type = indicator.get("ioc_type", "unknown")
            ioc_value = indicator.get("value", "")
            if not ioc_value:
                continue

            # Create unique IOC node ID
            ioc_id = f"IOC_{ioc_type}_{ioc_value[:20]}"
            graph.add_node(
                ioc_id,
                node_type="IOCNode",
                ioc_type=ioc_type,
                value=ioc_value,
                threat_level=indicator.get("threat_level", "unknown"),
            )

            # Add CONTAINS_IOC edge from Website to IOC
            graph.add_edge(website_id, ioc_id, edge_type="CONTAINS_IOC")

        # Add MITRE ATT&CK technique nodes
        for technique in result.cti_techniques:
            if not isinstance(technique, dict):
                continue

            technique_id = technique.get("technique_id", "")
            if not technique_id:
                continue

            mitre_id = f"MITRE_{technique_id}"
            graph.add_node(
                mitre_id,
                node_type="MITRETacticNode",
                technique_id=technique_id,
                technique_name=technique.get("technique_name", ""),
                tactic=technique.get("tactic", ""),
                confidence=technique.get("confidence", 0.0),
            )

            # Add EXHIBITS_PATTERN edge from Website to MITRE technique
            graph.add_edge(website_id, mitre_id, edge_type="EXHIBITS_PATTERN")

    # ================================================================
    # Private: Scoring
    # ================================================================

    def _compute_graph_score(
        self,
        verifications: list[VerificationResult],
        inconsistencies: list[GraphInconsistency],
    ) -> float:
        """
        Compute graph trust score (0-1, higher = more trustworthy).

        Logic:
        - Start at 0.5 (neutral)
        - Each confirmed verification adds up to +0.1
        - Each denied/contradicted verification deducts up to -0.15
        - Each inconsistency deducts based on severity
        """
        score = 0.5

        for v in verifications:
            if v.status == "confirmed":
                score += 0.1 * v.confidence
            elif v.status == "contradicted":
                score -= 0.15 * v.confidence
            elif v.status == "denied":
                score -= 0.12 * v.confidence
            # "unverifiable" doesn't change score

        for inc in inconsistencies:
            severity_penalty = {
                "critical": 0.15,
                "high": 0.10,
                "medium": 0.05,
                "low": 0.02,
            }.get(inc.severity, 0.05)
            score -= severity_penalty * inc.confidence

        return round(max(0.0, min(1.0, score)), 3)

    def _calculate_enhanced_graph_score(self, result: GraphResult, graph: nx.DiGraph) -> float:
        """
        Calculate enhanced graph score incorporating OSINT and CTI signals.

        Uses *evidence-aware dynamic weighting* (Dempster-Shafer principle):
        sources that contribute no information ("vacuous evidence") have
        their weight redistributed proportionally to informative sources.

        Default allocation when ALL sources are informative:
          meta_score  : 40%   (domain age, SSL, WHOIS — always available)
          entity_score: 30%   (cross-referencing claims against the web)
          osint_score : 20%   (multi-source consensus)
          cti_score   : 10%   (threat-intel indicators)

        When a source is vacuous (e.g. all entities "unverifiable"),
        its weight is set to 0 and the surplus is spread to the
        remaining sources in proportion to their original weights.

        Args:
            result: GraphResult with OSINT/CTI data
            graph: Knowledge graph

        Returns:
            Enhanced graph score (0.0 to 1.0)
        """
        # ------ Sub-scores --------------------------------------------------
        meta_score = result.meta_score if result.meta_score else 0.5

        # Entity verification score
        entity_score = 0.5
        entity_is_vacuous = True  # assume vacuous until proven otherwise
        if result.verifications:
            score_sum = 0.0
            has_informative = False
            for v in result.verifications:
                if v.status == "confirmed":
                    score_sum += 0.9 * v.confidence
                    has_informative = True
                elif v.status in ("denied", "contradicted"):
                    score_sum += 0.1 * v.confidence
                    has_informative = True
                else:  # unverifiable → neutral
                    score_sum += 0.5
            entity_score = score_sum / len(result.verifications)
            entity_is_vacuous = not has_informative

        # OSINT consensus score
        osint_score = 0.5
        osint_is_vacuous = True
        if result.osint_consensus:
            status_scores = {
                "confirmed": 0.9,
                "likely": 0.8,
                "possible": 0.6,
                "insufficient": 0.4,
                "conflicted": 0.5,
            }
            consensus_status = result.osint_consensus.get("consensus_status", "")
            osint_score = status_scores.get(consensus_status, 0.5)

            # Invert score if verdict is malicious
            verdict = result.osint_consensus.get("verdict", "")
            if verdict == "malicious":
                osint_score = 1.0 - osint_score
            osint_is_vacuous = consensus_status in ("", "insufficient")

        # CTI threat score
        threat_scores = {
            "critical": 0.0,
            "high": 0.2,
            "medium": 0.4,
            "low": 0.7,
            "none": 1.0,
        }
        cti_score = threat_scores.get(result.threat_level, 1.0)

        # Only blend CTI with OSINT confidence when CTI itself
        # provided the confidence (i.e. CTI actually executed and
        # found meaningful indicators).  If osint_confidence was
        # derived from consensus agreement (Fix 4 fallback), the
        # semantics differ and blending would incorrectly pull the
        # benign CTI score toward 0.5.
        cti_provided_confidence = (
            result.osint_confidence > 0
            and len(result.osint_indicators) > 0
        )
        if cti_provided_confidence:
            cti_score = cti_score * (1 - result.osint_confidence) + 0.5 * result.osint_confidence

        # ------ Dynamic weight redistribution (Dempster-Shafer) ---------------
        # Base weights
        base_weights = {
            "meta":   0.40,
            "entity": 0.30,
            "osint":  0.20,
            "cti":    0.10,
        }
        # Mark vacuous sources
        vacuous = set()
        if entity_is_vacuous:
            vacuous.add("entity")
        if osint_is_vacuous:
            vacuous.add("osint")
        # meta & cti are never vacuous (always produce a score)

        # Redistribute vacuous weight proportionally
        if vacuous:
            informative = {k: v for k, v in base_weights.items() if k not in vacuous}
            surplus = sum(base_weights[k] for k in vacuous)
            total_informative = sum(informative.values())
            if total_informative > 0:
                for k in informative:
                    informative[k] += surplus * (informative[k] / total_informative)
            # Zero out vacuous sources
            weights = {k: (informative.get(k, 0.0)) for k in base_weights}
        else:
            weights = dict(base_weights)

        # ------ Weighted combination -----------------------------------------
        scores = {"meta": meta_score, "entity": entity_score, "osint": osint_score, "cti": cti_score}
        final_score = sum(weights[k] * scores[k] for k in base_weights)

        # Apply inconsistency penalties on top
        for inc in result.inconsistencies:
            penalty = {
                "critical": 0.12,
                "high": 0.08,
                "medium": 0.04,
                "low": 0.02,
            }.get(inc.severity, 0.04)
            final_score -= penalty * inc.confidence

        return max(0.0, min(1.0, final_score))

    def _compute_meta_score(self, intel: DomainIntel) -> float:
        """
        Compute meta trust score from domain intelligence (0-1).

        Factors: domain age, SSL, WHOIS transparency, name servers.
        """
        score = 0.5

        # Domain age (biggest factor)
        if intel.age_days >= 0:
            if intel.age_days > 365 * 3:
                score += 0.25   # 3+ years old
            elif intel.age_days > 365:
                score += 0.15   # 1-3 years
            elif intel.age_days > 90:
                score += 0.05   # 3-12 months
            elif intel.age_days > 30:
                score -= 0.05   # 1-3 months
            elif intel.age_days > 7:
                score -= 0.10   # 1-4 weeks
            else:
                score -= 0.20   # < 1 week

        # SSL
        if intel.ssl_issuer:
            score += 0.10
        else:
            score -= 0.15

        # Privacy protection (slight negative for business sites)
        if intel.is_privacy_protected:
            score -= 0.05

        # Known registrars (positive signal)
        reputable_registrars = ["godaddy", "cloudflare", "namecheap", "google", "aws", "gandi"]
        if any(r in intel.registrar.lower() for r in reputable_registrars):
            score += 0.05

        return round(max(0.0, min(1.0, score)), 3)

    # ================================================================
    # Private: IP Geolocation
    # ================================================================

    async def _ip_geolocation(self, ip: str) -> dict:
        """Resolve IP to geolocation using free ip-api.com."""
        try:
            data = await self._run_blocking(
                self._ip_geolocation_sync,
                timeout_s=max(2, self._dns_timeout_s),
                step=f"ip-geo:{ip}",
                ip=ip,
            )
            if data.get("status") == "success":
                geo = {
                    "country": data.get("country", ""),
                    "city": data.get("city", ""),
                    "isp": data.get("isp", ""),
                    "org": data.get("org", ""),
                    "as": data.get("as", ""),
                }
                logger.info(f"IP geolocation: {ip} → {geo['country']}, {geo['city']} ({geo['org']})")
                return geo
        except TimeoutError:
            logger.debug(f"IP geolocation timed out for {ip}")
        except Exception as e:
            logger.debug(f"IP geolocation failed for {ip}: {e}")
        return {}

    async def _run_with_timeout(self, coro, timeout_s: int, step: str):
        """Run coroutine with explicit timeout to prevent graph-phase stalls."""
        async with asyncio.timeout(timeout_s):
            return await coro

    async def _run_blocking(self, fn, timeout_s: int, step: str, **kwargs):
        """Run blocking I/O in thread with timeout so event loop never blocks."""
        try:
            async with asyncio.timeout(timeout_s):
                return await asyncio.to_thread(fn, **kwargs)
        except TimeoutError:
            raise TimeoutError(f"{step} exceeded {timeout_s}s")

    def _whois_lookup_sync(self, domain: str):
        import whois
        return whois.whois(domain)

    def _dns_lookup_sync(self, domain: str) -> str:
        return socket.gethostbyname(domain)

    def _ssl_issuer_lookup_sync(self, domain: str, ssl_timeout_s: int) -> str:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=ssl_timeout_s) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as tls_sock:
                cert = tls_sock.getpeercert() or {}
                return str(cert.get("issuer", ""))

    def _ip_geolocation_sync(self, ip: str) -> dict:
        import urllib.request

        url = f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as"
        req = urllib.request.Request(url, headers={"User-Agent": "Veritas/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

    # ================================================================
    # Public: Graph Export (for report visualization)
    # ================================================================

    def export_graph_data(self, graph: nx.DiGraph) -> dict:
        """Export graph as a JSON-serializable dict for reporting."""
        if not graph:
            return {"nodes": [], "edges": []}

        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            nodes.append({
                "id": str(node_id),
                "label": str(node_id)[:60],
                **{k: str(v)[:200] for k, v in attrs.items()},
            })

        edges = []
        for src, dst, attrs in graph.edges(data=True):
            edges.append({
                "source": str(src),
                "target": str(dst),
                **{k: str(v)[:200] for k, v in attrs.items()},
            })

        return {"nodes": nodes, "edges": edges}

    # ================================================================
    # Private: Helpers
    # ================================================================

    def _extract_domain(self, url: str) -> str:
        """Extract domain from a URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.hostname or url
        except Exception:
            return url

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from text that may have preamble/postamble."""
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

