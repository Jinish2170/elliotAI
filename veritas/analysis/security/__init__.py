"""
Security Analysis Modules Namespace

Auto-discovered security modules for the VERITAS SecurityAgent.
"""

from .darknet import DarknetAnalyzer

__all__ = ["DarknetAnalyzer"]
