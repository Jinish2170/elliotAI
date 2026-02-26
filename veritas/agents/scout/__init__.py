"""
Veritas Scout Navigation Components

Intelligent scrolling and lazy-load detection for comprehensive page capture.
"""

from .lazy_load_detector import LazyLoadDetector, MUTATION_OBSERVER_SCRIPT
from .scroll_orchestrator import ScrollOrchestrator

__all__ = [
    "LazyLoadDetector",
    "MUTATION_OBSERVER_SCRIPT",
    "ScrollOrchestrator",
]
