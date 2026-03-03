"""
Veritas Core — NVIDIA NIM API Client

4-Level Fallback Chain:
    Level 1: NVIDIA NIM primary VLM (nvidia/neva-22b)
    Level 2: NVIDIA NIM fallback VLM (microsoft/phi-3-vision)
    Level 3: Local Tesseract OCR + heuristic pattern matching
    Level 4: No AI — returns raw indicator for manual review

Features:
    - OpenAI-compatible API format (NVIDIA NIM standard)
    - Async rate limiting via asyncio.Semaphore
    - Disk-based response caching (24h TTL, MD5 keys)
    - Retry logic with exponential backoff (tenacity)
    - API call counting for budget tracking

Patterns carried forward from:
    - Rag_v5.0.0/ingestion/scrapers.py → RateLimiter, DiskCache, retry_with_backoff
"""

import asyncio
import base64
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI
from tenacity import (before_sleep_log, retry, retry_if_exception_type,
                      stop_after_attempt, wait_exponential)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import settings

logger = logging.getLogger("veritas.nim")


# ============================================================
# Custom Exceptions
# ============================================================

class NIMCreditExhausted(Exception):
    """NVIDIA NIM API credits are exhausted."""
    pass


class NIMUnavailable(Exception):
    """All NIM endpoints are unreachable."""
    pass


# ============================================================
# NIM Client
# ============================================================

