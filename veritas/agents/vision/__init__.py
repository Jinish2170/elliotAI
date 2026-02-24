"""
Veritas Vision Agent Module

Computer vision and temporal analysis components for detecting dark patterns
and visual anomalies in screenshots.

Note: This package imports from the sibling vision.py to maintain backward
compatibility while enabling the subdirectory structure.
"""

# Import from temporal_analysis sub-module
from veritas.agents.vision.temporal_analysis import TemporalAnalyzer

# Import all public exports from sibling vision.py for backward compatibility
# The vision.py file and vision/ subdirectory coexist, so we explicitly import
# from the module file to maintain the import path used by orchestrator.py
import sys
from pathlib import Path
vision_module_path = Path(__file__).parent.parent / 'vision.py'
if vision_module_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location('veritas.agents.vision_module', str(vision_module_path))
    vision_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vision_module)
    sys.modules['veritas.agents.vision_module'] = vision_module

    # Re-export all public symbols from vision.py
    for attr in dir(vision_module):
        if not attr.startswith('_'):
            globals()[attr] = getattr(vision_module, attr)

__all__ = [
    "VisionAgent",
    "VisionPassPriority",
    "should_run_pass",
    "get_confidence_tier",
    "get_pass_prompt",
    "DarkPatternFinding",
    "TemporalFinding",
    "VisionResult",
    "TemporalAnalyzer",
]