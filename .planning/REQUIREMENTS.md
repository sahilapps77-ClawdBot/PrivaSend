# PrivaSend — Requirements

> **Last updated:** 2026-01-28
> **Status:** MVP Phase — Scope Frozen

## Product Summary

PrivaSend is a runtime prompt governance system that detects and redacts PII from user input before it reaches AI tools. It protects sensitive data while preserving the ability to use AI effectively.

## Scope — MVP (Phase 1)

### Input Formats

| Format | Method | Library |
|--------|--------|---------|
| Plain text | Direct input | — |
| PDF | File upload | `pdfplumber` |
| DOCX | File upload | `python-docx` |
| Images (PNG, JPG, TIFF) | File upload + OCR | `pytesseract` / Tesseract |

### PII Detection — Two-Layer Engine

**Layer 1: Regex (Deterministic, <10ms)**
Catches structured patterns with known formats.

| PII Type | Example | Region |
|----------|---------|--------|
| Email | `user@example.com` | Global |
| Phone number | `+1-555-123-4567`, `+91 98765 43210` | US, India, Intl |
| SSN | `123-45-6789` | US |
| Credit card | `4111-1111-1111-1111` | Global |
| API key | `sk-...`, `AKIA...` | Global |
| Aadhaar | `1234 5678 9012` | India |
| PAN | `ABCDE1234F` | India |
| Passport | `A12345678` | US, India |
| Driver's license | Various state formats | US |
| IBAN | `GB29 NWBK 6016 1331 9268 19` | Intl |
| Bank account | Various formats | US, India |
| Date of birth | `01/15/1990`, `15-Jan-1990` | Global |
| Medical record number | `MRN-123456` | US |
| IP address | `192.168.1.1`, IPv6 | Global |
| MAC address | `00:1A:2B:3C:4D:5E` | Global |
| VIN | `1HGCM82633A004352` | Global |
| URL with credentials | `https://user:pass@host` | Global |

**Layer 2: Presidio + spaCy NER (ML-based, ~100-200ms)**
Catches context-dependent PII that regex cannot.

| PII Type | Example |
|----------|---------|
| Person names | `John Smith`, `Priya Sharma` |
| Addresses | `42 Oak Street, New York, NY 10001` |
| Organizations | `Goldman Sachs`, `Infosys` |
| Locations | `Mumbai`, `California` |
| Medical conditions | `diagnosed with diabetes` |
| Date/time (contextual) | `born on January 15` |

**Merging strategy:** Run both layers, deduplicate overlapping spans, keep highest-confidence match.

### Redaction

- Reversible: placeholders like `[EMAIL_1]`, `[NAME_2]` with a mapping table
- Mapping stored in-memory per request (no persistence for MVP)
- De-redaction available when AI response comes back

### Output

1. **Redacted text** — with numbered placeholders
2. **Detection report** — table of findings: entity type, original value (masked), confidence score, detection layer (regex/NER)
3. **Send to AI** — forward redacted text to OpenAI, receive response, de-redact and display

### Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Backend | FastAPI (Python 3.11+) | Async, auto OpenAPI docs, production-ready |
| PII Detection | Regex + Microsoft Presidio | Deterministic + ML hybrid |
| NER Model | spaCy `en_core_web_lg` | Best accuracy for English NER |
| PDF extraction | `pdfplumber` | Handles tables, layouts |
| DOCX extraction | `python-docx` | Native .docx parsing |
| OCR | `pytesseract` + Tesseract | Open source, proven |
| LLM | OpenAI API (`gpt-4o`) | User's choice |
| Frontend | Vanilla HTML/CSS/JS | Simple, no build step |

### Non-Goals (MVP)

- User authentication / multi-tenancy
- Persistent storage / database
- Browser extension
- Real-time streaming redaction
- Custom PII type training
- n8n integration (deferred to Phase 2)
- Deployment to cloud (local only for MVP)

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-28 | Standalone Python app, not n8n | Build and test logic locally first, migrate later |
| 2026-01-28 | Hybrid framework (WAT + GSD planning) | WAT for code structure, GSD for project tracking |
| 2026-01-28 | Presidio as pip package, not Docker | Simpler local dev, same accuracy |
| 2026-01-28 | FastAPI over Flask | Async, OpenAPI docs, pydantic validation |
| 2026-01-28 | All input formats from day one | Phased internally (text → PDF/DOCX → images) |
| 2026-01-28 | Reversible redaction | Required for send-to-AI → de-redact flow |
| 2026-01-28 | Everything possible PII scope | Comprehensive coverage from start |
