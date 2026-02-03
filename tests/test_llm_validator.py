"""Tests for LLM validator — all use mocked Ollama responses."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from tools.detect_pii import DetectedEntity, DetectionSource, PIIType
from tools.llm_validator import (
    validate_entities,
    _compute_final_confidence,
)


def _entity(
    value: str = "Test",
    pii_type: PIIType = PIIType.PERSON,
    confidence: float = 0.70,
    start: int = 0,
) -> DetectedEntity:
    return DetectedEntity(
        start=start,
        end=start + len(value),
        pii_type=pii_type,
        value=value,
        confidence=confidence,
        source=DetectionSource.PRESIDIO,
    )


# ---- Confidence math ----

def test_is_pii_true_blending():
    final, llm_conf, validated = _compute_final_confidence(0.70, {"is_pii": True, "confidence": 0.9})
    assert validated is True
    assert llm_conf == 0.9
    assert abs(final - (0.6 * 0.70 + 0.4 * 0.9)) < 0.001  # 0.78


def test_is_pii_false_kills_confidence():
    final, llm_conf, validated = _compute_final_confidence(0.70, {"is_pii": False, "confidence": 0.2})
    assert validated is True
    assert abs(final - 0.21) < 0.001  # 0.70 * 0.3


def test_none_result_passthrough():
    final, llm_conf, validated = _compute_final_confidence(0.70, None)
    assert validated is False
    assert llm_conf is None
    assert final == 0.70


# ---- Entity filtering (which go to LLM) ----

@patch("tools.llm_validator._call_ollama")
def test_high_confidence_skips_llm(mock_ollama):
    """Entities above 0.85 should NOT go to LLM."""
    entities = [_entity(confidence=0.90)]
    result = validate_entities(entities, "Test text")
    mock_ollama.assert_not_called()
    assert result[0].confidence == 0.90


@patch("tools.llm_validator._call_ollama")
def test_low_confidence_skips_llm(mock_ollama):
    """Entities below 0.60 should NOT go to LLM."""
    entities = [_entity(confidence=0.50)]
    result = validate_entities(entities, "Test text")
    mock_ollama.assert_not_called()
    assert result[0].confidence == 0.50


@patch("tools.llm_validator._call_ollama")
def test_medium_confidence_calls_llm(mock_ollama):
    """Entities between 0.60-0.85 SHOULD go to LLM."""
    mock_ollama.return_value = {"is_pii": True, "confidence": 0.9}
    entities = [_entity(confidence=0.70)]
    result = validate_entities(entities, "Test text with Test in it")
    mock_ollama.assert_called_once()
    assert result[0].llm_validated is True
    assert result[0].pre_llm_confidence == 0.70
    assert abs(result[0].confidence - 0.78) < 0.01


# ---- Fail-open ----

@patch("tools.llm_validator._call_ollama")
def test_fail_open_on_ollama_failure(mock_ollama):
    """When Ollama fails, entities pass through unchanged."""
    mock_ollama.return_value = None
    entities = [_entity(confidence=0.70), _entity(value="Second", confidence=0.75, start=10)]
    result = validate_entities(entities, "Test text Second text here")
    # First call fails, second should be skipped (ollama_available = False)
    assert mock_ollama.call_count == 1
    assert result[0].confidence == 0.70  # unchanged
    assert result[1].confidence == 0.75  # unchanged


@patch("tools.llm_validator._call_ollama")
def test_empty_entities(mock_ollama):
    result = validate_entities([], "some text")
    mock_ollama.assert_not_called()
    assert result == []
