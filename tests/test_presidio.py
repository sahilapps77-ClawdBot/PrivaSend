"""
Tests for Presidio + spaCy NER layer (Layer 2).

These tests load the spaCy model so they are slower (~10s first run).
They test what regex CANNOT catch: names, addresses, organizations.

Run:  python -m pytest tests/test_presidio.py -v
"""

import pytest

from tools.detect_pii import PIIType, detect, DetectionSource


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def full_detect(text: str):
    """Run full detection (regex + Presidio)."""
    return detect(text, use_presidio=True)


def types_found(text: str) -> set[PIIType]:
    return {e.pii_type for e in full_detect(text)}


def presidio_types(text: str) -> set[PIIType]:
    """Only entities caught by Presidio (not regex)."""
    return {e.pii_type for e in full_detect(text) if e.source == DetectionSource.PRESIDIO}


def values_of_type(text: str, pii_type: PIIType) -> list[str]:
    return [e.value for e in full_detect(text) if e.pii_type == pii_type]


# ---------------------------------------------------------------------------
# Person names — this is what regex CANNOT do
# ---------------------------------------------------------------------------

class TestPersonNames:
    def test_western_name(self):
        assert PIIType.PERSON in types_found("Please contact John Smith for details.")

    def test_full_name_in_sentence(self):
        assert PIIType.PERSON in types_found(
            "The report was prepared by Dr. Sarah Johnson on Monday."
        )

    def test_indian_name(self):
        # spaCy may or may not catch Indian names — this tests capability
        entities = full_detect("Rahul Sharma submitted the application yesterday.")
        person_values = values_of_type(
            "Rahul Sharma submitted the application yesterday.", PIIType.PERSON
        )
        # At minimum, Presidio should flag something here
        assert len(person_values) > 0, "Expected at least one PERSON entity for 'Rahul Sharma'"

    def test_multiple_names(self):
        text = "Meeting between Alice Cooper and Bob Williams at 3pm."
        persons = values_of_type(text, PIIType.PERSON)
        assert len(persons) >= 2, f"Expected at least 2 persons, got {persons}"


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

class TestOrganizations:
    def test_company_name(self):
        assert PIIType.ORGANIZATION in types_found(
            "She works at Goldman Sachs in New York."
        )

    def test_tech_company(self):
        assert PIIType.ORGANIZATION in types_found(
            "The contract was signed with Microsoft Corporation."
        )


# ---------------------------------------------------------------------------
# Locations / Addresses
# ---------------------------------------------------------------------------

class TestLocations:
    def test_city(self):
        assert PIIType.LOCATION in types_found("He moved to San Francisco last year.")

    def test_country(self):
        assert PIIType.LOCATION in types_found("She is traveling to Germany next week.")


# ---------------------------------------------------------------------------
# Mixed: Regex + Presidio working together
# ---------------------------------------------------------------------------

class TestMixedDetection:
    def test_name_plus_email(self):
        text = "Contact John Smith at john.smith@example.com for details."
        found = types_found(text)
        assert PIIType.PERSON in found, "Presidio should catch 'John Smith'"
        assert PIIType.EMAIL in found, "Regex should catch the email"

    def test_name_plus_phone_plus_ssn(self):
        text = (
            "Patient Jane Doe, SSN 123-45-6789, "
            "can be reached at (555) 867-5309."
        )
        found = types_found(text)
        assert PIIType.PERSON in found
        assert PIIType.SSN in found
        assert PIIType.PHONE in found

    def test_realistic_paragraph(self):
        text = (
            "Dear Mr. Robert Chen,\n\n"
            "Your account (ending 4111-1111-1111-1111) has been flagged. "
            "Please contact our office at +1-800-555-0199 or email "
            "support@acmebank.com. Your case reference is MRN-789012.\n\n"
            "Regards,\nACME Bank"
        )
        found = types_found(text)
        assert PIIType.PERSON in found, "Should catch 'Robert Chen'"
        assert PIIType.CREDIT_CARD in found, "Should catch credit card"
        assert PIIType.PHONE in found, "Should catch phone"
        assert PIIType.EMAIL in found, "Should catch email"
        assert PIIType.MEDICAL_RECORD in found, "Should catch MRN"

    def test_no_pii_paragraph(self):
        text = (
            "The quarterly report shows revenue increased by 15% compared "
            "to the previous quarter. Market conditions remain favorable "
            "for continued growth in the technology sector."
        )
        entities = full_detect(text)
        # Filter to only high-confidence results
        high_confidence = [e for e in entities if e.confidence >= 0.7]
        assert len(high_confidence) == 0, (
            f"Expected no high-confidence PII in clean text, got: "
            f"{[(e.pii_type.value, e.value, e.confidence) for e in high_confidence]}"
        )


# ---------------------------------------------------------------------------
# Redaction roundtrip with Presidio entities
# ---------------------------------------------------------------------------

class TestPresidioRedaction:
    def test_name_redaction_roundtrip(self):
        from tools.redact import redact, deredact

        text = "Please contact John Smith at john.smith@example.com."
        entities = full_detect(text)
        result = redact(text, entities)

        # Should have placeholders for name and email
        assert "[PERSON_1]" in result.redacted_text or "[EMAIL_1]" in result.redacted_text
        assert "john.smith@example.com" not in result.redacted_text

        # Roundtrip
        restored = deredact(result.redacted_text, result.mapping)
        assert restored == text
