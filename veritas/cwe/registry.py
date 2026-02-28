"""
CWE (Common Weakness Enumeration) registry for vulnerability categorization.

Maps threat findings to CWE identifiers for professional security reporting.
Based on MITRE CWE database: https://cwe.mitre.org/
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CWECategory(str, Enum):
    """CWE vulnerability categories."""

    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHORIZATION = "authorization"
    CRYPTO = "crypto"
    INPUT_VALIDATION = "input_validation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INFO_DISCLOSURE = "info_disclosure"
    DEFAULT_CREDENTIALS = "default_credentials"
    HARD_CODED_CREDENTIALS = "hard_coded_credentials"
    INSECURE_STORAGE = "insecure_storage"
    MISCONFIGURATION = "misconfiguration"


@dataclass(frozen=True)
class CWEEntry:
    """
    CWE entry with identifier, name, description, and URL.

    Attributes:
        cwe_id: CWE identifier (e.g., "CWE-787")
        name: Short descriptive name
        description: Full description of the weakness
        url: MITRE CWE definition URL
    """

    cwe_id: str
    name: str
    description: str
    url: str


# CWE Registry with minimum 10 entries covering critical vulnerability categories
CWE_REGISTRY: dict[str, CWEEntry] = {
    "CWE-787": CWEEntry(
        cwe_id="CWE-787",
        name="Out-of-bounds Write",
        description="The software writes data past the end, or before the beginning, of the intended buffer.",
        url="https://cwe.mitre.org/data/definitions/787.html",
    ),
    "CWE-79": CWEEntry(
        cwe_id="CWE-79",
        name="Cross-site Scripting (XSS)",
        description="The software does not properly neutralize or incorrectly neutralizes user-controllable input before it is placed in output that is used as a web page.",
        url="https://cwe.mitre.org/data/definitions/79.html",
    ),
    "CWE-352": CWEEntry(
        cwe_id="CWE-352",
        name="Cross-Site Request Forgery (CSRF)",
        description="The web application does not, or can not, sufficiently verify whether a well-formed, valid, consistent request was intentionally provided by the user who submitted the request.",
        url="https://cwe.mitre.org/data/definitions/352.html",
    ),
    "CWE-287": CWEEntry(
        cwe_id="CWE-287",
        name="Improper Authentication",
        description="The product does not properly verify credentials before allowing access.",
        url="https://cwe.mitre.org/data/definitions/287.html",
    ),
    "CWE-862": CWEEntry(
        cwe_id="CWE-862",
        name="Missing Authorization",
        description="The product does not perform an authorization check when an actor attempts to access a resource or perform an action.",
        url="https://cwe.mitre.org/data/definitions/862.html",
    ),
    "CWE-327": CWEEntry(
        cwe_id="CWE-327",
        name="Use of a Broken or Risky Cryptographic Algorithm",
        description="The product uses an algorithm that is insecure or deprecated for cryptographic purposes.",
        url="https://cwe.mitre.org/data/definitions/327.html",
    ),
    "CWE-319": CWEEntry(
        cwe_id="CWE-319",
        name="Cleartext Transmission of Sensitive Information",
        description="The product transmits sensitive or security-critical data in cleartext in a communication channel that can be sniffed by malicious actors.",
        url="https://cwe.mitre.org/data/definitions/319.html",
    ),
    "CWE-20": CWEEntry(
        cwe_id="CWE-20",
        name="Improper Input Validation",
        description="The product does not validate or incorrectly validates input.",
        url="https://cwe.mitre.org/data/definitions/20.html",
    ),
    "CWE-601": CWEEntry(
        cwe_id="CWE-601",
        name="URL Redirection to Untrusted Site",
        description="The product uses data from an upstream component in a security-critical context without neutralizing or incorrectly neutralizing it.",
        url="https://cwe.mitre.org/data/definitions/601.html",
    ),
    "CWE-525": CWEEntry(
        cwe_id="CWE-525",
        name="Use of Web Browser Cache Containing Sensitive Information",
        description="The application uses a web browser's cache to store sensitive information, which can be accessed by unauthorized users.",
        url="https://cwe.mitre.org/data/definitions/525.html",
    ),
    # Additional critical CWEs for comprehensive coverage
    "CWE-125": CWEEntry(
        cwe_id="CWE-125",
        name="Out-of-bounds Read",
        description="The software reads data past the end, or before the beginning, of the intended buffer.",
        url="https://cwe.mitre.org/data/definitions/125.html",
    ),
    "CWE-89": CWEEntry(
        cwe_id="CWE-89",
        name="SQL Injection",
        description="The software constructs all or part of an SQL command using externally-influenced input, allowing untrusted input to inject SQL commands.",
        url="https://cwe.mitre.org/data/definitions/89.html",
    ),
    "CWE-798": CWEEntry(
        cwe_id="CWE-798",
        name="Use of Hard-coded Credentials",
        description="The product contains hard-coded credentials, such as a password or cryptographic key.",
        url="https://cwe.mitre.org/data/definitions/798.html",
    ),
    "CWE-532": CWEEntry(
        cwe_id="CWE-532",
        name="Insertion of Sensitive Information into Log File",
        description="The product inserts sensitive information into log files or debugging output.",
        url="https://cwe.mitre.org/data/definitions/532.html",
    ),
}


def find_cwe_by_category(category: CWECategory, limit: int = 3) -> list[CWEEntry]:
    """
    Find CWE entries by category.

    Args:
        category: CWECategory to filter by
        limit: Maximum number of entries to return (default 3)

    Returns:
        List of CWEEntry objects matching the category
    """
    category_keywords = {
        CWECategory.INJECTION: ["injection", "sql", "code"],
        CWECategory.XSS: ["xss", "cross-site scripting"],
        CWECategory.CSRF: ["csrf", "cross-site request"],
        CWECategory.AUTHORIZATION: ["authorization", "privilege", "access"],
        CWECategory.CRYPTO: ["crypto", "encryption", "cipher"],
        CWECategory.INPUT_VALIDATION: ["input", "validation", "sanitization"],
        CWECategory.PRIVILEGE_ESCALATION: ["privilege", "escalation", "elevation"],
        CWECategory.INFO_DISCLOSURE: ["disclosure", "information", "leak"],
        CWECategory.DEFAULT_CREDENTIALS: ["default", "credential", "hardcoded"],
        CWECategory.HARD_CODED_CREDENTIALS: ["hard", "code", "credential", "password"],
        CWECategory.INSECURE_STORAGE: ["storage", "encrypt", "sensitive"],
        CWECategory.MISCONFIGURATION: ["config", "misconfig"],
    }

    keywords = category_keywords.get(category, [])
    results = []

    for cwe_id, entry in CWE_REGISTRY.items():
        cwe_lower = entry.name.lower() + " " + entry.description.lower()
        for keyword in keywords:
            if keyword in cwe_lower:
                results.append(entry)
                break

        if len(results) >= limit:
            break

    return results[:limit]


def map_finding_to_cwe(finding_category: str, severity: str) -> Optional[CWEEntry]:
    """
    Map a threat finding to a CWE entry based on category and severity.

    Args:
        finding_category: Category of the finding (e.g., "injection", "xss", "phishing")
        severity: Severity level ("critical", "high", "medium", "low")

    Returns:
        CWEntry matching the finding, or None if no match found
    """
    # Category mapping to CWE ID
    category_to_cwe = {
        "injection": "CWE-787",
        "xss": "CWE-79",
        "cross-site scripting": "CWE-79",
        "csrf": "CWE-352",
        "authorization": "CWE-287",
        "auth": "CWE-287",
        "authentication": "CWE-287",
        "crypto": "CWE-327",
        "encryption": "CWE-327",
        "ssl": "CWE-319",
        "tls": "CWE-319",
        "https": "CWE-319",
        "input": "CWE-20",
        "validation": "CWE-20",
        "phishing": "CWE-601",
        "redirect": "CWE-601",
        "credential": "CWE-798",
        "password": "CWE-798",
        "cache": "CWE-525",
        "log": "CWE-532",
        "privilege": "CWE-862",
        "access": "CWE-862",
    }

    # Normalize category input
    category_lower = finding_category.lower().strip()

    # Try direct match first
    for cat_key, cwe_id in category_to_cwe.items():
        if cat_key in category_lower:
            return CWE_REGISTRY.get(cwe_id)

    # Return a default entry for unknown categories, preferring CVSS-suitable
    # For security findings, default to input validation or injection
    if "malware" in category_lower or "virus" in category_lower:
        return CWE_REGISTRY.get("CWE-20")  # Input validation
    if "scan" in category_lower or "suspicious" in category_lower:
        return CWE_REGISTRY.get("CWE-862")  # Missing authorization

    return None
