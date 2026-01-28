# PrivaSend — Roadmap

> **Last updated:** 2026-01-28

## Milestone 1: Local MVP

### Phase 1A: Core Detection Engine
- [ ] Set up project structure (folders, venv, dependencies)
- [ ] Build regex PII detector — all pattern types
- [ ] Integrate Presidio + spaCy NER
- [ ] Build merge/deduplication logic (regex + NER results)
- [ ] Build reversible redaction engine (placeholder mapping)
- [ ] Write unit tests for detection + redaction

### Phase 1B: File Extraction
- [ ] PDF text extraction (`pdfplumber`)
- [ ] DOCX text extraction (`python-docx`)
- [ ] Image OCR extraction (`pytesseract`)
- [ ] Write tests for each extraction format

### Phase 1C: API Server
- [ ] FastAPI app with endpoints: `/analyze`, `/redact`, `/send-to-ai`
- [ ] Request/response schemas (pydantic models)
- [ ] File upload handling
- [ ] Error handling and validation
- [ ] OpenAI proxy with de-redaction

### Phase 1D: Frontend
- [ ] Simple HTML form (text input + file upload)
- [ ] Display redacted output + detection report
- [ ] "Send to AI" button with response display
- [ ] Basic styling (clean, functional)

### Phase 1E: Testing & Hardening
- [ ] End-to-end tests
- [ ] Edge case testing (mixed PII, overlapping entities, empty input)
- [ ] Performance benchmarks
- [ ] Documentation

---

## Milestone 2: n8n Integration (Future)
- [ ] Wrap detection engine as HTTP microservice
- [ ] Build n8n workflow calling the microservice
- [ ] Connect to Supabase for logging
- [ ] Lovable/Bubble frontend integration

## Milestone 3: Production Deployment (Future)
- [ ] Docker containerization
- [ ] Cloud deployment (Railway/Render)
- [ ] Auth & multi-tenancy
- [ ] Usage analytics dashboard
- [ ] Rate limiting & API keys
