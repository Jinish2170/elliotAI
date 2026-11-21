"""
Social Engineering analysis module (MEDIUM tier).

Detects in page text:
- Employee PII exposure (email addresses → spear-phishing risk)
- Tech-support scam phrases
- Manipulative urgency copy
- Baiting / credential-harvesting language

Implements the SecurityModule contract (category_id + analyze(url, page_content,
headers, dom_meta) -> List[SecurityFinding]). The previous version targeted an
older interface, could not be instantiated, and its failure took the whole
MEDIUM tier (GDPR, PCI-DSS, …) down with it.
"""

import logging
import re
from typing import List, Optional

from elliot.analysis.security.base import SecurityFinding, SecurityModule, SecurityTier

logger = logging.getLogger("elliot.analysis.security.social_engineering")

_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_TAGS = re.compile(r"<[^>]+>")
_GENERIC_MAILBOXES = ("no-reply", "noreply", "support", "info", "contact", "hello", "sales")

_RULES = [
    # (pattern_type, severity, confidence, description, patterns)
    ("tech_support_scam", "high", 0.85,
     "Phrases typical of tech-support scams", [
         r"call toll free now", r"windows defender security center",
         r"your computer (?:may be|has been|is) infected", r"system has been infected",
         r"do not (?:shut down|restart) your computer"]),
    ("baiting_language", "high", 0.75,
     "Baiting / credential-harvesting language", [
         r"claim your prize", r"you have been selected", r"verify your account now",
         r"\bfree gift\b", r"congratulations,? you(?:'ve| have) won"]),
    ("manipulative_urgency", "medium", 0.6,
     "Artificial urgency copy", [
         r"only \d+ left", r"expires in \d+", r"offer ends soon", r"don't miss out",
         r"\bact fast\b", r"\bhurry up\b"]),
]


class SocialEngineeringAnalyzer(SecurityModule):
    _default_timeout: int = 10
    _default_tier: SecurityTier = SecurityTier.MEDIUM

    @property
    def category_id(self) -> str:
        return "social_engineering"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        text = _TAGS.sub(" ", page_content or "").lower()
        if not text.strip():
            return []
        findings: List[SecurityFinding] = []

        personal = sorted({e for e in _EMAIL.findall(text)
                           if not e.split("@")[0].startswith(_GENERIC_MAILBOXES)
                           and not e.endswith((".png", ".jpg", ".svg", ".webp"))})
        if personal:
            findings.append(SecurityFinding(
                category_id=self.category_id, pattern_type="pii_email_exposure",
                severity="low", confidence=0.6,
                description=f"{len(personal)} personal email address(es) exposed in page text",
                evidence=", ".join(personal[:3]),
                cwe_id="CWE-200",
                recommendation="Use role mailboxes or contact forms instead of personal addresses.",
            ))

        for ptype, sev, conf, desc, patterns in _RULES:
            hits = [p for p in patterns if re.search(p, text)]
            if hits:
                findings.append(SecurityFinding(
                    category_id=self.category_id, pattern_type=ptype, severity=sev,
                    confidence=conf, description=desc,
                    evidence=f"{len(hits)} pattern(s) matched",
                    recommendation="Remove deceptive or pressuring copy.",
                ))
        return findings
