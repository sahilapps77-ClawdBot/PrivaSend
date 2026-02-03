# Workflow: Redact Text

> **Objective:** Replace detected PII with reversible placeholders

## When to Use

- Before sending user input to AI
- Sanitizing documents for sharing
- Creating training data without real PII

## Required Inputs

| Input | Type | Description |
|-------|------|-------------|
| `text` | string | Original text with PII |
| `entities` | list | Output from `detect_pii()` |

## Tool to Execute

```bash
python -c "
from tools.detect_pii import detect_pii
from tools.redact import redact_text

text = 'Contact john@example.com'
entities = detect_pii(text)
result = redact_text(text, entities)
print(result)
"
```

Or via API:
```bash
curl -X POST http://localhost:8000/redact \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact john@example.com or call 555-123-4567"}'
```

## Expected Output

```json
{
  "redacted_text": "Contact [EMAIL_1] or call [PHONE_NUMBER_1]",
  "mapping": {
    "[EMAIL_1]": "john@example.com",
    "[PHONE_NUMBER_1]": "555-123-4567"
  },
  "entity_count": 2
}
```

## Placeholder Format

```
[{ENTITY_TYPE}_{INDEX}]
```

Examples:
- `[EMAIL_1]`, `[EMAIL_2]`
- `[PERSON_1]`, `[PERSON_2]`
- `[PHONE_NUMBER_1]`

## De-redaction

To restore original values:

```python
from tools.redact import deredact_text

redacted = "Hello [PERSON_1], your email is [EMAIL_1]"
mapping = {"[PERSON_1]": "John", "[EMAIL_1]": "john@example.com"}
original = deredact_text(redacted, mapping)
# "Hello John, your email is john@example.com"
```

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No entities | Return original text unchanged |
| Same value multiple times | Same placeholder reused |
| Nested entities | Outer entity takes precedence |

## Verification

```bash
pytest tests/test_redact.py -v
```

## Security Notes

- Mapping stored in-memory only (no persistence for MVP)
- Mapping should be cleared after request completes
- Never log original PII values
