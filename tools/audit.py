"""Audit logging for PII redaction decisions.

Logs structured JSON per entity — never stores raw PII values,
only SHA-256 hashes.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.detect_pii import DetectedEntity

logger = logging.getLogger("privasend.audit")


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def log_redaction(entity: DetectedEntity, redacted: bool) -> None:
    """Log a single redaction decision as structured JSON."""
    record = {
        "entity_type": entity.pii_type.value,
        "start": entity.start,
        "end": entity.end,
        "confidence_pre_llm": entity.pre_llm_confidence,
        "confidence_final": round(entity.confidence, 4),
        "llm_validated": entity.llm_validated,
        "redacted": redacted,
        "value_hash": _hash_value(entity.value),
    }
    logger.info(json.dumps(record))
