"""
VLM Caching Tests

Tests for pass-level caching functionality in Vision Agent:
1. Cache key generation includes pass_type parameter
2. Cache-aware execution returns cached responses
3. Cache hit rate >60% on repeated URLs

Run:
    cd veritas
    python -m pytest tests/test_vlm_caching.py -v
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add veritas root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.nim_client import NIMClient
from agents.vision import VisionAgent, DarkPatternFinding


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        yield tmpdir_path


@pytest.fixture
def mock_image_file():
    """Create a mock image file with consistent content."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        # Write some consistent bytes
        tmp.write(b"MOCK_IMAGE_DATA")
        tmp.flush()
        yield tmp.name
        # Cleanup happens in NamedTemporaryFile context


@pytest.fixture
def nim_client(temp_cache_dir):
    """Create a NIMClient with temp cache directory."""
    with patch("config.settings.CACHE_DIR", temp_cache_dir):
        client = NIMClient()
        client._initialized = True
        return client


@pytest.fixture
def vision_agent(nim_client):
    """Create a VisionAgent with mocked NIM client."""
    return VisionAgent(nim_client=nim_client)


# ============================================================
# Task 1: Cache Key Generation Tests
# ============================================================

class TestCacheKeyGeneration:
    """Test that cache keys include pass_type parameter."""

    def test_cache_key_includes_pass_type(self, nim_client, mock_image_file):
        """Different pass types should generate different cache keys."""
        prompt = "Analyze this image for dark patterns."

        key_pass_1 = nim_client.get_cache_key(mock_image_file, prompt, pass_type=1)
        key_pass_2 = nim_client.get_cache_key(mock_image_file, prompt, pass_type=2)
        key_pass_none = nim_client.get_cache_key(mock_image_file, prompt, pass_type=None)

        # Each pass type should have a unique key
        assert key_pass_1 != key_pass_2, "Pass type 1 and 2 should have different cache keys"
        assert key_pass_1 != key_pass_none, "Pass type 1 and None should have different cache keys"
        assert key_pass_2 != key_pass_none, "Pass type 2 and None should have different cache keys"

    def test_cache_key_same_for_same_params(self, nim_client, mock_image_file):
        """Same parameters should generate same cache key."""
        prompt = "Analyze this image for dark patterns."
        pass_type = 1

        key1 = nim_client.get_cache_key(mock_image_file, prompt, pass_type)
        key2 = nim_client.get_cache_key(mock_image_file, prompt, pass_type)

        assert key1 == key2, "Same parameters should generate identical cache keys"

    def test_cache_key_different_for_different_prompts(self, nim_client, mock_image_file):
        """Different prompts should generate different cache keys."""
        pass_type = 1
        prompt1 = "Analyze for false urgency"
        prompt2 = "Analyze for social engineering"

        key1 = nim_client.get_cache_key(mock_image_file, prompt1, pass_type)
        key2 = nim_client.get_cache_key(mock_image_file, prompt2, pass_type)

        assert key1 != key2, "Different prompts should generate different cache keys"

    def test_cache_key_is_valid_md5(self, nim_client, mock_image_file):
        """Cache keys should be valid MD5 hex strings."""
        key = nim_client.get_cache_key(mock_image_file, "Test prompt", pass_type=1)

        # MD5 hash is 32 hex characters
        assert len(key) == 32, "Cache key should be 32 characters (MD5)"
        assert all(c in "0123456789abcdef" for c in key), "Cache key should be hex string"


# ============================================================
# Task 2: Cache-Aware Execution Tests
# ============================================================

