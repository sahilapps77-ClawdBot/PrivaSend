# PrivaSend — Architecture

> **Last updated:** 2026-01-28

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                           │
│  HTML Form: text input / file upload / send-to-AI btn   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP POST
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI SERVER                         │
│                                                         │
│  POST /analyze    → detect PII, return findings         │
│  POST /redact     → detect + redact, return redacted    │
│  POST /send-to-ai → redact → OpenAI → de-redact        │
│                                                         │
└──────┬──────────────┬──────────────┬────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│  EXTRACT   │ │  DETECT    │ │  AI PROXY  │
│            │ │            │ │            │
│ PDF→text   │ │ Layer 1:   │ │ Redact     │
│ DOCX→text  │ │  Regex     │ │ → OpenAI   │
│ Image→OCR  │ │ Layer 2:   │ │ → De-redact│
│            │ │  Presidio  │ │ → Return   │
│ pdfplumber │ │  + spaCy   │ │            │
│ python-docx│ │ Merge +    │ │ openai SDK │
│ pytesseract│ │ Dedup      │ │            │
└────────────┘ └────────────┘ └────────────┘
       ▲              ▲              ▲
       │              │              │
       └──────────────┴──────────────┘
                tools/ directory
```

## Data Flow

### Standard Redaction Flow

```
1. User submits text or file
2. If file → extract_text.py converts to plain text
3. detect_pii.py runs:
   a. Regex layer scans for structured patterns (<10ms)
   b. Presidio+spaCy scans for names/addresses/orgs (~100-200ms)
   c. Results merged, overlapping spans deduplicated (keep highest confidence)
4. redact.py replaces each PII span with [TYPE_N] placeholder
   - Stores mapping: { "[EMAIL_1]": "john@example.com", "[NAME_1]": "John Smith" }
5. Returns: redacted text + detection report + mapping ID
```

### Send-to-AI Flow

```
1. User clicks "Send to AI" with redacted text
2. ai_proxy.py sends redacted text to OpenAI
3. OpenAI responds (sees only placeholders, never real PII)
4. ai_proxy.py replaces placeholders back with original values
5. Returns de-redacted AI response to user
```

## Component Responsibilities

### tools/detect_pii.py
- Owns ALL detection logic
- Regex patterns organized by PII type (email, phone, ssn, etc.)
- Presidio analyzer initialization and execution
- Result merging and deduplication
- Returns list of `DetectedEntity(type, start, end, value, confidence, source)`

### tools/redact.py
- Takes text + list of detected entities
- Generates numbered placeholders per type: `[EMAIL_1]`, `[EMAIL_2]`, `[NAME_1]`
- Builds reversible mapping dict
- De-redaction function: takes text + mapping, restores originals

### tools/extract_text.py
- Dispatches by file type (MIME or extension)
- PDF: `pdfplumber` → concatenate page text
- DOCX: `python-docx` → concatenate paragraph text
- Image: `pytesseract.image_to_string()`
- Returns plain text string

### tools/ai_proxy.py
- Accepts redacted text + mapping
- Sends to OpenAI chat completions API
- De-redacts the response using mapping
- Returns final response with original values restored

### server/main.py
- FastAPI app with 3 endpoints
- File upload handling (multipart/form-data)
- Request validation via pydantic models
- Serves static frontend

## Security Considerations

- Original PII never leaves the server (Presidio runs locally)
- OpenAI only sees redacted text
- Mapping is in-memory, per-request (not persisted)
- `.env` stores API keys, gitignored
- No logging of original PII values
