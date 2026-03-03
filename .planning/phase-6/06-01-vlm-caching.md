---
id: 06-01
phase: 6
wave: 1
autonomous: true

objective: Implement VLM caching with pass-level keys to reduce GPU costs by enabling pass-skipping and reusing cached VLM responses.

files_modified:
  - veritas/core/nim_client.py
  - veritas/agents/vision.py

tasks:
  - Extend NIM cache key generation to include pass_type parameter
  - Implement cache-aware vision pass execution method
  - Test cache hit rate >60% on repeated URLs

has_summary: false
gap_closure: false
---

# Plan 06-01: VLM Caching with Pass-Level Keys

**Goal:** Enable pass-specific VLM caching to reduce GPU costs by 10x through intelligent pass skipping and response reuse.

## Context

Phase 6 introduces a 5-pass vision pipeline that would otherwise multiply GPU costs. Aggressive caching based on screenshot pixels + prompt + pass type is essential for cost control.

**Current State:**
- Basic VLM caching exists (24h TTL, disk-based JSON)
- Cache keys don't include pass type
- No pass-skipping optimization

**Target State:**
- Pass-specific cache keys
- Cache-aware execution
- Conditional pass execution based on cache hits

## Implementation

### Task 1: Extend NIM cache key to include pass type

**File:** `veritas/core/nim_client.py`

```python
def get_cache_key(image_path: str, prompt: str, pass_type: int) -> str:
    """
    Generate cache key including pass type for pass-specific caching.

    Key format: md5(image_bytes + prompt + pass_type)
    """
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    key_data = image_bytes + prompt.encode() + str(pass_type).encode()
    return hashlib.md5(key_data).hexdigest()
```

### Task 2: Implement cache-aware vision pass execution

**File:** `veritas/agents/vision.py`

```python
async def run_pass_with_cache(pass_num: int, screenshot: str, prompt: str) -> Finding:
    """Execute vision pass with caching."""
    cache_key = get_cache_key(screenshot, prompt, pass_num)
    cached = self.nim_client.get_from_cache(cache_key)

    if cached:
        logger.info(f"Cache hit for Pass {pass_num}")
        return Finding.from_dict(cached)

    # Execute VLM call
    vlm_response = await self.nim_client.analyze_image(screenshot, prompt)
    finding = self._parse_vlm_response(vlm_response)

    # Cache result (24h TTL)
    self.nim_client.write_to_cache(cache_key, finding.to_dict(), ttl=86400)

    return finding
```

## Success Criteria

1. ✅ Cache key generation includes pass_type parameter
2. ✅ Cache-aware execution returns cached responses when available
3. ✅ Test shows >60% cache hit rate on repeated URLs
4. ✅ VLM call count reduced accordingly

## Dependencies

- None (foundational)
