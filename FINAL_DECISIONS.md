# PrivaSend - FINAL DECISIONS
> **Date:** 2026-02-06
> **Status:** CONFIRMED - Ready for Implementation

---

## ✅ FINAL ARCHITECTURE DECISIONS

### 1. UI Framework
**DECISION:** Keep **current custom HTML/JS**
- ❌ NOT switching to Lovable/Bubble for now
- ✅ Enhance current UI later
- 🎯 Make it "more functional" as we go

### 2. Backend
**DECISION:** Keep **FastAPI Python**
- ❌ NO n8n (correctly rejected)
- ✅ Direct Python implementation
- ✅ Better performance and control

### 3. LLM Integration
**DECISION:** Use **OpenRouter**
- ✅ Multi-LLM support (GPT-4o, Gemini, Claude)
- ✅ User choice of model
- ✅ Single API key management

### 4. Database & Auth
**DECISION:** **Supabase**
- ✅ User data storage
- ✅ Authorization/authentication
- ✅ NOT just for logging (I misread earlier)

---

## ❌ CORRECTIONS TO MY EARLIER ANALYSIS

### What I Got Wrong:

| Feature | I Said | Actually | Status |
|---------|--------|----------|--------|
| **OCR** | ✅ Complete | ❌ NOT done | **NEED TO BUILD** |
| **File Upload** | ✅ Complete | ❌ NOT done | **NEED TO BUILD** |
| **Supabase** | Just logging | Auth + User Data | **CRITICAL FEATURE** |
| **3rd Layer** | Disabled | Guardrails AI | **NEED TO ADD** |

### What Needs to be Built (Priority Order):

1. **File Upload System**
   - PDF upload and text extraction
   - DOCX upload and text extraction
   - Image upload + OCR
   - File size limits, validation

2. **OCR (Optical Character Recognition)**
   - Scanned PDFs
   - Images (medical reports, bank statements)
   - pytesseract integration

3. **Supabase Integration**
   - User authentication
   - User data storage
   - Session management
   - NOT just logging

4. **Guardrails AI (3rd Layer)**
   - PRD mentions this as 3rd layer
   - For high-value validation
   - Different from local LLM we disabled

5. **Placeholder/Entity Detection Improvements**
   - Fix: "Area" being tagged as NAME
   - Improve NER accuracy
   - Better false positive filtering

6. **User Confirmation UI**
   - Show ambiguous items (0.50-0.85 confidence)
   - Category toggles
   - Review panel

---

## 📋 COMPLETE FEATURE LIST (What's Done vs What's Needed)

### ✅ ALREADY IMPLEMENTED

| Feature | Status | Files |
|---------|--------|-------|
| Basic web UI | ✅ | `server/static/index.html` |
| Text input | ✅ | Working |
| PII Detection (Regex) | ✅ | `tools/detect_pii.py` |
| PII Detection (Presidio/spaCy) | ✅ | `tools/detect_pii.py` |
| Reversible Redaction | ✅ | `tools/redact.py` |
| FastAPI server | ✅ | `server/main.py` |
| Security hardening | ✅ | CORS, rate limiting, etc. |
| Tests | ✅ | 187 passing |
| Deployment | ✅ | Live at test.smcloud.cloud |

### ❌ NEEDS TO BE BUILT

| Feature | Priority | Complexity | Notes |
|---------|----------|------------|-------|
| **File Upload** | P0 | Medium | PDF, DOCX, images |
| **OCR** | P0 | Medium | Scanned docs, images |
| **Supabase Auth** | P0 | High | User login, sessions |
| **Supabase Data** | P0 | High | User profiles, history |
| **Guardrails AI** | P1 | Medium | 3rd validation layer |
| **User Confirmation UI** | P1 | Medium | Review panel, toggles |
| **OpenRouter Integration** | P1 | Low | API client |
| **Placeholder Fixes** | P1 | Low | Better NER filtering |
| **Send to AI Flow** | P1 | Medium | End-to-end with de-redaction |

---

## 🎯 REVISED MVP SCOPE (Based on Corrections)

### Phase 1: Infrastructure (P0 - Must Have)
1. File Upload (PDF, DOCX, images)
2. OCR for scanned documents
3. Supabase setup (Auth + Database)
4. User authentication flow

### Phase 2: Core Features (P1)
1. OpenRouter integration
2. User confirmation UI
3. Send to AI flow
4. Guardrails AI layer

### Phase 3: Polish (P2)
1. Placeholder detection improvements
2. UI enhancements
3. Testing & hardening

---

## 🔧 TECHNICAL CORRECTIONS NEEDED

### 1. Placeholder/Entity Detection Issues
**Problem:** "Area" being tagged as NAME
**Solution:** Improve NER blacklist and validators

**Files to modify:**
- `tools/detect_pii.py` - Add more blacklisted terms
- `_looks_like_person()` validator - Reject common words
- Presidio configuration - Tune confidence thresholds

### 2. Guardrails AI vs Local LLM
**What we had:** Local LLM (Llama via Ollama) - DISABLED
**What PRD wants:** Guardrails AI - 3rd layer
**Difference:** 
- Local LLM = On-premise Llama for validation
- Guardrails AI = Cloud service for structured validation

**Decision needed:** Use Guardrails AI or build custom validation?

### 3. File Upload Architecture
**Current:** Text input only
**Needed:** 
- File upload endpoint
- Temporary file handling
- Text extraction pipeline
- OCR pipeline for images

---

## ✅ CONFIRMED FINAL STACK

| Component | Technology | Status |
|-----------|------------|--------|
| Frontend | Custom HTML/CSS/JS | ✅ Keep |
| Backend | FastAPI (Python) | ✅ Keep |
| PII Detection | Regex + Presidio | ✅ Keep |
| 3rd Layer | Guardrails AI | 🔄 Add |
| LLM | OpenRouter | 🔄 Add |
| Database | Supabase | 🔄 Add |
| Auth | Supabase Auth | 🔄 Add |
| OCR | pytesseract | 🔄 Add |
| File Handling | pdfplumber, python-docx | 🔄 Add |
| Deployment | Docker + VPS | ✅ Keep |

---

## 📁 FILES CREATED TODAY

1. ✅ `/home/node/clawd/projects/PrivaSend/PRD_v2.0.md` - Full PRD
2. ✅ `/home/node/clawd/projects/PrivaSend/PROJECT_REVIEW_2026-02-06.md` - Initial review
3. ✅ `/home/node/clawd/projects/PrivaSend/ACTIVE_DISCUSSION_CONTEXT.md` - Discussion notes
4. ✅ `/home/node/clawd/projects/PrivaSend/FINAL_DECISIONS.md` - This file

---

## 🚀 READY TO START

**When you say "go", I will:**

1. Start with **Phase 1: File Upload + OCR** (P0)
2. Use **Kimi K2.5** for coding
3. Update **STATE.md** after each session
4. Follow **AGENTIC_BIBLE.md** principles

**Correct understanding?**
- ❌ OCR not done → Need to build
- ❌ File upload not done → Need to build  
- ❌ Supabase for auth → Critical feature
- ❌ Guardrails AI wanted → 3rd layer
- ❌ Placeholder issues → Need fixes

**Ready for implementation when you confirm.**
