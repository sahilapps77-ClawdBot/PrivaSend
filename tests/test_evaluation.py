"""
Automated evaluation — runs both datasets and produces an accuracy report.

Run:
    python -m pytest tests/test_evaluation.py -v --tb=no -q
    OR for full report:
    python -m tests.test_evaluation
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.detect_pii import PIIType, detect

from tests.dataset_realistic import SAMPLES as REALISTIC
from tests.dataset_adversarial import SAMPLES as ADVERSARIAL


def _evaluate_sample(sample: dict, use_presidio: bool = True) -> dict:
    """Evaluate a single sample and return results."""
    text = sample["text"]
    expected: set[PIIType] = sample["expected"]
    acceptable_fps: set[PIIType] = sample.get("acceptable_false_positives", set())

    entities = detect(text, use_presidio=use_presidio)
    detected_types = {e.pii_type for e in entities if e.confidence >= 0.5}

    # True positives: expected and detected
    true_positives = expected & detected_types
    # False negatives: expected but not detected
    false_negatives = expected - detected_types
    # False positives: detected but not expected (excluding acceptable ones)
    false_positives = detected_types - expected - acceptable_fps

    return {
        "id": sample["id"],
        "description": sample["description"],
        "expected": expected,
        "detected": detected_types,
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "pass": len(false_negatives) == 0 and len(false_positives) == 0,
    }


def _run_evaluation(samples: list[dict], name: str, use_presidio: bool = True):
    """Run evaluation on a dataset and print report."""
    results = [_evaluate_sample(s, use_presidio=use_presidio) for s in samples]

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    failed = total - passed

    total_expected = sum(len(r["expected"]) for r in results)
    total_tp = sum(len(r["true_positives"]) for r in results)
    total_fn = sum(len(r["false_negatives"]) for r in results)
    total_fp = sum(len(r["false_positives"]) for r in results)

    recall = total_tp / total_expected * 100 if total_expected > 0 else 100
    precision = total_tp / (total_tp + total_fp) * 100 if (total_tp + total_fp) > 0 else 100

    print()
    print("=" * 70)
    print(f"  {name}")
    print("=" * 70)
    print(f"  Samples: {total} | Passed: {passed} | Failed: {failed}")
    print(f"  Recall:    {recall:.1f}% ({total_tp}/{total_expected} PII types detected)")
    print(f"  Precision: {precision:.1f}% ({total_fp} false positives)")
    print()

    if failed > 0:
        print("  FAILURES:")
        print(f"  {'ID':<10} {'Description':<40} {'Missed':<25} {'False Pos'}")
        print(f"  {'-'*10} {'-'*40} {'-'*25} {'-'*25}")
        for r in results:
            if not r["pass"]:
                missed = ", ".join(t.value for t in r["false_negatives"]) or "—"
                fps = ", ".join(t.value for t in r["false_positives"]) or "—"
                print(f"  {str(r['id']):<10} {r['description']:<40} {missed:<25} {fps}")
        print()

    return {
        "total": total,
        "passed": passed,
        "recall": recall,
        "precision": precision,
        "total_fn": total_fn,
        "total_fp": total_fp,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Pytest integration — each sample is a test case
# ---------------------------------------------------------------------------

import pytest


@pytest.mark.parametrize(
    "sample",
    REALISTIC,
    ids=[f"realistic-{s['id']}" for s in REALISTIC],
)
def test_realistic(sample):
    result = _evaluate_sample(sample)
    if result["false_negatives"]:
        missed = ", ".join(t.value for t in result["false_negatives"])
        pytest.fail(
            f"[{sample['description']}] Missed PII types: {missed}"
        )
    # We don't fail on false positives for realistic dataset — just warn
    if result["false_positives"]:
        fps = ", ".join(t.value for t in result["false_positives"])
        import warnings
        warnings.warn(f"[{sample['description']}] False positives: {fps}")


@pytest.mark.parametrize(
    "sample",
    ADVERSARIAL,
    ids=[f"adversarial-{s['id']}" for s in ADVERSARIAL],
)
def test_adversarial(sample):
    result = _evaluate_sample(sample)
    if result["false_negatives"]:
        missed = ", ".join(t.value for t in result["false_negatives"])
        pytest.fail(
            f"[{sample['description']}] Missed PII types: {missed}"
        )


# ---------------------------------------------------------------------------
# Standalone report
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  PRIVASEND — PII DETECTION ACCURACY REPORT")
    print("=" * 70)

    r1 = _run_evaluation(REALISTIC, "REALISTIC DATASET (50 samples)")
    r2 = _run_evaluation(ADVERSARIAL, "ADVERSARIAL DATASET (30 samples)")

    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    total_samples = r1["total"] + r2["total"]
    total_passed = r1["passed"] + r2["passed"]
    print(f"  Overall: {total_passed}/{total_samples} samples passed")
    print(f"  Realistic recall:    {r1['recall']:.1f}%")
    print(f"  Adversarial recall:  {r2['recall']:.1f}%")
    print(f"  Total missed types:  {r1['total_fn'] + r2['total_fn']}")
    print(f"  Total false pos:     {r1['total_fp'] + r2['total_fp']}")
    print("=" * 70)
