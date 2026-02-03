# Workflow: Detect PII

> **Objective:** Run PII detection on input text using the two-layer engine (Regex + Presidio NER)

## When to Use

- Processing user input before sending to AI
- Analyzing documents for sensitive data
- Testing detection accuracy

## Required Inputs

| Input | Type | Description |
|-------|------|-------------|
| `text` | string | The text to analyze |
| `language` | string | Language code (default: `en`) |

## Tool to Execute

```bash
# From project root
python -c "from tools.detect_pii import detect_pii; print(detect_pii('Your text here'))"
```

Or via API:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact john@example.com or call 555-123-4567"}'
```

## Expected Output

```json
{
  "entities": [
    {
      "type": "EMAIL",
      "value": "john@example.com",
      "start": 8,
      "end": 24,
      "confidence": 1.0,
      "source": "regex"
    },
    {
      "type": "PHONE_NUMBER",
      "value": "555-123-4567",
      "start": 33,
      "end": 45,
      "confidence": 1.0,
      "source": "regex"
    }
  ]
}
```

## Detection Layers

### Layer 1: Regex (Deterministic, <10ms)
- Runs first, catches structured patterns
- High confidence (1.0) for exact matches
- See `tools/config.py` for all patterns

### Layer 2: Presidio + spaCy NER (~100-200ms)
- Runs second, catches context-dependent PII
- Names, addresses, organizations, locations
- Confidence varies (0.0-1.0)

### Merge Strategy
1. Run both layers
2. Deduplicate overlapping spans
3. Keep highest-confidence match for overlaps

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Empty input | Return empty entities list |
| No PII found | Return empty entities list |
| Overlapping entities | Keep highest confidence |
| Mixed languages | Best-effort detection |

## Verification

```bash
pytest tests/test_detect_pii.py -v
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Presidio not loading | Run `python -m spacy download en_core_web_lg` |
| Slow performance | Check if spaCy model loaded correctly |
| False positives | Review `tools/config.py` patterns |
