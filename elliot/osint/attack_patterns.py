"""MITRE ATT&CK framework mapping for cyber threat intelligence.

Provides technique mapping, attribution suggestions, and standardized
threat classification using the MITRE ATT&CK framework.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from .ioc_detector import Indicator


# Phrases that, when they appear within a small window around a positive marker,
# flip its meaning from "attack technique present" to "defensive content about
# the technique." Without this, a security vendor's page describing how it
# blocks phishing matches the spearphishing technique with high confidence.
#
# The window covers ~40 characters on either side of the marker. Anything in
# that window from this list suppresses the match.
_NEGATION_PHRASES: tuple[str, ...] = (
    "anti-", "anti ", "protection", "protect", "protected", "protections",
    "prevention", "prevent", "preventing", "prevents",
    "awareness", "training", "educate", "education",
    "report", "reporting", "reports",
    "block", "blocks", "blocked", "blocking",
    "defense", "defenses", "defend", "defends", "defending",
    "detection", "detect", "detects", "detected", "detecting",
    "filter", "filters", "filtering", "filtered",
    "secure from", "safe from", "guard against", "guards against",
    "stops", "stop ", "stop.",
    "monitor", "monitors", "monitoring", "monitored",
    "alert about", "alerted about", "alerting on",
    "fight against", "fighting against",
    "avoid", "avoids", "avoiding",
    "how to spot", "how to identify", "how to recognize",
    "tips to", "guide to avoiding",
    "free from", "without ",
)

# Minimum distinct positive markers required to surface a technique, regardless
# of the ratio. Prevents a single keyword from triggering a high-stakes label.
_MIN_DISTINCT_MARKERS: int = 2

# Confidence cutoff (kept identical to the previous behavior so downstream
# consumers don't shift sensitivity unexpectedly).
_CONFIDENCE_CUTOFF: float = 0.3

# Half-width of the context window scanned for negation phrases.
_CONTEXT_HALF_WIDTH: int = 40


def _marker_pattern(marker: str) -> re.Pattern:
    """Build a regex that matches a marker with sensible boundaries.

    - Word-character markers ("phishing", "rce") get full \\b...\\b boundaries
      so "rce" doesn't fire inside "force" and "trojan" doesn't fire inside
      "Trojan University".
    - Markers containing non-word characters (".bat", "cve-", "file.exe") use
      a left word boundary plus literal escape — preserves "cve-" matching
      "cve-2024-..." while still rejecting "device".
    """
    escaped = re.escape(marker.lower())
    if re.fullmatch(r"\w[\w\s]*\w|\w", marker.lower()):
        return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)
    return re.compile(r"(?<!\w)" + escaped, re.IGNORECASE)


def _has_negation_in_window(text: str, span_start: int, span_end: int) -> bool:
    """True iff any negation phrase appears within the marker's local context."""
    lo = max(0, span_start - _CONTEXT_HALF_WIDTH)
    hi = min(len(text), span_end + _CONTEXT_HALF_WIDTH)
    window = text[lo:hi].lower()
    return any(phrase in window for phrase in _NEGATION_PHRASES)


class MITRETactic(str, Enum):
    """MITRE ATT&CK tactics."""
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    COMMAND_AND_CONTROL = "command_and_control"
    IMPACT = "impact"


@dataclass
class MITRETechnique:
    """A MITRE ATT&CK technique with metadata.

    Attributes:
        technique_id: The technique ID (e.g., "T1566.001")
        technique_name: Human-readable technique name
        tactic: The tactic this technique belongs to
        description: Description of what this technique does
        detection_markers: Keywords or patterns that indicate this technique
    """
    technique_id: str
    technique_name: str
    tactic: MITRETactic
    description: str
    detection_markers: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "technique_id": self.technique_id,
            "technique_name": self.technique_name,
            "tactic": self.tactic.value,
            "description": self.description,
            "detection_markers": self.detection_markers,
        }


