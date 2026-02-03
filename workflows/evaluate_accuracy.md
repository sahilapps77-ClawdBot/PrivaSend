# Workflow: Evaluate Detection Accuracy

> **Objective:** Measure PII detection precision, recall, and false positive rate

## When to Use

- After adding new PII patterns
- Before releasing a new version
- Comparing detection approaches
- Debugging false positives/negatives

## Required Inputs

| Input | Type | Description |
|-------|------|-------------|
| Dataset | Python module | Test cases with expected results |

## Datasets Available

| Dataset | Location | Purpose |
|---------|----------|---------|
| Realistic | `tests/dataset_realistic.py` | Common real-world patterns |
| Adversarial | `tests/dataset_adversarial.py` | Edge cases, tricky patterns |

## Tool to Execute

```bash
# Run full evaluation
pytest tests/test_evaluation.py -v

# Run with detailed output
pytest tests/test_evaluation.py -v --tb=long
```

## Metrics Explained

### Precision
```
Precision = True Positives / (True Positives + False Positives)
```
- High precision = Few false alarms
- Low precision = Flagging non-PII as PII

### Recall
```
Recall = True Positives / (True Positives + False Negatives)
```
- High recall = Catching most PII
- Low recall = Missing real PII

### F1 Score
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```
- Balanced measure of both

## Expected Output

```
================== Evaluation Results ==================
Dataset: realistic
Total cases: 50
Correct detections: 47
Missed detections: 2
False positives: 1

Precision: 97.9%
Recall: 95.9%
F1 Score: 96.9%

By Entity Type:
  EMAIL:        100.0% precision, 100.0% recall
  PHONE_NUMBER: 95.0% precision, 100.0% recall
  PERSON:       90.0% precision, 85.0% recall
  ADDRESS:      85.0% precision, 80.0% recall
========================================================
```

## Interpreting Results

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Precision | > 95% | Review false positives, tighten patterns |
| Recall | > 90% | Add more patterns, check NER coverage |
| F1 | > 92% | Balance precision/recall tradeoffs |

## Adding Test Cases

### To Realistic Dataset

```python
# tests/dataset_realistic.py
REALISTIC_CASES = [
    {
        "text": "Contact support@company.com for help",
        "expected": [{"type": "EMAIL", "value": "support@company.com"}]
    },
    # Add more cases...
]
```

### To Adversarial Dataset

```python
# tests/dataset_adversarial.py
ADVERSARIAL_CASES = [
    {
        "text": "Version 1.2.3.4 released",  # Looks like IP but isn't
        "expected": []  # Should NOT detect as IP
    },
    # Add more edge cases...
]
```

## Troubleshooting

| Issue | Investigation |
|-------|---------------|
| Low recall for names | Check spaCy model loaded correctly |
| High false positives | Review regex patterns in `tools/config.py` |
| Slow evaluation | Consider running subsets: `-k "email"` |

## Verification Checklist

Before shipping:
- [ ] Realistic dataset: F1 > 92%
- [ ] Adversarial dataset: Precision > 90%
- [ ] No regressions from previous version
- [ ] New patterns tested in both datasets
