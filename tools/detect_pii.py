"""
PII Detection Engine — Two-layer hybrid approach.

Layer 1: Regex patterns for structured PII (emails, phones, SSNs, credit cards, etc.)
Layer 2: Microsoft Presidio + spaCy NER for context-dependent PII (names, addresses, orgs)

Both layers run independently, results are merged and deduplicated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class PIIType(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    API_KEY = "API_KEY"
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    IBAN = "IBAN"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    MEDICAL_RECORD = "MEDICAL_RECORD"
    IP_ADDRESS = "IP_ADDRESS"
    MAC_ADDRESS = "MAC_ADDRESS"
    VIN = "VIN"
    URL_WITH_CREDENTIALS = "URL_WITH_CREDENTIALS"
    UPI_ID = "UPI_ID"
    USERNAME_PASSWORD = "USERNAME_PASSWORD"
    CRYPTO_WALLET = "CRYPTO_WALLET"
    UK_NI_NUMBER = "UK_NI_NUMBER"
    CANADIAN_SIN = "CANADIAN_SIN"
    US_EIN = "US_EIN"
    VEHICLE_PLATE = "VEHICLE_PLATE"
    SWIFT_BIC = "SWIFT_BIC"
    PERSON = "PERSON"
    ADDRESS = "ADDRESS"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    MEDICAL_CONDITION = "MEDICAL_CONDITION"
    DATE_TIME = "DATE_TIME"
    CREDENTIAL = "CREDENTIAL"


class DetectionSource(str, Enum):
    REGEX = "regex"
    PRESIDIO = "presidio"


@dataclass(order=True)
class DetectedEntity:
    """A single PII detection result."""
    start: int
    end: int
    pii_type: PIIType = field(compare=False)
    value: str = field(compare=False)
    confidence: float = field(compare=False)
    source: DetectionSource = field(compare=False)
    pre_llm_confidence: float | None = field(default=None, compare=False)
    llm_validated: bool = field(default=False, compare=False)


# ---------------------------------------------------------------------------
# Layer 1: Regex patterns
# ---------------------------------------------------------------------------

# Each entry: (PIIType, compiled regex, confidence score)
# Patterns ordered from most specific to least specific within each type.

_REGEX_PATTERNS: list[tuple[PIIType, re.Pattern, float]] = []


def _add(pii_type: PIIType, pattern: str, confidence: float, flags: int = 0) -> None:
    _REGEX_PATTERNS.append((pii_type, re.compile(pattern, flags), confidence))


# --- Email ---
_add(PIIType.EMAIL, r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", 0.95)

# --- Phone numbers ---
# International with country code: +1-555-123-4567, +91 98765 43210, +44 20 7946 0958
_add(PIIType.PHONE, r"\+\d{1,3}[\s\-.]?\(?\d{1,4}\)?[\s\-.]?\d{1,4}[\s\-.]?\d{1,9}", 0.85)
# US format: (555) 123-4567, 555-123-4567, 555.123.4567
_add(PIIType.PHONE, r"\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b", 0.80)
# Indian 10-digit mobile: 98765 43210, 9876543210
_add(PIIType.PHONE, r"\b[6-9]\d{4}[\s\-]?\d{5}\b", 0.75)

# --- SSN (US) ---
_add(PIIType.SSN, r"\b\d{3}-\d{2}-\d{4}\b", 0.90)
# SSN with zero-width characters between digits/dashes
_add(PIIType.SSN, r"\b\d{3}[\u200b\u200c\u200d\ufeff]+-[\u200b\u200c\u200d\ufeff]*\d{2}[\u200b\u200c\u200d\ufeff]*-[\u200b\u200c\u200d\ufeff]*\d{4}\b", 0.90)
# SSN with spaces around dashes: 123 - 45 - 6789
_add(PIIType.SSN, r"\b\d{3}\s+-\s+\d{2}\s+-\s+\d{4}\b", 0.85)
_add(PIIType.SSN, r"\b\d{9}\b", 0.40)  # low confidence — could be any 9-digit number

# --- Credit card ---
# Visa
_add(PIIType.CREDIT_CARD, r"\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", 0.90)
# Mastercard
_add(PIIType.CREDIT_CARD, r"\b5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", 0.90)
# Amex
_add(PIIType.CREDIT_CARD, r"\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b", 0.90)
# Discover
_add(PIIType.CREDIT_CARD, r"\b6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", 0.90)
# Generic 16-digit with separators (lower confidence)
_add(PIIType.CREDIT_CARD, r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b", 0.70)

# --- API keys / secrets ---
# OpenAI
_add(PIIType.API_KEY, r"\bsk-[A-Za-z0-9]{20,}\b", 0.95)
# Stripe keys (sk_live_, sk_test_, rk_live_, rk_test_)
_add(PIIType.API_KEY, r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{10,}\b", 0.95)
# AWS access key
_add(PIIType.API_KEY, r"\bAKIA[0-9A-Z]{16}\b", 0.95)
# GitHub tokens
_add(PIIType.API_KEY, r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b", 0.95)
# Generic key=value secrets (API_KEY=..., secret=..., token=..., password=...)
_add(PIIType.API_KEY, r"(?:api[_\-]?key|secret|token|password|passwd|credential)\s*[=:]\s*[A-Za-z0-9\-_\.]{8,}", 0.85, re.IGNORECASE)
# Bearer tokens (with optional "token:" prefix)
_add(PIIType.API_KEY, r"\bBearer\s+(?:token:\s*)?[A-Za-z0-9\-_\.]{20,}\b", 0.90)
# Generic long hex/base64 tokens (40+ chars) with keyword prefix
_add(PIIType.API_KEY, r"\b(?:api[_\-]?key|token|secret)[\"'\s:=]+[A-Za-z0-9\-_]{32,}\b", 0.80, re.IGNORECASE)

# --- Aadhaar (India) ---
_add(PIIType.AADHAAR, r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b", 0.75)

# --- PAN (India) ---
_add(PIIType.PAN, r"\b[A-Z]{5}\d{4}[A-Z]\b", 0.90)

# --- Passport ---
# US passport
_add(PIIType.PASSPORT, r"\b[A-Z]\d{8}\b", 0.60)
# Indian passport
_add(PIIType.PASSPORT, r"\b[A-Z][1-9]\d{6}\b", 0.55)

# --- Driver's license (US — common formats) ---
_add(PIIType.DRIVERS_LICENSE, r"\b[A-Z]\d{7,8}\b", 0.45)  # low — overlaps with passport

# --- IBAN ---
_add(PIIType.IBAN, r"\b[A-Z]{2}\d{2}[\s]?[A-Z0-9]{4}[\s]?(?:[A-Z0-9]{4}[\s]?){1,7}[A-Z0-9]{1,4}\b", 0.85)

# --- Bank account (US routing + account) ---
_add(PIIType.BANK_ACCOUNT, r"\b\d{9}[\s\-]?\d{7,17}\b", 0.50)

# --- Date of birth ---
# MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD
_add(
    PIIType.DATE_OF_BIRTH,
    r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b",
    0.65,
)
_add(
    PIIType.DATE_OF_BIRTH,
    r"\b(?:19|20)\d{2}[/\-](?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])\b",
    0.65,
)
# Written: 15-Jan-1990, January 15, 1990
_add(
    PIIType.DATE_OF_BIRTH,
    r"\b\d{1,2}[\s\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-,]*\d{4}\b",
    0.55,
    re.IGNORECASE,
)
_add(
    PIIType.DATE_OF_BIRTH,
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-]+\d{1,2}[\s,]+\d{4}\b",
    0.55,
    re.IGNORECASE,
)

# --- Medical record number ---
_add(PIIType.MEDICAL_RECORD, r"\bMRN[\s\-:#]?\d{4,10}\b", 0.85, re.IGNORECASE)

# --- IP address ---
# IPv4
_add(
    PIIType.IP_ADDRESS,
    r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\."
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
    0.80,
)
# IPv6 (simplified — full hex groups)
_add(PIIType.IP_ADDRESS, r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", 0.80)

# --- MAC address ---
_add(PIIType.MAC_ADDRESS, r"\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b", 0.85)

# --- VIN ---
_add(PIIType.VIN, r"\b[A-HJ-NPR-Z0-9]{17}\b", 0.50)  # low — many 17-char strings exist

# --- Street address ---
# Pattern: number + street name + street suffix (e.g., "42 Oak Street", "123 Main Blvd")
_STREET_SUFFIXES = (
    r"Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|"
    r"Court|Ct|Place|Pl|Way|Circle|Cir|Trail|Trl|Parkway|Pkwy|"
    r"Highway|Hwy|Terrace|Ter|Crescent|Cres|Square|Sq"
)
# Full address: number + street + optional apt/suite + optional city/state/zip
_add(
    PIIType.ADDRESS,
    r"\b\d{1,6}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:" + _STREET_SUFFIXES + r")\.?"
    r"(?:\s*,?\s*(?:Apt|Suite|Unit|#)\s*\w+)?"
    r"(?:\s*,\s*[A-Z][a-zA-Z\s]+)?"
    r"(?:\s*,?\s*[A-Z]{2})?"
    r"(?:\s+\d{5}(?:-\d{4})?)?\b",
    0.85,
)

# --- URL with credentials ---
_add(
    PIIType.URL_WITH_CREDENTIALS,
    r"https?://[^\s:]+:[^\s@]+@[^\s]+",
    0.95,
)

# --- UPI ID (India) ---
# Format: name@bankcode (e.g., rahul@oksbi, user@upi, merchant@ybl)
_add(PIIType.UPI_ID, r"\b[a-zA-Z0-9.\-_]{3,}@(?:oksbi|okaxis|okicici|okhdfcbank|ybl|apl|paytm|ibl|upi|axl|sbi|icici|hdfc|hdfcbank|barodampay|indus|kotak|federal|rbl|citi|idbi|pnb|unionbank|bob|cnrb|dlb|tjsb|kvb|axisbank|idfcbank|yesbank|dbs|scb|hsbc|csbpay|equitas|fino|jupiter|freecharge|slice|gpay|phonepe)\b", 0.90, re.IGNORECASE)

# --- Username:password pairs ---
# Catches "username: admin password: secret123" and "user/pass = admin/secret"
_add(PIIType.USERNAME_PASSWORD, r"(?:user(?:name)?|login)\s*[:=]\s*\S+\s+(?:pass(?:word)?|pwd)\s*[:=]\s*\S+", 0.90, re.IGNORECASE)
# Also: "admin:password123" format (not URL, standalone)
_add(PIIType.USERNAME_PASSWORD, r"(?:password|passwd|pwd)\s*[:=]\s*\S{6,}", 0.80, re.IGNORECASE)

# --- Cryptocurrency wallet addresses ---
# Bitcoin (starts with 1, 3, or bc1, 26-62 chars)
_add(PIIType.CRYPTO_WALLET, r"\b(?:1|3)[1-9A-HJ-NP-Za-km-z]{25,34}\b", 0.75)
_add(PIIType.CRYPTO_WALLET, r"\bbc1[a-zA-HJ-NP-Z0-9]{25,87}\b", 0.80)
# Ethereum (0x followed by 40 hex chars)
_add(PIIType.CRYPTO_WALLET, r"\b0x[0-9a-fA-F]{40}\b", 0.85)

# --- UK National Insurance number ---
# Format: AB 12 34 56 C (with or without spaces)
_add(PIIType.UK_NI_NUMBER, r"\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b", 0.85)

# --- Canadian SIN ---
# Format: 123-456-789 or 123 456 789
_add(PIIType.CANADIAN_SIN, r"\b\d{3}[\s\-]\d{3}[\s\-]\d{3}\b", 0.60)  # low — overlaps with phone fragments

# --- US EIN (Employer Identification Number) ---
# Format: 12-3456789
_add(PIIType.US_EIN, r"\b\d{2}-\d{7}\b", 0.65)

# --- Vehicle registration plates ---
# India: AB 12 CD 3456 or AB12CD3456
_add(PIIType.VEHICLE_PLATE, r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{4}\b", 0.70)
# US: varies by state, common pattern: ABC-1234, ABC 1234, 1ABC234
_add(PIIType.VEHICLE_PLATE, r"\b[A-Z]{3}[\s\-]?\d{4}\b", 0.45)  # low — common letter-number combos
# UK: AB12 CDE
_add(PIIType.VEHICLE_PLATE, r"\b[A-Z]{2}\d{2}\s?[A-Z]{3}\b", 0.65)

# --- SWIFT/BIC code ---
# Format: 8 or 11 chars, e.g., HDFCINBBXXX, SBININBB
_add(PIIType.SWIFT_BIC, r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b", 0.55)  # low — many 8-letter words match


# Context keywords for DATE_OF_BIRTH — only flag a date as DOB if one of
# these appears within 80 characters before or after the match.
_DOB_CONTEXT_KEYWORDS = re.compile(
    r"\b(?:born|birth|dob|d\.o\.b|date\s+of\s+birth|birthday|birthdate|age|DOB)\b",
    re.IGNORECASE,
)


def _has_dob_context(text: str, start: int, end: int) -> bool:
    """Check if a date match has DOB context within 40 chars."""
    window_start = max(0, start - 40)
    window_end = min(len(text), end + 40)
    window = text[window_start:window_end]
    return bool(_DOB_CONTEXT_KEYWORDS.search(window))


def _detect_regex(text: str) -> list[DetectedEntity]:
    """Run all regex patterns against text. Returns raw matches (may overlap)."""
    results: list[DetectedEntity] = []
    for pii_type, pattern, confidence in _REGEX_PATTERNS:
        for match in pattern.finditer(text):
            # DOB requires context keyword nearby
            if pii_type == PIIType.DATE_OF_BIRTH:
                if not _has_dob_context(text, match.start(), match.end()):
                    continue
            results.append(
                DetectedEntity(
                    start=match.start(),
                    end=match.end(),
                    pii_type=pii_type,
                    value=match.group(),
                    confidence=confidence,
                    source=DetectionSource.REGEX,
                )
            )

    # Extract emails embedded in URLs (e.g., ?email=user@example.com)
    for match in re.finditer(r"[?&]email=([^&\s]+@[^&\s]+)", text):
        results.append(
            DetectedEntity(
                start=match.start(1),
                end=match.end(1),
                pii_type=PIIType.EMAIL,
                value=match.group(1),
                confidence=0.95,
                source=DetectionSource.REGEX,
            )
        )

    # Context-aware: detect PII values inside JSON-like structures
    # Matches "key": "value" where key hints at PII type
    _JSON_PII_KEYS = {
        "ssn": PIIType.SSN, "social_security": PIIType.SSN,
        "user": PIIType.CREDENTIAL, "username": PIIType.CREDENTIAL,
        "login": PIIType.CREDENTIAL, "account": PIIType.CREDENTIAL,
        "token": PIIType.CREDENTIAL, "tokens": PIIType.CREDENTIAL,
        "secret": PIIType.CREDENTIAL, "password": PIIType.CREDENTIAL,
        "api_key": PIIType.API_KEY, "apikey": PIIType.API_KEY,
        "email": PIIType.EMAIL, "mail": PIIType.EMAIL,
        "phone": PIIType.PHONE, "mobile": PIIType.PHONE,
        "name": PIIType.PERSON, "full_name": PIIType.PERSON,
        "card": PIIType.CREDIT_CARD, "cards": PIIType.CREDIT_CARD,
        "cc": PIIType.CREDIT_CARD, "credit_card": PIIType.CREDIT_CARD,
        "address": PIIType.ADDRESS, "addr": PIIType.ADDRESS,
        "aadhaar": PIIType.AADHAAR, "pan": PIIType.PAN,
    }
    for match in re.finditer(
        r'"(' + "|".join(re.escape(k) for k in _JSON_PII_KEYS) + r')"\s*:\s*'
        r'(?:"([^"]{2,})"|\[([^\]]+)\])',
        text, re.IGNORECASE,
    ):
        key = match.group(1).lower()
        pii_type = _JSON_PII_KEYS.get(key)
        if not pii_type:
            continue
        if match.group(2):
            # Simple string value: "key": "value"
            val = match.group(2)
            val_start = match.start(2)
            val_end = match.end(2)
            # Skip if already detected at this span
            already = any(r.start == val_start and r.end == val_end for r in results)
            if not already:
                results.append(DetectedEntity(
                    start=val_start, end=val_end,
                    pii_type=pii_type, value=val,
                    confidence=0.85, source=DetectionSource.REGEX,
                ))
        elif match.group(3):
            # Array: "key": ["val1", "val2"]
            array_text = match.group(3)
            array_offset = match.start(3)
            for arr_match in re.finditer(r'"([^"]{2,})"', array_text):
                val = arr_match.group(1)
                val_start = array_offset + arr_match.start(1)
                val_end = array_offset + arr_match.end(1)
                already = any(r.start == val_start and r.end == val_end for r in results)
                if not already:
                    results.append(DetectedEntity(
                        start=val_start, end=val_end,
                        pii_type=pii_type, value=val,
                        confidence=0.80, source=DetectionSource.REGEX,
                    ))

    # Context-aware: detect token=VALUE, secret=VALUE in plain text
    for match in re.finditer(
        r"\b(token|secret|credential|auth)\s*=\s*([A-Za-z0-9\-_\.]{3,})",
        text, re.IGNORECASE,
    ):
        val = match.group(2)
        val_start = match.start(2)
        val_end = match.end(2)
        already = any(r.start == val_start and r.end == val_end for r in results)
        if not already:
            results.append(DetectedEntity(
                start=val_start, end=val_end,
                pii_type=PIIType.CREDENTIAL, value=val,
                confidence=0.85, source=DetectionSource.REGEX,
            ))

    return results


# ---------------------------------------------------------------------------
# Layer 2: Presidio + spaCy
# ---------------------------------------------------------------------------

# Lazy-loaded to avoid slow import on module load.
_analyzer = None

_PRESIDIO_TYPE_MAP: dict[str, PIIType] = {
    "PERSON": PIIType.PERSON,
    "LOCATION": PIIType.LOCATION,
    "ORGANIZATION": PIIType.ORGANIZATION,
    "EMAIL_ADDRESS": PIIType.EMAIL,
    "PHONE_NUMBER": PIIType.PHONE,
    "US_SSN": PIIType.SSN,
    "CREDIT_CARD": PIIType.CREDIT_CARD,
    "IBAN_CODE": PIIType.IBAN,
    "IP_ADDRESS": PIIType.IP_ADDRESS,
    # DATE_TIME excluded — Presidio flags generic words like "quarterly", "last month".
    # Specific dates (DOB) are handled by regex with proper patterns.
    "NRP": PIIType.PERSON,  # nationality/religion/political group
    "MEDICAL_LICENSE": PIIType.MEDICAL_RECORD,
    "US_DRIVER_LICENSE": PIIType.DRIVERS_LICENSE,
    "US_PASSPORT": PIIType.PASSPORT,
    "UK_NHS": PIIType.MEDICAL_RECORD,
    "US_BANK_NUMBER": PIIType.BANK_ACCOUNT,
    "US_ITIN": PIIType.SSN,
    "AU_ABN": PIIType.ORGANIZATION,
    "AU_ACN": PIIType.ORGANIZATION,
    "AU_TFN": PIIType.SSN,
    "AU_MEDICARE": PIIType.MEDICAL_RECORD,
    "IN_AADHAAR": PIIType.AADHAAR,
    "IN_PAN": PIIType.PAN,
    "IN_ADDRESS": PIIType.ADDRESS,
}


def _get_analyzer():
    """Lazy-init Presidio analyzer with spaCy NER backend."""
    global _analyzer
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        })
        nlp_engine = provider.create_engine()
        _analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

        # Register custom Indian address recognizer
        from tools.indian_address_recognizer import create_indian_recognizers
        for recognizer in create_indian_recognizers():
            _analyzer.registry.add_recognizer(recognizer)

    return _analyzer


# ---------------------------------------------------------------------------
# NER quality filters
# ---------------------------------------------------------------------------

# Technical keywords that spaCy NER wrongly classifies as ORG/PERSON/LOCATION
_NER_BLACKLIST = {
    # Protocols & standards
    "ip", "tcp", "udp", "dns", "ftp", "smtp", "imap", "pop3", "http",
    "https", "ssh", "ssl", "tls", "cors", "rest", "graphql", "oauth",
    "saml", "ldap", "snmp", "mqtt", "grpc", "websocket",
    # Data formats
    "json", "xml", "html", "css", "csv", "pdf", "yaml", "toml", "svg",
    "png", "jpg", "gif", "mp4", "wav",
    # Tech terms commonly misidentified
    "api", "api_key", "api key", "url", "uri", "sql", "jwt", "uuid",
    "guid", "regex", "cron", "ascii", "utf", "utf-8", "utf8", "iso",
    "ssn", "vin", "iban", "bic", "ein", "pan", "upi", "otp", "pin",
    "mac", "nfc", "rfid", "gps",
    # Platforms & tools
    "unix", "linux", "macos", "windows", "docker", "nginx", "redis",
    "kafka", "kubernetes", "git", "npm", "pip", "aws", "gcp", "azure",
    # Timezones & units
    "utc", "gmt", "est", "pst", "cst", "mst", "ist", "bst", "cet",
    "aest", "jst", "kst",
    # OS / architecture fragments from user-agent strings
    "win64", "win32", "x64", "x86", "x86_64", "arm64", "amd64",
    "intel", "mozilla",
    # Common NER false positives
    "social security", "api_key", "the", "end",
    # Directional / address fragments
    "nw", "ne", "sw", "se", "n", "s", "e", "w",
}

# Multi-word phrases that should never be ORGANIZATION
_ORG_PHRASE_BLACKLIST = {
    "social security", "third-party monitoring systems",
    "third party monitoring systems", "error messages",
    "stack traces", "crash reports", "error logs",
}


def _looks_like_person(value: str) -> bool:
    """Check if a PERSON entity actually looks like a human name."""
    v = value.strip()
    if not v or not any(c.isalpha() for c in v):
        return False
    # Single short ALL-CAPS word = likely acronym, not a name
    if len(v) < 6 and v.isupper() and " " not in v:
        return False
    # Contains = or : → likely key=value, not a name
    if "=" in v or ":" in v:
        return False
    # Single lowercase word → names are capitalized
    words = v.split()
    if len(words) == 1 and v[0].islower():
        return False
    # Purely numeric or hex-like → not a name
    if all(c in "0123456789abcdefABCDEF-_ " for c in v):
        return False
    # Contains digits mixed in → likely a token/identifier, not a name
    if any(c.isdigit() for c in v):
        return False
    return True


def _looks_like_organization(value: str) -> bool:
    """Check if an ORGANIZATION entity is plausible (not a tech term or noise)."""
    v = value.strip()
    low = v.lower()
    # Check phrase blacklist
    if low in _ORG_PHRASE_BLACKLIST:
        return False
    # Single word that's ALL-CAPS and short → likely acronym/keyword
    if " " not in v and len(v) <= 5 and v.isupper():
        return False
    # Contains only hex/base64 chars and is long → likely encoded data, not org
    if len(v) > 15 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in v):
        return False
    # Contains digits mixed with letters in non-org patterns
    if any(c.isdigit() for c in v) and not any(w in low for w in ("inc", "ltd", "corp", "llc", "co", "group", "bank", "systems")):
        return False
    return True


def _detect_presidio(text: str) -> list[DetectedEntity]:
    """Run Presidio analyzer against text."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(text=text, language="en")
    entities: list[DetectedEntity] = []
    for result in results:
        pii_type = _PRESIDIO_TYPE_MAP.get(result.entity_type)
        if pii_type is None:
            continue
        # Filter out low-confidence Presidio guesses
        if result.score < 0.6:
            continue
        value = text[result.start:result.end]
        # Blacklist technical keywords misidentified by NER
        if value.lower().strip() in _NER_BLACKLIST:
            continue
        # Trim PERSON entities that grabbed non-name trailing text
        # e.g., "Michael R. Thompson - Case" → "Michael R. Thompson"
        if pii_type == PIIType.PERSON:
            sep = re.search(r"\s[-–—]\s", value)
            if sep:
                value = value[:sep.start()]
                result_end = result.start + len(value)
            else:
                result_end = result.end
        else:
            result_end = result.end
        # Validate PERSON entities look like real human names
        if pii_type == PIIType.PERSON and not _looks_like_person(value):
            continue
        # Validate ORGANIZATION entities are plausible
        if pii_type == PIIType.ORGANIZATION and not _looks_like_organization(value):
            continue
        # Reject EMAIL entities that are actually URLs (Presidio grabs full
        # URL containing email query params as a single EMAIL entity)
        if pii_type == PIIType.EMAIL and ("/" in value or "?" in value):
            continue
        entities.append(
            DetectedEntity(
                start=result.start,
                end=result_end,
                pii_type=pii_type,
                value=value,
                confidence=round(result.score, 2),
                source=DetectionSource.PRESIDIO,
            )
        )
    return entities


