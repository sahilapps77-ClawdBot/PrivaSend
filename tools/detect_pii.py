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
    PERSON = "PERSON"
    ADDRESS = "ADDRESS"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    MEDICAL_CONDITION = "MEDICAL_CONDITION"
    DATE_TIME = "DATE_TIME"


class DetectionSource(str, Enum):
    REGEX = "regex"
    PRESIDIO = "presidio"


@dataclass(frozen=True, order=True)
class DetectedEntity:
    """A single PII detection result."""
    start: int
    end: int
    pii_type: PIIType = field(compare=False)
    value: str = field(compare=False)
    confidence: float = field(compare=False)
    source: DetectionSource = field(compare=False)


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

# --- API keys ---
# OpenAI
_add(PIIType.API_KEY, r"\bsk-[A-Za-z0-9]{20,}\b", 0.95)
# AWS access key
_add(PIIType.API_KEY, r"\bAKIA[0-9A-Z]{16}\b", 0.95)
# Generic long hex/base64 tokens (40+ chars)
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

# --- URL with credentials ---
_add(
    PIIType.URL_WITH_CREDENTIALS,
    r"https?://[^\s:]+:[^\s@]+@[^\s]+",
    0.95,
)


def _detect_regex(text: str) -> list[DetectedEntity]:
    """Run all regex patterns against text. Returns raw matches (may overlap)."""
    results: list[DetectedEntity] = []
    for pii_type, pattern, confidence in _REGEX_PATTERNS:
        for match in pattern.finditer(text):
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
    "DATE_TIME": PIIType.DATE_TIME,
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
    return _analyzer


def _detect_presidio(text: str) -> list[DetectedEntity]:
    """Run Presidio analyzer against text."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(text=text, language="en")
    entities: list[DetectedEntity] = []
    for result in results:
        pii_type = _PRESIDIO_TYPE_MAP.get(result.entity_type)
        if pii_type is None:
            continue
        entities.append(
            DetectedEntity(
                start=result.start,
                end=result.end,
                pii_type=pii_type,
                value=text[result.start:result.end],
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


def _merge_results(
    regex_results: list[DetectedEntity],
    presidio_results: list[DetectedEntity],
) -> list[DetectedEntity]:
    """
    Merge results from both layers. When spans overlap:
    - If same PII type: keep the one with higher confidence.
    - If different PII types: keep both (different findings for same span).
    """
    # Start with all regex results
    merged: list[DetectedEntity] = list(regex_results)

    for p_entity in presidio_results:
        overlapping = [
            m for m in merged
            if _spans_overlap(m, p_entity) and m.pii_type == p_entity.pii_type
        ]
        if not overlapping:
            # No overlap with same type — add it
            merged.append(p_entity)
        else:
            # Overlap exists with same type — replace if Presidio has higher confidence
            for existing in overlapping:
                if p_entity.confidence > existing.confidence:
                    merged.remove(existing)
                    merged.append(p_entity)

    # Sort by position in text
    merged.sort(key=lambda e: (e.start, e.end))
    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect(text: str, use_presidio: bool = True) -> list[DetectedEntity]:
    """
    Detect all PII in the given text.

    Args:
        text: The input text to scan.
        use_presidio: If True, runs both regex and Presidio layers.
                      If False, runs regex only (faster, less accurate).

    Returns:
        List of DetectedEntity objects sorted by position.
    """
    if not text or not text.strip():
        return []

    regex_results = _detect_regex(text)

    if use_presidio:
        presidio_results = _detect_presidio(text)
        return _merge_results(regex_results, presidio_results)

    return sorted(regex_results, key=lambda e: (e.start, e.end))
