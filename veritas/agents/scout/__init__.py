"""
Veritas Scout Navigation Components

Intelligent scrolling and lazy-load detection for comprehensive page capture.
"""

from .lazy_load_detector import LazyLoadDetector, MUTATION_OBSERVER_SCRIPT

__all__ = [
    "LazyLoadDetector",
    "MUTATION_OBSERVER_SCRIPT",
]
