"""Tests for the reversible redaction engine."""

from tools.detect_pii import DetectedEntity, DetectionSource, PIIType
from tools.redact import deredact, redact


def _entity(start, end, pii_type, value, confidence=0.9):
    return DetectedEntity(
        start=start,
        end=end,
        pii_type=pii_type,
        value=value,
        confidence=confidence,
        source=DetectionSource.REGEX,
    )


class TestRedact:
    def test_single_email(self):
        text = "Contact john@example.com for info"
        entities = [_entity(8, 24, PIIType.EMAIL, "john@example.com")]
        result = redact(text, entities)
        assert result.redacted_text == "Contact [EMAIL_1] for info"
        assert result.mapping["[EMAIL_1]"] == "john@example.com"
        assert result.entity_count == 1

    def test_multiple_same_type(self):
        text = "Email john@a.com or jane@b.com"
        entities = [
            _entity(6, 16, PIIType.EMAIL, "john@a.com"),
            _entity(20, 30, PIIType.EMAIL, "jane@b.com"),
        ]
        result = redact(text, entities)
        assert "[EMAIL_1]" in result.redacted_text
        assert "[EMAIL_2]" in result.redacted_text
        assert result.entity_count == 2

    def test_multiple_different_types(self):
        text = "john@a.com and 123-45-6789"
        entities = [
            _entity(0, 10, PIIType.EMAIL, "john@a.com"),
            _entity(15, 26, PIIType.SSN, "123-45-6789"),
        ]
        result = redact(text, entities)
        assert "[EMAIL_1]" in result.redacted_text
        assert "[SSN_1]" in result.redacted_text

    def test_empty_input(self):
        result = redact("hello world", [])
        assert result.redacted_text == "hello world"
        assert result.mapping == {}
        assert result.entity_count == 0

    def test_overlapping_entities_keeps_wider(self):
        text = "Call +1-555-123-4567 now"
        entities = [
            _entity(5, 20, PIIType.PHONE, "+1-555-123-4567"),
            _entity(8, 20, PIIType.PHONE, "555-123-4567"),
        ]
        result = redact(text, entities)
        assert result.entity_count == 1
        assert result.mapping["[PHONE_1]"] == "+1-555-123-4567"


class TestDeredact:
    def test_roundtrip(self):
        text = "Contact john@example.com for info"
        entities = [_entity(8, 24, PIIType.EMAIL, "john@example.com")]
        result = redact(text, entities)
        restored = deredact(result.redacted_text, result.mapping)
        assert restored == text

    def test_multiple_roundtrip(self):
        text = "john@a.com and 123-45-6789"
        entities = [
            _entity(0, 10, PIIType.EMAIL, "john@a.com"),
            _entity(15, 26, PIIType.SSN, "123-45-6789"),
        ]
        result = redact(text, entities)
        restored = deredact(result.redacted_text, result.mapping)
        assert restored == text