# MITRE ATT&CK patterns database
MITRE_ATTACK_PATTERNS: Dict[str, MITRETechnique] = {
    "T1566.001": MITRETechnique(
        technique_id="T1566.001",
        technique_name="Spearphishing Link",
        tactic=MITRETactic.INITIAL_ACCESS,
        description="User target phishing via malicious link emails",
        detection_markers=[
            "phishing",
            "malicious link",
            "email scam",
            "spearphishing",
            "click here",
            "verify your account",
            "urgent action required",
            "update payment information",
        ],
    ),
    "T1566.003": MITRETechnique(
        technique_id="T1566.003",
        technique_name="Spearphishing via Service Providers",
        tactic=MITRETactic.INITIAL_ACCESS,
        description="Phishing messages impersonating service providers to deliver malicious links",
        detection_markers=[
            "service provider",
            "billing notification",
            "account suspended",
            "payment declined",
            "invoice pending",
            "business email compromise",
            "impersonation",
        ],
    ),
    "T1056.002": MITRETechnique(
        technique_id="T1056.002",
        technique_name="Input Capture: GUI Input Capture",
        tactic=MITRETactic.CREDENTIAL_ACCESS,
        description="Capturing GUI input from target system (keylogging)",
        detection_markers=[
            "keylogger",
            "key logger",
            "input capture",
            "keystroke logging",
            "form grabbing",
            "credential theft",
            "password capture",
        ],
    ),
    "T1204.002": MITRETechnique(
        technique_id="T1204.002",
        technique_name="User Execution: Malicious File",
        tactic=MITRETactic.EXECUTION,
        description="User executes malicious file thinking it is legitimate",
        detection_markers=[
            "malicious file",
            "trojan",
            "virus",
            "ransomware",
            "malware download",
            "dropper",
            "loader",
            "payload",
            "file.exe",
            "setup.exe",
            ".scr",
            ".pif",
        ],
    ),
    "T1059.003": MITRETechnique(
        technique_id="T1059.003",
        technique_name="Command and Scripting Interpreter: Windows Command Shell",
        tactic=MITRETactic.EXECUTION,
        description="Executes commands via cmd.exe or PowerShell",
        detection_markers=[
            "cmd.exe",
            "powershell",
            "powershell script",
            "batch file",
            ".bat",
            ".cmd",
            "script execution",
        ],
    ),
    "T1106": MITRETechnique(
        technique_id="T1106",
        technique_name="Native API",
        tactic=MITRETactic.EXECUTION,
        description="Uses native OS API for execution",
        detection_markers=[
            "native api",
            "system call",
            "dll injection",
            "api call",
            "winapi",
        ],
    ),
    "T1190": MITRETechnique(
        technique_id="T1190",
        technique_name="Exploit Public-Facing Application",
        tactic=MITRETactic.INITIAL_ACCESS,
        description="Attacks vulnerable services exposed to the internet",
        detection_markers=[
            "exploit",
            "vulnerability",
            "cve-",
            "remote code execution",
            "rce",
            "buffer overflow",
        ],
    ),
}


