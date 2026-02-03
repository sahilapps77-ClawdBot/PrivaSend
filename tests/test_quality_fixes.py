"""Tests for production-grade quality fixes — false positive suppression,
expanded patterns, and merge improvements."""

from __future__ import annotations

import pytest

from tools.detect_pii import (
    PIIType,
    DetectionSource,
    _looks_like_person,
    _NER_BLACKLIST,
    detect,
)


# ---------------------------------------------------------------------------
# NER Blacklist
# ---------------------------------------------------------------------------

class TestNERBlacklist:
    def test_blacklist_has_common_tech_terms(self):
        for term in ("ip", "ssn", "json", "api", "api_key", "jwt", "sql"):
            assert term in _NER_BLACKLIST

    def test_ip_not_flagged_as_org(self):
        entities = detect("logged in from IP 192.168.1.1", use_presidio=True, use_llm=False)
        org_values = [e.value for e in entities if e.pii_type == PIIType.ORGANIZATION]
        assert "IP" not in org_values

    def test_json_not_flagged_as_org(self):
        entities = detect("The payload contained JSON data", use_presidio=True, use_llm=False)
        org_values = [e.value for e in entities if e.pii_type == PIIType.ORGANIZATION]
        assert "JSON" not in org_values


# ---------------------------------------------------------------------------
# PERSON validation
# ---------------------------------------------------------------------------

class TestPersonValidation:
    def test_real_name_passes(self):
        assert _looks_like_person("José Álvarez") is True

    def test_single_capitalized_name(self):
        assert _looks_like_person("Alice") is True

    def test_short_uppercase_acronym_rejected(self):
        assert _looks_like_person("SSN") is False
        assert _looks_like_person("API") is False
        assert _looks_like_person("JSON") is False

    def test_key_value_rejected(self):
        assert _looks_like_person("abc123 token=abc123") is False

    def test_single_lowercase_rejected(self):
        assert _looks_like_person("jose") is False

    def test_hex_string_rejected(self):
        assert _looks_like_person("abc123") is False

    def test_empty_rejected(self):
        assert _looks_like_person("") is False
        assert _looks_like_person("   ") is False


# ---------------------------------------------------------------------------
# Expanded API key / secret patterns
# ---------------------------------------------------------------------------

class TestAPIKeyPatterns:
    def test_stripe_live_key(self):
        entities = detect("key: sk_live_ABCdef1234567890XYZ", use_presidio=False, use_llm=False)
        api_keys = [e for e in entities if e.pii_type == PIIType.API_KEY]
        assert any("sk_live_" in e.value for e in api_keys)

    def test_stripe_test_key(self):
        entities = detect("key: sk_test_abc123def456", use_presidio=False, use_llm=False)
        api_keys = [e for e in entities if e.pii_type == PIIType.API_KEY]
        assert any("sk_test_" in e.value for e in api_keys)

    def test_key_equals_value(self):
        entities = detect("API_KEY=sk_live_ABCdef1234567890XYZ", use_presidio=False, use_llm=False)
        api_keys = [e for e in entities if e.pii_type == PIIType.API_KEY]
        assert len(api_keys) >= 1

    def test_bearer_token(self):
        entities = detect("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature", use_presidio=False, use_llm=False)
        api_keys = [e for e in entities if e.pii_type == PIIType.API_KEY]
        assert any("Bearer" in e.value for e in api_keys)

    def test_generic_password_equals(self):
        entities = detect("password=MyS3cretPass!", use_presidio=False, use_llm=False)
        api_keys = [e for e in entities if e.pii_type == PIIType.API_KEY]
        assert len(api_keys) >= 1


# ---------------------------------------------------------------------------
# SSN variants
# ---------------------------------------------------------------------------

class TestSSNVariants:
    def test_standard_ssn(self):
        entities = detect("SSN 123-45-6789", use_presidio=False, use_llm=False)
        ssns = [e for e in entities if e.pii_type == PIIType.SSN]
        assert any("123-45-6789" in e.value for e in ssns)

    def test_ssn_with_spaces_around_dashes(self):
        entities = detect("sent as 123 - 45 - 6789 yesterday", use_presidio=False, use_llm=False)
        ssns = [e for e in entities if e.pii_type == PIIType.SSN]
        assert any("123" in e.value and "6789" in e.value for e in ssns)

    def test_ssn_with_zero_width_spaces(self):
        text = "SSN 123\u200b-45\u200b-6789"
        entities = detect(text, use_presidio=False, use_llm=False)
        ssns = [e for e in entities if e.pii_type == PIIType.SSN]
        assert any("123" in e.value and "6789" in e.value for e in ssns)


# ---------------------------------------------------------------------------
# URL email extraction
# ---------------------------------------------------------------------------

class TestURLEmailExtraction:
    def test_email_in_url_query_param(self):
        text = "https://example.com/reset?email=jose@gmail.com&token=abc"
        entities = detect(text, use_presidio=False, use_llm=False)
        emails = [e for e in entities if e.pii_type == PIIType.EMAIL]
        assert any("jose@gmail.com" in e.value for e in emails)


# ---------------------------------------------------------------------------
# Merge: suppress generic NER over specific regex
# ---------------------------------------------------------------------------

class TestMergeSuppression:
    def test_org_suppressed_when_credit_card_exists(self):
        """Presidio often tags credit card numbers as ORGANIZATION — should be suppressed."""
        text = "card 4111-1111-1111-1111 expired"
        entities = detect(text, use_presidio=True, use_llm=False)
        # Should have CREDIT_CARD but NOT ORGANIZATION on same span
        cc = [e for e in entities if e.pii_type == PIIType.CREDIT_CARD]
        org = [e for e in entities if e.pii_type == PIIType.ORGANIZATION and "4111" in e.value]
        assert len(cc) >= 1
        assert len(org) == 0
