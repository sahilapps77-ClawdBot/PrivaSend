"""Tests for audit logging."""

from __future__ import annotations

import hashlib
import json
import logging

from tools.audit import log_redaction, _hash_value
from tools.detect_pii import DetectedEntity, DetectionSource, PIIType


def _entity(**kwargs) -> DetectedEntity:
    defaults = dict(
        start=0, end=5, pii_type=PIIType.EMAIL,
        value="test@example.com", confidence=0.95,
        source=DetectionSource.REGEX,
        pre_llm_confidence=None, llm_validated=False,
    )
    defaults.update(kwargs)
    return DetectedEntity(**defaults)


def test_hash_value():
    h = _hash_value("test@example.com")
    assert h == hashlib.sha256(b"test@example.com").hexdigest()


def test_log_contains_no_raw_pii(caplog):
    entity = _entity(value="secret@email.com")
    with caplog.at_level(logging.INFO, logger="privasend.audit"):
        log_redaction(entity, redacted=True)
    assert "secret@email.com" not in caplog.text
    record = json.loads(caplog.records[-1].message)
    assert record["entity_type"] == "EMAIL"
    assert record["redacted"] is True
    assert "value_hash" in record
    assert record["value_hash"] == _hash_value("secret@email.com")


def test_log_includes_llm_metadata(caplog):
    entity = _entity(
        confidence=0.78,
        pre_llm_confidence=0.70,
        llm_validated=True,
    )
    with caplog.at_level(logging.INFO, logger="privasend.audit"):
        log_redaction(entity, redacted=True)
    record = json.loads(caplog.records[-1].message)
    assert record["confidence_pre_llm"] == 0.70
    assert record["confidence_final"] == 0.78
    assert record["llm_validated"] is True


def test_log_non_redacted_entity(caplog):
    entity = _entity(confidence=0.50)
    with caplog.at_level(logging.INFO, logger="privasend.audit"):
        log_redaction(entity, redacted=False)
    record = json.loads(caplog.records[-1].message)
    assert record["redacted"] is False
