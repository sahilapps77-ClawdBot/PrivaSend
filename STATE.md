# PrivaSend — State

> **Current phase:** MVP Architecture Pivot — Security hardened, ready for implementation
> **Last session:** 2026-02-04

## Next Steps

**Implementation plan saved to:** `.planning/MVP_ARCHITECTURE_PIVOT.md`

When you return, run:
```
Execute the plan in .planning/MVP_ARCHITECTURE_PIVOT.md
```

The plan covers 5 phases:
1. Backend config (confidence thresholds, LLM disable flag, OpenRouter config)
2. OpenRouter integration (new `tools/openrouter.py`)
3. New API endpoints (analyze-for-review, redact-selected, send-to-ai)
4. Frontend redesign (review panel, category toggles, AI modal)
5. Deployment

---

## Deployment Info

- **VPS IP:** 72.61.171.205
- **SSH user:** root
- **Live URL:** https://test.smcloud.cloud
- **Container name:** privasend
- **App listens on:** port 8000 (inside container)
- **Host port mapping:** `-p 8100:8000`
- **Reverse proxy:** Nginx Proxy Manager (admin on port 81) → `test.smcloud.cloud` → `172.17.0.1:8100`
- **Project path on VPS:** `/opt/privasend` (NOT a git repo — files are scp'd)
- **Ollama:** running on same VPS, port 11434, container env `OLLAMA_URL=http://172.17.0.1:11434`
- **Docker image:** `privasend:latest`

### Deploy after code changes
```bash
# 1. Copy files
scp -r tools/ server/ Dockerfile pyproject.toml root@72.61.171.205:/opt/privasend/

# 2. Rebuild and restart
ssh root@72.61.171.205 "cd /opt/privasend && docker stop privasend && docker rm privasend && docker build -t privasend . && docker run -d --name privasend -p 8100:8000 -e OLLAMA_URL=http://172.17.0.1:11434 privasend"
```

### Port reference (IMPORTANT — don't change these)
| Service | Container port | Host port | Why |
|---|---|---|---|
| PrivaSend (uvicorn) | 8000 | 8100 | Nginx Proxy Manager forwards test.smcloud.cloud → 172.17.0.1:8100 |
| Ollama | 11434 | 11434 | PrivaSend container reaches it via http://172.17.0.1:11434 |
| Nginx Proxy Manager | 80/443 | 80/443 | Public HTTPS |
| NPM Admin | 81 | 81 | Proxy manager UI |

### Debugging
```bash
# Check container status
ssh root@72.61.171.205 "docker ps --filter name=privasend"

# Check logs
ssh root@72.61.171.205 "docker logs privasend --tail 50"

# Test locally on VPS
ssh root@72.61.171.205 "curl -s http://localhost:8100/"

# Check nginx proxy config
ssh root@72.61.171.205 "docker exec nginx-proxy-manager cat /data/nginx/proxy_host/3.conf"
```

---

## Session Log

### 2026-02-04 (Session 6) — Security Hardening

**What happened:**
- Reviewed security audit report (`security_audit_report.md`) and verified findings against actual code
- Fixed 4 Critical/High security issues:
  1. **CORS Restriction** — Changed from `allow_origins=["*"]` to explicit whitelist:
     - `https://test.smcloud.cloud` (production)
     - `http://localhost:8000`, `http://localhost:8100` (dev)
     - `http://127.0.0.1:8000`, `http://127.0.0.1:8100` (dev)
  2. **Rate Limiting** — Added slowapi to `/api/send-to-ai` endpoint (10 requests/minute per IP)
  3. **API Key Validation** — Added format check in `tools/openrouter.py` (must start with `sk-or-v1-`)
  4. **Pre-commit Hooks** — Set up detect-secrets to prevent future secret commits

**Audit corrections (report inaccuracies):**
- Issue 1 (API key in .env): Report claimed not gitignored — FALSE, `.env` IS gitignored
- Issue 3 (XSS): Report claimed direct innerHTML injection — FALSE, code uses `escapeHtml()` properly
- Issue 6 (HTTPS): Already handled by Nginx Proxy Manager

**Files created:**
- `.pre-commit-config.yaml` — detect-secrets + basic file checks
- `.secrets.baseline` — detect-secrets baseline

**Files modified:**
- `server/main.py` — CORS whitelist, rate limiting middleware
- `tools/openrouter.py` — API key format validation
- `pyproject.toml` — Added slowapi dependency
- `.gitignore` — Added `security_audit_report.md`

**Pre-commit hooks installed:**
- `detect-secrets` — Scans for API keys/secrets
- `check-added-large-files` — Max 1000KB
- `check-case-conflict`, `check-merge-conflict`, `check-yaml`
- `end-of-file-fixer`, `trailing-whitespace`
- `no-commit-to-branch` — Prevents direct commits to main

**Tests:** 187 passed, 1 pre-existing failure (ADV-24)

**Action required before deploying:**
- Consider rotating OpenRouter API key (it appeared in the audit report)

---

### 2026-02-03 (Session 5) — Applied Agentic Bible Framework

**What happened:**
- Reviewed AGENTIC_BIBLE.md and mapped it to PrivaSend project
- Created workflow documentation in `workflows/`:
  - `detect_pii.md` — How to run PII detection
  - `redact_text.md` — Redaction process and de-redaction
  - `add_pii_type.md` — Steps to add new regex/NER patterns
  - `evaluate_accuracy.md` — How to measure detection accuracy
- Created `.planning/` directory with:
  - `REQUIREMENTS.md` (copied from root)
  - `ROADMAP.md` (copied from root)
  - `CONTEXT_MANAGEMENT.md` — Guide for AI context management in long sessions
- Updated `CLAUDE.md` with Bible discipline rules:
  - Three Laws (AI reasons/code executes, evidence before assertions, simplicity)
  - Verification Protocol (exists/substantive/wired checks)
  - Commit Standards (conventional commits)
  - Context Management rules
  - AI Discipline Checklist
- Added global user memory (`~/.claude/CLAUDE.md`) for context management:
  - Proactive subagent suggestions for exploration
  - Context degradation warnings
  - /clear suggestions between tasks
  - STATE.md documentation reminders

**Files created:**
- `workflows/detect_pii.md`
- `workflows/redact_text.md`
- `workflows/add_pii_type.md`
- `workflows/evaluate_accuracy.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/CONTEXT_MANAGEMENT.md`

**Files modified:**
- `CLAUDE.md` — Added Agentic Bible discipline layer

**Next when resuming:**
- If team approves architecture → implement confidence bucketing and review UI
- Continue using Bible workflow: DISCOVER → PLAN → EXECUTE → VERIFY → SHIP
- Use subagents for exploration tasks to keep main context clean

---

### 2026-01-30 (Session 4) — Architecture Pivot Discussion (no code changes)

**What happened:**
- Shared team-briefing.html with team, received feedback via group chat
- Team decided: **drop Layer 3 (LLM validator) for MVP**, replace with user confirmation gate
- Discussed and agreed on new architecture:
  - Two automated layers (Regex + Presidio/spaCy) stay as-is
  - Confidence buckets: ≥0.85 auto-redact, 0.50–0.85 ask user, <0.50 ignore (tunable)
  - LLM code kept behind feature flag, disabled by default
  - New UX: highlighted preview + side panel with grouped category toggles + smart defaults
  - Two actions: "Redact Only" (copy) and "Send to AI"
  - User preferences: "Remember my choices" for session
- Both modes confirmed: redact-only + send-to-AI
- Market not decided yet (India or US), English only for MVP
- OCR confirmed as must-have (Phase 1B)

**Team decisions (from chat):**
- No cloud LLM for MVP — "data never leaves" positioning
- Ambiguous PII → user confirms (not machine)
- Grouped category toggles, not per-item review
- Smart defaults (high-risk pre-checked, low-risk optional)
- Sector test datasets being collected by team members

**Status:** Summary shared back with team for final sign-off. No code changes yet — awaiting team approval before implementation.

**Next when resuming:**
- If team approves → plan implementation (backend confidence bucketing, new API flow, review UI)
- If team has changes → adjust architecture accordingly

---

### 2026-01-29 (Session 3) — Mobile Responsive Fixes

**What happened:**
- Fixed mobile scroll-lock after redaction results appear
- Disabled animated background orbs (`position: fixed` pseudo-elements) on mobile — they blocked touch scrolling
- Replaced horizontally-scrolling tables with vertically-stacked card layouts on mobile (details table + mapping table)
- Added `-webkit-overflow-scrolling: touch` on body and redacted output
- Constrained `.container` and `.sidebar` with `max-width: 100%; overflow: hidden` on mobile
- Compact sizing for all mobile elements: flowchart nodes, tags, badges, fonts, padding
- Deployed to VPS

**Files modified:**
- `server/static/index.html` — mobile responsive CSS overhaul in `@media (max-width: 600px)`

**Known issue:**
- User reports page still has navigation issues on mobile after redaction — may need further testing/iteration

---

### 2026-01-29 (Session 2) — Production-Grade Quality Fixes + Deploy

**What happened:**
- Fixed CSS unicode bug: `\u25BC` → `\25BC` (CSS uses different escape syntax than JS)
- Fixed 504 gateway timeout: added LLM time budget (45s total, 15s per entity)
- Added `CREDENTIAL` PII type for JSON key-value and context-aware detection
- Massively expanded NER blacklist (~80+ terms): protocols, formats, platforms, timezones, OS fragments
- Added `_ORG_PHRASE_BLACKLIST` for multi-word false positives (e.g., "THIRD-PARTY MONITORING SYSTEMS")
- Added `_looks_like_person()` validator: rejects digits, acronyms, key=value, hex strings
- Added `_looks_like_organization()` validator: rejects base64 strings, short acronyms, digit-containing non-business names
- Added PERSON trimming: "Michael R. Thompson - Case" → "Michael R. Thompson"
- Expanded API key patterns: Stripe, GitHub, Bearer, generic key=value
- Added SSN variants: spaces around dashes, zero-width characters
- Added URL email extraction from query params
- Added context-aware JSON key-value detection (`"ssn": "987-65-4321"`, `"tokens": ["abc"]`)
- Added context-aware `token=VALUE` detection in plain text
- Value-aware deduplication: same SSN value appearing 5 times → all get `[SSN_1]`
- Fixed password= regex to capture special characters
- Merge suppression: generic NER types suppressed when specific regex type exists on same span
- DOB context window tightened from 80→40 chars
- Added directional abbreviations (NW, NE, etc.) to blacklist
- Tests: **187 passed, 1 pre-existing failure (ADV-24), 16 warnings**
- Deployed to VPS at test.smcloud.cloud

**Files modified:**
- `tools/detect_pii.py` — major changes (all quality filters, new patterns, new PII type)
- `tools/redact.py` — value-aware deduplication
- `tools/config.py` — LLM_TIMEOUT=15, LLM_TOTAL_BUDGET=45
- `tools/llm_validator.py` — budget tracking
- `server/static/index.html` — CSS unicode fix
- `tests/test_quality_fixes.py` — NEW (20 tests)

**Known remaining gaps:**
- `01/15/2024` sometimes tagged as DOB if "date of birth" appears within 40 chars (even for a different date)
- Base64-encoded secrets not detected
- URL-encoded secrets not detected
- ADV-24 (jammed PII without spaces) still fails
- "Washington" detected as LOCATION (correct but not always desired)

---

### 2026-01-29 — Phase 1A Complete (Detection + Redaction Engine)

**What happened:**
- Built `tools/detect_pii.py` — two-layer PII detection engine (regex + Presidio/spaCy)
- Built `tools/redact.py` — reversible redaction with numbered placeholders
- Built `try_it.py` — interactive tester (full mode: regex + Presidio + spaCy)
- 25 PII types covered: email, phone, SSN, credit card, API key, Aadhaar, PAN, passport, driver's license, IBAN, bank account, DOB, medical record, IP, MAC, VIN, URL-with-creds, UPI ID, username:password, crypto wallet (BTC/ETH), UK NI, Canadian SIN, US EIN, vehicle plates, SWIFT/BIC
- Plus Presidio NER: person names, addresses, organizations, locations
- Built evaluation system: 50 realistic + 30 adversarial test samples
- Accuracy: 100% recall (realistic), 93.9% recall (adversarial), 61 false positives
- 70 unit tests passing

**Fixes applied:**
- Excluded DATE_TIME from Presidio (flagged generic words like "quarterly")
- Added street address regex (42 Oak Street, etc.)
- Presidio confidence threshold >= 0.6 (reduces ORGANIZATION/LOCATION false positives)
- DOB requires context keyword within 80 chars (born/DOB/birthday)
- Added missing UPI bank codes (hdfcbank, axisbank, etc.)

**Known limitations:**
- ORGANIZATION false positives (~25) — Presidio still flags common words at >=0.6 confidence
- AADHAAR false positives (~6) — 12-digit numbers match pattern (kept deliberately: better to over-detect)
- Obfuscated PII not detected (spaced-out emails, spelled-out numbers)
- PII jammed without spaces not fully detected (ADV-24)

**Git:** 4 commits on `feature/detect-pii` branch. `main` untouched.

**Next:** Phase 1B (file extraction: PDF, DOCX, OCR) or Phase 1C (FastAPI server)

**Quality debt (7.5/10 → target 9-10):**

| Gap | Fix in | Reason |
|---|---|---|
| No logging | Phase 1C | Logging makes sense when there's a server to log from |
| In-memory mapping only | Phase 1C | Server needs persistence anyway (Redis/SQLite) |
| No input validation | Phase 1C | Validation belongs at the API boundary |
| Global lazy-loaded Presidio | Phase 1C | Refactor to dependency injection for server |
| 61 false positives | Ongoing | Incrementally improve with more test cases |
| No async support | Phase 1C | Build async detect path for FastAPI |
| Regex patterns in one file | Phase 1E | Refactor to registry pattern during hardening |
| No CI/CD | Phase 1E | GitHub Actions after all features are in |

---

### 2026-01-28 — Project Kickoff

**What happened:**
- Explored existing project files (PRD, team brief, architecture docs, Presidio guide)
- Reviewed GSD framework from `glittercowboy/get-shit-done`
- Made all key architectural decisions (see REQUIREMENTS.md)
- Chose hybrid framework: WAT (code structure) + GSD (planning docs)
- Created project documentation (REQUIREMENTS.md, ROADMAP.md, this file, docs/architecture.md)
- Organized root folder — moved reference docs to `docs/reference/`

**Decisions made:**
1. Standalone Python (FastAPI) app — not n8n for MVP
2. Regex + Presidio (pip, not Docker) for PII detection
3. spaCy `en_core_web_lg` model for NER
4. Reversible redaction with in-memory mapping
5. All input formats (text, PDF, DOCX, images)
6. All PII types (comprehensive coverage)
7. WAT + GSD hybrid framework

**Open questions:**
- None currently — ready to begin Phase 1A

**Blockers:**
- None

## Quick Reference

- **Framework:** WAT (tools/ + workflows/) + GSD (planning docs)
- **Stack:** Python 3.11+, FastAPI, Presidio, spaCy, pdfplumber, python-docx, pytesseract
- **Detection:** Regex (Layer 1) → Presidio/spaCy (Layer 2) → Merge → LLM Validation (Layer 3) → Threshold → Redact
- **Redaction:** Reversible, numbered placeholders, value-aware dedup, in-memory mapping
- **LLM:** Ollama llama3:8b, validates 0.60–0.85 confidence entities, fail-open, 45s budget
