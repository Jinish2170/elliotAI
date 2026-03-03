"""MITRE ATT&CK framework mapping for cyber threat intelligence.

Provides technique mapping, attribution suggestions, and standardized
threat classification using the MITRE ATT&CK framework.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .ioc_detector import Indicator


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

        Args:
            indicators: List of detected IOCs
            site_features: Optional site features dict

        Returns:
            List of technique matches sorted by confidence (descending),
            filtered to include only matches with confidence > 0.3
        """
        if site_features is None:
            site_features = {}

        technique_matches = []

        for technique_id, technique in self.patterns.items():
            confidence = self._calculate_technique_confidence(
                technique, indicators, site_features
            )

            if confidence > 0.3:  # Only include confident matches
                matched_markers = self._get_matched_markers(
                    technique, indicators, site_features
                )

                technique_matches.append({
                    "technique_id": technique.technique_id,
                    "technique_name": technique.technique_name,
                    "tactic": technique.tactic.value,
                    "confidence": round(confidence, 2),
                    "matched_markers": matched_markers,
                })

        # Sort by confidence descending
        technique_matches.sort(key=lambda x: x["confidence"], reverse=True)

        return technique_matches

    def _calculate_technique_confidence(
        self,
        technique: MITRETechnique,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for a technique match.

        Args:
            technique: The technique to evaluate
            indicators: List of detected IOCs
            site_features: Site feature dict

        Returns:
            Confidence score from 0.0 to 1.0
        """
        markers = technique.detection_markers
        if not markers:
            return 0.0

        matched_count = 0
        for marker in markers:
            if self._marker_matches(marker, indicators, site_features):
                matched_count += 1

        # Confidence is the ratio of matched markers to total markers
        return matched_count / len(markers) if markers else 0.0

    def _marker_matches(
        self,
        marker: str,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> bool:
        """Check if a detection marker matches indicators or site features.

        Args:
            marker: The keyword or pattern to look for
            indicators: List of detected IOCs
            site_features: Site feature dict

        Returns:
            True if marker matches, False otherwise
        """
        marker_lower = marker.lower()

        # Check against indicator values
        for indicator in indicators:
            if marker_lower in indicator.value.lower():
                return True

        # Check against site features
        for key, value in site_features.items():
            if isinstance(value, str) and marker_lower in value.lower():
                return True
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and marker_lower in item.lower():
                        return True

        return False

    def _get_matched_markers(
        self,
        technique: MITRETechnique,
        indicators: List[Indicator],
        site_features: Dict[str, Any],
    ) -> List[str]:
        """Get list of detection markers that matched.

        Args:
            technique: The technique to check
            indicators: List of detected IOCs
            site_features: Site feature dict

        Returns:
            List of matched marker strings
        """
        matched_markers = []
        for marker in technique.detection_markers:
            if self._marker_matches(marker, indicators, site_features):
                matched_markers.append(marker)

        return matched_markers

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