class TestCacheAwareExecution:
    """Test cache-aware vision pass execution."""

    @pytest.mark.asyncio
    async def test_run_pass_with_cache_hits(self, vision_agent, mock_image_file):
        """First call caches result, second call returns cached result."""
        pass_num = 1
        prompt = "Analyze this image"

        # Mock the NIM analyze_image method
        mock_response = {
            "response": json.dumps({
                "findings": [{
                    "pattern_type": "fake_countdown",
                    "confidence": 0.85,
                    "evidence": "Timer detected"
                }]
            }),
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
            "cached": False,
        }

        original_analyze = vision_agent._nim.analyze_image
        call_count = 0

        async def tracked_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        vision_agent._nim.analyze_image = tracked_analyze

        # First call - should execute VLM
        findings1 = await vision_agent.run_pass_with_cache(
            pass_num, mock_image_file, prompt
        )
        assert call_count == 1, "First call should execute VLM"
        assert len(findings1) == 1, "First call should return one finding"
        assert findings1[0].pattern_type == "fake_countdown"
        assert findings1[0].confidence == 0.85

        # Second call with same parameters - should hit cache
        findings2 = await vision_agent.run_pass_with_cache(
            pass_num, mock_image_file, prompt
        )
        assert call_count == 1, "Second call should hit cache, not execute VLM"
        assert len(findings2) == 1, "Cached result should return same findings"
        assert findings2[0].pattern_type == "fake_countdown"
        assert findings2[0].confidence == 0.85

        # Restore original method
        vision_agent._nim.analyze_image = original_analyze

    @pytest.mark.asyncio
    async def test_run_pass_different_pass_types_cache_separately(self, vision_agent, mock_image_file):
        """Different pass types should cache separately."""
        prompt = "Analyze this image"
        mock_response1 = {
            "response": json.dumps({
                "findings": [{
                    "pattern_type": "fake_countdown",
                    "confidence": 0.85,
                }]
            }),
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
        }
        mock_response2 = {
            "response": json.dumps({
                "findings": [{
                    "pattern_type": "social_proof",
                    "confidence": 0.75,
                }]
            }),
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
        }

        call_count = 0

        async def tracked_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response1
            else:
                return mock_response2

        vision_agent._nim.analyze_image = tracked_analyze

        # First pass
        findings1 = await vision_agent.run_pass_with_cache(
            1, mock_image_file, prompt
        )
        assert call_count == 1

        # Second pass with different pass_type - should not cache hit
        findings2 = await vision_agent.run_pass_with_cache(
            2, mock_image_file, prompt
        )
        assert call_count == 2, "Different pass should not hit cache"

        # Call first pass again - should hit cache now
        findings1_cached = await vision_agent.run_pass_with_cache(
            1, mock_image_file, prompt
        )
        assert call_count == 2, "First pass should hit cache on repeated call"
        assert findings1_cached[0].pattern_type == "fake_countdown"


# ============================================================
# Task 3: Cache Hit Rate Tests
# ============================================================