# ---------------------------------------------------------------------------
# Merge & deduplicate
# ---------------------------------------------------------------------------

def _spans_overlap(a: DetectedEntity, b: DetectedEntity) -> bool:
    """Check if two entity spans overlap."""
    return a.start < b.end and b.start < a.end


# Generic NER types that should be suppressed when a specific regex type exists
_GENERIC_NER_TYPES = {PIIType.ORGANIZATION, PIIType.PERSON, PIIType.LOCATION}
_SPECIFIC_REGEX_TYPES = {
    PIIType.SSN, PIIType.CREDIT_CARD, PIIType.IP_ADDRESS, PIIType.API_KEY,
    PIIType.AADHAAR, PIIType.PAN, PIIType.PHONE, PIIType.EMAIL,
    PIIType.ADDRESS, PIIType.USERNAME_PASSWORD, PIIType.CREDENTIAL,
}


def _merge_results(
    regex_results: list[DetectedEntity],
    presidio_results: list[DetectedEntity],
) -> list[DetectedEntity]:
    """
    Merge results from both layers. When spans overlap:
    - If same PII type: keep the one with higher confidence.
    - If different PII types: keep both (different findings for same span).
    - Suppress generic NER types (ORG/PERSON/LOCATION) when a specific regex
      type (SSN/CREDIT_CARD/IP/API_KEY/etc.) exists on the same span.
    """
    merged: list[DetectedEntity] = list(regex_results)

    for p_entity in presidio_results:
        # If this is a generic NER type, check if a specific regex already covers this span
        if p_entity.pii_type in _GENERIC_NER_TYPES:
            has_specific = any(
                _spans_overlap(m, p_entity)
                and m.source == DetectionSource.REGEX
                and m.pii_type in _SPECIFIC_REGEX_TYPES
                for m in merged
            )
            if has_specific:
                continue  # suppress generic NER

        overlapping = [
            m for m in merged
            if _spans_overlap(m, p_entity) and m.pii_type == p_entity.pii_type
        ]
        if not overlapping:
            merged.append(p_entity)
        else:
            for existing in overlapping:
                if p_entity.confidence > existing.confidence:
                    merged.remove(existing)
                    merged.append(p_entity)

    merged.sort(key=lambda e: (e.start, e.end))
    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def bucket_entities(
    entities: list[DetectedEntity],
) -> dict[str, list[DetectedEntity]]:
    """
    Group entities by confidence level for user review UI.

    Args:
        entities: List of detected entities.

    Returns:
        Dictionary with keys:
        - "high": entities with confidence >= 0.85 (pre-checked in UI)
        - "medium": entities with 0.50 <= confidence < 0.85 (shown for review)
        - "low": entities with confidence < 0.50 (ignored)
    """
    from tools.config import CONFIDENCE_HIGH, CONFIDENCE_LOW

    buckets: dict[str, list[DetectedEntity]] = {
        "high": [],
        "medium": [],
        "low": [],
    }
    for e in entities:
        if e.confidence >= CONFIDENCE_HIGH:
            buckets["high"].append(e)
        elif e.confidence >= CONFIDENCE_LOW:
            buckets["medium"].append(e)
        else:
            buckets["low"].append(e)
    return buckets


def detect(
    text: str,
    use_presidio: bool = True,
    use_llm: bool | None = None,
) -> list[DetectedEntity]:
    """
    Detect all PII in the given text.

    Args:
        text: The input text to scan.
        use_presidio: If True, runs both regex and Presidio layers.
                      If False, runs regex only (faster, less accurate).
        use_llm: If True, validates medium-confidence entities via Ollama LLM.
                 If None, uses the USE_LLM_VALIDATION config setting (default: False).

    Returns:
        List of DetectedEntity objects sorted by position.
    """
    if not text or not text.strip():
        return []

    # Respect config flag if not explicitly set
    if use_llm is None:
        from tools.config import USE_LLM_VALIDATION
        use_llm = USE_LLM_VALIDATION

    regex_results = _detect_regex(text)

    if use_presidio:
        presidio_results = _detect_presidio(text)
        merged = _merge_results(regex_results, presidio_results)
    else:
        merged = sorted(regex_results, key=lambda e: (e.start, e.end))

    if use_llm:
        from tools.llm_validator import validate_entities
        from tools.config import REDACTION_THRESHOLD
        merged = validate_entities(merged, text)
        merged = [e for e in merged if e.confidence >= REDACTION_THRESHOLD]

    return merged
