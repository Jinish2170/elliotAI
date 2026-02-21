"""
Veritas — Global Configuration

Extends RAGv5 centralized config pattern (Rag_v5.0.0/rag-core/config/settings.py)
with all Veritas-specific settings: NIM endpoints, audit budgets, concurrency,
browser tuning, and tier definitions.

All values are overridable via environment variables (.env file).
Directories are auto-created on import.
"""

import hashlib
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("veritas.settings")

# Load .env from veritas root
_veritas_root = Path(__file__).resolve().parent.parent
load_dotenv(_veritas_root / ".env")

# ============================================================
# Paths
# ============================================================
BASE_DIR = _veritas_root
DATA_DIR = BASE_DIR / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"
REPORTS_DIR = DATA_DIR / "reports"
CACHE_DIR = DATA_DIR / "cache"
VECTORDB_DIR = DATA_DIR / "vectordb"
TEMPLATES_DIR = BASE_DIR / "reporting" / "templates"

# Auto-create all data directories
for _dir in [EVIDENCE_DIR, REPORTS_DIR, CACHE_DIR, VECTORDB_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# NVIDIA NIM — Inference API
# ============================================================
NIM_API_KEY: str = os.getenv("NVIDIA_NIM_API_KEY", "")
NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_ENDPOINT", "https://integrate.api.nvidia.com/v1")

# Vision models (for Agent 2: Visual Forensics)
NIM_VISION_MODEL: str = os.getenv("NIM_VISION_MODEL", "meta/llama-3.2-90b-vision-instruct")
NIM_VISION_FALLBACK: str = os.getenv("NIM_VISION_FALLBACK", "microsoft/phi-3.5-vision-instruct")

# LLM model (for Agent 4: Judge)
NIM_LLM_MODEL: str = os.getenv("NIM_LLM_MODEL", "meta/llama-3.1-70b-instruct")

# API tuning
NIM_TIMEOUT: int = int(os.getenv("NIM_TIMEOUT", "30"))
NIM_RETRY_COUNT: int = int(os.getenv("NIM_RETRY_COUNT", "2"))
NIM_REQUESTS_PER_MINUTE: int = int(os.getenv("NIM_REQUESTS_PER_MINUTE", "10"))


# ============================================================
# Tavily — External Search for Entity Verification
# ============================================================
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
TAVILY_REQUESTS_PER_MINUTE: int = int(os.getenv("TAVILY_REQUESTS_PER_MINUTE", "5"))


# ============================================================
# Graph Intelligence Timeouts / Concurrency
# ============================================================
GRAPH_PHASE_TIMEOUT_S: int = int(os.getenv("GRAPH_PHASE_TIMEOUT_S", "90"))
GRAPH_WHOIS_TIMEOUT_S: int = int(os.getenv("GRAPH_WHOIS_TIMEOUT_S", "12"))
GRAPH_DNS_TIMEOUT_S: int = int(os.getenv("GRAPH_DNS_TIMEOUT_S", "6"))
GRAPH_SSL_TIMEOUT_S: int = int(os.getenv("GRAPH_SSL_TIMEOUT_S", "6"))
GRAPH_META_TIMEOUT_S: int = int(os.getenv("GRAPH_META_TIMEOUT_S", "12"))
GRAPH_VERIFY_TIMEOUT_S: int = int(os.getenv("GRAPH_VERIFY_TIMEOUT_S", "20"))
GRAPH_SEARCH_TIMEOUT_S: int = int(os.getenv("GRAPH_SEARCH_TIMEOUT_S", "15"))
GRAPH_VERIFY_CONCURRENCY: int = int(os.getenv("GRAPH_VERIFY_CONCURRENCY", "3"))
GRAPH_SEARCH_FOLLOW_LINKS: bool = os.getenv("GRAPH_SEARCH_FOLLOW_LINKS", "false").lower() == "true"


# ============================================================
# Audit Budget Controls
# ============================================================
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
MAX_PAGES_PER_AUDIT: int = int(os.getenv("MAX_PAGES_PER_AUDIT", "10"))
SCREENSHOT_TIMEOUT: int = int(os.getenv("SCREENSHOT_TIMEOUT", "15"))
TEMPORAL_DELAY: int = int(os.getenv("TEMPORAL_DELAY", "10"))
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
MIN_EVIDENCE_COUNT: int = int(os.getenv("MIN_EVIDENCE_COUNT", "3"))


# ============================================================
# Concurrency (tuned for 8GB RAM)
# ============================================================
MAX_CONCURRENT_AUDITS: int = int(os.getenv("MAX_CONCURRENT_AUDITS", "2"))
MAX_CONCURRENT_BROWSER_PAGES: int = int(os.getenv("MAX_CONCURRENT_BROWSER_PAGES", "3"))
INTER_REQUEST_DELAY_MS: int = int(os.getenv("INTER_REQUEST_DELAY_MS", "500"))


# ============================================================
# Embedding Model (local, lightweight — ~90MB)
# ============================================================
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# ============================================================
# Playwright Browser
# ============================================================
BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_VIEWPORT_WIDTH: int = int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1920"))
BROWSER_VIEWPORT_HEIGHT: int = int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080"))
MOBILE_VIEWPORT_WIDTH: int = int(os.getenv("MOBILE_VIEWPORT_WIDTH", "390"))
MOBILE_VIEWPORT_HEIGHT: int = int(os.getenv("MOBILE_VIEWPORT_HEIGHT", "844"))


# ============================================================
# Security Modules — toggleable checks
# ============================================================
ENABLED_SECURITY_MODULES: list[str] = [
    m.strip()
    for m in os.getenv(
        "ENABLED_SECURITY_MODULES",
        "security_headers,phishing_db",
    ).split(",")
    if m.strip()
]

# Google Safe Browsing API key (optional, free tier = 10K lookups/day)
SAFE_BROWSING_API_KEY: str = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")


# ============================================================
# SecurityAgent Configuration (Agent-based refactoring)
# ============================================================
# Feature flag: Use agent-based implementation vs function-based
USE_SECURITY_AGENT: bool = os.getenv("USE_SECURITY_AGENT", "true").lower() == "true"

# Gradual rollout: 0.0 to 1.0 (100%), random users below this threshold use agent
SECURITY_AGENT_ROLLOUT: float = float(os.getenv("SECURITY_AGENT_ROLLOUT", "1.0"))

# Timeout per security module (seconds)
SECURITY_AGENT_TIMEOUT: int = int(os.getenv("SECURITY_AGENT_TIMEOUT", "15"))

# Retry attempts for failed modules
SECURITY_AGENT_RETRY_COUNT: int = int(os.getenv("SECURITY_AGENT_RETRY_COUNT", "2"))

# Fail fast mode: stop on first module failure if True
SECURITY_AGENT_FAIL_FAST: bool = os.getenv("SECURITY_AGENT_FAIL_FAST", "false").lower() == "true"


# ============================================================
# Verdict Mode — user experience level
# ============================================================
DEFAULT_VERDICT_MODE: str = os.getenv("DEFAULT_VERDICT_MODE", "expert")  # "simple" or "expert"


# ============================================================
# Tor / .onion Support (experimental)
# ============================================================
TOR_ENABLED: bool = os.getenv("TOR_ENABLED", "false").lower() == "true"
TOR_SOCKS_HOST: str = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_SOCKS_PORT: int = int(os.getenv("TOR_SOCKS_PORT", "9050"))


# ============================================================
# Audit Tiers — Budget per scan type
# ============================================================
AUDIT_TIERS: dict = {
    "quick_scan": {
        "description": "Homepage-only fast check",
        "pages": 1,
        "screenshots": 2,
        "nim_calls": 3,
        "estimated_credits": 5,
    },
    "standard_audit": {
        "description": "Default multi-page audit",
        "pages": 5,
        "screenshots": 10,
        "nim_calls": 12,
        "estimated_credits": 20,
        "max_verifications": 10,
    },
    "deep_forensic": {
        "description": "Full investigation with entity verification",
        "pages": 10,
        "screenshots": 20,
        "nim_calls": 30,
        "estimated_credits": 50,
        "max_verifications": 15,
    },
}


# ============================================================
# State Machine Transitions (for LangGraph orchestrator)
# ============================================================
STATE_TRANSITIONS: dict = {
    "START": ["SCOUT"],
    "SCOUT": ["VISION", "RETRY_SCOUT", "ABORT"],
    "RETRY_SCOUT": ["SCOUT", "ABORT"],
    "VISION": ["GRAPH", "JUDGE"],
    "GRAPH": ["JUDGE", "SCOUT"],
    "JUDGE": ["REPORT", "SCOUT"],
    "REPORT": ["END"],
    "ABORT": ["PARTIAL_REPORT"],
    "PARTIAL_REPORT": ["END"],
}


# ============================================================
# SecurityAgent Rollout Helpers (Plan 02-03)
# ============================================================


def get_security_agent_rollout() -> float:
    """Get SecurityAgent rollout percentage from environment.

    Reads SECURITY_AGENT_ROLLOUT env var (float 0.0-1.0), defaults to 1.0 (100%).
    Clamps to valid range.

    Returns:
        float: Rollout percentage between 0.0 and 1.0
    """
    rollout = os.getenv("SECURITY_AGENT_ROLLOUT", "1.0")
    try:
        percentage = float(rollout)
    except ValueError:
        percentage = 1.0

    # Clamp to 0.0-1.0 range
    return max(0.0, min(1.0, percentage))


def should_use_security_agent(url: str = "") -> bool:
    """Determine if SecurityAgent should be used for this URL.

    Implements consistent hash-based rollout:
    - If USE_SECURITY_AGENT=true → always use agent
    - If USE_SECURITY_AGENT=false → always use function
    - If USE_SECURITY_AGENT=auto → use rollout percentage with hash consistency

    Consistent hash routing ensures same URL always gets same mode (important for debugging).

    Args:
        url: Target URL (if empty, simple random selection)

    Returns:
        bool: True if SecurityAgent should be used, False for function mode
    """
    # Override: force agent mode
    if USE_SECURITY_AGENT:
        return True

    # Override: force function mode
    mode = os.getenv("USE_SECURITY_AGENT", "true").lower()
    if mode == "false":
        return False

    # Auto mode: use rollout percentage with consistent hash
    rollout = get_security_agent_rollout()

    if url:
        # Consistent hash: same URL always gets same decision
        hash_value = int(hashlib.md5(url.lower().encode()).hexdigest()[:8], 16)
        normalized = hash_value / (2**32 - 1)
        return normalized < rollout
    else:
        # No URL provided: simple random selection
        import random
        return random.random() < rollout


# Log rollout configuration on startup
_rollout_pct = get_security_agent_rollout()
logger.info(
    f"SecurityAgent: USE_SECURITY_AGENT={USE_SECURITY_AGENT}, "
    f"ROLLOUT={_rollout_pct:.0%}"
)
