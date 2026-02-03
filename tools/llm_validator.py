"""LLM-based PII validation using Ollama.

Validates medium-confidence entities (0.60-0.85) by asking a local LLM
whether the detected entity is truly PII in context.

Non-negotiable rules:
- LLM must NOT discover new PII
- LLM must NOT see full documents
- LLM must ONLY validate entities already detected
- LLM must return JSON only
- System must fail-open (never block pipeline)
"""

from __future__ import annotations

import json
import logging
import time

import httpx

from tools.config import (
    LLM_CONFIDENCE_HIGH,
    LLM_CONFIDENCE_LOW,
    LLM_CONTEXT_CHARS,
    LLM_TIMEOUT,
    LLM_TOTAL_BUDGET,
    OLLAMA_MODEL,
    OLLAMA_URL,
)
from tools.detect_pii import DetectedEntity

logger = logging.getLogger("privasend.llm")

SYSTEM_PROMPT = (
    "You are a PII validation engine.\n"
    "You must NOT identify new entities.\n"
    "You must ONLY validate the provided entity.\n"
    "Return JSON only. No explanations."
)


def _build_user_prompt(entity: DetectedEntity, context: str) -> str:
    return (
        f'Entity: "{entity.value}"\n'
        f"Entity Type: {entity.pii_type.value}\n"
        f'Context: "{context}"\n\n'
        "Decide if this entity is personally identifiable information.\n"
        "Respond ONLY in JSON:\n"
        '{"is_pii": true | false, "confidence": 0.0 - 1.0}'
    )


def _extract_context(text: str, entity: DetectedEntity) -> str:
    start = max(0, entity.start - LLM_CONTEXT_CHARS)
    end = min(len(text), entity.end + LLM_CONTEXT_CHARS)
    return text[start:end]


def _call_ollama(prompt: str) -> dict | None:
    """Call Ollama and parse JSON response. Returns None on any failure."""
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "num_ctx": 512,
                },
            },
            timeout=LLM_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        # Try to extract JSON from the response
        raw = raw.strip()
        # Handle cases where LLM wraps JSON in markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except httpx.ConnectError:
        logger.warning("Ollama unreachable at %s — failing open", OLLAMA_URL)
        return None
    except httpx.TimeoutException:
        logger.warning("Ollama request timed out — failing open")
        return None
    except (json.JSONDecodeError, KeyError, httpx.HTTPStatusError) as e:
        logger.warning("Ollama response parse error: %s — failing open", e)
        return None


def _compute_final_confidence(
    detector_score: float, llm_result: dict | None
) -> tuple[float, float | None, bool]:
    """Returns (final_confidence, llm_confidence, llm_validated).

    If llm_result is None (fail-open), returns detector_score unchanged.
    """
    if llm_result is None:
        return detector_score, None, False

    is_pii = llm_result.get("is_pii", True)
    llm_conf = float(llm_result.get("confidence", 0.5))
    llm_conf = max(0.0, min(1.0, llm_conf))  # clamp

    if is_pii:
        final = 0.6 * detector_score + 0.4 * llm_conf
    else:
        final = detector_score * 0.3

    return final, llm_conf, True


def validate_entities(
    entities: list[DetectedEntity], text: str
) -> list[DetectedEntity]:
    """Validate medium-confidence entities via LLM.

    Entities outside the 0.60-0.85 band pass through unchanged.
    On Ollama failure, all entities pass through unchanged (fail-open).
    """
    if not entities:
        return entities

    ollama_available = True
    budget_start = time.monotonic()
    result = []

    for entity in entities:
        budget_elapsed = time.monotonic() - budget_start
        needs_llm = (
            ollama_available
            and budget_elapsed < LLM_TOTAL_BUDGET
            and LLM_CONFIDENCE_LOW <= entity.confidence <= LLM_CONFIDENCE_HIGH
        )

        if not needs_llm:
            result.append(entity)
            continue

        context = _extract_context(text, entity)
        prompt = _build_user_prompt(entity, context)
        llm_result = _call_ollama(prompt)

        # If connection failed, stop trying for remaining entities
        if llm_result is None and not ollama_available:
            result.append(entity)
            continue
        if llm_result is None:
            # First failure — check if it was a connection issue
            # We already logged; mark as unavailable for remaining
            ollama_available = False
            result.append(entity)
            continue

        final_conf, llm_conf, validated = _compute_final_confidence(
            entity.confidence, llm_result
        )

        # Create updated entity with new confidence and LLM metadata
        updated = DetectedEntity(
            start=entity.start,
            end=entity.end,
            pii_type=entity.pii_type,
            value=entity.value,
            confidence=final_conf,
            source=entity.source,
            pre_llm_confidence=entity.confidence,
            llm_validated=validated,
        )
        result.append(updated)

    return result
