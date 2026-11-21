"""Regression: one non-conforming module silently failed the whole MEDIUM tier
(GDPR, PCI-DSS, social engineering, darknet never ran in production)."""
import pytest

from elliot.analysis.security.base import SecurityModule, SecurityTier
from elliot.analysis.security.utils import execute_tier


def _discovered():
    from elliot.analysis.security.utils import get_all_security_modules
    return get_all_security_modules()


def test_every_discovered_module_is_instantiable():
    mods = _discovered()
    assert len(mods) >= 7
    for m in mods:
        inst = m()  # raised TypeError for SocialEngineeringAnalyzer before the fix
        assert isinstance(inst.category_id, str) and inst.category_id


@pytest.mark.asyncio
async def test_broken_module_does_not_take_down_its_tier():
    class Broken(SecurityModule):  # abstract method missing → cannot instantiate
        _default_tier = SecurityTier.MEDIUM

        async def analyze(self, url, page_content=None, headers=None, dom_meta=None):
            return []

    from elliot.analysis.security.social_engineering import SocialEngineeringAnalyzer

    findings = await execute_tier([Broken, SocialEngineeringAnalyzer], "https://x.example",
                                  page_content="Hurry up! Only 2 left. Mail rahul.sharma@x.example")
    types = {f.pattern_type for f in findings}
    assert {"manipulative_urgency", "pii_email_exposure"} <= types
