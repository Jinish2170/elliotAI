import asyncio
import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.services.audit_runner import AuditRunner
from veritas.core.ipc import IPC_MODE_QUEUE, IPC_MODE_STDOUT, ProgressEvent, create_queue


def _sample_result(screenshot_path: str) -> dict:
    return {
        "status": "completed",
        "url": "https://example.com",
        "audit_tier": "standard_audit",
        "verdict_mode": "expert",
        "elapsed_seconds": 12.4,
        "site_type": "ecommerce",
        "site_type_confidence": 0.93,
        "scout_results": [
            {
                "status": "OK",
                "screenshots": [screenshot_path],
                "screenshot_labels": ["Homepage"],
            }
        ],
        "vision_result": {
            "findings": [
                {
                    "category": "visual_interference",
                    "sub_type": "fake_urgency",
                    "confidence": 0.91,
                    "severity": "high",
                    "evidence": "Countdown timer resets on refresh.",
                    "screenshot_path": screenshot_path,
                }
            ],
            "temporal_findings": [
                {
                    "finding_type": "fake_countdown",
                    "value_at_t0": "00:10:00",
                    "value_at_t_delay": "00:10:00",
                    "delta_seconds": 10,
                    "is_suspicious": True,
                    "explanation": "Timer did not progress.",
                    "confidence": 0.88,
                }
            ],
            "screenshots_analyzed": 1,
            "prompts_sent": 5,
            "nim_calls_made": 5,
            "fallback_used": False,
            "errors": [],
        },
        "security_results": {
            "owasp_a05": {"findings": [{"id": "owasp-a05-1"}], "score": 0.2},
            "phishing_db": {"verdict": "clean", "confidence": 0.72},
        },
        "security_summary": {
            "modules_executed": 2,
            "modules_failed": [],
            "analysis_time_ms": 187,
            "findings": [{"id": "owasp-a05-1"}],
        },
        "graph_result": {
            "claims_extracted": [{"claim": "Example Store"}],
            "verifications": [{"status": "confirmed"}],
            "inconsistencies": [{"explanation": "WHOIS owner differs from footer entity."}],
            "osint_sources": {
                "abuseipdb": {"found": True, "confidence_score": 0.65, "data": {"reports": 4}},
                "darknet_alpha": {"found": True, "confidence_score": 0.81, "data": {"market": "AlphaBay"}},
            },
            "osint_indicators": [{"type": "ip", "value": "203.0.113.10"}],
        },
        "judge_decision": {
            "narrative": "Multiple trust and security inconsistencies detected.",
            "recommendations": ["Avoid entering payment details."],
            "green_flags": ["HTTPS present"],
            "trust_score_result": {
                "final_score": 42,
                "risk_level": "high",
                "signal_scores": {"visual": 20.0, "security": 35.0, "graph": 50.0},
            },
            "technical_verdict": {
                "risk_level": "high",
                "trust_score": 42,
                "summary": "Security and entity signals are inconsistent.",
                "recommendations": ["Block checkout flow until verified."],
            },
            "non_technical_verdict": {
                "risk_level": "high",
                "summary": "This site looks risky.",
                "actionable_advice": ["Leave the site."],
                "green_flags": ["HTTPS present"],
            },
        },
        "errors": [],
    }


class TestIpcModeDetermination:
    def test_ipc_mode_determined_in_init(self):
        runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
        assert runner.ipc_mode in (IPC_MODE_QUEUE, IPC_MODE_STDOUT)

    def test_ipc_mode_from_env_queue(self):
        with patch.dict("os.environ", {"QUEUE_IPC_MODE": "queue"}):
            runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
            assert runner.ipc_mode == IPC_MODE_QUEUE

    def test_ipc_mode_from_env_stdout(self):
        with patch.dict("os.environ", {"QUEUE_IPC_MODE": "stdout"}):
            runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
            assert runner.ipc_mode == IPC_MODE_STDOUT


