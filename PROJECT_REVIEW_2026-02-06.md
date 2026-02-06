# PrivaSend — Project Review & Development Plan

> **Document created:** 2026-02-06
> **Reviewed by:** Arya
> **Status:** Ready for development (awaiting updated PRD)

---

## Executive Summary

PrivaSend is a runtime prompt governance system that detects and redacts PII from user input before it reaches AI tools. Currently in **MVP Phase 1A-1C** with security hardening completed.

**Key Decision:** Use **Kimi K2.5** for coding (approved by Sahil)

---

## Current Project State

### What's Implemented ✅

| Component | Status | Files |
|-----------|--------|-------|
| PII Detection Engine | ✅ Complete | `tools/detect_pii.py` — Regex + Presidio/spaCy |
| Reversible Redaction | ✅ Complete | `tools/redact.py` — Numbered placeholders |
| LLM Validation | ✅ Complete (disabled) | `tools/llm_validator.py` — Feature-flagged off |
| FastAPI Server | ✅ Complete | `server/main.py` — Core endpoints |
| Frontend | ✅ Complete | `server/static/index.html` — Basic UI |
| Tests | ✅ 187 passing | `tests/` — Unit + integration tests |
| Security Hardening | ✅ Complete | CORS, rate limiting, API key validation, pre-commit hooks |
| Deployment | ✅ Live | https://test.smcloud.cloud |

### Architecture Decisions (Frozen)

| Decision | Rationale |
|----------|-----------|
| **Kimi K2.5 for coding** | Approved by Sahil — best reasoning quality |
| **No LLM validation for MVP** | Data privacy — "data never leaves" positioning |
| **Confidence bucketing** | High (≥0.85) auto, Medium (0.50-0.85) user review, Low (<0.50) ignore |
| **OpenRouter integration** | User choice: ChatGPT, Gemini, Claude |
| **Reversible redaction** | Required for send-to-AI → de-redact flow |
| **English only for MVP** | Market TBD (India vs US) |

---

## Implementation Plan (Next Phase)

### Source of Truth
**`.planning/MVP_ARCHITECTURE_PIVOT.md`** — Complete 5-phase implementation plan

### The 5 Phases

#### Phase 1: Backend Configuration
- Update `tools/config.py` — Add confidence thresholds, LLM toggle, OpenRouter config
- Create `tools/pii_categories.py` — Map PII types to UI categories
- Update `tools/detect_pii.py` — Add bucketing function

#### Phase 2: OpenRouter Integration  
- Create `tools/openrouter.py` — New file for OpenRouter API client
- Support models: GPT-4o, Gemini 2.0 Flash, Claude 3.5 Sonnet
- Handle de-redaction after AI response

#### Phase 3: New API Endpoints
- `POST /api/analyze-for-review` — Returns entities with confidence buckets
- `POST /api/redact-selected` — Redacts only user-selected entities
- `POST /api/send-to-ai` — Sends to OpenRouter, returns de-redacted response

#### Phase 4: Frontend Redesign
- Review panel with category toggles
- Confidence-based pre-checking (high=checked, medium=optional, low=hidden)
- Smart defaults by category
- Two actions: "Redact Only" vs "Send to AI"
- AI model selector modal

#### Phase 5: Deployment
- Deploy to VPS
- Update Nginx Proxy Manager
- Test end-to-end flow

---

## File Structure

```
PrivaSend/
├── AGENTIC_BIBLE.md          # Coding standards (APPLIED ✅)
├── CLAUDE.md                 # Agent instructions (WAT framework)
├── STATE.md                  # Session logs (UP TO DATE ✅)
├── REQUIREMENTS.md           # Product requirements
├── ROADMAP.md                # Development roadmap
├── MVP_ARCHITECTURE_PIVOT.md # Next implementation plan ⭐
├── Sahil.md                  # User context/preferences
│
├── .planning/                # Architecture & decisions
│   ├── MVP_ARCHITECTURE_PIVOT.md
│   ├── CONTEXT_MANAGEMENT.md
│   ├── REQUIREMENTS.md
│   └── ROADMAP.md
│
├── workflows/                # SOPs for common tasks
│   ├── detect_pii.md
│   ├── redact_text.md
│   ├── add_pii_type.md
│   └── evaluate_accuracy.md
│
├── tools/                    # Execution layer (Python)
│   ├── detect_pii.py         # PII detection engine ⭐
│   ├── redact.py             # Reversible redaction ⭐
│   ├── llm_validator.py      # LLM validation (disabled) ⭐
│   ├── openrouter.py         # NEW: OpenRouter client
│   ├── config.py             # Configuration
│   └── pii_categories.py     # UI category mapping
│
├── server/                   # FastAPI app
│   ├── main.py               # API endpoints ⭐
│   └── static/
│       └── index.html        # Frontend ⭐
│
├── tests/                    # Test suite (187 passing)
│   ├── test_detect_pii.py
│   ├── test_redact.py
│   └── ...
│
└── docs/                     # Documentation
    └── reference/
```

---

## Development Approach

### Version Control
- **Branch:** Create `feature/mvp-architecture-pivot` from current state
- **Commits:** Atomic, conventional commit format
- **Push:** Regular pushes to GitHub
- **Merge:** PR to main after testing

### Model Usage
- **Kimi K2.5** for all coding tasks (approved)
- **DeepSeek** for WhatsApp only (already configured)
- **No Claude Code** until Monday (Sahil's instruction)

### Testing
- Maintain 187+ passing tests
- Add tests for new endpoints
- Test OpenRouter integration with mock responses

### Documentation
- Update STATE.md after each session
- Log decisions in memory/YYYY-MM-DD.md
- Update MVP_ARCHITECTURE_PIVOT.md if plans change

---

## Key Files to Review Before Coding

1. **`.planning/MVP_ARCHITECTURE_PIVOT.md`** — Complete implementation guide ⭐
2. **`STATE.md`** — Current progress and context
3. **`tools/detect_pii.py`** — Understand detection engine
4. **`server/main.py`** — Current API structure
5. **`AGENTIC_BIBLE.md`** — Coding standards

---

## Open Questions (To Discuss Monday)

1. **Updated PRD** — Sahil mentioned bringing updated PRD
2. **Feature priorities** — Any changes to the 5-phase plan?
3. **OCR priority** — Team mentioned OCR as must-have (Phase 1B)
4. **Market decision** — India vs US for post-MVP
5. **Budget** — OpenRouter API key setup for production

---

## Deployment Info (For Reference)

| Item | Value |
|------|-------|
| VPS IP | 72.61.171.205 |
| Live URL | https://test.smcloud.cloud |
| SSH | root@72.61.171.205 |
| Container | privasend (port 8000 → 8100) |
| Nginx PM | port 81 |
| Ollama | http://172.17.0.1:11434 |

---

## Next Steps

**Monday Session:**
1. Review updated PRD from Sahil
2. Discuss any architecture changes
3. Confirm priority of Phase 1-5 implementation
4. Begin coding with Kimi K2.5
5. Update STATE.md with progress

**Ready to start when you are.**
