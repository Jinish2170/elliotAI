"""
Backend Package for Elliot FastAPI Server

Provides HTTP API endpoints and WebSocket streaming for Elliot audits.
"""

import sys
import multiprocessing

# Set spawn context ONCE at module import time (required for Windows)
if sys.platform == "win32":
    multiprocessing.set_start_method('spawn', force=True)
