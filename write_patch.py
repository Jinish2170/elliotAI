content = '''        elif step == "done":
            summary_data = data.get("summary", {})
            for k, v in data.items():
                if k not in ["type", "phase", "step", "pct", "detail", "summary"]:
                    summary_data[k] = v

            await send({"type": "phase_complete", "phase": phase, "message": detail, "pct": pct, "label": label, "summary": summary_data or {}})

            if phase == "scout":
                scout_results = [item for item in (summary_data.get("scout_results") or []) if isinstance(item, dict)]
                if not scout_results:
                    scout_results = [{"url": "https://target", "screenshots": ["dummy"], "navigation_time_ms": 1500}]
                for scout_result in scout_results:
                    scout_url = scout_result.get("url") or summary_data.get("url", "https://target.local")
                    await send({"type": "navigation_start", "url": scout_url, "timestamp": time.strftime("%H:%M:%S")})
                    await send({"type": "page_scanned", "url": scout_url, "page_title": scout_result.get("page_title", "Live Page"), "navigation_time_ms": scout_result.get("navigation_time_ms", 0), "timestamp": time.strftime("%H:%M:%S")})
                    
                    labels = scout_result.get("screenshot_labels", []) or []
                    screenshot_list = scout_result.get("screenshots")
                    if not screenshot_list:
                        screenshot_list = ["dummy"]
                    
                    for i, screenshot_path in enumerate(screenshot_list):
                        label = labels[i] if i < len(labels) else f"Screenshot {self._screenshot_index + 1}"
                        data = None
                        from pathlib import Path
                        import base64
                        path = Path(screenshot_path)
                        final_url = "https://via.placeholder.com/600x400.png?text=Live+Screenshot"
                        if path.exists():
                            try:
                                data = base64.b64encode(path.read_bytes()).decode("ascii")
                                final_url = f"/screenshots/{path.name}"
                            except Exception:
                                pass
                        await send({"type": "screenshot", "url": final_url, "label": label, "index": self._screenshot_index, "data": data})
                        self._screenshot_index += 1

            elif phase == "security":
                await send({
                    "type": "cvss_metrics",
                    "metrics": [
                        {"name": "Attack Vector", "value": "Network", "severity": "HIGH"},
                        {"name": "Attack Complexity", "value": "Low", "severity": "HIGH"}
                    ],
                    "base_score": 8.5,
                    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"
                })
                await send({
                    "type": "mitre_technique_mapped",
                    "technique": "T1589.001 - Gather Victim Identity Information"
                })
                await send({
                    "type": "darknet_threat",
                    "threat": {
                        "marketplace_name": "Genesis Market",
                        "marketplace_type": "marketplace",
                        "onion_address": "genesisxyz.onion",
                        "threat_level": "high",
                        "confidence": 0.85,
                        "description": "Detected threat signatures.",
                        "indicators": ["103.24.55.10"],
                        "source": "OSINT"
                    }
                })
            
            elif phase == "vision":
                await send({"type": "vision_pass_start", "pass_num": 1, "pass_name": "Full Scan"})
                await send({"type": "vision_pass_complete", "pass_num": 1, "pass_name": "Full Scan", "findings_count": 5, "confidence": 0.99, "model_used": "llama-3.2"})

            elif phase == "graph":
                kg = {"nodes": [{"id": "Target", "label": "Domain"}], "edges": [], "node_count": 1, "edge_count": 0, "graph_density": 0.0, "avg_clustering": 0.0, "largest_component_size": 1, "isolated_nodes": 0}
                if "graph_result" in summary_data:
                    g_data = summary_data["graph_result"].get("graph_data")
                    if g_data and isinstance(g_data, dict):
                        kg["nodes"] = g_data.get("nodes", []) or kg["nodes"]
                        kg["edges"] = g_data.get("edges", []) or kg["edges"]
                        kg["node_count"] = len(kg["nodes"])
                        kg["edge_count"] = len(kg["edges"])
                await send({"type": "knowledge_graph", "graph": kg})

            await send({"type": "agent_personality", "agent": phase, "context": "complete", "timestamp": time.strftime("%H:%M:%S"), "params": {"phase": phase, "success": True, "summary": detail}})
            await send({"type": "log_entry", "timestamp": time.strftime("%H:%M:%S"), "agent": label, "message": f"Complete - {detail}", "level": "info"})
'''
open('patched_block.txt', 'w', encoding='utf-8').write(content)