class NIMClient:
    """
    Async NVIDIA NIM client with rate limiting, caching, and 4-level fallback.

    Usage:
        client = NIMClient()

        # Vision analysis (screenshots → dark pattern detection)
        result = await client.analyze_image("screenshot.jpg", "Describe this page")

        # Text generation (judge reasoning)
        result = await client.generate_text("Synthesize this evidence...")

        # Check budget usage
        print(f"API calls made: {client.call_count}")
    """

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._semaphore = asyncio.Semaphore(settings.NIM_REQUESTS_PER_MINUTE)
        self._min_delay = 60.0 / max(settings.NIM_REQUESTS_PER_MINUTE, 1)
        self._cache_dir = settings.CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Budget tracking
        self._call_count = 0
        self._cache_hits = 0
        self._fallback_count = 0
        self._errors: list[str] = []

        # Lazy-init the client (allows creation without API key for testing)
        self._initialized = False

    def _ensure_client(self):
        """Lazy-initialize the OpenAI client."""
        if not self._initialized:
            if not settings.NIM_API_KEY:
                logger.warning("NVIDIA_NIM_API_KEY not set — NIM calls will fallback to heuristics")
            self._client = AsyncOpenAI(
                base_url=settings.NIM_BASE_URL,
                api_key=settings.NIM_API_KEY or "dummy-key-for-fallback",
            )
            self._initialized = True

    # ================================================================
    # Public API
    # ================================================================

    def get_cache_key(
        self, image_path: str, prompt: str, pass_type: Optional[int] = None
    ) -> str:
        """
        Generate cache key including pass type for pass-specific caching.

        Key format: md5(image_bytes + prompt + pass_type)

        Args:
            image_path: Path to image file
            prompt: The prompt text
            pass_type: Optional pass type identifier (for Vision Agent multi-pass pipeline)

        Returns:
            MD5 hash as cache key
        """
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        key_data = image_bytes + prompt.encode()
        if pass_type is not None:
            key_data += str(pass_type).encode()
        return hashlib.md5(key_data).hexdigest()

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        category_hint: str = "",
        pass_type: Optional[int] = None,
    ) -> dict:
        """
        Analyze an image using VLM with 4-level fallback chain.

        Args:
            image_path: Path to JPEG/PNG screenshot file
            prompt: The VLM forensic prompt (from dark_patterns.py)
            category_hint: Optional dark pattern category for cache grouping
            pass_type: Optional pass type for pass-specific caching (Vision Agent multi-pass)

        Returns:
            {
                "response": str,       # VLM response text (or JSON string)
                "model": str,          # Which model produced this response
                "fallback_mode": bool, # True if not using primary NIM model
                "cached": bool,        # True if served from cache
            }
        """
        self._ensure_client()

        # Check cache - use pass-aware key if pass_type provided
        if pass_type is not None:
            cache_key = self.get_cache_key(image_path, prompt, pass_type)
        else:
            cache_key = self._cache_key(f"vision:{image_path}:{prompt}:{category_hint}")

        cached = self._read_cache(cache_key)
        if cached:
            self._cache_hits += 1
            logger.debug(f"Cache hit for vision analysis: {cache_key[:8]}...")
            return {**cached, "cached": True}

        # Level 1: Primary NIM VLM
        result = await self._try_vision_model(
            settings.NIM_VISION_MODEL, image_path, prompt
        )
        if result:
            self._write_cache(cache_key, result)
            return {**result, "cached": False}

        # Level 2: Fallback NIM VLM
        logger.info(f"Primary VLM failed, trying fallback: {settings.NIM_VISION_FALLBACK}")
        result = await self._try_vision_model(
            settings.NIM_VISION_FALLBACK, image_path, prompt
        )
        if result:
            self._fallback_count += 1
            self._write_cache(cache_key, result)
            return {**result, "cached": False}

        # Level 3: Tesseract OCR + heuristic rules
        logger.warning("Both NIM VLM endpoints failed — falling back to Tesseract OCR")
        self._fallback_count += 1
        result = self._tesseract_fallback(image_path)
        return {**result, "cached": False}

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> dict:
        """
        Generate text using NIM LLM (for Judge agent reasoning).

        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (low = deterministic)

        Returns:
            {
                "response": str,
                "model": str,
                "fallback_mode": bool,
                "cached": bool,
            }
        """
        self._ensure_client()

        # Check cache
        cache_key = self._cache_key(f"text:{system_prompt}:{prompt}")
        cached = self._read_cache(cache_key)
        if cached:
            self._cache_hits += 1
            return {**cached, "cached": True}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            result = await self._rate_limited_call(
                model=settings.NIM_LLM_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            output = {
                "response": result.choices[0].message.content,
                "model": settings.NIM_LLM_MODEL,
                "fallback_mode": False,
            }
            self._write_cache(cache_key, output)
            return {**output, "cached": False}

        except Exception as e:
            error_msg = f"NIM LLM call failed: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            self._errors.append(error_msg)
            return {
                "response": f"[NIM_UNAVAILABLE] {error_msg}",
                "model": "none",
                "fallback_mode": True,
                "cached": False,
            }

    async def batch_analyze_image(
        self,
        image_path: str,
        prompts: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Send multiple prompts for the same image in sequence.
        This is more credit-efficient than separate calls.

        Args:
            image_path: Path to screenshot
            prompts: List of (category_id, prompt) tuples

        Returns:
            List of result dicts, one per prompt
        """
        results = []
        for category_id, prompt in prompts:
            result = await self.analyze_image(
                image_path, prompt, category_hint=category_id
            )
            results.append({**result, "category": category_id})
        return results

    # ================================================================
    # Budget & Stats
    # ================================================================

    @property
    def call_count(self) -> int:
        """Total NIM API calls made (excludes cache hits)."""
        return self._call_count

    @property
    def cache_hits(self) -> int:
        """Total responses served from cache."""
        return self._cache_hits

    @property
    def fallback_count(self) -> int:
        """Number of times fallback models were used."""
        return self._fallback_count

    @property
    def errors(self) -> list[str]:
        """List of error messages from failed calls."""
        return self._errors.copy()

    def get_stats(self) -> dict:
        """Get full usage statistics."""
        return {
            "api_calls": self._call_count,
            "cache_hits": self._cache_hits,
            "fallback_count": self._fallback_count,
            "error_count": len(self._errors),
            "total_requests": self._call_count + self._cache_hits,
        }

    # ================================================================
    # Private: API Calls
    # ================================================================

    async def _try_vision_model(
        self, model: str, image_path: str, prompt: str
    ) -> Optional[dict]:
        """Attempt a single VLM call. Returns None on any failure."""
        try:
            base64_image = self._encode_image(image_path)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]

            result = await self._rate_limited_call(
                model=model,
                messages=messages,
                max_tokens=1024,
                temperature=0.1,
            )

            return {
                "response": result.choices[0].message.content,
                "model": model,
                "fallback_mode": model != settings.NIM_VISION_MODEL,
            }
        except asyncio.CancelledError:
            error_msg = (
                f"VLM call to {model} was cancelled; treating as recoverable and falling back"
            )
            logger.warning(error_msg)
            self._errors.append(error_msg)
            return None
        except Exception as e:
            error_msg = f"VLM call to {model} failed: {type(e).__name__}: {str(e)}"
            logger.warning(error_msg)
            self._errors.append(error_msg)
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _rate_limited_call(
        self,
        model: str,
        messages: list,
        max_tokens: int,
        temperature: float = 0.1,
    ):
        """
        Rate-limited NIM API call with retry.
        Uses asyncio.Semaphore to enforce requests-per-minute budget.
        """
        async with self._semaphore:
            self._call_count += 1
            logger.debug(f"NIM call #{self._call_count} to {model}")

            result = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
                timeout=settings.NIM_TIMEOUT,
            )

            # Respect rate limit
            try:
                await asyncio.sleep(self._min_delay)
            except asyncio.CancelledError:
                logger.warning(
                    "Rate-limit delay cancelled after successful NIM response; continuing without delay"
                )
            return result

    # ================================================================
    # Private: Fallbacks
    # ================================================================

    def _tesseract_fallback(self, image_path: str) -> dict:
        """
        Level 3 fallback: Tesseract OCR → extract text → apply heuristic rules.
        Does NOT require any API calls or network access.
        """
        try:
            import pytesseract
            from PIL import Image

            text = pytesseract.image_to_string(Image.open(image_path))
            analysis = self._heuristic_analysis(text)
            return {
                "response": json.dumps(analysis, indent=2),
                "model": "tesseract+heuristics",
                "fallback_mode": True,
            }
        except ImportError:
            logger.error("Tesseract not available — returning Level 4 (no AI) fallback")
            # Level 4: No AI at all
            return {
                "response": json.dumps({
                    "patterns": [],
                    "note": "All AI services unavailable. Manual review required.",
                    "fallback_level": 4,
                }),
                "model": "none",
                "fallback_mode": True,
            }
        except Exception as e:
            logger.error(f"Tesseract failed: {e}")
            return {
                "response": json.dumps({
                    "patterns": [],
                    "note": f"OCR failed: {str(e)}. Manual review required.",
                    "fallback_level": 4,
                }),
                "model": "none",
                "fallback_mode": True,
            }

    def _heuristic_analysis(self, text: str) -> dict:
        """
        Rule-based dark pattern detection from OCR text.
        No AI needed — pure regex pattern matching.
        """
        patterns = []
        text_lower = text.lower()

        # --- False Urgency ---
        if re.search(r"only \d+ left|limited stock|selling fast|almost gone", text_lower):
            patterns.append({
                "type": "fake_scarcity",
                "category": "false_urgency",
                "confidence": 0.6,
                "evidence": "Scarcity language detected in page text",
            })

        if re.search(r"timer|countdown|\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2}", text_lower):
            patterns.append({
                "type": "possible_urgency_timer",
                "category": "false_urgency",
                "confidence": 0.5,
                "evidence": "Timer or countdown text detected",
            })

        if re.search(r"act now|hurry|don't miss|last chance|expires|ending soon", text_lower):
            patterns.append({
                "type": "urgency_language",
                "category": "false_urgency",
                "confidence": 0.5,
                "evidence": "Urgency language detected",
            })

        # --- Social Engineering ---
        if re.search(r"\d+ people (are )?(viewing|watching|bought|looking)", text_lower):
            patterns.append({
                "type": "social_proof_pressure",
                "category": "social_engineering",
                "confidence": 0.5,
                "evidence": "Social proof counter detected",
            })

        if re.search(r"verified|trusted|secure|guaranteed|certified", text_lower):
            patterns.append({
                "type": "trust_badge_language",
                "category": "social_engineering",
                "confidence": 0.3,
                "evidence": "Trust language detected (needs visual verification)",
            })

        # --- Sneaking ---
        if re.search(r"pre.?selected|added to (your )?(cart|bag|order)", text_lower):
            patterns.append({
                "type": "pre_selected_option",
                "category": "sneaking",
                "confidence": 0.7,
                "evidence": "Pre-selection language detected",
            })

        if re.search(r"free trial.{0,40}(credit card|payment|billing|card number)", text_lower):
            patterns.append({
                "type": "forced_continuity_risk",
                "category": "sneaking",
                "confidence": 0.6,
                "evidence": "Free trial requiring payment info",
            })

        # --- Forced Continuity ---
        if re.search(r"(cancel|unsubscribe).{0,20}(call|phone|email|write|mail)", text_lower):
            patterns.append({
                "type": "roach_motel",
                "category": "forced_continuity",
                "confidence": 0.7,
                "evidence": "Cancellation requires non-digital action",
            })

        if re.search(r"you('ll| will) (lose|miss|forfeit)|are you sure", text_lower):
            patterns.append({
                "type": "guilt_tripping",
                "category": "forced_continuity",
                "confidence": 0.5,
                "evidence": "Guilt-tripping language detected",
            })

        return {
            "patterns": patterns,
            "pattern_count": len(patterns),
            "fallback_mode": True,
            "fallback_level": 3,
            "ocr_text_length": len(text),
        }

    # ================================================================
    # Private: Caching
    # ================================================================

    def _cache_key(self, *args) -> str:
        """Generate a deterministic cache key from arguments."""
        raw = "|".join(str(a) for a in args)
        return hashlib.md5(raw.encode()).hexdigest()

    def _read_cache(self, key: str) -> Optional[dict]:
        """
        Read from disk cache. Returns None if expired (24h TTL) or missing.
        Pattern from: Rag_v5.0.0/ingestion/scrapers.py → DiskCache
        """
        cache_file = self._cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            # 24-hour TTL
            if time.time() - data.get("_timestamp", 0) > 86400:
                cache_file.unlink(missing_ok=True)
                return None
            data.pop("_timestamp", None)
            return data
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def _write_cache(self, key: str, data: dict):
        """Write to disk cache with timestamp."""
        try:
            cache_file = self._cache_dir / f"{key}.json"
            cache_data = {**data, "_timestamp": time.time()}
            cache_file.write_text(
                json.dumps(cache_data, indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning(f"Cache write failed: {e}")

    def _encode_image(self, image_path: str) -> str:
        """Read and base64-encode an image file."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def clear_cache(self):
        """Clear all cached NIM responses."""
        count = 0
        for f in self._cache_dir.glob("*.json"):
            f.unlink(missing_ok=True)
            count += 1
        logger.info(f"Cleared {count} cached responses")
        return count
