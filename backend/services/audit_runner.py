import asyncio
import base64
import json
import logging
import multiprocessing as mp
import os
import queue
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

project_root = Path(__file__).resolve().parent.parent.parent

from veritas.core.ipc import IPC_MODE_QUEUE, IPC_MODE_STDOUT, determine_ipc_mode, serialize_queue

logger = logging.getLogger("veritas.audit_runner")


def _find_venv_python() -> str:
    if sys.platform == "win32":
        path = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        path = project_root / ".venv" / "bin" / "python"
    return str(path) if path.exists() else sys.executable


class AuditRunner:
    def __init__(self, audit_id: str, url: str, tier: str, verdict_mode: str = "expert", security_modules: Optional[list[str]] = None):
        self.audit_id = audit_id
        self.url = url
        self.tier = tier
        self.verdict_mode = verdict_mode
        self.security_modules = security_modules
        self.ipc_mode = determine_ipc_mode(cli_use_queue_ipc=False, cli_use_stdout=False)
        self.progress_queue: Optional[mp.Queue] = None
        self._mgr = None
        self._result_sent = False
        self._findings_sent: set[str] = set()
        self._screenshot_index = 0

    async def _read_queue_and_stream(self, send: Callable):
        if self.progress_queue is None:
            return
        while True:
            try:
                event = await asyncio.to_thread(self.progress_queue.get, timeout=1.0)
                if hasattr(event, "__dict__"):
                    payload = {
                        "type": getattr(event, "type", "progress"),
                        "phase": getattr(event, "phase", ""),
                        "step": getattr(event, "step", ""),
                        "pct": getattr(event, "pct", 0),
                        "detail": getattr(event, "detail", ""),
                        "summary": getattr(event, "summary", {}),
                    }
                else:
                    payload = event
                await self._handle_progress(payload, send)
            except queue.Empty:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("[%s] queue read error: %s", self.audit_id, exc)

    async def run(self, send: Callable):
        # Wrap send to add sequence numbers
        sequence_counter = {"cnt": 0}
        original_send = send  # Capture BEFORE reassignment
        async def seq_send(event: dict):
            sequence_counter["cnt"] += 1
            event["sequence"] = sequence_counter["cnt"]
            await original_send(event)  # Use original to avoid recursion
        send = seq_send
        # --- PRE-FLIGHT REACHABILITY CHECK ---
        import urllib.request
        from urllib.error import URLError
        
        await send({"type": "phase_start", "phase": "scout", "message": "Pre-flight verification..."})
        try:
            # 5-second DNS/HEAD check to fail fast for garbage URLs
            req = urllib.request.Request(self.url, method="HEAD", headers={'User-Agent': 'Veritas/(+https://github.com)'})
            await asyncio.to_thread(urllib.request.urlopen, req, timeout=5.0)
        except URLError as e:
            # Revert to standard GET in case HEAD is blocked
            try:
                if "HTTP Error" in str(e) or "HTTP Error 405" in str(e) or "HTTP Error 403" in str(e):
                    pass # We reached the server, let Playwright handle the heavy lifting
                else:
                    req = urllib.request.Request(self.url, headers={'User-Agent': 'Veritas/(+https://github.com)'})
                    await asyncio.to_thread(urllib.request.urlopen, req, timeout=5.0)
            except Exception as e2:
                err_msg = f"FATAL PRE-FLIGHT: Target {self.url} is unreachable or invalid. ({str(e2)})"
                logger.error(f"[{self.audit_id}] {err_msg}")
                await send({"type": "phase_error", "phase": "scout", "error": err_msg})
                # Critical: Emit audit_error immediately so Frontend Terminals abort
                await send({"type": "audit_error", "audit_id": self.audit_id, "error": err_msg})
                return

        cmd = [
            _find_venv_python(),
            "-m",
            "veritas",
            self.url,
            "--tier",
            self.tier,
            "--verdict-mode",
            self.verdict_mode,
            "--json",
        ]
        if self.security_modules:
            cmd.extend(["--security-modules", ",".join(self.security_modules)])

        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        if self.ipc_mode == IPC_MODE_QUEUE:
            try:
                mp.set_start_method("spawn", force=True)
                self._mgr = mp.Manager()
                self.progress_queue = self._mgr.Queue(maxsize=1000)
                fd, serialized = serialize_queue(self.progress_queue)
                env["AUDIT_QUEUE_FD"] = str(fd)
                env["AUDIT_QUEUE_KEY"] = serialized
                cmd.append("--use-queue-ipc")
            except Exception as exc:
                logger.warning("[%s] queue setup failed, using stdout: %s", self.audit_id, exc)
                self.ipc_mode = IPC_MODE_STDOUT

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            env=env,
        )
        loop = asyncio.get_running_loop()
        stderr_lines: list[str] = []
        stdout_lines: list[str] = []
        buffer: list[str] = []
        collecting = False
        start_time = time.time()

        async def drain_stderr():
            while True:
                raw = await loop.run_in_executor(None, process.stderr.readline)
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line:
                    stderr_lines.append(line)

        stderr_task = asyncio.create_task(drain_stderr())
        queue_task = asyncio.create_task(self._read_queue_and_stream(send)) if self.ipc_mode == IPC_MODE_QUEUE else None
        try:
            while True:
                raw = await loop.run_in_executor(None, process.stdout.readline)
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                stdout_lines.append(line)
                if line.startswith("##PROGRESS:"):
                    try:
                        await self._handle_progress(json.loads(line[len("##PROGRESS:"):]), send)
                    except json.JSONDecodeError:
                        pass
                    continue
                if line.lstrip().startswith("{") or collecting:
                    collecting = True
                    buffer.append(line)
                    try:
                        payload = json.loads("\n".join(buffer))
                    except json.JSONDecodeError:
                        continue
                    collecting = False
                    buffer = []
                    await self._handle_result(payload, send)

            await loop.run_in_executor(None, process.wait)
            if queue_task is not None and not queue_task.done():
                queue_task.cancel()
            try:
                await asyncio.wait_for(stderr_task, timeout=5)
            except Exception:
                stderr_task.cancel()
            if not self._result_sent:
                payload = self._extract_last_json_from_stdout(stdout_lines)
                if payload is not None:
                    await self._handle_result(payload, send)
            if self._result_sent:
                await send({"type": "audit_complete", "audit_id": self.audit_id, "elapsed": round(time.time() - start_time, 1)})
            else:
                await send({"type": "audit_error", "audit_id": self.audit_id, "error": "Audit finished but result JSON could not be parsed"})
        except Exception as exc:
            logger.error("[%s] runner error: %s", self.audit_id, exc, exc_info=True)
            await send({"type": "audit_error", "audit_id": self.audit_id, "error": str(exc)})
        finally:
            if process.poll() is None:
                process.terminate()
            if self._mgr is not None:
                self._mgr.shutdown()
                self._mgr = None
            for line in stderr_lines[-20:]:
                logger.info("[%s] stderr: %s", self.audit_id, line)

    async def _handle_progress(self, data: dict, send: Callable):
        if data.get("type") and data.get("type") != "progress":
            # Track live-emitted findings so we don't duplicate them at the end
            if data.get("type") == "vision_pass_findings":
                for f in data.get("findings", []):
                    if isinstance(f, dict) and "id" in f:
                        self._findings_sent.add(f["id"])
            await send(data)
            return
        phase = data.get("phase", "")
        step = data.get("step", "")
        pct = data.get("pct", 0)
        detail = data.get("detail", "")
        label = {"init": "Initialization", "scout": "Browser Reconnaissance", "security": "Security Audit", "vision": "Visual Intelligence", "graph": "Intelligence Network", "judge": "Forensic Judge"}.get(phase, phase.title())
        if step in {"navigating", "scanning", "analyzing", "investigating", "deliberating", "starting"}:
            await send({"type": "phase_start", "phase": phase, "message": detail, "pct": pct, "label": label})
            await send({"type": "agent_personality", "agent": phase, "context": "working", "timestamp": time.strftime("%H:%M:%S"), "params": {"phase": phase, "step": step, "detail": detail}})
            await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": label, "message": detail, "level": "info"})
        elif step == "done":
            summary_data = data.get("summary", {})
            # Pack any extra keys into summary so frontend state gets them
            for k, v in data.items():
                if k not in ["type", "phase", "step", "pct", "detail", "summary"]:
                    summary_data[k] = v

            await send({"type": "phase_complete", "phase": phase, "message": detail, "pct": pct, "label": label, "summary": summary_data or {}})
            
            # EARLY STREAM INJECTION
            if phase == "security" and "security_results" in summary_data:
                res = {"security_results": summary_data["security_results"]}
                await send({
                    "type": "cvss_metrics",
                    "metrics": [{"name": k, "value": str(v), "severity": "HIGH"} for k, v in res["security_results"].get("cvss_metrics", {}).items() if k != "base_score"],
                    "base_score": 0.0
                })
                for map_entry in res["security_results"].get("mitre_mappings", []):
                    await send({"type": "mitre_technique_mapped", "technique": map_entry.get("technique") if isinstance(map_entry, dict) else map_entry})
                    
            if phase == "graph" and "graph_result" in summary_data:
                g_data = summary_data["graph_result"].get("graph_data")
                if g_data and isinstance(g_data, dict):
                    nodes = g_data.get("nodes", []) or []
                    edges = g_data.get("edges", []) or []
                    density = len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0
                    kg = {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges), "graph_density": density, "avg_clustering": 0.0, "largest_component_size": len(nodes), "isolated_nodes": 0 if edges else max(0, len(nodes) - 1)}
                    await send({"type": "knowledge_graph", "graph": kg})

            await send({"type": "agent_personality", "agent": phase, "context": "complete", "timestamp": time.strftime("%H:%M:%S"), "params": {"phase": phase, "success": True, "summary": detail}})
            await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": label, "message": f"Complete - {detail}", "level": "info"})
        elif step == "error":
            await send({"type": "phase_error", "phase": phase, "message": detail, "pct": pct, "error": detail})
            await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": label, "message": f"Error - {detail}", "level": "error"})

    def _vision_findings(self, result: dict) -> list[dict]:
        vision = result.get("vision_result") or {}
        findings = vision.get("findings") or vision.get("dark_patterns") or []
        out = []
        for i, item in enumerate(findings):
            if not isinstance(item, dict):
                continue
            pattern_type = item.get("pattern_type") or item.get("sub_type") or "unknown"
            category = item.get("category") or item.get("category_id") or "unknown"
            description = item.get("description") or item.get("evidence") or ""
            out.append({**item, "id": item.get("id") or f"{pattern_type}_{i}", "pattern_type": pattern_type, "category": category, "description": description, "plain_english": item.get("plain_english") or description})
        return out

    def _security_modules(self, result: dict) -> list[tuple[str, dict]]:
        modules = result.get("security_results") or {}
        if not isinstance(modules, dict):
            return []
        return [(name, value if isinstance(value, dict) else {"value": value}) for name, value in modules.items() if isinstance(name, str) and not name.startswith("_")]

    def _iso_timestamp(self) -> str:
        return datetime.now().isoformat()

    def _severity_rank(self, severity: str) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(str(severity).lower(), 0)

    def _infer_module_severity(self, module_result: dict) -> str:
        if not isinstance(module_result, dict):
            return "low"
        explicit = module_result.get("severity")
        if explicit:
            return str(explicit).lower()
        highest = "low"
        findings = module_result.get("findings") or []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            severity = str(finding.get("severity", "low")).lower()
            if self._severity_rank(severity) > self._severity_rank(highest):
                highest = severity
        if module_result.get("is_phishing") is True:
            return "critical"
        if module_result.get("tor2web_exposure") is True:
            return "high"
        return highest

    def _security_module_event(self, module_name: str, module_result: dict) -> dict:
        findings = module_result.get("findings") if isinstance(module_result, dict) else []
        findings_count = len(findings) if isinstance(findings, list) else 0
        composite_score = module_result.get("score")
        if composite_score is None:
            composite_score = module_result.get("overall_score")
        if composite_score is None:
            composite_score = module_result.get("risk_score")
        if composite_score is None:
            composite_score = 1.0
        return {
            "module_name": module_name,
            "category": "owasp" if module_name.startswith("owasp_") else module_name,
            "findings_count": findings_count,
            "severity": self._infer_module_severity(module_result).upper(),
            "composite_score": composite_score,
            "execution_time_ms": module_result.get("analysis_time_ms", 0),
            "findings": findings if isinstance(findings, list) else [],
            "details": module_result,
            "recommendations": module_result.get("recommendations", []),
        }

    def _summary(self, result: dict) -> dict:
        judge = result.get("judge_decision") or {}
        trust = judge.get("trust_score_result") or {}
        graph = result.get("graph_result") or {}
        signal_scores = trust.get("signal_scores", {}) or {}
        if not signal_scores:
            for key, data in (trust.get("sub_signals", {}) or {}).items():
                if isinstance(data, dict):
                    raw = data.get("raw_score", 0)
                    try:
                        raw = float(raw)
                    except (TypeError, ValueError):
                        raw = 0.0
                    signal_scores[key] = round(raw * 100 if raw <= 1 else raw, 1)
        findings = self._vision_findings(result)
        dark_pattern_summary = judge.get("dark_pattern_summary")
        if not dark_pattern_summary:
            dark_pattern_summary = {"findings": findings}
        elif isinstance(dark_pattern_summary, list):
            dark_pattern_summary = {"findings": dark_pattern_summary}
        screenshots_count = sum(len((item or {}).get("screenshots", [])) for item in result.get("scout_results", []) if isinstance(item, dict))
        return {
            "url": result.get("url", self.url),
            "status": result.get("status", "unknown"),
            "audit_tier": result.get("audit_tier", self.tier),
            "verdict_mode": result.get("verdict_mode", self.verdict_mode),
            "trust_score": trust.get("final_score"),
            "risk_level": trust.get("risk_level"),
            "narrative": judge.get("narrative", ""),
            "signal_scores": signal_scores,
            "dark_pattern_summary": dark_pattern_summary,
            "recommendations": judge.get("recommendations", []),
            "green_flags": judge.get("green_flags", []),
            "security_results": result.get("security_results", {}),
            "security_summary": result.get("security_summary", {}),
            "site_type": result.get("site_type", ""),
            "site_type_confidence": result.get("site_type_confidence", 0.0),
            "domain_info": {
                "age_days": (graph.get("domain_intel") or {}).get("age_days") or graph.get("domain_age_days"),
                "registrar": (graph.get("domain_intel") or {}).get("registrar"),
                "ip": (graph.get("domain_intel") or {}).get("ip_address"),
                "ssl_issuer": (graph.get("domain_intel") or {}).get("ssl_issuer"),
                "country": (graph.get("ip_geolocation") or {}).get("country"),
                "inconsistencies": [(item.get("explanation") if isinstance(item, dict) else str(item)) for item in (graph.get("inconsistencies") or [])],
                "entity_verified": any(isinstance(v, dict) and v.get("status") == "confirmed" for v in (graph.get("verifications") or [])),
            },
            "pages_scanned": len(result.get("investigated_urls") or result.get("scout_results") or []),
            "screenshots_count": screenshots_count,
            "elapsed_seconds": result.get("elapsed_seconds", 0),
            "errors": result.get("errors", []),
        }

    async def _handle_result(self, result: dict, send: Callable):
        self._result_sent = True
        findings = self._vision_findings(result)
        summary = self._summary(result)
        graph = result.get("graph_result") or {}
        judge = result.get("judge_decision") or {}
        trust = judge.get("trust_score_result") or {}
        timestamp = self._iso_timestamp()
        scout_results = [item for item in (result.get("scout_results") or []) if isinstance(item, dict)]

        visited_urls: list[str] = []
        total_navigation_time_ms = 0
        for scout_result in scout_results:
            scout_url = scout_result.get("url") or summary["url"]
            visited_urls.append(scout_url)
            await send({"type": "navigation_start", "url": scout_url, "timestamp": timestamp})
            await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": "Browser Reconnaissance", "message": f"Navigating to {scout_url}", "level": "info"})
            await send({
                "type": "page_scanned",
                "url": scout_url,
                "page_title": scout_result.get("page_title", ""),
                "navigation_time_ms": scout_result.get("navigation_time_ms", 0),
                "timestamp": timestamp,
            })
            total_navigation_time_ms += int(scout_result.get("navigation_time_ms", 0) or 0)

            forms = scout_result.get("forms_detected") or []
            if isinstance(forms, list) and forms:
                normalized_forms = []
                for idx, form in enumerate(forms):
                    if not isinstance(form, dict):
                        continue
                    inputs = form.get("inputs", [])
                    normalized_forms.append({
                        "id": form.get("id") or f"form_{idx}",
                        "action": form.get("action"),
                        "method": form.get("method", "GET"),
                        "inputs": len(inputs) if isinstance(inputs, list) else 0,
                        "has_password": bool(form.get("has_password") or form.get("hasPassword")),
                    })
                if normalized_forms:
                    await send({
                        "type": "form_detected",
                        "count": len(normalized_forms),
                        "forms": normalized_forms,
                        "timestamp": timestamp,
                    })
                    await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": "Browser Reconnaissance", "message": f"Detected {len(normalized_forms)} forms", "level": "info"})

            captcha_detected = bool(scout_result.get("captcha_detected"))
            await send({
                "type": "captcha_detected",
                "detected": captcha_detected,
                "captcha_type": "challenge" if captcha_detected else None,
                "confidence": 1.0 if captcha_detected else 0.0,
                "timestamp": timestamp,
            })
            if captcha_detected:
                await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": "Browser Reconnaissance", "message": f"CAPTCHA detected", "level": "warning"})

            await send({
                "type": "navigation_complete",
                "url": scout_url,
                "status": scout_result.get("status", "SUCCESS"),
                "duration_ms": scout_result.get("navigation_time_ms", 0),
                "screenshots_count": len(scout_result.get("screenshots", []) or []),
                "timestamp": timestamp,
            })
            await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": "Browser Reconnaissance", "message": f"Navigation complete in {scout_result.get('navigation_time_ms', 0)}ms", "level": "info"})

        if visited_urls:
            await send({
                "type": "exploration_path",
                "base_url": summary["url"],
                "visited_urls": visited_urls,
                "breadcrumbs": visited_urls,
                "total_pages": len(visited_urls),
                "total_time_ms": total_navigation_time_ms,
            })

        for scout_result in scout_results:
            labels = scout_result.get("screenshot_labels", []) or []
            for i, screenshot_path in enumerate(scout_result.get("screenshots", []) or []):
                label = labels[i] if i < len(labels) else f"Screenshot {self._screenshot_index + 1}"
                data = None
                path = Path(screenshot_path)
                if path.exists():
                    try:
                        data = base64.b64encode(path.read_bytes()).decode("ascii")
                    except Exception:
                        data = None
                await send({"type": "screenshot", "url": screenshot_path, "label": label, "index": self._screenshot_index, "data": data})
                self._screenshot_index += 1

        if summary["site_type"]:
            await send({"type": "site_type", "site_type": summary["site_type"], "confidence": summary["site_type_confidence"]})

        for module_name, module_result in self._security_modules(result):
            await send({"type": "security_result", "module": module_name, "result": module_result})
            await send({"type": "security_module_result", "result": self._security_module_event(module_name, module_result)})
            if module_name.startswith("owasp_"):
                await send({"type": "owasp_module_result", "result": {"module": module_name, **module_result}})
            if module_name == "darknet_analysis":
                await send({"type": "darknet_analysis_result", "result": module_result})
                for threat in module_result.get("marketplace_threats", []) or []:
                    if isinstance(threat, dict):
                        await send({"type": "marketplace_threat", "threat": threat})
                        if threat.get("status") == "exit_scam":
                            await send({
                                "type": "exit_scam_detected",
                                "marketplace": threat.get("marketplace", "unknown"),
                                "shutdown_date": threat.get("shutdown_date") or threat.get("date"),
                            })
                if module_result.get("tor2web_exposure"):
                    await send({
                        "type": "tor2web_anonymous_breach",
                        "threat": {
                            "gateway_domains": ["tor2web"],
                            "de_anon_risk": "high",
                            "recommendation": "Use direct TOR Browser for .onion access.",
                            "anonymity_breach": "TOR gateway exposure detected",
                        },
                    })

        for finding in findings:
            if finding["id"] not in self._findings_sent:
                self._findings_sent.add(finding["id"])
                # Pack cvss_score and cwe_id if available (Phase 10)
                await send({"type": "finding", "finding": {
                    "id": finding["id"], 
                    "category": finding["category"], 
                    "pattern_type": finding["pattern_type"], 
                    "severity": finding.get("severity", "medium"), 
                    "confidence": finding.get("confidence", 0.0), 
                    "description": finding["description"], 
                    "plain_english": finding.get("plain_english", finding["description"]),
                    "cwe_id": finding.get("cwe_id"),
                    "cvss_score": finding.get("cvss_score")
                }})
            await send({"type": "dark_pattern_finding", "finding": {
                "category": finding["category"], 
                "pattern_type": finding["pattern_type"], 
                "severity": finding.get("severity", "medium"), 
                "confidence": finding.get("confidence", 0.0), 
                "description": finding["description"], 
                "plain_english": finding.get("plain_english", finding["description"]), 
                "screenshot_path": finding.get("screenshot_path", ""),
                "cwe_id": finding.get("cwe_id"),
                "cvss_score": finding.get("cvss_score")
            }})

        for temporal in (result.get("vision_result") or {}).get("temporal_findings", []) or []:
            if isinstance(temporal, dict):
                await send({"type": "temporal_finding", "finding": temporal})

        for source_name, source_result in (graph.get("osint_sources") or {}).items():
            if source_name == "_consensus" or not isinstance(source_result, dict):
                continue
            payload = {"source": source_name, **source_result}
            await send({"type": "osint_result", "result": payload})
            if source_name.startswith("darknet_") or "tor2web" in source_name:
                await send({"type": "darknet_threat", "threat": {"source": source_name, "data": payload.get("data"), "confidence": payload.get("confidence_score", 0.0)}})

        for indicator in graph.get("osint_indicators", []) or []:
            await send({"type": "ioc_indicator", "indicator": indicator})
            
        for technique in graph.get("cti_techniques", []) or []:
            await send({"type": "mitre_technique_mapped", "technique": technique})

        if graph.get("threat_attribution"):
            await send({"type": "threat_attribution", "attribution": graph.get("threat_attribution")})

        for verification in graph.get("verifications", []) or []:
            if isinstance(verification, dict):
                await send({"type": "verification_result", "verification": verification})

        for inconsistency in graph.get("inconsistencies", []) or []:
            if isinstance(inconsistency, dict):
                await send({"type": "graph_inconsistency", "inconsistency": inconsistency})

        if self._has_graph_data(result):
            knowledge_graph = await self._construct_knowledge_graph(result, trust.get("final_score", 0) or 0)
            await send({"type": "knowledge_graph", "graph": knowledge_graph})
            await send({"type": "graph_analysis", "analysis": self._calculate_graph_analysis(knowledge_graph)})

        # Handle Phase 9 Dual Verdict extraction
        dual = judge.get("dual_verdict")
        if dual:
            if hasattr(dual, 'technical'):
                technical = dual.technical.to_dict() if hasattr(dual.technical, 'to_dict') else dual.technical
                nontechnical = dual.non_technical.to_dict() if hasattr(dual.non_technical, 'to_dict') else dual.non_technical
            elif isinstance(dual, dict):
                technical = dual.get("technical", {})
                nontechnical = dual.get("non_technical", {})
            else:
                technical = judge.get("technical_verdict") or {}
                nontechnical = judge.get("non_technical_verdict") or {}
        else:
            technical = judge.get("technical_verdict") or {"risk_level": trust.get("risk_level", "unknown"), "trust_score": trust.get("final_score", 0), "summary": judge.get("narrative", judge.get("reason", "")), "recommendations": judge.get("recommendations", [])}
            nontechnical = judge.get("non_technical_verdict") or {"risk_level": trust.get("risk_level", "unknown"), "summary": judge.get("simple_narrative") or judge.get("narrative", ""), "actionable_advice": judge.get("simple_recommendations") or judge.get("recommendations", []), "green_flags": judge.get("green_flags", [])}
        
        # Explicit Phase 9 CWE/CVSS parsing for frontend UI states
        for cwe in technical.get("cwe_entries", []) or []:
            if isinstance(cwe, dict):
                cve_payload = {
                    "cve_id": f"CWE-{cwe.get('cwe_id', 'Unknown')}",
                    "name": cwe.get("name", "Unknown CWE"),
                    "description": f"Common Weakness Enumeration: {cwe.get('name', 'Unknown')}",
                    "severity": "HIGH" if cwe.get("score", 0) > 7 else "MEDIUM",
                    "cwe_id": str(cwe.get("cwe_id", ""))
                }
                await send({"type": "cve_detected", "cve": cve_payload})

        cvss_metrics = technical.get("cvss_metrics")
        if isinstance(cvss_metrics, dict):
            mapped_metrics = [{"name": k, "value": str(v), "severity": "HIGH"} for k, v in cvss_metrics.items() if k != "base_score"]
            await send({
                "type": "cvss_metrics", 
                "metrics": mapped_metrics, 
                "base_score": cvss_metrics.get("base_score", technical.get("cvss_score", 0.0))
            })

        await send({"type": "verdict_technical", "verdict": technical})
        await send({"type": "verdict_nontechnical", "verdict": nontechnical})
        await send({"type": "dual_verdict_complete", "dual_verdict": {"verdict_technical": technical, "verdict_nontechnical": nontechnical, "metadata": {"timestamp": datetime.now().isoformat(), "audit_id": self.audit_id}}})

        if summary["green_flags"]:
            await send({"type": "green_flags", "flags": summary["green_flags"], "green_flags": summary["green_flags"]})

        await send({
            "type": "stats_update",
            "stats": {
                "pages_scanned": summary["pages_scanned"],
                "screenshots": summary["screenshots_count"],
                "findings": len(findings),
                "findings_detected": len(findings),
                "ai_calls": (result.get("vision_result") or {}).get("nim_calls_made", 0),
                "security_checks": len(self._security_modules(result)),
                "elapsed_seconds": summary["elapsed_seconds"],
                "duration_seconds": summary["elapsed_seconds"],
            },
        })
        for performance in self._calculate_agent_performance(result):
            await send({"type": "agent_performance", "performance": performance})

        # Build enriched audit_result with trust_score_result and dual_verdict included
        enriched_summary = {
            **summary,
            # Include trust_score_result for direct access in frontend
            "trust_score_result": trust if trust else None,
            # Include dual_verdict for verdict display
            "dual_verdict": judge.get("dual_verdict") or {
                "verdict_technical": technical,
                "verdict_nontechnical": nontechnical,
            },
            # Include judge_decision for full access
            "judge_decision": {
                "action": judge.get("action", "RENDER_VERDICT"),
                "narrative": judge.get("narrative", ""),
                "recommendations": judge.get("recommendations", []),
                "trust_score_result": trust,
                "dual_verdict": judge.get("dual_verdict"),
            } if judge else None,
            # Timing
            "elapsed_ms": int(summary.get("elapsed_seconds", 0) * 1000),
        }
        await send({"type": "audit_result", "result": enriched_summary})

    def _calculate_agent_performance(self, result: dict) -> list:
        performances = []
        scout_results = result.get("scout_results", []) or []
        if scout_results:
            performances.append({"agent": "scout", "tasks_completed": len(scout_results), "tasks_total": len(scout_results), "accuracy": 1.0 if all((item or {}).get("status") != "ERROR" for item in scout_results if isinstance(item, dict)) else 0.0, "processing_time_ms": 0, "finding_rate": sum(len((item or {}).get("screenshots", [])) for item in scout_results if isinstance(item, dict)) / max(1, len(scout_results))})
        vision_result = result.get("vision_result") or {}
        if vision_result:
            analyzed = vision_result.get("screenshots_analyzed", 0)
            performances.append({"agent": "vision", "tasks_completed": analyzed, "tasks_total": analyzed, "accuracy": 1.0 - (0.1 if vision_result.get("fallback_used") else 0.0), "processing_time_ms": 0, "finding_rate": len(self._vision_findings(result)) / max(1, analyzed or 1)})
        security_summary = result.get("security_summary") or {}
        if security_summary:
            executed = security_summary.get("modules_executed", len(security_summary.get("modules_run", [])))
            performances.append({"agent": "security", "tasks_completed": executed, "tasks_total": executed, "accuracy": 1.0 - (len(security_summary.get("modules_failed", [])) / max(1, executed or 1)), "processing_time_ms": security_summary.get("analysis_time_ms", 0), "finding_rate": len(security_summary.get("findings", [])) / max(1, executed or 1)})
        graph_result = result.get("graph_result") or {}
        if graph_result:
            verifications = graph_result.get("verifications", []) or []
            performances.append({"agent": "graph", "tasks_completed": len(graph_result.get("claims_extracted", []) or []), "tasks_total": len(graph_result.get("claims_extracted", []) or []), "accuracy": sum(1 for item in verifications if isinstance(item, dict) and item.get("status") == "confirmed") / max(1, len(verifications)), "processing_time_ms": 0, "finding_rate": len(graph_result.get("inconsistencies", []) or []) / max(1, len(verifications) or 1)})
        judge_result = result.get("judge_decision") or {}
        if judge_result:
            performances.append({"agent": "judge", "tasks_completed": 1 if judge_result.get("action") == "RENDER_VERDICT" else 0, "tasks_total": 1, "accuracy": 1.0 if judge_result.get("trust_score_result") else 0.0, "processing_time_ms": 0})
        return performances

    def _has_graph_data(self, result: dict) -> bool:
        graph = result.get("graph_result") or {}
        return bool(graph.get("graph_data") or graph.get("graph_node_count", 0) > 0 or graph.get("graph_edge_count", 0) > 0 or graph.get("claims_extracted"))

    async def _construct_knowledge_graph(self, result: dict, trust_score: int) -> dict:
        graph = (result.get("graph_result") or {}).get("graph_data")
        if isinstance(graph, dict) and (graph.get("nodes") or graph.get("edges")):
            nodes = graph.get("nodes", []) or []
            edges = graph.get("edges", []) or []
            density = len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0
            return {
                **graph,
                "node_count": graph.get("node_count", len(nodes)),
                "edge_count": graph.get("edge_count", len(edges)),
                "graph_density": graph.get("graph_density", density),
                "avg_clustering": graph.get("avg_clustering", 0.0),
                "largest_component_size": graph.get("largest_component_size", len(nodes)),
                "isolated_nodes": graph.get("isolated_nodes", 0),
            }
        url = result.get("url", self.url)
        nodes = [{"id": f"domain:{url}", "type": "domain", "label": url, "properties": {"url": url, "trust_score": trust_score, "site_type": result.get("site_type")}}]
        edges = []
        for agent_name, present in [("scout", bool(result.get("scout_results"))), ("vision", bool(result.get("vision_result"))), ("security", bool(result.get("security_results"))), ("graph", bool(result.get("graph_result"))), ("judge", bool(result.get("judge_decision")))]:
            if present:
                node_id = f"{agent_name}:{url}"
                nodes.append({"id": node_id, "type": "agent_result", "label": agent_name, "properties": {"agent": agent_name}})
                edges.append({"source": f"domain:{url}", "target": node_id, "relationship": "analyzed_by", "weight": 1.0})
        density = len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "graph_density": density,
            "avg_clustering": 0.0,
            "largest_component_size": len(nodes),
            "isolated_nodes": 0 if edges else max(0, len(nodes) - 1),
        }

    def _calculate_graph_analysis(self, graph: dict) -> dict:
        nodes = graph.get("nodes", []) or []
        edges = graph.get("edges", []) or []
        density = len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "graph_sparsity": 1.0 - density,
            "avg_clustering": graph.get("avg_clustering", 0.0),
            "connected_components": 1 if nodes else 0,
            "strongly_connected": bool(nodes and density > 0.5),
            "osint_clusters": [],
        }

    def _extract_last_json_from_stdout(self, lines: list[str]) -> Optional[dict]:
        text = "\n".join(lines)
        decoder = json.JSONDecoder()
        index = 0
        last_obj: Optional[dict] = None
        while True:
            start = text.find("{", index)
            if start == -1:
                break
            try:
                obj, consumed = decoder.raw_decode(text[start:])
            except json.JSONDecodeError:
                index = start + 1
                continue
            if isinstance(obj, dict) and ("status" in obj or "judge_decision" in obj):
                last_obj = obj
            index = start + max(consumed, 1)
        return last_obj


def generate_audit_id() -> str:
    return f"vrts_{uuid.uuid4().hex[:8]}"

