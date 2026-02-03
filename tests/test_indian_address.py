"""Tests for Indian address custom Presidio recognizers."""

from __future__ import annotations

import pytest

from tools.detect_pii import detect, PIIType


@pytest.fixture(autouse=True)
def _no_llm():
    """All tests here run without LLM."""
    pass


def _find_type(entities, pii_type: PIIType) -> list:
    return [e for e in entities if e.pii_type == pii_type]


def test_model_town_detected():
    entities = detect("my address is Model Town phase 3", use_presidio=True, use_llm=False)
    addresses = _find_type(entities, PIIType.ADDRESS)
    values = [e.value for e in addresses]
    assert any("Model Town" in v for v in values), f"Expected Model Town in {values}"


def test_sector_with_city():
    entities = detect("I live in Sector 15, Noida", use_presidio=True, use_llm=False)
    addresses = _find_type(entities, PIIType.ADDRESS)
    values = [e.value for e in addresses]
    assert any("Sector" in v for v in values), f"Expected Sector address in {values}"


def test_lajpat_nagar():
    entities = detect("Office is at Lajpat Nagar", use_presidio=True, use_llm=False)
    addresses = _find_type(entities, PIIType.ADDRESS)
    values = [e.value for e in addresses]
    assert any("Lajpat Nagar" in v for v in values), f"Expected Lajpat Nagar in {values}"


def test_pin_code_with_city_context():
    entities = detect("Send to Delhi 110001", use_presidio=True, use_llm=False)
    addresses = _find_type(entities, PIIType.ADDRESS)
    values = [e.value for e in addresses]
    assert any("110001" in v for v in values), f"Expected PIN code in {values}"


def test_colony_pattern():
    entities = detect("Located at Ashok Vihar", use_presidio=True, use_llm=False)
    addresses = _find_type(entities, PIIType.ADDRESS)
    values = [e.value for e in addresses]
    assert any("Vihar" in v for v in values), f"Expected locality with Vihar in {values}"


def test_defence_colony():
    entities = detect("Meeting at Defence Colony", use_presidio=True, use_llm=False)
    addresses = _find_type(entities, PIIType.ADDRESS)
    values = [e.value for e in addresses]
    assert any("Defence Colony" in v for v in values), f"Expected Defence Colony in {values}"
