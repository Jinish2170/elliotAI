"""CVSS v3.1 base score calculator + finding-driven metric derivation.

Replaces the prior reverse-engineered scoring (cvss_score hardcoded from
risk_level bucket, preset metrics ignored) with:

1. A spec-compliant CVSS v3.1 base score formula. See FIRST.org Specification
   Document, Section 7.1 (Base Metrics):
   https://www.first.org/cvss/v3.1/specification-document

2. A finding-driven metric derivation that inspects the actual evidence
   (dark patterns, SSL status, JS risk, phishing flags, credential capture
   indicators) and produces metrics that reflect what was observed, rather
   than guessing from a coarse risk bucket.

3. A vector string builder that emits the canonical CVSS:3.1/... form
   downstream tools (SIEMs, ticketing systems, scanners) actually understand.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Metric value tables (CVSS v3.1 base, FIRST.org Table 14).
# ---------------------------------------------------------------------------

_AV_VALUES = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
_AC_VALUES = {"L": 0.77, "H": 0.44}
_UI_VALUES = {"N": 0.85, "R": 0.62}
# PR values depend on Scope.
_PR_VALUES_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PR_VALUES_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.50}
# Impact sub-metrics (Confidentiality / Integrity / Availability).
_IMPACT_CIA_VALUES = {"N": 0.0, "L": 0.22, "H": 0.56}


@dataclass(frozen=True)
class CvssV31Metrics:
    """The eight base metrics required for a CVSS v3.1 base score.

    All fields use the single-character CVSS abbreviations.

    AV: Attack Vector             — N | A | L | P
    AC: Attack Complexity         — L | H
    PR: Privileges Required       — N | L | H
    UI: User Interaction          — N | R
    S:  Scope                     — U | C
    C:  Confidentiality Impact    — N | L | H
    I:  Integrity Impact          — N | L | H
    A:  Availability Impact       — N | L | H
    """
    AV: str
    AC: str
    PR: str
    UI: str
    S: str
    C: str
    I: str
    A: str

    def vector(self) -> str:
        """Canonical CVSS v3.1 vector string."""
        return (
            "CVSS:3.1/"
            f"AV:{self.AV}/AC:{self.AC}/PR:{self.PR}/UI:{self.UI}/"
            f"S:{self.S}/C:{self.C}/I:{self.I}/A:{self.A}"
        )

    def as_full_names(self) -> dict[str, str]:
        """Long-form metric names (for UI display / JSON consumers)."""
        return {
            "attack_vector": _AV_NAMES[self.AV],
            "attack_complexity": _AC_NAMES[self.AC],
            "privileges_required": _PR_NAMES[self.PR],
            "user_interaction": _UI_NAMES[self.UI],
            "scope": _S_NAMES[self.S],
            "confidentiality": _CIA_NAMES[self.C],
            "integrity": _CIA_NAMES[self.I],
            "availability": _CIA_NAMES[self.A],
        }


_AV_NAMES = {"N": "Network", "A": "Adjacent", "L": "Local", "P": "Physical"}
_AC_NAMES = {"L": "Low", "H": "High"}
_PR_NAMES = {"N": "None", "L": "Low", "H": "High"}
_UI_NAMES = {"N": "None", "R": "Required"}
_S_NAMES = {"U": "Unchanged", "C": "Changed"}
_CIA_NAMES = {"N": "None", "L": "Low", "H": "High"}


def _roundup(value: float) -> float:
    """CVSS roundUp1 function: round up to the nearest 0.1.

    Per spec, this is NOT the same as Python's round(). E.g.
    roundUp1(4.02) = 4.1; roundUp1(4.00) = 4.0.
    """
    int_input = int(round(value * 100_000))
    if int_input % 10_000 == 0:
        return int_input / 100_000
    return (math.floor(int_input / 10_000) + 1) / 10.0


def compute_base_score(m: CvssV31Metrics) -> float:
    """Compute the CVSS v3.1 base score for the given metrics.

    Returns 0.0 when the impact sub-score is non-positive (i.e. no observable
    impact on confidentiality, integrity, or availability).
    """
    if m.S not in ("U", "C"):
        raise ValueError(f"Invalid Scope: {m.S!r}")
    c = _IMPACT_CIA_VALUES[m.C]
    i = _IMPACT_CIA_VALUES[m.I]
    a = _IMPACT_CIA_VALUES[m.A]
    iss = 1.0 - ((1.0 - c) * (1.0 - i) * (1.0 - a))

    if m.S == "U":
        impact = 6.42 * iss
    else:  # Scope Changed
        impact = 7.52 * (iss - 0.029) - 3.25 * pow(iss - 0.02, 15)

    if impact <= 0:
        return 0.0

    pr_table = _PR_VALUES_UNCHANGED if m.S == "U" else _PR_VALUES_CHANGED
    exploitability = 8.22 * _AV_VALUES[m.AV] * _AC_VALUES[m.AC] * pr_table[m.PR] * _UI_VALUES[m.UI]

    base = (impact + exploitability) if m.S == "U" else (1.08 * (impact + exploitability))
    return _roundup(min(base, 10.0))


def severity_band(base_score: float) -> str:
    """CVSS v3.1 qualitative severity band (Table 17)."""
    if base_score == 0.0:
        return "None"
    if base_score < 4.0:
        return "Low"
    if base_score < 7.0:
        return "Medium"
    if base_score < 9.0:
        return "High"
    return "Critical"


# ---------------------------------------------------------------------------
# Finding-driven metric derivation.
# ---------------------------------------------------------------------------
#
# Web auditing produces a fairly narrow class of "findings" compared to
# traditional CVE-style vulnerabilities. The mapping below is intentionally
# explicit so reviewers can see why a particular site ended up at a particular
# CVSS vector — no magic numbers, no risk-level back-projection.

def derive_metrics_from_findings(
    *,
    dark_patterns: Optional[list[Any]] = None,
    has_ssl: bool = True,
    phishing_flag: bool = False,
    credential_capture: bool = False,
    malware_distribution: bool = False,
    js_obfuscation: bool = False,
    js_risk_score: float = 0.0,
    domain_abuse: bool = False,
) -> CvssV31Metrics:
    """Map observed findings to a CVSS v3.1 metric set.

    Defaults assume a typical web target: Network attack vector, no privileges
    required, user interaction required (click), unchanged scope. Impact
    metrics escalate based on what was actually observed.

    The function picks the **worst applicable** impact across findings — CVSS
    represents a single vulnerability, but we conflate the audit into one
    summary score, so we take the upper envelope rather than averaging.
    """
    dark_patterns = dark_patterns or []

    # --- Attack vector / complexity / privileges / interaction ------------
    # Web-fronted: nearly always reachable over the network.
    AV = "N"
    # Most findings require no special conditions — page load is enough.
    AC = "L"
    # Anonymous / unauthenticated.
    PR = "N"
    # Most fraud requires the user to click / submit. Drive-by malware shifts
    # this to None.
    UI = "R" if not (malware_distribution and js_obfuscation) else "N"

    # MITM-style findings (missing SSL) require the attacker to be in path,
    # which raises complexity.
    if not has_ssl and not (credential_capture or phishing_flag):
        AC = "H"

    # --- Scope --------------------------------------------------------------
    # Drive-by exploits / credential reuse that pivot to other accounts change
    # scope; pure on-site fraud doesn't.
    S = "C" if (malware_distribution or credential_capture) else "U"

    # --- Impact (worst applicable across findings) --------------------------
    # Defaults to no impact; we raise as evidence accumulates.
    C, I, A = "N", "N", "N"

    if phishing_flag or credential_capture:
        # Stealing credentials breaches confidentiality fully; the attacker
        # can also impersonate the user (integrity).
        C = _max_cia(C, "H")
        I = _max_cia(I, "L")

    if malware_distribution:
        # Drive-by payload can read, modify, and brick the host.
        C = _max_cia(C, "H")
        I = _max_cia(I, "H")
        A = _max_cia(A, "L")

    if js_obfuscation or js_risk_score > 70:
        # Obfuscated/malicious JS at minimum reads sensitive page state.
        C = _max_cia(C, "L")
        I = _max_cia(I, "L")

    if not has_ssl:
        # In-transit eavesdropping risk for any data the user submits.
        C = _max_cia(C, "L")

    if dark_patterns:
        # Manipulation findings indicate integrity-of-decision impact.
        # Only escalate from None to Low; dark patterns alone aren't High.
        I = _max_cia(I, "L")

    if domain_abuse:
        # Reputational/abuse signal — modest integrity impact.
        I = _max_cia(I, "L")

    return CvssV31Metrics(AV=AV, AC=AC, PR=PR, UI=UI, S=S, C=C, I=I, A=A)


def _max_cia(current: str, candidate: str) -> str:
    """Return whichever of {N,L,H} carries more impact."""
    order = {"N": 0, "L": 1, "H": 2}
    return candidate if order[candidate] > order[current] else current


def build_cvss_report(
    *,
    dark_patterns: Optional[list[Any]] = None,
    has_ssl: bool = True,
    phishing_flag: bool = False,
    credential_capture: bool = False,
    malware_distribution: bool = False,
    js_obfuscation: bool = False,
    js_risk_score: float = 0.0,
    domain_abuse: bool = False,
) -> dict[str, Any]:
    """One-shot helper: derive metrics, compute score, build the dict the
    Judge embeds in the verdict.

    Returns:
        Dict with `base_score`, `severity`, `vector_string`, plus full-name
        metric fields (`attack_vector`, `attack_complexity`, ...) so existing
        UI consumers that read named fields don't break.
    """
    metrics = derive_metrics_from_findings(
        dark_patterns=dark_patterns,
        has_ssl=has_ssl,
        phishing_flag=phishing_flag,
        credential_capture=credential_capture,
        malware_distribution=malware_distribution,
        js_obfuscation=js_obfuscation,
        js_risk_score=js_risk_score,
        domain_abuse=domain_abuse,
    )
    base_score = compute_base_score(metrics)
    return {
        "base_score": base_score,
        "severity": severity_band(base_score),
        "vector_string": metrics.vector(),
        **metrics.as_full_names(),
    }
