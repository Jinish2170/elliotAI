"""Structured outputs: extraction, taxonomy validation, repair retry."""
import json

import pytest

from elliot.core.structured import (EntityResponse, VisionResponse, extract_json,
                                    parse_structured, response_format_for)


def test_extract_json_handles_think_fences_and_nesting():
    text = '<think>hmm {"no": 1}</think>Here:\n```json\n{"a": {"b": {"c": [1, {"d": "}"}]}}}\n```'
    assert extract_json(text) == {"a": {"b": {"c": [1, {"d": "}"}]}}}


def test_extract_json_deeply_nested_without_fence():
    # The old regex handled at most 2 nesting levels and returned None here.
    assert extract_json('Answer: {"x": {"y": {"z": {"w": 1}}}} done') == {"x": {"y": {"z": {"w": 1}}}}


def test_vision_rejects_invented_pattern_type_and_maps_category():
    obj, err = parse_structured(json.dumps({"findings": [
        {"pattern_type": "fake_countdown", "confidence": "0.9", "evidence": "timer resets"},
        {"pattern_type": "made_up_thing", "confidence": 0.9},
    ]}), VisionResponse)
    assert err is None and len(obj.findings) == 1
    f = obj.findings[0]
    assert f.category_id == "false_urgency" and f.confidence == 0.9


def test_vision_all_invalid_returns_repairable_error():
    obj, err = parse_structured('{"findings": [{"pattern_type": "nope", "confidence": 1}]}', VisionResponse)
    assert obj is None and "not allowed" in err


def test_entity_schema_has_escape_value():
    schema = response_format_for(EntityResponse)["json_schema"]["schema"]
    assert "other" in schema["properties"]["entities"]["items"]["properties"]["type"]["enum"]


@pytest.mark.asyncio
async def test_repair_retry_feeds_error_back_once():
    from elliot.core.nim_client import NIMClient

    c = NIMClient()
    prompts = []
    replies = iter(['{"entities": [{"type": "city", "value": "Paris"}]}',
                    '{"entities": [{"type": "other", "value": "Paris", "context": ""}]}'])

    async def fake_generate_text(prompt, *a, **k):
        prompts.append(prompt)
        return {"response": next(replies), "model": "m", "fallback_mode": False}

    c.generate_text = fake_generate_text
    obj, _ = await c.generate_structured("extract", EntityResponse)
    assert obj is not None and obj.entities[0].type == "other"
    assert len(prompts) == 2 and "previous reply was invalid" in prompts[1]
    assert c.get_stats()["parse_failures"] == 1
