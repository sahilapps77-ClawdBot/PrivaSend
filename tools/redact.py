"""
Reversible Redaction Engine.

Replaces detected PII with numbered placeholders (e.g., [EMAIL_1], [NAME_2])
and maintains a mapping so the original values can be restored.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.detect_pii import DetectedEntity, PIIType


@dataclass
class RedactionResult:
    """Output of the redaction process."""
    redacted_text: str
    mapping: dict[str, str]  # placeholder -> original value
    entity_count: int


def redact(text: str, entities: list[DetectedEntity]) -> RedactionResult:
    """
    Replace detected PII entities with numbered placeholders.

    Entities must be non-overlapping or pre-deduplicated. Processes from
    end-to-start so character offsets remain valid.

    Args:
        text: Original input text.
        entities: Detected PII entities (from detect_pii.detect).

    Returns:
        RedactionResult with redacted text and reversible mapping.
    """
    if not entities:
        return RedactionResult(redacted_text=text, mapping={}, entity_count=0)

    # Resolve overlapping spans: keep the entity with the wider span,
    # or if same span, the higher confidence.
    resolved = _resolve_overlaps(entities)

    # Assign numbered placeholders per type
    type_counters: dict[PIIType, int] = {}
    mapping: dict[str, str] = {}
    placeholders: list[tuple[int, int, str]] = []  # (start, end, placeholder)

    for entity in resolved:
        count = type_counters.get(entity.pii_type, 0) + 1
        type_counters[entity.pii_type] = count
        placeholder = f"[{entity.pii_type.value}_{count}]"
        mapping[placeholder] = entity.value
        placeholders.append((entity.start, entity.end, placeholder))

    # Replace from end to start to preserve offsets
    redacted = text
    for start, end, placeholder in reversed(placeholders):
        redacted = redacted[:start] + placeholder + redacted[end:]

    return RedactionResult(
        redacted_text=redacted,
        mapping=mapping,
        entity_count=len(resolved),
    )


def deredact(text: str, mapping: dict[str, str]) -> str:
    """
    Restore original values from placeholders.

    Args:
        text: Text containing placeholders like [EMAIL_1].
        mapping: Placeholder-to-original mapping from RedactionResult.

    Returns:
        Text with original values restored.
    """
    result = text
    for placeholder, original in mapping.items():
        result = result.replace(placeholder, original)
    return result


def _resolve_overlaps(entities: list[DetectedEntity]) -> list[DetectedEntity]:
    """
    Remove overlapping entities, keeping the best match.

    Strategy: sort by start position, then for overlapping spans keep the one
    that is wider (covers more text). If same width, keep higher confidence.
    """
    if not entities:
        return []

    sorted_entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
    resolved: list[DetectedEntity] = [sorted_entities[0]]

    for entity in sorted_entities[1:]:
        prev = resolved[-1]
        if entity.start < prev.end:
            # Overlap — keep the better one
            prev_span = prev.end - prev.start
            curr_span = entity.end - entity.start
            if curr_span > prev_span or (
                curr_span == prev_span and entity.confidence > prev.confidence
            ):
                resolved[-1] = entity
        else:
            resolved.append(entity)

    return resolved
