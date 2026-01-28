"""Tests for the PII detection engine (regex layer only — fast, no model load)."""

import pytest

from tools.detect_pii import PIIType, detect


# ---------------------------------------------------------------------------
# Helper: run regex-only detection (fast, no spaCy load)
# ---------------------------------------------------------------------------

def detect_regex(text: str):
    return detect(text, use_presidio=False)


def types_found(text: str) -> set[PIIType]:
    return {e.pii_type for e in detect_regex(text)}


def values_found(text: str) -> list[str]:
    return [e.value for e in detect_regex(text)]


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

class TestEmail:
    def test_simple_email(self):
        assert PIIType.EMAIL in types_found("Contact john@example.com for info")

    def test_email_with_dots(self):
        assert PIIType.EMAIL in types_found("Send to john.doe.smith@company.co.uk")

    def test_email_with_plus(self):
        assert PIIType.EMAIL in types_found("Use user+tag@gmail.com")

    def test_no_false_positive(self):
        assert PIIType.EMAIL not in types_found("This is a plain sentence.")


# ---------------------------------------------------------------------------
# Phone
# ---------------------------------------------------------------------------

class TestPhone:
    def test_us_format_dashes(self):
        assert PIIType.PHONE in types_found("Call 555-123-4567")

    def test_us_format_parens(self):
        assert PIIType.PHONE in types_found("Call (555) 123-4567")

    def test_international(self):
        assert PIIType.PHONE in types_found("Reach me at +1-555-123-4567")

    def test_indian_mobile(self):
        assert PIIType.PHONE in types_found("My number is 98765 43210")

    def test_indian_with_country_code(self):
        assert PIIType.PHONE in types_found("Call +91 98765 43210")


# ---------------------------------------------------------------------------
# SSN
# ---------------------------------------------------------------------------

class TestSSN:
    def test_ssn_dashes(self):
        assert PIIType.SSN in types_found("SSN: 123-45-6789")

    def test_no_false_positive_on_short_number(self):
        # "12345" should not match SSN
        assert PIIType.SSN not in types_found("Code is 12345")


# ---------------------------------------------------------------------------
# Credit card
# ---------------------------------------------------------------------------

class TestCreditCard:
    def test_visa(self):
        assert PIIType.CREDIT_CARD in types_found("Card: 4111-1111-1111-1111")

    def test_visa_no_separator(self):
        assert PIIType.CREDIT_CARD in types_found("Card: 4111111111111111")

    def test_mastercard(self):
        assert PIIType.CREDIT_CARD in types_found("Card: 5500 0000 0000 0004")

    def test_amex(self):
        assert PIIType.CREDIT_CARD in types_found("Card: 3782 822463 10005")

    def test_no_false_positive(self):
        assert PIIType.CREDIT_CARD not in types_found("Order number 123456")


# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------

class TestAPIKey:
    def test_openai_key(self):
        assert PIIType.API_KEY in types_found("key: sk-abcdefghijklmnopqrstuv")

    def test_aws_key(self):
        assert PIIType.API_KEY in types_found("key: AKIAIOSFODNN7EXAMPLE")


# ---------------------------------------------------------------------------
# Indian IDs
# ---------------------------------------------------------------------------

class TestIndianIDs:
    def test_aadhaar(self):
        assert PIIType.AADHAAR in types_found("Aadhaar: 2345 6789 0123")

    def test_pan(self):
        assert PIIType.PAN in types_found("PAN: ABCDE1234F")


# ---------------------------------------------------------------------------
# Other patterns
# ---------------------------------------------------------------------------

class TestAddress:
    def test_street_address(self):
        assert PIIType.ADDRESS in types_found("He lives at 42 Oak Street in the city")

    def test_full_address_with_city(self):
        assert PIIType.ADDRESS in types_found("Office at 123 Main Blvd, Suite 400")

    def test_address_with_avenue(self):
        assert PIIType.ADDRESS in types_found("Visit us at 789 Park Avenue")

    def test_no_false_positive_plain_number(self):
        assert PIIType.ADDRESS not in types_found("I bought 42 apples today")


class TestOther:
    def test_iban(self):
        assert PIIType.IBAN in types_found("IBAN: GB29 NWBK 6016 1331 9268 19")

    def test_ip_v4(self):
        assert PIIType.IP_ADDRESS in types_found("Server at 192.168.1.100")

    def test_mac_address(self):
        assert PIIType.MAC_ADDRESS in types_found("MAC: 00:1A:2B:3C:4D:5E")

    def test_medical_record(self):
        assert PIIType.MEDICAL_RECORD in types_found("Patient MRN-123456")

    def test_url_with_creds(self):
        assert PIIType.URL_WITH_CREDENTIALS in types_found(
            "Connect to https://admin:password123@db.example.com/data"
        )

    def test_date_of_birth_slash(self):
        assert PIIType.DATE_OF_BIRTH in types_found("DOB: 01/15/1990")

    def test_date_of_birth_written(self):
        assert PIIType.DATE_OF_BIRTH in types_found("Born January 15, 1990")


# ---------------------------------------------------------------------------
# Mixed PII (multiple types in one text)
# ---------------------------------------------------------------------------

class TestMixed:
    def test_multiple_types(self):
        text = (
            "John's email is john@example.com and his SSN is 123-45-6789. "
            "Call him at 555-123-4567. Card: 4111-1111-1111-1111."
        )
        found = types_found(text)
        assert PIIType.EMAIL in found
        assert PIIType.SSN in found
        assert PIIType.PHONE in found
        assert PIIType.CREDIT_CARD in found

    def test_no_pii(self):
        text = "The weather today is sunny with a high of 75 degrees."
        assert detect_regex(text) == [] or all(
            e.confidence < 0.5 for e in detect_regex(text)
        )
