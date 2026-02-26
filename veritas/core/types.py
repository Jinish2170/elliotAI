"""
Veritas Core Data Types

Shared data structures used across the Veritas architecture:
- Security-related types (Severity, SecurityFinding, SecurityConfig, SecurityResult)
- Type-safe dataclasses for cross-module communication

All types are JSON-serializable via to_dict() / from_dict() methods.
"""

import dataclasses
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("veritas.core.types")


# ============================================================
# Security Agent Types
# ============================================================

class Severity(str, Enum):
    """Severity levels for security findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityFinding:
    """
    A single security finding from a security module.

    Attributes:
        category: Module category (e.g., "security_headers", "phishing", "redirects", "js_analysis", "forms")
        severity: Severity level of the finding
        evidence: Human-readable description of what was found
        source_module: Name of the module that generated this finding
        timestamp: ISO format timestamp when finding was created
        confidence: Confidence score 0.0 to 1.0
    """
    category: str
    severity: Severity
    evidence: str
    source_module: str
    timestamp: str
    confidence: float

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    @classmethod
    def create(
        cls,
        category: str,
        severity: str | Severity,
        evidence: str,
        source_module: str,
        confidence: float = 1.0,
    ) -> "SecurityFinding":
        """
        Factory method for creating SecurityFinding.

        Args:
            category: Module category
            severity: Severity (string or Severity enum)
            evidence: Human-readable description
            source_module: Name of generating module
            confidence: Confidence 0.0-1.0

        Returns:
            SecurityFinding instance
        """
        if isinstance(severity, str):
            severity = Severity(severity.upper())

        return cls(
            category=category,
            severity=severity,
            evidence=evidence,
            source_module=source_module,
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=confidence,
        )


@dataclass
class SecurityConfig:
    """
    Configuration for SecurityAgent execution.

    Attributes:
        timeout: Seconds per module before timeout
        retry_count: Number of retry attempts for failed modules
        fail_fast: If True, stop analysis on first module failure
    """
    timeout: int = 15
    retry_count: int = 2
    fail_fast: bool = False

    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout < 1:
            raise ValueError(f"Timeout must be at least 1 second, got {self.timeout}")
        if self.retry_count < 0:
            raise ValueError(f"Retry count must be non-negative, got {self.retry_count}")

    @classmethod
    def from_settings(cls) -> "SecurityConfig":
        """
        Create SecurityConfig from global settings.

        Returns:
            SecurityConfig instance with values from settings module
        """
        try:
            from config.settings import (
                SECURITY_AGENT_FAIL_FAST,
                SECURITY_AGENT_RETRY_COUNT,
                SECURITY_AGENT_TIMEOUT,
            )
            return cls(
                timeout=SECURITY_AGENT_TIMEOUT,
                retry_count=SECURITY_AGENT_RETRY_COUNT,
                fail_fast=SECURITY_AGENT_FAIL_FAST,
            )
        except ImportError:
            logger.warning("Could not import SECURITY_AGENT_* settings, using defaults")
            return cls()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return dataclasses.asdict(self)


@dataclass
class SecurityResult:
    """
    Complete result from SecurityAgent analysis.

    Attributes:
        url: URL that was analyzed
        audit_id: Optional audit ID for tracking
        timestamp: ISO format timestamp of analysis completion
        composite_score: Aggregated security score 0.0-1.0 (higher = more secure)
        findings: List of SecurityFinding objects
        modules_results: Nested per-module results (e.g., {"security_headers": {...}})
        modules_run: List of module names that were executed
        modules_failed: List of module names that failed
        errors: List of error messages captured during analysis
        analysis_time_ms: Analysis duration in milliseconds
    """
    url: str
    audit_id: Optional[str] = None
    timestamp: str = ""
    composite_score: float = 1.0
    findings: list[SecurityFinding] = field(default_factory=list)
    modules_results: dict[str, Any] = field(default_factory=dict)
    modules_run: list[str] = field(default_factory=list)
    modules_failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    analysis_time_ms: int = 0

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not 0.0 <= self.composite_score <= 1.0:
            raise ValueError(f"Composite score must be between 0.0 and 1.0, got {self.composite_score}")

    def add_finding(self, finding: SecurityFinding) -> None:
        """Add a security finding to this result."""
        self.findings.append(finding)

    def add_error(self, error: str) -> None:
        """Add an error message to this result."""
        self.errors.append(error)

    def to_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary.

        Returns:
            Dictionary with all SecurityResult fields, including nested findings as dicts
        """
        return {
            "url": self.url,
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "composite_score": self.composite_score,
            "findings": [self._finding_to_dict(f) for f in self.findings],
            "modules_results": self.modules_results,
            "modules_run": self.modules_run,
            "modules_failed": self.modules_failed,
            "errors": self.errors,
            "analysis_time_ms": self.analysis_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityResult":
        """
        Create SecurityResult from JSON-serializable dictionary.

        Args:
            data: Dictionary containing SecurityResult fields

        Returns:
            SecurityResult instance
        """
        findings = [cls._finding_from_dict(f) for f in data.get("findings", [])]

        return cls(
            url=data["url"],
            audit_id=data.get("audit_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            composite_score=data.get("composite_score", 1.0),
            findings=findings,
            modules_results=data.get("modules_results", {}),
            modules_run=data.get("modules_run", []),
            modules_failed=data.get("modules_failed", []),
            errors=data.get("errors", []),
            analysis_time_ms=data.get("analysis_time_ms", 0),
        )

    @staticmethod
    def _finding_to_dict(finding: SecurityFinding) -> dict:
        """Convert SecurityFinding to dict for JSON serialization."""
        return {
            "category": finding.category,
            "severity": finding.severity.value,
            "evidence": finding.evidence,
            "source_module": finding.source_module,
            "timestamp": finding.timestamp,
            "confidence": finding.confidence,
        }

    @staticmethod
    def _finding_from_dict(data: dict) -> SecurityFinding:
        """Create SecurityFinding from dict."""
        return SecurityFinding(
            category=data["category"],
            severity=Severity(data["severity"]),
            evidence=data["evidence"],
            source_module=data["source_module"],
            timestamp=data["timestamp"],
            confidence=data["confidence"],
        )

    @property
    def critical_findings(self) -> list[SecurityFinding]:
        """Get all critical severity findings."""
        return [f for f in self.findings if f.severity == Severity.CRITICAL]

    @property
    def high_findings(self) -> list[SecurityFinding]:
        """Get all high severity findings."""
        return [f for f in self.findings if f.severity == Severity.HIGH]

    @property
    def total_findings(self) -> int:
        """Get total count of all findings."""
        return len(self.findings)


# ============================================================
# Scroll Orchestration Types
# ============================================================

@dataclass
class ScrollState:
    """
    Snapshot of scroll state at a specific cycle.

    Tracks scroll position, page height, and content changes for
    lazy-load detection during intelligent scrolling.

    Attributes:
        cycle: Current scroll cycle number (0-indexed)
        has_lazy_load: Whether new content was detected this cycle
        last_scroll_y: Vertical scroll position after scroll
        last_scroll_height: Total document height after scroll
        cycles_without_content: Counter for stabilization detection
        stabilized: Whether page has stabilized (no new content)
    """
    cycle: int
    has_lazy_load: bool
    last_scroll_y: int
    last_scroll_height: int
    cycles_without_content: int
    stabilized: bool


@dataclass
class ScrollResult:
    """
    Complete result from intelligent page scrolling.

    Contains scroll statistics and state history for analysis.

    Attributes:
        total_cycles: Number of scroll cycles completed
        stabilized: Whether scrolling terminated due to stabilization
        lazy_load_detected: Whether lazy-loaded content was detected
        screenshots_captured: Number of screenshots captured during scroll
        scroll_states: List of ScrollState objects for each cycle
    """
    total_cycles: int
    stabilized: bool
    lazy_load_detected: bool
    screenshots_captured: int
    scroll_states: list[ScrollState] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "total_cycles": self.total_cycles,
            "stabilized": self.stabilized,
            "lazy_load_detected": self.lazy_load_detected,
            "screenshots_captured": self.screenshots_captured,
            "scroll_states": [
                {
                    "cycle": s.cycle,
                    "has_lazy_load": s.has_lazy_load,
                    "last_scroll_y": s.last_scroll_y,
                    "last_scroll_height": s.last_scroll_height,
                    "cycles_without_content": s.cycles_without_content,
                    "stabilized": s.stabilized,
                }
                for s in self.scroll_states
            ],
        }


# ============================================================
# Multi-Page Exploration Types
# ============================================================

@dataclass
class LinkInfo:
    """
    Information about a discovered link with priority ranking.

    Attributes:
        url: Absolute URL of the link
        text: Anchor text content
        location: One of "nav", "footer", "content" - where link was found
        priority: Lower values = higher visitation priority (nav=1, footer=2, content=3)
        depth: Link depth level (default 0, can be increased for hierarchical tracking)
    """
    url: str
    text: str
    location: str  # "nav", "footer", "content"
    priority: int  # Lower = higher priority
    depth: int = 0


@dataclass
class PageVisit:
    """
    Result of visiting a single page during multi-page exploration.

    Attributes:
        url: URL that was visited
        status: One of "SUCCESS", "TIMEOUT", "ERROR"
        screenshot_path: Optional path to screenshot capture
        page_title: Title of the page
        navigation_time_ms: Time taken to navigate to and load page
        scroll_result: Optional ScrollResult if intelligent scrolling was performed
    """
    url: str
    status: str  # "SUCCESS", "TIMEOUT", "ERROR"
    screenshot_path: Optional[str] = None
    page_title: str = ""
    navigation_time_ms: int = 0
    scroll_result: Optional["ScrollResult"] = None


@dataclass
class ExplorationResult:
    """
    Complete result of multi-page exploration.

    Attributes:
        base_url: Starting URL for exploration
        pages_visited: List of PageVisit objects for each visited page
        total_pages: Total number of pages visited
        total_time_ms: Total time spent on all navigations
        breadcrumbs: List of URLs visited in order
        links_discovered: List of LinkInfo objects discovered during exploration
    """
    base_url: str
    pages_visited: list[PageVisit] = field(default_factory=list)
    total_pages: int = 0
    total_time_ms: int = 0
    breadcrumbs: list[str] = field(default_factory=list)
    links_discovered: list[LinkInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "base_url": self.base_url,
            "total_pages": self.total_pages,
            "total_time_ms": self.total_time_ms,
            "breadcrumbs": self.breadcrumbs,
            "pages_visited": [
                {
                    "url": pv.url,
                    "status": pv.status,
                    "screenshot_path": pv.screenshot_path,
                    "page_title": pv.page_title,
                    "navigation_time_ms": pv.navigation_time_ms,
                    "scroll_result": pv.scroll_result.to_dict() if pv.scroll_result else None,
                }
                for pv in self.pages_visited
            ],
            "links_discovered": [
                {
                    "url": li.url,
                    "text": li.text,
                    "location": li.location,
                    "priority": li.priority,
                    "depth": li.depth,
                }
                for li in self.links_discovered
            ],
        }
