"""
Security Module Utilities - Discovery and Tier Execution.

Provides auto-discovery, tier grouping, and parallel execution of
security modules with timeout handling.

Main Functions:
    - get_all_security_modules(): Discover all SecurityModule subclasses
    - group_modules_by_tier(): Group modules by execution tier
    - execute_tier(): Execute modules in the same tier in parallel
"""

import asyncio
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List

from .base import SecurityModule, SecurityFinding, SecurityTier


logger = logging.getLogger("veritas.analysis.security.utils")


# ============================================================
# Module Auto-Discovery
# ============================================================

def get_all_security_modules(package_path: str = "veritas.analysis.security") -> List[type[SecurityModule]]:
    """
    Auto-discover all SecurityModule subclasses in a package.

    Scans the specified package for all classes that inherit from
    SecurityModule and returns them in a list.

    Args:
        package_path: Python package path to scan (default: veritas.analysis.security)

    Returns:
        List of SecurityModule subclass types
    """
    modules = []

    try:
        # Import the package
        package = importlib.import_module(package_path)
        package_dir = Path(package.__file__).parent

        # Scan all Python files in the package directory
        for file_path in package_dir.glob("*.py"):
            # Skip __init__.py and base.py (they don't contain modules)
            if file_path.name in ("__init__.py", "base.py", "utils.py"):
                continue

            # Import the module
            module_name = f"{package_path}.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)

                # Find all SecurityModule subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a SecurityModule subclass (but not the base class itself)
                    if (
                        issubclass(obj, SecurityModule)
                        and obj is not SecurityModule
                        and obj.__module__ == module_name
                    ):
                        # Check if module is discoverable
                        if obj.is_discoverable():
                            modules.append(obj)
                            logger.debug(f"Discovered security module: {name}")
            except Exception as e:
                logger.warning(f"Failed to import module {module_name}: {e}")

        logger.info(f"Discovered {len(modules)} security modules from {package_path}")

    except Exception as e:
        logger.error(f"Failed to discover security modules: {e}")

    return modules


def group_modules_by_tier(modules: List[type[SecurityModule]]) -> Dict[SecurityTier, List[type[SecurityModule]]]:
    """
    Group security modules by their execution tier.

    Args:
        modules: List of SecurityModule classes

    Returns:
        Dictionary mapping SecurityTier to list of module classes:
        {
            SecurityTier.FAST: [class1, class2, ...],
            SecurityTier.MEDIUM: [class3, ...],
            SecurityTier.DEEP: [class4, ...]
        }
    """
    grouped = {
        SecurityTier.FAST: [],
        SecurityTier.MEDIUM: [],
        SecurityTier.DEEP: [],
    }

    for module_class in modules:
        try:
            # Get module instance to access tier property
            module_info = module_class.get_module_info()
            tier_str = module_info.get("tier", "MEDIUM")
            tier = SecurityTier(tier_str)

            grouped[tier].append(module_class)
        except Exception as e:
            logger.warning(f"Failed to group module {module_class.__name__}: {e}, defaulting to MEDIUM")
            grouped[SecurityTier.MEDIUM].append(module_class)

    # Log grouping results
    for tier, tier_modules in grouped.items():
        module_names = [m.__name__ for m in tier_modules]
        logger.debug(f"Tier {tier.value}: {len(tier_modules)} modules ({module_names})")

    return grouped


# ============================================================
# Tier Execution (Parallel)
# ============================================================

async def execute_tier(
    modules: List[type[SecurityModule]],
    url: str,
    page_content: str = None,
    headers: dict = None,
    dom_meta: dict = None,
) -> List[SecurityFinding]:
    """
    Execute all modules in the same tier in parallel.

    Uses asyncio.gather to run all modules concurrently with
    per-module timeout and exception handling.

    Args:
        modules: List of SecurityModule classes (must be in same tier)
        url: Target URL to analyze
        page_content: Optional HTML page content
        headers: Optional HTTP response headers dict
        dom_meta: Optional DOM metadata

    Returns:
        Flattened list of all SecurityFinding objects from all modules
    """
    all_findings: List[SecurityFinding] = []

    if not modules:
        logger.warning("No modules to execute in this tier")
        return all_findings

    # Create tasks for each module
    tasks = []
    for module_class in modules:
        # Create module instance lazily before each execution
        instance = module_class()
        timeout = instance.timeout

        # Create timeout-wrapped task
        task = _execute_module_with_timeout(
            instance, url, page_content, headers, dom_meta, timeout
        )
        tasks.append(task)

    # Execute all tasks in parallel
    # asyncio.gather() returns results or exceptions in order
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for module_class, result in zip(modules, results):
        if isinstance(result, Exception):
            logger.error(f"Module {module_class.__name__} failed: {result}")
        elif result is not None:
            # result is List[SecurityFinding]
            all_findings.extend(result)
            logger.debug(f"Module {module_class.__name__} returned {len(result)} findings")

    logger.info(f"Tier execution complete: {len(all_findings)} total findings from {len(modules)} modules")

    return all_findings


# ============================================================
# Module Execution with Timeout
# ============================================================

async def _execute_module_with_timeout(
    module: SecurityModule,
    url: str,
    page_content: str = None,
    headers: dict = None,
    dom_meta: dict = None,
    timeout: int = 10,
) -> List[SecurityFinding]:
    """
    Execute a security module with timeout handling.

    Wraps the module's analyze() method in asyncio.timeout() and
    gracefully handles exceptions.

    Args:
        module: SecurityModule instance
        url: Target URL to analyze
        page_content: Optional HTML page content
        headers: Optional HTTP response headers dict
        dom_meta: Optional DOM metadata
        timeout: Timeout in seconds

    Returns:
        List of SecurityFinding objects (empty if timeout or error)
    """
    try:
        # Use asyncio.timeout for Python 3.11+
        async with asyncio.timeout(timeout):
            return await module.analyze(url, page_content, headers, dom_meta)

    except TimeoutError:
        logger.error(f"Module {module.category_id} timed out after {timeout}s")
        return []
    except Exception as e:
        logger.error(f"Module {module.category_id} failed: {e}")
        return []


# ============================================================
# Utility Functions
# ============================================================

async def execute_all_modules(
    url: str,
    page_content: str = None,
    headers: dict = None,
    dom_meta: dict = None,
    package_path: str = "veritas.analysis.security",
) -> Dict[SecurityTier, List[SecurityFinding]]:
    """
    Execute all discovered security modules grouped by tier.

    Convenience function that discovers, groups, and executes all
    modules in their respective tiers.

    Args:
        url: Target URL to analyze
        page_content: Optional HTML page content
        headers: Optional HTTP response headers dict
        dom_meta: Optional DOM metadata
        package_path: Python package path to scan for modules

    Returns:
        Dictionary mapping SecurityTier to list of findings
    """
    # Discover all modules
    modules = get_all_security_modules(package_path)

    # Group by tier
    grouped = group_modules_by_tier(modules)

    # Execute each tier
    results = {}
    for tier, tier_modules in grouped.items():
        if tier_modules:
            logger.info(f"Executing {tier.value} tier with {len(tier_modules)} modules")
            findings = await execute_tier(tier_modules, url, page_content, headers, dom_meta)
            results[tier] = findings
        else:
            logger.debug(f"No modules in {tier.value} tier")
            results[tier] = []

    return results


def get_module_timeout(tier: SecurityTier) -> int:
    """
    Get suggested timeout for a given tier.

    Args:
        tier: SecurityTier enum value

    Returns:
        Timeout in seconds
    """
    return tier.timeout_suggestion
