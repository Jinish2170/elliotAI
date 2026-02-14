"""
Veritas Audit Runner — Wraps VeritasOrchestrator for WebSocket streaming.

Captures ##PROGRESS stdout markers from the orchestrator and converts them
into typed WebSocket JSON events for the frontend.

Uses subprocess.Popen + asyncio.run_in_executor for Windows compatibility
(asyncio.create_subprocess_exec raises NotImplementedError on Windows
when the event loop is SelectorEventLoop).
"""

import asyncio
import base64
import functools
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("veritas.audit_runner")


def _find_venv_python() -> str:
    """Locate the .venv Python executable relative to the project root."""
    project_root = Path(__file__).resolve().parent.parent.parent
    if sys.platform == "win32":
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = project_root / ".venv" / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)

    # Fallback to current interpreter
    return sys.executable


class AuditRunner:
    """
    Runs a Veritas audit in a subprocess and streams structured events
    via a callback function (typically WebSocket.send_json).
    """

    def __init__(self, audit_id: str, url: str, tier: str,
                 verdict_mode: str = "expert",
                 security_modules: Optional[list[str]] = None):
        self.audit_id = audit_id
        self.url = url
        self.tier = tier
        self.verdict_mode = verdict_mode
        self.security_modules = security_modules
        self._screenshot_index = 0
        self._findings_sent: set[str] = set()

    async def run(self, send: Callable):
        """
        Run the audit as a subprocess and stream typed events via `send`.
        `send` is an async callable that takes a dict and sends it as JSON.

        Uses subprocess.Popen + run_in_executor to avoid the Windows
        NotImplementedError with asyncio.create_subprocess_exec.
        """
        veritas_dir = Path(__file__).resolve().parent.parent.parent / "veritas"
        python_exe = _find_venv_python()

        cmd = [
            python_exe, "-m", "veritas",
            self.url,
            "--tier", self.tier,
            "--verdict-mode", self.verdict_mode,
            "--json",
        ]

        if self.security_modules:
            cmd.extend(["--security-modules", ",".join(self.security_modules)])

        env = {**os.environ}
        env["PYTHONIOENCODING"] = "utf-8"

        cwd = str(veritas_dir.parent)

        logger.info(f"[{self.audit_id}] Python: {python_exe}")
        logger.info(f"[{self.audit_id}] CWD:    {cwd}")
        logger.info(f"[{self.audit_id}] CMD:    {' '.join(cmd)}")

        # Start subprocess (sync Popen — works on all platforms)
        loop = asyncio.get_running_loop()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        # Parse stdout line-by-line (blocking reads run in thread pool)
        json_buffer: list[str] = []
        collecting_json = False
        start_time = time.time()

        try:
            while True:
                # Read one line in a thread so we don't block the event loop
                raw_line = await loop.run_in_executor(
                    None, process.stdout.readline
                )
                if not raw_line:
                    break  # EOF — subprocess finished writing

                line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")

                if line.startswith("##PROGRESS:"):
                    payload = line[len("##PROGRESS:"):]
                    try:
                        data = json.loads(payload)
                        await self._handle_progress(data, send)
                    except json.JSONDecodeError:
                        pass
                elif line.strip().startswith("{") or collecting_json:
                    collecting_json = True
                    json_buffer.append(line)
                    # Try to parse accumulated JSON
                    try:
                        full_json = "\n".join(json_buffer)
                        result = json.loads(full_json)
                        collecting_json = False
                        json_buffer = []
                        await self._handle_result(result, send)
                    except json.JSONDecodeError:
                        pass

            # Wait for process to finish
            await loop.run_in_executor(None, process.wait)

            # Log stderr if any
            stderr_bytes = await loop.run_in_executor(
                None, process.stderr.read
            )
            if stderr_bytes:
                stderr_text = stderr_bytes.decode("utf-8", errors="replace")
                for stderr_line in stderr_text.strip().splitlines()[-10:]:
                    logger.info(f"[{self.audit_id}] stderr: {stderr_line}")

            # Ensure completion event
            elapsed = time.time() - start_time
            await send({
                "type": "audit_complete",
                "audit_id": self.audit_id,
                "elapsed": round(elapsed, 1),
            })

        except Exception as e:
            logger.error(f"[{self.audit_id}] Runner error: {e}", exc_info=True)
            await send({
                "type": "audit_error",
                "audit_id": self.audit_id,
                "error": str(e),
            })
        finally:
            # Clean up if process is still running
            if process.poll() is None:
                process.terminate()

    async def _handle_progress(self, data: dict, send: Callable):
        """Convert a ##PROGRESS message into typed WebSocket events."""
        phase = data.get("phase", "")
        step = data.get("step", "")
        pct = data.get("pct", 0)
        detail = data.get("detail", "")

        # Map phase names to user-friendly labels
        phase_labels = {
            "init": "Initialization",
            "scout": "Browser Reconnaissance",
            "security": "Security Audit",
            "vision": "Visual Intelligence",
            "graph": "Intelligence Network",
            "judge": "Forensic Judge",
            "complete": "Complete",
            "iteration": "Iteration",
        }

        if step == "start" and phase == "iteration":
            return  # Skip raw iteration markers

        if step in ("navigating", "scanning", "analyzing", "investigating", "deliberating"):
            await send({
                "type": "phase_start",
                "phase": phase,
                "message": detail,
                "pct": pct,
                "label": phase_labels.get(phase, phase.title()),
            })

            # Send log entry
            await send({
                "type": "log_entry",
                "timestamp": time.strftime("%H:%M:%S"),
                "agent": phase_labels.get(phase, phase.title()),
                "message": detail,
                "level": "info",
            })

        elif step == "done":
            summary = {}
            if phase == "scout":
                summary = {
                    "pages": data.get("iteration", 1),
                    "screenshots": data.get("screenshots", 0),
                }
            elif phase == "security":
                summary = {"modules": data.get("modules", [])}
            elif phase == "vision":
                summary = {
                    "findings_count": data.get("findings", 0),
                    "ai_calls": data.get("nim_calls", 0),
                }
            elif phase == "graph":
                summary = {
                    "domain_age_days": data.get("domain_age", "?"),
                    "nodes": data.get("nodes", 0),
                }
            elif phase == "judge":
                summary = {
                    "trust_score": data.get("trust_score", "?"),
                    "risk_level": data.get("risk_level", "?"),
                }

            await send({
                "type": "phase_complete",
                "phase": phase,
                "message": detail,
                "pct": pct,
                "label": phase_labels.get(phase, phase.title()),
                "summary": summary,
            })

            await send({
                "type": "log_entry",
                "timestamp": time.strftime("%H:%M:%S"),
                "agent": phase_labels.get(phase, phase.title()),
                "message": f"Complete — {detail}",
                "level": "info",
            })

        elif step == "error":
            await send({
                "type": "phase_error",
                "phase": phase,
                "message": detail,
                "pct": pct,
                "label": phase_labels.get(phase, phase.title()),
                "error": detail,
            })

            await send({
                "type": "log_entry",
                "timestamp": time.strftime("%H:%M:%S"),
                "agent": phase_labels.get(phase, phase.title()),
                "message": f"Error — {detail}",
                "level": "error",
            })

        elif step == "starting" and phase == "init":
            await send({
                "type": "phase_start",
                "phase": "init",
                "message": detail,
                "pct": 0,
                "label": "Initialization",
            })

    async def _handle_result(self, result: dict, send: Callable):
        """Process the final JSON result from the CLI and send detailed events."""

        # Extract screenshots
        for scout_result in result.get("scout_results", []):
            for i, screenshot_path in enumerate(scout_result.get("screenshots", [])):
                labels = scout_result.get("screenshot_labels", [])
                label = labels[i] if i < len(labels) else f"Screenshot {self._screenshot_index + 1}"

                # Try to read and base64-encode the screenshot
                img_data = None
                p = Path(screenshot_path)
                if p.exists():
                    try:
                        img_data = base64.b64encode(p.read_bytes()).decode("ascii")
                    except Exception:
                        pass

                await send({
                    "type": "screenshot",
                    "url": screenshot_path,
                    "label": label,
                    "index": self._screenshot_index,
                    "data": img_data,
                })
                self._screenshot_index += 1

        # Extract site type
        site_type = result.get("site_type", "")
        if site_type:
            await send({
                "type": "site_type",
                "site_type": site_type,
                "confidence": result.get("site_type_confidence", 0),
            })

        # Extract security results
        for module_name, module_result in result.get("security_results", {}).items():
            await send({
                "type": "security_result",
                "module": module_name,
                "result": module_result,
            })

        # Extract findings from vision
        vision = result.get("vision_result", {}) or {}
        for finding in vision.get("findings", []):
            fid = finding.get("pattern_type", "") + str(finding.get("confidence", 0))
            if fid not in self._findings_sent:
                self._findings_sent.add(fid)
                await send({
                    "type": "finding",
                    "finding": {
                        "id": fid,
                        "category": finding.get("category", "unknown"),
                        "pattern_type": finding.get("pattern_type", "unknown"),
                        "severity": finding.get("severity", "medium"),
                        "confidence": finding.get("confidence", 0.5),
                        "description": finding.get("description", ""),
                        "plain_english": finding.get("plain_english",
                                                     finding.get("description", "")),
                    },
                })

        # Extract judge decision
        judge = result.get("judge_decision", {}) or {}
        trust_result = judge.get("trust_score_result", {}) or {}
        signal_scores = trust_result.get("signal_scores", {}) or {}
        overrides = trust_result.get("overrides_applied", []) or []

        # Stats update
        n_screenshots = sum(
            len(sr.get("screenshots", []))
            for sr in result.get("scout_results", [])
        )
        n_findings = len(vision.get("findings", []))

        await send({
            "type": "stats_update",
            "stats": {
                "pages_scanned": len(result.get("investigated_urls", [])),
                "screenshots": n_screenshots,
                "findings": n_findings,
                "ai_calls": result.get("nim_calls_used", 0),
                "security_checks": len(result.get("security_results", {})),
                "elapsed_seconds": result.get("elapsed_seconds", 0),
            },
        })

        # Full result
        await send({
            "type": "audit_result",
            "result": {
                "url": result.get("url", self.url),
                "status": result.get("status", "unknown"),
                "trust_score": trust_result.get("final_score", 0),
                "risk_level": trust_result.get("risk_level", "unknown"),
                "signal_scores": signal_scores,
                "overrides": overrides,
                "narrative": judge.get("narrative", ""),
                "recommendations": judge.get("recommendations", []),
                "findings": vision.get("findings", []),
                "dark_pattern_summary": vision.get("dark_pattern_summary", {}),
                "security_results": result.get("security_results", {}),
                "site_type": result.get("site_type", ""),
                "site_type_confidence": result.get("site_type_confidence", 0),
                "domain_info": {
                    "age_days": (result.get("graph_result") or {}).get("domain_age_days"),
                    "registrar": (result.get("graph_result") or {}).get("registrar"),
                    "country": (result.get("graph_result") or {}).get("hosting_country"),
                    "ip": (result.get("graph_result") or {}).get("ip_address"),
                    "ssl_issuer": (result.get("graph_result") or {}).get("ssl_issuer"),
                    "inconsistencies": (result.get("graph_result") or {}).get("inconsistencies", []),
                    "entity_verified": (result.get("graph_result") or {}).get("entity_verified", False),
                },
                "pages_scanned": len(result.get("investigated_urls", [])),
                "screenshots_count": n_screenshots,
                "elapsed_seconds": result.get("elapsed_seconds", 0),
                "errors": result.get("errors", []),
                "verdict_mode": result.get("verdict_mode", "expert"),
            },
        })


def generate_audit_id() -> str:
    """Generate a short unique audit ID."""
    return f"vrts_{uuid.uuid4().hex[:8]}"
