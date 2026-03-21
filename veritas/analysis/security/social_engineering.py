"""
Social Engineering & OSINT Analysis Module

Deep OSINT and Social Engineering module for Veritas.
Detects:
- Manipulative urgency ("Only 1 left in stock!", "Expires in 5 minutes")
- Employee PII Leakage (Exposed emails, phone numbers)
- Deceptive baiting strings
- Spear-phishing and credential harvesting indicators
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Optional, Dict, Any, List

from veritas.analysis import ModuleInfo
from veritas.analysis.security.base import SecurityModule, SecurityTier, SecurityFinding as ModuleSecurityFinding
from veritas.core.types import SecurityFinding as CoreSecurityFinding, Severity

logger = logging.getLogger("veritas.analysis.security.social_engineering")

@dataclass
class SocialEngineeringResult:
    has_urgency_manipulation: bool = False
    has_pii_leakage: bool = False
    has_baiting: bool = False
    exposed_emails: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

class SocialEngineeringAnalyzer(SecurityModule):
    """
    Analyzes site for Social Engineering and Deep OSINT vulnerabilities.
    """
    
    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            id="social_engineering",
            name="Social Engineering & OSINT",
            description="Deep analysis for social engineering vectors, manipulative copy, and PII leakage",
            tier=SecurityTier.MEDIUM,
            cwe_mappings=[],
            mitre_mappings=["T1566"] # Phishing
        )

    async def analyze(
        self,
        url: str,
        scout_result: Optional[dict] = None,
        vision_result: Optional[dict] = None,
        graph_result: Optional[dict] = None,
        **kwargs: Any,
    ) -> ModuleSecurityFinding:
        """
        Run social engineering and deep OSINT checks.
        """
        logger.info(f"[{self.info.id}] Starting social engineering OSINT scan for {url}")
        
        result = SocialEngineeringResult()
        findings = []
        score = 100.0
        
        page_content = ""
        if scout_result:
            page_content = scout_result.get("page_content", "").lower()
            if not page_content:
                # Try getting it from metadata
                meta = scout_result.get("page_metadata", {})
                if isinstance(meta, dict):
                    page_content = meta.get("page_text", "").lower()
                    
        # 1. PII/Employee Leakage (Email Regex)
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = re.findall(email_pattern, page_content)
        unique_emails = list(set([e for e in emails if not e.startswith('no-reply') and not e.startswith('support')]))
        
        if unique_emails:
            result.has_pii_leakage = True
            result.exposed_emails = unique_emails
            
            # Rate limit the display list
            display_emails = unique_emails[:3]
            findings.append(f"PII Leakage: Found {len(unique_emails)} potentially exposed employee email(s) (e.g., {', '.join(display_emails)}). This increases spear-phishing risk.")
            score -= 15.0
            
        # 2. Tech Support Scam / Deceptive Customer Service Strings
        scam_patterns = [
            r"call toll free now",
            r"windows defender security center",
            r"your computer may be infected",
            r"system has been infected",
            r"do not shut down or restart your computer"
        ]
        scam_hits = [p for p in scam_patterns if re.search(p, page_content)]
        if scam_hits:
            result.has_baiting = True
            findings.append(f"Tech Support Scam Indicators: Highly suspicious phrases commonly used in tech-support scams detected.")
            score -= 40.0
            
        # 3. Manipulative Urgency
        urgency_patterns = [
            r"only \d+ left",
            r"expires in \d+",
            r"offer ends soon",
            r"don't miss out",
            r"act fast",
            r"hurry up"
        ]
        
        urgency_hits = [p for p in urgency_patterns if re.search(p, page_content)]
        if urgency_hits:
            result.has_urgency_manipulation = True
            findings.append(f"Manipulative Copy: Found artificial urgency indicators capable of exploiting human psychology ({len(urgency_hits)} patterns matched).")
            score -= 20.0
            
        # 3. Baiting & Credential Harvesting flags
        baiting_patterns = [
            r"claim your prize",
            r"you have been selected",
            r"winner",
            r"free gift",
            r"verify your account now"
        ]
        baiting_hits = [p for p in baiting_patterns if re.search(p, page_content)]
        if baiting_hits:
            result.has_baiting = True
            findings.append(f"Baiting Vectors: Language consistent with phishing or baiting was detected.")
            score -= 25.0

        score = max(0.0, score)
        result.confidence_score = (100.0 - score) / 100.0
        
        if score < 100.0:
            result.recommendations.append("Obfuscate employee contact details to prevent scraping and targeted spear-phishing.")
            result.recommendations.append("Ensure marketing copy complies with FTC regulations regarding transparent pricing and actual inventory.")

        is_passed = score > 70.0
        
        return ModuleSecurityFinding(
            module_id=self.info.id,
            passed=is_passed,
            score=score,
            findings=findings,
            severity=Severity.HIGH if score < 60 else (Severity.MEDIUM if score < 90 else Severity.LOW),
            details=result.to_dict(),
            remediation="\n".join(result.recommendations) if result.recommendations else None
        )