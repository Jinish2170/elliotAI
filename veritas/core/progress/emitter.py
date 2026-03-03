"""
Progress Emitter for Real-time Audit Feedback via WebSocket

Handles streaming of progress events, screenshots, findings, and agent status
to clients via WebSocket with token-bucket rate limiting.

From PLAN 09-03: Real-time Progress Streaming
"""

import base64
import io
import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from websockets.server import WebSocketServerProtocol

from PIL import Image

from veritas.core.progress.event_priority import EventPriority
from veritas.core.progress.rate_limiter import RateLimiterConfig, TokenBucketRateLimiter

logger = logging.getLogger("veritas.progress.emitter")


class ProgressEmitter:
    """
    Emits real-time progress events via WebSocket with rate limiting.

    Supports:
        - Screenshot streaming (with thumbnail compression)
        - Finding notifications (batched)
        - Agent status updates
        - Progress updates
        - Error reporting

    Example:
        emitter = ProgressEmitter(websocket=ws)

        # Emit a progress event
        await emitter.emit_progress("Scout", "capturing", 50, "Capturing screenshot...")

        # Emit a screenshot (thumbnail)
        await emitter.emit_screenshot(screenshot_bytes, "page_1", "Scout")

        # Emit a finding
        await emitter.emit_finding(
            category="dark_pattern",
            severity="HIGH",
            message="Misleading countdown timer detected",
            phase="Vision",
            confidence=85
        )

        # Flush any buffered findings
        await emitter.flush()
    """

    def __init__(
        self,
        websocket: Optional["WebSocketServerProtocol"] = None,
        rate_limiter: Optional[TokenBucketRateLimiter] = None,
    ):
        """
        Initialize progress emitter.

        Args:
            websocket: WebSocket connection for streaming events
            rate_limiter: Token bucket rate limiter (creates default if None)
        """
        self.websocket = websocket
        self.rate_limiter = rate_limiter or TokenBucketRateLimiter(
            RateLimiterConfig(max_rate=5.0, burst=10)
        )
        self.findings_batch_size = 5
        self.sequence_number = 0
        self.findings_buffer = []

    async def emit_event(
        self, event_type: str, priority: int = EventPriority.MEDIUM, **kwargs
    ) -> bool:
        """
        Emit an event with rate limiting.

        Args:
            event_type: Type of event (e.g., "progress", "screenshot", "finding")
            priority: Event priority (use EventPriority enum)
            **kwargs: Event data to include in payload

        Returns:
            True if event was emitted immediately, False if rate limited
        """
        self.sequence_number += 1
        event = {
            "type": event_type,
            "priority": priority,
            "seq": self.sequence_number,
            "timestamp": time.time(),
            **kwargs,
        }

        allowed = await self.rate_limiter.acquire(event.data if hasattr(event, "data") else event, priority)

        if allowed and self.websocket:
            await self._send_event(event)
        else:
            logger.debug(f"Event rate-limited: {event_type}")

        return allowed

    async def emit_screenshot(
        self,
        screenshot_data: bytes,
        label: str,
        phase: str,
        thumbnail: bool = True,
    ) -> bool:
        """
        Emit a screenshot event (with optional thumbnail compression).

        Args:
            screenshot_data: Raw screenshot bytes
            label: Screenshot label (e.g., "page_1", "scroll_2")
            phase: Phase name (e.g., "Scout", "Vision")
            thumbnail: If True, generate 200x150 JPEG thumbnail

        Returns:
            True if event was emitted immediately, False if rate limited
        """
        image_bytes = screenshot_data
        is_thumbnail = False
        image_size = len(screenshot_data)

        if thumbnail:
            # Generate 200x150 thumbnail via PIL
            try:
                img = Image.open(io.BytesIO(screenshot_data))
                img.thumbnail((200, 150))
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=70)
                image_bytes = output.getvalue()
                is_thumbnail = True
                image_size = len(image_bytes)
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}, using full screenshot")

        # Base64 encode for JSON transmission
        import base64

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        return await self.emit_event(
            "screenshot",
            EventPriority.MEDIUM,
            phase=phase,
            label=label,
            image=image_b64,
            size=image_size,
            is_thumbnail=is_thumbnail,
        )

    async def emit_finding(
        self,
        category: str,
        severity: str,
        message: str,
        phase: str,
        confidence: Optional[int] = None,
    ) -> bool:
        """
        Emit a finding event (batched with other findings).

        Args:
            category: Finding category (e.g., "dark_pattern", "security")
            severity: Severity level (e.g., "CRITICAL", "HIGH", "MEDIUM", "LOW")
            message: Human-readable finding message
            phase: Phase where finding was detected
            confidence: Confidence score (0-100), optional

        Returns:
            True if event was emitted immediately, False if rate limited or batched
        """
        finding = {
            "category": category,
            "severity": severity,
            "message": message,
            "phase": phase,
            "confidence": confidence,
        }
        self.findings_buffer.append(finding)

        if len(self.findings_buffer) >= self.findings_batch_size:
            await self._flush_findings_buffer()

        return len(self.findings_buffer) == 0  # True if immediately flushed

    async def _flush_findings_buffer(self):
        """Flush buffered findings as a single event."""
        if self.findings_buffer:
            await self.emit_event(
                "findings_batch",
                EventPriority.HIGH,
                findings=self.findings_buffer.copy(),
                count=len(self.findings_buffer),
            )
            self.findings_buffer.clear()

    async def emit_progress(self, phase: str, step: str, pct: int, detail: str = ""):
        """
        Emit a progress event.

        Args:
            phase: Phase name (e.g., "Scout", "Vision", "Overall")
            step: Step name (e.g., "capturing", "pass_1", "complete")
            pct: Progress percentage (0-100)
            detail: Optional detail message
        """
        await self.emit_event(
            "progress",
            EventPriority.LOW,
            phase=phase,
            step=step,
            pct=pct,
            detail=detail,
        )

    async def emit_agent_status(self, agent: str, status: str, detail: str = ""):
        """
        Emit an agent status event.

        Args:
            agent: Agent name (e.g., "Scout", "Vision", "Graph")
            status: Status (started, running, completed, failed, degraded)
            detail: Optional detail message
        """
        priority = EventPriority.CRITICAL if status == "failed" else EventPriority.MEDIUM
        await self.emit_event(
            "agent_status",
            priority,
            agent=agent,
            status=status,
            detail=detail,
        )

    async def emit_error(
        self, error_type: str, message: str, phase: str, recoverable: bool = False
    ):
        """
        Emit an error event.

        Args:
            error_type: Type of error (e.g., "captcha_blocked", "vlm_error")
            message: Error message
            phase: Phase where error occurred
            recoverable: True if recovery is possible
        """
        priority = EventPriority.CRITICAL if not recoverable else EventPriority.HIGH
        await self.emit_event(
            "error",
            priority,
            error_type=error_type,
            message=message,
            phase=phase,
            recoverable=recoverable,
        )

    async def emit_heartbeat(self, detail: str = ""):
        """
        Emit a heartbeat event to maintain 5-10s activity signals.

        Args:
            detail: Optional detail message
        """
        await self.emit_event("heartbeat", EventPriority.LOW, detail=detail or "Processing...")

    async def emit_interesting_highlight(self, message: str, context: str = ""):
        """
        Emit an interesting highlight during long-running agents.

        Args:
            message: Interesting discovery or status
            context: Optional context (e.g., phase name)
        """
        await self.emit_event(
            "highlight",
            EventPriority.HIGH,
            message=message,
            context=context,
        )

    async def flush(self):
        """Flush any buffered findings."""
        await self._flush_findings_buffer()

    async def _send_event(self, event: dict):
        """Send event via WebSocket (or log warning if no connection)."""
        if self.websocket:
            try:
                await self.websocket.send_json(event)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket event: {e}")
        else:
            logger.debug("No WebSocket connection, event not sent")
