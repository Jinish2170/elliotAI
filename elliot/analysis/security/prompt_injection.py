"""
Prompt-injection detection module (FAST tier, deterministic).

A legitimate website has no reason to address AI auditors. Text that tries to
instruct AI systems (in comments, meta tags, hidden elements or visible copy) is
reported as a HIGH-severity finding; the Judge turns it into a trust-score cap.
"""

from typing import List, Optional

from elliot.analysis.security.base import SecurityFinding, SecurityModule, SecurityTier
from elliot.core.injection import detect_injection

_CHANNEL_RISK = {"hidden": 0.95, "comment": 0.9, "meta": 0.9, "attribute": 0.85,
                 "title": 0.85, "visible": 0.75}


class PromptInjectionAnalyzer(SecurityModule):
    _default_timeout: int = 5
    _default_tier: SecurityTier = SecurityTier.FAST

    @property
    def category_id(self) -> str:
        return "prompt_injection"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        hits = detect_injection(page_content or "")
        return [
            SecurityFinding(
                category_id=self.category_id,
                pattern_type=f"ai_injection_{h.channel}",
                severity="high",
                confidence=_CHANNEL_RISK.get(h.channel, 0.75),
                description=f"Text addressed to AI systems found in {h.channel} content ({h.pattern})",
                evidence=h.excerpt,
                cwe_id="CWE-77",
                recommendation="Treat as a manipulation attempt: legitimate sites do not instruct AI auditors.",
            )
            for h in hits
        ]
