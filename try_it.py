"""
Manual testing script — Run this to test PII detection yourself.

Usage:
    python try_it.py

Loads both regex AND Presidio+spaCy (full detection).
First run takes ~10 seconds to load the spaCy model, then each scan is fast.
"""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from tools.detect_pii import detect
from tools.redact import redact, deredact


def main():
    print("=" * 60)
    print("  PrivaSend — Manual PII Detection Tester")
    print("  (Full mode: Regex + Presidio + spaCy NER)")
    print("=" * 60)
    print()
    print("Loading spaCy model... (one-time, ~10 seconds)")
    print()

    # Force-load the model now so the user sees the wait upfront
    from tools.detect_pii import _get_analyzer
    _get_analyzer()

    print("Model loaded. Ready to scan.")
    print()
    print("Type or paste text below, then press Enter twice to scan.")
    print("Type 'quit' to exit.")
    print()

    while True:
        print("-" * 60)
        print("Enter text (press Enter twice when done):")
        print()

        lines = []
        while True:
            line = input()
            if line == "":
                if lines:
                    break
                continue
            if line.strip().lower() == "quit":
                print("Goodbye.")
                return
            lines.append(line)

        text = "\n".join(lines)

        print()
        print("Scanning with Regex + Presidio + spaCy...")
        print()

        # Full detection: regex + Presidio
        entities = detect(text, use_presidio=True)

        if not entities:
            print("  No PII detected.")
            print()
            continue

        # Show what was found
        print(f"  Found {len(entities)} PII item(s):")
        print()
        print(f"  {'#':<4} {'Type':<25} {'Value':<35} {'Conf':<8} {'Source'}")
        print(f"  {'-'*4} {'-'*25} {'-'*35} {'-'*8} {'-'*10}")

        for i, entity in enumerate(entities, 1):
            val_display = entity.value if len(entity.value) <= 33 else entity.value[:30] + "..."
            print(
                f"  {i:<4} {entity.pii_type.value:<25} "
                f"{val_display:<35} {entity.confidence:<8.0%} "
                f"{entity.source.value}"
            )

        print()

        # Show redacted version
        result = redact(text, entities)
        print("  Redacted text:")
        for line in result.redacted_text.split("\n"):
            print(f"    {line}")
        print()

        # Show mapping
        print("  Mapping (for de-redaction):")
        for placeholder, original in result.mapping.items():
            print(f"    {placeholder} -> {original}")
        print()

        # Show roundtrip
        restored = deredact(result.redacted_text, result.mapping)
        if restored == text:
            print("  Roundtrip: PASS (de-redaction restores original perfectly)")
        else:
            print("  Roundtrip: FAIL")
            print(f"    Original:  {text[:100]}")
            print(f"    Restored:  {restored[:100]}")
        print()


if __name__ == "__main__":
    main()
