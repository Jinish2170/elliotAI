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

def derive_metrics_from_findings(**kwargs) -> CvssV31Metrics:
    """Map observed findings to a CVSS v3.1 metric set (see derive_metrics_with_reasons)."""
    return derive_metrics_with_reasons(**kwargs)[0]


def derive_metrics_with_reasons(
    *,
    dark_patterns: Optional[list[Any]] = None,
    has_ssl: bool = True,
    phishing_flag: bool = False,
    credential_capture: bool = False,
    malware_distribution: bool = False,
    js_obfuscation: bool = False,
    js_risk_score: float = 0.0,
    domain_abuse: bool = False,
) -> tuple[CvssV31Metrics, dict[str, list[str]]]:
    """Map observed findings to CVSS v3.1 metrics AND the evidence behind each one.

    Defaults assume a typical web target: Network attack vector, no privileges
    required, user interaction required (click), unchanged scope. Impact
    metrics escalate based on what was actually observed.

    The function picks the **worst applicable** impact across findings: CVSS
    represents a single vulnerability, but we conflate the audit into one
    summary score, so we take the upper envelope rather than averaging.

    Returns (metrics, reasons) where reasons[abbr] lists plain-English evidence.
    """
    dark_patterns = dark_patterns or []
    why: dict[str, list[str]] = {k: [] for k in ("AV", "AC", "PR", "UI", "S", "C", "I", "A")}

    AV = "N"
    why["AV"].append("Every website can be reached over the internet by anyone.")
    AC = "L"
    why["AC"].append("Nothing special is needed: loading the page is enough.")
    PR = "N"
    why["PR"].append("No login is needed to visit the site.")
    UI = "R" if not (malware_distribution and js_obfuscation) else "N"
    if UI == "R":
        why["UI"].append("Harm usually needs the visitor to click, type or submit something.")
    else:
        why["UI"].append("Malware + obfuscated code found: harm can happen just by opening the page.")

    if not has_ssl and not (credential_capture or phishing_flag):
        AC = "H"
        why["AC"] = ["No valid HTTPS: an attacker must sit between you and the site to abuse it."]

    S = "C" if (malware_distribution or credential_capture) else "U"
    if S == "C":
        why["S"].append("Credential capture or malware can reach beyond this site (your other accounts, your device).")
    else:
        why["S"].append("No sign that harm spreads beyond this site.")

    C, I, A = "N", "N", "N"

    if phishing_flag or credential_capture:
        C = _max_cia(C, "H")
        I = _max_cia(I, "L")
        why["C"].append("Phishing / credential-capture signal: private data could be stolen.")
        why["I"].append("Stolen credentials let an attacker act as the user.")
    if malware_distribution:
        C = _max_cia(C, "H"); I = _max_cia(I, "H"); A = _max_cia(A, "L")
        why["C"].append("Malware-distribution signal: files and data could be read.")
        why["I"].append("Malware-distribution signal: files and settings could be changed.")
        why["A"].append("Malware-distribution signal: the device could be disrupted.")
    if js_obfuscation or js_risk_score > 70:
        C = _max_cia(C, "L"); I = _max_cia(I, "L")
        why["C"].append(f"Suspicious or hidden JavaScript (risk score {js_risk_score:.0f}) can read page data.")
        why["I"].append("Suspicious or hidden JavaScript can alter what you see.")
    if not has_ssl:
        C = _max_cia(C, "L")
        why["C"].append("No valid HTTPS: data you send can be intercepted in transit.")
    if dark_patterns:
        I = _max_cia(I, "L")
        why["I"].append(f"{len(dark_patterns)} manipulative design pattern(s) detected: they can trick users into decisions they would not otherwise make.")
    if domain_abuse:
        I = _max_cia(I, "L")
        why["I"].append("Threat-intelligence sources flagged the domain or its network.")

    for k, label in (("C", "No sign of private data being exposed."), ("I", "No sign that content or decisions are being tampered with."),
                     ("A", "No sign the site or your device could be disrupted.")):
        if not why[k]:
            why[k].append(label)

    return CvssV31Metrics(AV=AV, AC=AC, PR=PR, UI=UI, S=S, C=C, I=I, A=A), why


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
    metrics, why = derive_metrics_with_reasons(
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
    vector = metrics.vector()
    return {
        "base_score": base_score,
        "severity": severity_band(base_score),
        "vector_string": vector,
        "calculator_url": f"https://www.first.org/cvss/calculator/3.1#{vector}",
        "metrics_detail": explain_metrics(metrics, why),
        **metrics.as_full_names(),
    }


# Plain-English presentation of each metric: (full name, short label, question, level fn)
_METRIC_UI = {
    "AV": ("attack_vector", "Reach", "Where can an attacker come from?", {"N": 4, "A": 3, "L": 2, "P": 1}),
    "AC": ("attack_complexity", "Ease", "How hard is it to abuse?", {"L": 4, "H": 1}),
    "PR": ("privileges_required", "Access", "Does the attacker need an account?", {"N": 4, "L": 2, "H": 1}),
    "UI": ("user_interaction", "Click needed", "Must the visitor do something?", {"N": 4, "R": 1}),
    "S": ("scope", "Spread", "Can harm spread beyond this site?", {"U": 1, "C": 4}),
    "C": ("confidentiality", "Data theft", "Could private data be exposed?", {"N": 0, "L": 2, "H": 4}),
    "I": ("integrity", "Tampering", "Could content or decisions be manipulated?", {"N": 0, "L": 2, "H": 4}),
    "A": ("availability", "Disruption", "Could service or device be disrupted?", {"N": 0, "L": 2, "H": 4}),
}


def explain_metrics(m: CvssV31Metrics, why: dict[str, list[str]]) -> list[dict[str, Any]]:
    """One row per CVSS metric: plain question, answer, 0-4 radar level, and the evidence."""
    full = m.as_full_names()
    out = []
    for abbr, (name, label, question, levels) in _METRIC_UI.items():
        letter = getattr(m, abbr)
        out.append({
            "name": name, "abbr": abbr, "label": label, "question": question,
            "value": full[name], "level": levels[letter], "why": " ".join(why.get(abbr, [])),
        })
    return out