class AttackPatternMapper:
    """Maps detected IOCs and site features to MITRE ATT&CK techniques."""

    # Threat actor attribution by technique ID
    threat_actor_map = {
        "T1566.001": [
            "Generic Phishing Campaigns",
            "APT-style Spearphishing Groups",
        ],
        "T1566.003": [
            "Business Email Compromise (BEC) Actors",
            "Service Provider Impersonators",
        ],
        "T1056.002": [
            "Keylogging Groups",
            "Information Stealers",
        ],
        "T1204.002": [
            "Malware Distributors",
            "Ransomware Groups",
            "Trojan Authors",
        ],
        "T1059.003": [
            "Script-based Attackers",
            "Living-off-the-Land (LotL) Actors",
        ],
        "T1106": [
            "Advanced APTs",
            "Sophisticated Malware Families",
        ],
        "T1190": [
            "Exploit Kit Operators",
            "Vulnerability Researchers",
        ],
    }

    def __init__(self) -> None:
        """Initialize the attack pattern mapper."""
        self.patterns = MITRE_ATTACK_PATTERNS

    def map_indicators_to_techniques(
        self,
        indicators: List[Indicator],
        site_features: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """Map detected IOCs to MITRE ATT&CK techniques.

        Matching is word-boundary aware and rejects positive markers that sit
        in a defensive/educational context (e.g. "phishing protection"). A
        technique must also collect at least _MIN_DISTINCT_MARKERS distinct
        marker hits before it is surfaced — a single keyword is no longer
        enough to label a site with an attack technique.

        Returns:
            List of technique matches sorted by confidence (descending),
            filtered to include only matches with confidence > _CONFIDENCE_CUTOFF
            AND at least _MIN_DISTINCT_MARKERS matched markers.
        """
        if site_features is None:
            site_features = {}

        # Build one searchable text blob per call so we don't tokenize the same
        # corpus N×|markers| times.
        corpus = self._build_corpus(indicators, site_features)

        technique_matches = []
        for technique in self.patterns.values():
            matched_markers = self._matched_markers_in_corpus(technique, corpus)
            if len(matched_markers) < _MIN_DISTINCT_MARKERS:
                continue
            confidence = len(matched_markers) / max(len(technique.detection_markers), 1)
            if confidence <= _CONFIDENCE_CUTOFF:
                continue
            technique_matches.append({
                "technique_id": technique.technique_id,
                "technique_name": technique.technique_name,
                "tactic": technique.tactic.value,
                "confidence": round(confidence, 2),
                "matched_markers": matched_markers,
            })

        technique_matches.sort(key=lambda x: x["confidence"], reverse=True)
        return technique_matches

    def _build_corpus(
        self,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> str:
        """Flatten indicators + string site_features into one searchable blob.

        Joining with "\\n\\n" preserves locality — negation context can't bleed
        across unrelated fields (e.g. an "anti-phishing" mention in the page
        title won't suppress a "phishing" hit inside an IOC URL).
        """
        parts: List[str] = []
        for indicator in indicators:
            val = getattr(indicator, "value", None)
            if isinstance(val, str) and val:
                parts.append(val)
        for value in site_features.values():
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        parts.append(item)
        return "\n\n".join(parts)

    def _matched_markers_in_corpus(
        self,
        technique: MITRETechnique,
        corpus: str,
    ) -> List[str]:
        """Return distinct markers from `technique` that fire on `corpus`.

        A marker fires when at least one regex match has no negation phrase
        in its surrounding context window. Markers with no surviving match
        are dropped.
        """
        if not corpus:
            return []
        matched: List[str] = []
        for marker in technique.detection_markers:
            pattern = _marker_pattern(marker)
            for m in pattern.finditer(corpus):
                if not _has_negation_in_window(corpus, m.start(), m.end()):
                    matched.append(marker)
                    break  # one clean hit per marker is enough
        return matched

    # Kept for backward compatibility with code that imports/uses these
    # internals directly. New code should go through map_indicators_to_techniques.
    def _calculate_technique_confidence(
        self,
        technique: MITRETechnique,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> float:
        corpus = self._build_corpus(indicators, site_features)
        matched = self._matched_markers_in_corpus(technique, corpus)
        if not technique.detection_markers:
            return 0.0
        return len(matched) / len(technique.detection_markers)

    def _marker_matches(
        self,
        marker: str,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> bool:
        corpus = self._build_corpus(indicators, site_features)
        if not corpus:
            return False
        pattern = _marker_pattern(marker)
        for m in pattern.finditer(corpus):
            if not _has_negation_in_window(corpus, m.start(), m.end()):
                return True
        return False

    def _get_matched_markers(
        self,
        technique: MITRETechnique,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> List[str]:
        corpus = self._build_corpus(indicators, site_features)
        return self._matched_markers_in_corpus(technique, corpus)

    def generate_attribution_suggestion(
        self,
        techniques: List[Dict],
    ) -> Dict:
        """Generate threat attribution suggestion based on matched techniques.

        Args:
            techniques: List of mapped techniques from map_indicators_to_techniques()

        Returns:
            Dict with threat_actor, attack_pattern, attack_tactic,
            technique_id, confidence, all_techniques, and explanation
        """
        if not techniques:
            return {
                "threat_actor": "Unknown",
                "attack_pattern": "Unknown",
                "attack_tactic": "Unknown",
                "technique_id": None,
                "confidence": 0.0,
                "all_techniques": [],
                "explanation": "No MITRE ATT&CK techniques matched.",
            }

        # Get the highest confidence technique
        top_technique = techniques[0]
        technique_id = top_technique["technique_id"]
        confidence = top_technique["confidence"]
        attack_tactic = top_technique["tactic"]
        attack_pattern = top_technique["technique_name"]

        # Select threat actor based on confidence
        threat_actors = self.threat_actor_map.get(technique_id, ["Unknown Actor"])

        if confidence > 0.6 and len(threat_actors) > 1:
            # High confidence - select specific actor
            threat_actor = threat_actors[1]  # More specific actor
        else:
            # Lower confidence - use generic description
            threat_actor = threat_actors[0]

        # Build explanation
        count = len(techniques)
        if count == 1:
            explanation = (
                f"Detected 1 MITRE ATT&CK technique: {attack_pattern} "
                f"({technique_id}) with {confidence:.0%} confidence. "
                f"This suggests potential {threat_actor} activity using "
                f"{attack_tactic.replace('_', ' ')} tactics."
            )
        else:
            explanation = (
                f"Detected {count} MITRE ATT&CK techniques with the primary "
                f"attack pattern: {attack_pattern} ({technique_id}) at "
                f"{confidence:.0%} confidence. The presence of multiple "
                f"techniques suggests sophisticated {threat_actor} activity "
                f"using {attack_tactic.replace('_', ' ')} tactics."
            )

        return {
            "threat_actor": threat_actor,
            "attack_pattern": attack_pattern,
            "attack_tactic": attack_tactic,
            "technique_id": technique_id,
            "confidence": confidence,
            "all_techniques": techniques,
            "explanation": explanation,
        }
