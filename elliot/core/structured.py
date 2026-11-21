"""
Structured outputs at every model/code seam.

Pipeline for every LLM answer that code consumes:

    constrained decoding (response_format=json_schema, NIM supports it)
      → extract JSON (strip <think>, ``` fences, balanced-brace scan)
      → validate with Pydantic (enums come from the taxonomy — single source of truth)
      → on failure: ONE repair retry that feeds the validation error back
      → on second failure: caller's deterministic fallback (never guess)

Enums always include an escape value ("none"/"other"). Without one, constrained
decoding forces the model to pick a wrong label (measured: with
type∈{company,person}, the model labelled "Paris" a company).
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, ValidationError, field_validator

from elliot.config.dark_patterns import DARK_PATTERN_TAXONOMY

# ----------------------------------------------------------------------------
# Taxonomy-derived enums
# ----------------------------------------------------------------------------

SUBTYPE_TO_CATEGORY: dict[str, str] = {
    sub.id: cat_id
    for cat_id, cat in DARK_PATTERN_TAXONOMY.items()
    for sub in cat.sub_types
}
PATTERN_TYPES: list[str] = sorted(SUBTYPE_TO_CATEGORY) + ["other", "none"]

ENTITY_TYPES: list[str] = [
    "company", "person", "address", "phone", "email", "founding_date",
    "partnership", "award", "certification", "other",
]


# ----------------------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------------------

def _coerce_confidence(v: Any) -> float:
    if isinstance(v, str):
        m = re.search(r"\d*\.?\d+", v)
        v = float(m.group()) if m else 0.0
    v = float(v)
    return v / 100.0 if 1.0 < v <= 100.0 else v


class VisionFinding(BaseModel):
    pattern_type: str = Field(description="Dark pattern id from the taxonomy, 'other', or 'none'")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(default="", description="What in the screenshot shows the pattern")
    element: str = Field(default="", description="The UI element involved")

    @field_validator("pattern_type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        v = v.strip().lower().replace(" ", "_").replace("-", "_")
        if v not in PATTERN_TYPES:
            raise ValueError(f"pattern_type '{v}' is not allowed; use one of: {', '.join(PATTERN_TYPES)}")
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def _conf(cls, v: Any) -> float:
        return _coerce_confidence(v)

    @property
    def category_id(self) -> str:
        return SUBTYPE_TO_CATEGORY.get(self.pattern_type, "other")


class VisionResponse(BaseModel):
    findings: list[VisionFinding] = Field(default_factory=list)


class Entity(BaseModel):
    type: str
    value: str = Field(min_length=1)
    context: str = ""

    @field_validator("type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ENTITY_TYPES:
            raise ValueError(f"entity type '{v}' is not allowed; use one of: {', '.join(ENTITY_TYPES)}")
        return v


class EntityResponse(BaseModel):
    entities: list[Entity] = Field(default_factory=list, max_length=10)


VERIFICATION_STATUSES = ["confirmed", "denied", "contradicted", "unverifiable"]


class VerificationResponse(BaseModel):
    status: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = ""

    @field_validator("status")
    @classmethod
    def _known(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VERIFICATION_STATUSES:
            raise ValueError(f"status '{v}' is not allowed; use one of: {', '.join(VERIFICATION_STATUSES)}")
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def _conf(cls, v: Any) -> float:
        return _coerce_confidence(v)


# JSON Schemas for constrained decoding (hand-written so enums are explicit and
# every object is closed: additionalProperties=false, all keys required).
_SCHEMAS: dict[type, dict] = {
    VisionResponse: {
        "type": "object", "additionalProperties": False, "required": ["findings"],
        "properties": {"findings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["pattern_type", "confidence", "evidence", "element"],
            "properties": {
                "pattern_type": {"type": "string", "enum": PATTERN_TYPES},
                "confidence": {"type": "number"},
                "evidence": {"type": "string"},
                "element": {"type": "string"},
            }}}},
    },
    EntityResponse: {
        "type": "object", "additionalProperties": False, "required": ["entities"],
        "properties": {"entities": {"type": "array", "maxItems": 10, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["type", "value", "context"],
            "properties": {
                "type": {"type": "string", "enum": ENTITY_TYPES},
                "value": {"type": "string"},
                "context": {"type": "string"},
            }}}},
    },
    VerificationResponse: {
        "type": "object", "additionalProperties": False,
        "required": ["status", "confidence", "explanation"],
        "properties": {
            "status": {"type": "string", "enum": VERIFICATION_STATUSES},
            "confidence": {"type": "number"},
            "explanation": {"type": "string"},
        },
    },
}


def response_format_for(model: Type[BaseModel]) -> dict:
    """OpenAI-compatible response_format for constrained decoding."""
    return {"type": "json_schema",
            "json_schema": {"name": model.__name__, "schema": _SCHEMAS[model], "strict": True}}


# ----------------------------------------------------------------------------
# Extraction + validation
# ----------------------------------------------------------------------------

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _balanced_objects(text: str):
    """Yield every top-level {...} substring using a brace scanner that respects strings."""
    depth, start, in_str, esc = 0, -1, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0:
                yield text[start:i + 1]


def extract_json(text: str) -> Optional[dict]:
    """Best-effort JSON object extraction from a model reply. None if absent."""
    if not text:
        return None
    text = _THINK.sub("", text).strip()
    candidates = [text] + [m.group(1).strip() for m in _FENCE.finditer(text)]
    candidates += list(_balanced_objects(text))
    for c in candidates:
        try:
            data = json.loads(c)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(data, dict):
            return data
    return None


def parse_structured(text: str, model: Type[BaseModel]) -> tuple[Optional[BaseModel], Optional[str]]:
    """Return (validated_object, None) or (None, error_message_for_repair)."""
    data = extract_json(text)
    if data is None:
        return None, "Your reply did not contain a JSON object."
    if model is VisionResponse:
        # Per-item leniency: drop invalid findings instead of failing the whole reply,
        # but report them so a repair retry can fix systematic errors.
        items, errors = [], []
        for raw in data.get("findings") or []:
            try:
                items.append(VisionFinding.model_validate(raw))
            except ValidationError as e:
                errors.append(e.errors()[0]["msg"])
        if errors and not items:
            return None, "; ".join(dict.fromkeys(errors))
        return VisionResponse(findings=items), None
    try:
        return model.model_validate(data), None
    except ValidationError as e:
        msgs = "; ".join(dict.fromkeys(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()))
        return None, msgs


def repair_prompt(original_prompt: str, error: str) -> str:
    return (f"{original_prompt}\n\nYour previous reply was invalid: {error}\n"
            "Reply again with ONLY a JSON object that satisfies the schema.")
