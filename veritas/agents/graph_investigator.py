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
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from core.nim_client import NIMClient

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

    @property
    def domain_age_days(self) -> int:
        return self.domain_intel.age_days if self.domain_intel else -1

    @property
    def has_ssl(self) -> bool:
        if self.domain_intel:
            return bool(self.domain_intel.ssl_issuer)
        return False


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

    def __init__(self, nim_client: Optional[NIMClient] = None):
        self._nim = nim_client or NIMClient()
        self._tavily_client = None
        self._search_count = 0

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
    ) -> GraphResult:
        """
        Full graph-based investigation of a URL.

        Args:
            url: Target URL
            page_metadata: Metadata dict from Scout
            page_text: Extracted text content from the page
            external_links: External links found on the page

        Returns:
            GraphResult with knowledge graph, verifications, and scores
        """
        result = GraphResult()
        graph = nx.DiGraph()

        # Extract domain from URL
        domain = self._extract_domain(url)
        logger.info(f"Starting graph investigation for {domain}")

        # -----------------------------------------------------------
        # Phase 1: Domain Intelligence (WHOIS + DNS)
        # -----------------------------------------------------------
        domain_intel = await self._gather_domain_intel(domain)
        result.domain_intel = domain_intel

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

        # -----------------------------------------------------------
        # Phase 2: Entity Extraction
        # -----------------------------------------------------------
        claims = await self._extract_entities(url, page_metadata, page_text)
        result.claims_extracted = claims

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
        # Phase 3: Entity Verification via Tavily
        # -----------------------------------------------------------
        verifications = await self._verify_entities(claims, domain)
        result.verifications = verifications

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
        # Phase 4: External Link Analysis
        # -----------------------------------------------------------
        if external_links:
            for ext_url in external_links[:10]:  # Limit to avoid graph bloat
                ext_domain = self._extract_domain(ext_url)
                if ext_domain and ext_domain != domain:
                    ext_id = f"site:{ext_domain}"
                    if ext_id not in graph:
                        graph.add_node(ext_id, node_type="WebsiteNode", domain=ext_domain)
                    graph.add_edge(url, ext_id, edge_type="LINKS_TO", link_type="outbound")

        # -----------------------------------------------------------
        # Phase 4b: MetaAnalyzer (MX/SPF/DMARC, deep SSL)
        # -----------------------------------------------------------
        try:
            from analysis.meta_analyzer import MetaAnalyzer
            meta_az = MetaAnalyzer()
            meta_result = await meta_az.analyze(domain)
            result.meta_analysis = meta_az.to_dict(meta_result)
            logger.info(
                f"MetaAnalyzer: score={meta_result.meta_score:.2f}, "
                f"signals={len(meta_result.risk_signals)}, "
                f"MX={len(meta_result.dns_info.mx_records)}, "
                f"SPF={meta_result.dns_info.has_spf}, "
                f"DMARC={meta_result.dns_info.has_dmarc}"
            )
        except Exception as e:
            logger.warning(f"MetaAnalyzer failed (non-critical): {e}")

        # -----------------------------------------------------------
        # Phase 4c: IP Geolocation
        # -----------------------------------------------------------
        if domain_intel.ip_address:
            geo = await self._ip_geolocation(domain_intel.ip_address)
            result.ip_geolocation = geo
            if geo.get("country"):
                domain_intel.ip_country = geo["country"]
                graph.nodes[url]["ip_country"] = geo["country"]

        # -----------------------------------------------------------
        # Phase 5: Inconsistency Detection
        # -----------------------------------------------------------
        inconsistencies = self._detect_inconsistencies(
            domain_intel, verifications, claims, site_type,
            form_validation=form_validation, ip_geo=result.ip_geolocation,
        )
        result.inconsistencies = inconsistencies

        # -----------------------------------------------------------
        # Phase 6: Compute Scores
        # -----------------------------------------------------------
        result.graph = graph
        result.graph_node_count = graph.number_of_nodes()
        result.graph_edge_count = graph.number_of_edges()
        result.graph_score = self._compute_graph_score(verifications, inconsistencies)
        result.meta_score = self._compute_meta_score(domain_intel)
        result.tavily_searches = self._search_count

        logger.info(
            f"Graph investigation complete for {domain} | "
            f"claims={len(claims)} | verifications={len(verifications)} | "
            f"inconsistencies={len(inconsistencies)} | "
            f"graph_score={result.graph_score:.2f} | meta_score={result.meta_score:.2f} | "
            f"nodes={result.graph_node_count} | edges={result.graph_edge_count}"
        )

        return result

    # ================================================================
    # Private: Domain Intelligence
    # ================================================================

    async def _gather_domain_intel(self, domain: str) -> DomainIntel:
        """Gather WHOIS + DNS intelligence about the domain."""
        intel = DomainIntel(domain=domain)

        # WHOIS lookup
        try:
            import whois
            w = whois.whois(domain)

            intel.registrar = str(w.registrar or "")
            intel.registrant_org = str(w.org or "")
            intel.registrant_country = str(w.country or "")
            intel.raw_whois = str(w.text or "")[:2000]

            # Parse creation date
            if w.creation_date:
                cd = w.creation_date
                if isinstance(cd, list):
                    cd = cd[0]
                if isinstance(cd, datetime):
                    intel.creation_date = cd
                    intel.age_days = (datetime.now(timezone.utc) - cd.replace(tzinfo=timezone.utc)).days

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

            # Privacy protection detection
            privacy_keywords = ["privacy", "proxy", "redacted", "whoisguard", "domains by proxy"]
            whois_text_lower = intel.raw_whois.lower()
            intel.is_privacy_protected = any(kw in whois_text_lower for kw in privacy_keywords)

        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {domain}: {e}")
            intel.errors.append(f"WHOIS failed: {str(e)}")

        # DNS lookup
        try:
            intel.ip_address = socket.gethostbyname(domain)
        except socket.gaierror as e:
            logger.warning(f"DNS lookup failed for {domain}: {e}")
            intel.errors.append(f"DNS failed: {str(e)}")

        # SSL check
        try:
            import ssl
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.settimeout(5)
                s.connect((domain, 443))
                cert = s.getpeercert()
                intel.ssl_issuer = str(cert.get("issuer", ""))
        except Exception:
            pass  # No SSL or unreachable — will be reflected in scoring

        return intel

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

        return claims

    async def _llm_extract_entities(
        self, url: str, text: str,
    ) -> list[EntityClaim]:
        """Use NIM LLM to extract verifiable entities from page text."""
        prompt = (
            "Extract all verifiable real-world entities from this website text. "
            "Focus on: company names, person names (CEO, founder, team), "
            "physical addresses, phone numbers, email addresses, founding dates, "
            "partnership claims, award claims, and certification claims.\n\n"
            "Respond ONLY in JSON:\n"
            '{"entities": [\n'
            '  {"type": "company|person|address|phone|email|founding_date|partnership|award|certification",\n'
            '   "value": "the exact claimed value",\n'
            '   "context": "brief surrounding context"}\n'
            "]}\n\n"
            f"Website text:\n{text}"
        )

        result = await self._nim.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are an entity extraction specialist. Extract only verifiable "
                "real-world claims. Do not extract generic terms or obvious truths. "
                "Focus on claims that can be cross-referenced against external databases."
            ),
            max_tokens=1024,
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

        for claim in to_verify:
            verification = await self._verify_single_claim(claim, domain)
            verifications.append(verification)

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

                response = await self._tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=3,
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

        # Fallback: custom Playwright-based DuckDuckGo scraper
        try:
            from core.web_searcher import web_search
            return await web_search(query=query, max_results=3, follow_links=True)
        except Exception as e:
            logger.warning(f"Custom web search also failed: {e}")
            return []

    async def _llm_verify(
        self, claim: EntityClaim, search_results: list[dict], domain: str,
    ) -> VerificationResult:
        """Use NIM LLM to interpret search results against a claim."""
        results_text = "\n".join(
            f"- [{r['title']}]({r['url']}): {r['content']}"
            for r in search_results
        )

        prompt = (
            f"The website {domain} claims: {claim.entity_type} = \"{claim.entity_value}\"\n"
            f"Context: {claim.context}\n\n"
            f"Search results about this claim:\n{results_text}\n\n"
            "Does the evidence CONFIRM, DENY, CONTRADICT, or is the claim UNVERIFIABLE "
            "based on these search results?\n\n"
            "Respond in JSON:\n"
            '{"status": "confirmed|denied|contradicted|unverifiable",\n'
            ' "confidence": 0.8,\n'
            ' "explanation": "brief explanation of your reasoning"}'
        )

        result = await self._nim.generate_text(
            prompt=prompt,
            system_prompt=(
                "You are a senior OSINT analyst conducting forensic verification. "
                "Compare the website's claim against the search evidence with extreme rigour. "
                "Check for: exact name matches (not partial), date consistency, address plausibility, "
                "known scam patterns, and source credibility (prefer official registries, LinkedIn, "
                "government databases over random blogs). "
                "Be conservative: if the evidence is ambiguous say 'unverifiable'. "
                "Only say 'confirmed' if the evidence clearly supports the claim from a credible source. "
                "Say 'contradicted' if the evidence directly conflicts."
            ),
            max_tokens=256,
            temperature=0.0,
        )

        try:
            data = self._extract_json(result.get("response", ""))
            if data:
                return VerificationResult(
                    claim=claim,
                    status=data.get("status", "unverifiable"),
                    evidence_source="Web Search + NIM LLM",
                    evidence_detail=data.get("explanation", ""),
                    confidence=float(data.get("confidence", 0.5)),
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
            import urllib.request
            url = f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as"
            req = urllib.request.Request(url, headers={"User-Agent": "Veritas/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
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
        except Exception as e:
            logger.debug(f"IP geolocation failed for {ip}: {e}")
        return {}

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
