# Workflow: Add New PII Type

> **Objective:** Add a new PII detection pattern (regex or NER-based)

## When to Use

- Adding support for a new document type (e.g., GSTIN, voter ID)
- Improving detection for a specific region
- Fixing false negatives for known patterns

## Decision: Regex vs NER

| Use Regex When | Use NER When |
|----------------|--------------|
| Pattern has fixed format | Pattern is context-dependent |
| High precision required | Need semantic understanding |
| Examples: SSN, credit card, email | Examples: names, addresses, organizations |

---

## Adding a Regex Pattern

### Step 1: Define the Pattern

Add to `tools/config.py`:

```python
PII_PATTERNS = {
    # ... existing patterns ...

    "GSTIN": {
        "pattern": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b",
        "description": "Indian GST Identification Number",
        "examples": ["22AAAAA0000A1Z5"],
        "region": "India"
    }
}
```

### Step 2: Add Test Cases

Create tests in `tests/test_detect_pii.py`:

```python
def test_gstin_detection():
    """Test GSTIN (Indian GST number) detection."""
    text = "Company GSTIN: 22AAAAA0000A1Z5"
    entities = detect_pii(text)

    assert len(entities) == 1
    assert entities[0]["type"] == "GSTIN"
    assert entities[0]["value"] == "22AAAAA0000A1Z5"

def test_gstin_false_positive():
    """Ensure random alphanumeric strings don't match."""
    text = "Reference code: ABC123XYZ"
    entities = detect_pii(text)

    gstin_entities = [e for e in entities if e["type"] == "GSTIN"]
    assert len(gstin_entities) == 0
```

### Step 3: Verify

```bash
pytest tests/test_detect_pii.py -v -k "gstin"
```

### Step 4: Add to Evaluation Dataset

Add examples to `tests/dataset_realistic.py`:

```python
GSTIN_CASES = [
    {"text": "Invoice from GSTIN 22AAAAA0000A1Z5", "expected": ["GSTIN"]},
    {"text": "Tax ID: 27AABCU9603R1ZM", "expected": ["GSTIN"]},
]
```

### Step 5: Run Full Evaluation

```bash
pytest tests/test_evaluation.py -v
```

---

## Adding a Presidio Recognizer

For context-dependent patterns, create a custom Presidio recognizer.

### Step 1: Create Recognizer

See `tools/indian_address_recognizer.py` as an example:

```python
from presidio_analyzer import Pattern, PatternRecognizer

class CustomRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern("PATTERN_NAME", r"your_regex_here", 0.5)
        ]
        super().__init__(
            supported_entity="YOUR_ENTITY_TYPE",
            patterns=patterns
        )
```

### Step 2: Register with Analyzer

In `tools/detect_pii.py`:

```python
from tools.custom_recognizer import CustomRecognizer

analyzer.registry.add_recognizer(CustomRecognizer())
```

### Step 3: Test and Verify

Same as regex steps 2-5.

---

## Checklist Before Merging

- [ ] Pattern tested with 5+ positive examples
- [ ] Pattern tested with 5+ negative examples (false positive check)
- [ ] Added to evaluation dataset
- [ ] All existing tests still pass
- [ ] Documentation updated (if user-facing)

## Verification

```bash
# Run all detection tests
pytest tests/test_detect_pii.py tests/test_evaluation.py -v
```