class TestQueueReader:
    @pytest.mark.asyncio
    async def test_reader_maps_progress_events(self):
        queue_obj = create_queue(maxsize=10)
        runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
        runner.progress_queue = queue_obj
        queue_obj.put(
            ProgressEvent(
                type="progress",
                phase="scout",
                step="navigating",
                pct=12,
                detail="Navigating to target",
            )
        )
        send = AsyncMock()

        task = asyncio.create_task(runner._read_queue_and_stream(send))
        await asyncio.sleep(0.2)
        task.cancel()
        await task

        event_types = [call.args[0]["type"] for call in send.await_args_list]
        assert event_types[:3] == ["phase_start", "agent_personality", "log_entry"]

    @pytest.mark.asyncio
    async def test_reader_passthroughs_explicit_events(self):
        queue_obj = create_queue(maxsize=10)
        runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
        runner.progress_queue = queue_obj
        queue_obj.put(
            {
                "type": "vision_pass_start",
                "pass": 1,
                "description": "UI layout analysis",
                "screenshots": 2,
            }
        )
        send = AsyncMock()

        task = asyncio.create_task(runner._read_queue_and_stream(send))
        await asyncio.sleep(0.2)
        task.cancel()
        await task

        assert send.await_args_list[0].args[0]["type"] == "vision_pass_start"
        assert send.await_args_list[0].args[0]["pass"] == 1


class TestRunnerResultContract:
    @pytest.mark.asyncio
    async def test_handle_result_emits_canonical_backend_events(self, tmp_path):
        screenshot_path = tmp_path / "shot.png"
        screenshot_bytes = b"test-image"
        screenshot_path.write_bytes(screenshot_bytes)

        runner = AuditRunner("test_audit", "https://example.com", "standard_audit")
        send = AsyncMock()

        await runner._handle_result(_sample_result(str(screenshot_path)), send)

        payloads = [call.args[0] for call in send.await_args_list]
        event_types = [payload["type"] for payload in payloads]

        assert "screenshot" in event_types
        assert "security_result" in event_types
        assert "owasp_module_result" in event_types
        assert "dark_pattern_finding" in event_types
        assert "temporal_finding" in event_types
        assert "osint_result" in event_types
        assert "darknet_threat" in event_types
        assert "ioc_indicator" in event_types
        assert "knowledge_graph" in event_types
        assert "graph_analysis" in event_types
        assert "verdict_technical" in event_types
        assert "verdict_nontechnical" in event_types
        assert "dual_verdict_complete" in event_types
        assert event_types[-1] == "audit_result"

        screenshot_event = next(payload for payload in payloads if payload["type"] == "screenshot")
        assert screenshot_event["label"] == "Homepage"
        assert screenshot_event["data"] == base64.b64encode(screenshot_bytes).decode("ascii")

        audit_result = payloads[-1]["result"]
        assert audit_result["trust_score"] == 42
        assert audit_result["risk_level"] == "high"
        assert audit_result["site_type"] == "ecommerce"
        assert audit_result["dark_pattern_summary"]["findings"][0]["pattern_type"] == "fake_urgency"
        assert audit_result["security_results"]["phishing_db"]["verdict"] == "clean"

    def test_extract_last_json_from_stdout_prefers_final_result(self):
        runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
        lines = [
            "noise",
            "{\"phase\": \"scout\"}",
            "{\"status\": \"completed\", \"url\": \"https://example.com\", \"judge_decision\": {\"narrative\": \"done\"}}",
        ]

        result = runner._extract_last_json_from_stdout(lines)

        assert result is not None
        assert result["status"] == "completed"
        assert result["judge_decision"]["narrative"] == "done"


class TestRunnerFallback:
    @pytest.mark.asyncio
    async def test_queue_creation_failure_falls_back_to_stdout(self):
        runner = AuditRunner("test_audit", "https://example.com", "quick_scan")
        runner.ipc_mode = IPC_MODE_QUEUE
        send = AsyncMock()

        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [b"", b""]
        mock_process.stderr.readline.side_effect = [b"", b""]
        mock_process.wait.return_value = 0
        mock_process.poll.return_value = 0

        with patch("backend.services.audit_runner.mp.Manager", side_effect=RuntimeError("queue unavailable")):
            with patch("backend.services.audit_runner.subprocess.Popen", return_value=mock_process):
                await runner.run(send)

        assert runner.ipc_mode == IPC_MODE_STDOUT
        assert any(call.args[0]["type"] == "audit_error" for call in send.await_args_list)