class TestCacheHitRate:
    """Test cache hit rate >60% on repeated URLs."""

    @pytest.mark.asyncio
    async def test_cache_hit_rate_above_60_percent(self, vision_agent, mock_image_file):
        """
        Simulate 5-pass pipeline with repeated analysis.
        First run: 5 VLM calls. Second run: >60% cache hits (at least 3 out of 5 passes cached).
        """
        pass_1_prompt = "Pass 1: Analyze static visual elements"
        pass_2_prompt = "Pass 2: Analyze for false urgency timers"
        pass_3_prompt = "Pass 3: Analyze for scarcity indicators"
        pass_4_prompt = "Pass 4: Analyze for misdirection elements"
        pass_5_prompt = "Pass 5: Analyze for dark pattern combinations"

        prompts = [
            (1, pass_1_prompt),
            (2, pass_2_prompt),
            (3, pass_3_prompt),
            (4, pass_4_prompt),
            (5, pass_5_prompt),
        ]

        mock_response = {
            "response": json.dumps({
                "findings": [{
                    "pattern_type": "test_pattern",
                    "confidence": 0.8,
                    "evidence": "Test finding"
                }]
            }),
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
        }

        vlm_call_count = 0

        async def tracked_analyze(*args, **kwargs):
            nonlocal vlm_call_count
            vlm_call_count += 1
            return mock_response

        vision_agent._nim.analyze_image = tracked_analyze

        # First run - all 5 passes should execute VLM
        for pass_num, prompt in prompts:
            await vision_agent.run_pass_with_cache(pass_num, mock_image_file, prompt)

        first_run_calls = vlm_call_count
        assert first_run_calls == 5, f"First run should make 5 VLM calls, got {first_run_calls}"

        # Second run - should hit cache
        vlm_call_count = 0
        for pass_num, prompt in prompts:
            await vision_agent.run_pass_with_cache(pass_num, mock_image_file, prompt)

        second_run_calls = vlm_call_count
        cache_hits = 5 - second_run_calls
        cache_hit_rate = (cache_hits / 5) * 100

        print(f"\nCache hit rate: {cache_hit_rate:.1f}% ({cache_hits}/5)")
        print(f"Second run VLM calls: {second_run_calls}")

        # Success criterion: >60% cache hit rate (at least 3 out of 5)
        assert cache_hits >= 3, f"Expected >=3 cache hits, got {cache_hits}"
        assert cache_hit_rate >= 60, f"Expected >=60% cache hit rate, got {cache_hit_rate:.1f}%"

    @pytest.mark.asyncio
    async def test_cache_hit_tracking_in_stats(self, vision_agent, mock_image_file):
        """Verify VLM calls are tracked and cache behavior works correctly."""
        prompt = "Analyze this image"
        pass_type = 1
        mock_response = {
            "response": json.dumps({"findings": []}),
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
        }

        call_count = 0

        async def tracked_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        vision_agent._nim.analyze_image = tracked_analyze

        # First call - should execute VLM (cache miss)
        await vision_agent.run_pass_with_cache(pass_type, mock_image_file, prompt)
        assert call_count == 1, "First call should execute VLM"

        # Second call - should hit cache (no VLM call)
        await vision_agent.run_pass_with_cache(pass_type, mock_image_file, prompt)
        assert call_count == 1, "Second call with cache hit should NOT execute VLM"

        # Third call with different pass_type - should execute VLM again
        await vision_agent.run_pass_with_cache(pass_type + 1, mock_image_file, prompt)
        assert call_count == 2, "Different pass_type should execute VLM"

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration_handling(self, vision_agent, mock_image_file, temp_cache_dir):
        """Verify expired cache entries are handled correctly."""
        prompt = "Analyze for TTL testing"
        pass_num = 1

        mock_response = {
            "response": json.dumps({"findings": []}),
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
        }

        call_count = 0

        async def tracked_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        vision_agent._nim.analyze_image = tracked_analyze

        # First call and cache
        await vision_agent.run_pass_with_cache(pass_num, mock_image_file, prompt)
        assert call_count == 1

        # Find the cache file and make it expired
        cache_key = vision_agent._nim.get_cache_key(mock_image_file, prompt, pass_num)
        cache_file = temp_cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            # Load and modify to make it expired (timestamp in the past)
            data = json.loads(cache_file.read_text())
            data["_timestamp"] = 0  # Expired
            cache_file.write_text(json.dumps(data))

        # Second call should re-execute due to expired cache
        await vision_agent.run_pass_with_cache(pass_num, mock_image_file, prompt)
        assert call_count == 2, "Expired cache should trigger re-execution"


# ============================================================
# Edge Cases and Error Handling
# ============================================================

class TestCachingEdgeCases:
    """Test edge cases in caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_with_nonexistent_image(self, vision_agent):
        """Handle missing image file gracefully."""
        nonexistent_file = "/tmp/nonexistent_image_12345.jpg"
        prompt = "Analyze this image"

        # This should raise an exception (expected behavior)
        with pytest.raises(FileNotFoundError):
            await vision_agent.run_pass_with_cache(1, nonexistent_file, prompt)

    def test_cache_key_with_empty_prompt(self, nim_client, mock_image_file):
        """Handle empty prompt in cache key generation."""
        key1 = nim_client.get_cache_key(mock_image_file, "", pass_type=1)
        key2 = nim_client.get_cache_key(mock_image_file, "", pass_type=1)
        assert key1 == key2, "Empty prompts should still generate consistent keys"

    def test_cache_key_with_special_characters(self, nim_client, mock_image_file):
        """Handle special characters in prompt."""
        special_prompts = [
            "Test!@#$%^&*()",
            "Test\nwith\nnewlines",
            "Test\twith\ttabs",
            "Test with \x00 null bytes",
        ]

        keys = []
        for prompt in special_prompts:
            key = nim_client.get_cache_key(mock_image_file, prompt, pass_type=1)
            keys.append(key)

        # Each unique prompt should have a unique key
        assert len(set(keys)) == len(keys), "Special characters should affect cache keys differently"
