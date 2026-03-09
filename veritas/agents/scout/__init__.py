"""Veritas Scout Agent

The "Hands & Legs" of Veritas. Navigates target URLs, captures evidence.
"""

# Direct imports from the actual scout module file
import sys
from pathlib import Path

# Add agents folder to path
_agents_path = str(Path(__file__).resolve().parent)
if _agents_path not in sys.path:
 sys.path.insert(0, _agents_path)

# Clear the module from cache if it exists to force reload
import importlib
if 'scout' in sys.modules:
 del sys.modules['scout']

# Import directly using file path approach
import importlib.util
_scout_module_path = str(Path(__file__).resolve().parent.parent / "scout.py")
_spec = importlib.util.spec_from_file_location("_scout_module", _scout_module_path)
_scout_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scout_module)

# Re-export classes
ScoutResult = _scout_module.ScoutResult
StealthScout = _scout_module.StealthScout
ScoutAgent = StealthScout

__all__ = [
 "ScoutResult",
 "StealthScout",
 "ScoutAgent",
]
