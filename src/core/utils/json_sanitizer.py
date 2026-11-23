"""
Resilient JSON Sanitizer and Repair Engine for LLM Structured Outputs.
Handles markdown fences, unescaped quotes, trailing commas, truncated brackets,
and structural wrapper mismatches across Gemini and OpenAI models.
"""

import re
import json
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from src.core.logging import get_logger

logger = get_logger("json_sanitizer")

T = TypeVar("T", bound=BaseModel)

try:
    import json_repair
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False


def clean_markdown_fences(raw_text: str) -> str:
    """Strips markdown code fences, headers, and trailing prose."""
    if not raw_text:
        return "{}"

    text = raw_text.strip()

    # Match code blocks: ```json ... ``` or ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        text = code_block_match.group(1).strip()
    else:
        # If code block is opened but not closed (e.g. streaming or truncated)
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    return text


def repair_and_parse_json(raw_text: str) -> Any:
    """
    Parses JSON with multiple defensive fallback stages:
    1. Standard json.loads on stripped content
    2. json_repair library (repairs missing quotes, trailing commas, unescaped chars)
    3. Balanced brace substring extraction
    4. Heuristic syntax repair
    """
    cleaned = clean_markdown_fences(raw_text)

    # Stage 1: Standard Fast Parse
    try:
        return json.loads(cleaned)
    except Exception as e_fast:
        logger.debug(f"Stage 1 fast JSON parse failed ({e_fast}). Escalating to repair...")

    # Stage 2: json-repair package if available
    if HAS_JSON_REPAIR:
        try:
            repaired = json_repair.repair_json(cleaned, return_objects=True)
            if repaired is not None:
                # If json_repair returned an empty string or None on non-empty input
                if isinstance(repaired, (dict, list)):
                    return repaired
        except Exception as e_repair:
            logger.debug(f"Stage 2 json-repair failed ({e_repair}). Escalating to substring extraction...")

    # Stage 3: Substring between outermost { ... } or [ ... ]
    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")

    start_idx = -1
    end_char = ""
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        start_idx = first_brace
        end_idx = cleaned.rfind("}")
        end_char = "}"
    elif first_bracket != -1:
        start_idx = first_bracket
        end_idx = cleaned.rfind("]")
        end_char = "]"
    else:
        end_idx = -1

    if start_idx != -1:
        if end_idx != -1 and end_idx > start_idx:
            sub = cleaned[start_idx : end_idx + 1]
        else:
            # Missing closing bracket/brace due to token truncation - auto-append
            sub = cleaned[start_idx:] + end_char

        # Try parsing substring
        try:
            return json.loads(sub)
        except Exception:
            if HAS_JSON_REPAIR:
                try:
                    repaired = json_repair.repair_json(sub, return_objects=True)
                    if isinstance(repaired, (dict, list)):
                        return repaired
                except Exception:
                    pass

    # Stage 4: Heuristic regex cleanups
    heuristic = cleaned
    # Remove trailing commas: , \s* } -> } and , \s* ] -> ]
    heuristic = re.sub(r",\s*([\}\]])", r"\1", heuristic)
    # Remove single line comments // ...
    heuristic = re.sub(r"//.*?\n", "\n", heuristic)
    # Fix single quotes to double quotes around simple keys
    heuristic = re.sub(r"(?<=[{\[,])\s*'([a-zA-Z0-9_\-]+)'\s*:", r'"\1":', heuristic)

    try:
        return json.loads(heuristic)
    except Exception as final_err:
        raise ValueError(
            f"Failed to parse or repair model JSON response: {final_err}. "
            f"Sample text snippet: {cleaned[:300]}..."
        ) from final_err


def normalize_to_schema(data: Any, schema_cls: Type[T]) -> T:
    """
    Validates data against a Pydantic schema, automatically resolving common
    LLM wrapper discrepancies (e.g. list returned when dict wrapper was expected,
    or key wrapper difference like 'items' / 'cases' vs 'test_cases').
    """
    if isinstance(data, schema_cls):
        return data

    # 1. Direct validation attempt
    try:
        return schema_cls.model_validate(data)
    except ValidationError as direct_err:
        logger.debug(f"Direct schema validation failed: {direct_err}. Attempting structural reconciliation...")

    # 2. Structural reconciliation for List wrappers
    # If schema expects a dict with a list field (e.g. TestCaseDesignOutput with test_cases)
    # and the model returned a bare list [...]
    if isinstance(data, list):
        # Look for the primary list field in the schema
        for field_name, field_info in schema_cls.model_fields.items():
            annotation = field_info.annotation
            origin = getattr(annotation, "__origin__", None)
            if origin is list or origin is List:
                try:
                    return schema_cls.model_validate({field_name: data, f"total_{field_name}": len(data), "summary": f"Generated {len(data)} items."})
                except Exception:
                    pass

    # 3. If data is dict but wrapper key is slightly off (e.g. "cases" or "data" instead of "test_cases")
    if isinstance(data, dict):
        for schema_field in schema_cls.model_fields.keys():
            if schema_field not in data:
                # Check for aliases or alternative keys
                for alt_key in ["data", "items", "results", "list", schema_field.replace("test_", ""), schema_field.rstrip("s")]:
                    if alt_key in data and isinstance(data[alt_key], list):
                        try:
                            reconciled = dict(data)
                            reconciled[schema_field] = data[alt_key]
                            return schema_cls.model_validate(reconciled)
                        except Exception:
                            pass

    # 4. Final attempt: raise validation error
    return schema_cls.model_validate(data)
