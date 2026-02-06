# PrivaSend - PRD
Version: 2.0
Date: February 2, 2026

Team: Naveli Garg, Hina Khan, Sahil Mehta, Fareed Shaik, Vani Aggarwal, Rajesh Sriram, Saikumar Vasudevan, Mohit Kumar, Mangesh Khodke, Saurabh Verma

Program: Outskill AI Generalist Fellowship C5
Demo Day: March 28, 2026 (Bangalore)

---

## Table of Contents
1. EXECUTIVE SUMMARY
2. PROBLEM STATEMENT
3. TARGET AUDIENCE (ICP)
4. SOLUTION OVERVIEW
5. MVP SCOPE (Must-Have for Demo)
6. TECHNICAL ARCHITECTURE
7. WHAT PII DO WE CATCH?

---

## EXECUTIVE SUMMARY

**Product Name:** PrivaSend
**Working Tagline:** "Safe by Design - Every Time You Use AI"

**Problem:** 57% of enterprise employees leak sensitive data into LLMs (TELUS survey). Average data breach costs $4.45M (IBM). SMBs lack affordable DLP tools ($10K-100K+ enterprise solutions).

**Solution:** Runtime prompt governance system that redacts PII/confidential data BEFORE sending to LLMs, then completes the user workflow by routing cleaned prompts and returning answers in one interface.

**Unique Value:**
- Completes the workflow (competitors stop at redaction)
- One-click AI answer (no copy-paste)
- Local-first privacy (ephemeral processing)
- SMB-focused pricing ($15-25/user/month vs. $10K+ enterprise)

**MVP Scope (6 weeks):** Web app with regex-based PII redaction, basic logging, Bubble/Lovable UI, n8n backend, one LLM integration (OpenAI).

**Success Metrics:**
- ≥95% redaction accuracy on test corpus
- <10% false positives
- Working demo by Product Qualifiers (late Feb)

---

## 1. PROBLEM STATEMENT

### The Privacy Paradox in AI Adoption

**Context:**
- LLM usage exploding in SMBs: 57% of employees use ChatGPT for work (TELUS Digital Study)
- Shadow AI adoption: Employees paste sensitive data without IT approval
- Breach costs: $4.45M average (IBM); GDPR fines up to 4% revenue

**Pain Points:**

**For Employees:**
- Need AI productivity (code gen, document drafting, research)
- Don't realize they're leaking PII (SSNs, emails, API keys)
- Manual redaction = time-consuming, error-prone

**For SMBs (10-500 employees):**
- Can't afford enterprise DLP ($10K-100K+/year)
- Lack in-house compliance teams
- Face regulatory risk (GDPR, HIPAA, CCPA) without protection

**For Decision-Makers (CISOs, Compliance Officers):**
- Need to enable AI use (competitive pressure)
- Must prevent data leakage (legal liability)
- Current solutions: Ban LLMs (kills productivity) OR ignore risk (invites breach)

**Evidence:**
- Samsung incident: Employees leaked source code to ChatGPT (pre-paid subscription)
- 40% of data breaches stem from "forgetting to blur a name on a PDF" (anecdotal but directionally correct)
- GDPR: 4% revenue fine; HIPAA: $50K per violation

---

## 2. TARGET AUDIENCE (ICP)

### Primary ICP: Individuals
People who are working at companies with enterprise solutions but require privacy (B2C)
- Sectors: Finance, Healthcare, Legal, HR
- Location: India OR USA
- Pain: Acute compliance risk from shadow AI; existing tools too expensive

### Secondary ICP: SMBs
- Size: 10-100 employees
- Sectors: Tech startups, consulting agencies, small healthcare practices
- Pain: Using LLMs for productivity (code, customer support), no budget for enterprise tools
- Willingness to Pay: $1K-10K/year if easy to deploy
- Decision-Makers: Founders, Ops Managers
- Example: 20-person SaaS startup using ChatGPT for support tickets, risking API key leakage

### Out-of-Scope (For MVP):
- Large enterprises with in-house governance (already have solutions)
- Non-LLM AI users (computer vision, robotics)
- Unregulated startups prioritizing speed over safety

### Persona Example (From Pitch):
- "The Busy HR Manager" - Uses ChatGPT to draft job descriptions, accidentally pastes employee SSNs from internal spreadsheet
- "The Consultant" - Needs AI for client reports but works with NDAs, can't risk leakage
- "The Small Clinic Owner" - Uses AI for patient summaries, must stay HIPAA-compliant

---

## 3. SOLUTION OVERVIEW

### Product Vision:
PrivaSend is the "Grammarly of AI Safety" - a lightweight, always-on governance layer that lets SMBs use LLMs safely without manual redaction or expensive enterprise tools.

### Core Workflow:

1. **User uploads file/pastes text** (via web interface - exact TBD)
   - Paste text, or upload a PDF, Word document, or image. If it's a file, we first extract the text from it.

2. **Two-Layer PII Filtering**
   - **First layer: Regex pattern matching**
     - We run 25+ pattern-matching rules that look for things with a known format — email addresses, phone numbers, credit card numbers, Aadhaar, PAN, etc. This is instant (under 10 milliseconds).
   - **Second layer: AI/NER**
     - An AI model reads the text and understands context — it catches things like person names, street addresses, and organization names that don't follow a fixed pattern. Takes about 100–200ms.
   - Detects: Emails, SSNs, phone numbers, API keys, credit cards, medical records
   - Replaces with placeholders: [EMAIL], [PHONE], [SSN], [API_KEY]
   - Version 1 will be custom coded and version 2 will be automated (using n8n)
   - Filtration is built with GDPR/CCPA principles but is not 100% compliant
   - Shows what was hidden (transparency: "6 emails redacted, 2 phone numbers removed")
   - IF ambiguity, user confirms/clears the question. Then steps 2a-h repeat until >85% redaction confidence.

3. **One-click AI button** (sends redacted text to LLM via n8n API call)
   - LLM API Cost Research: NOTE: for MVP, we only need 1 LLM API to show complete flow. In future, can expand to many LLMs/i10x AI type
   - Keep a private mapping table so we can reverse this later.

4. **AI/LLM streams answer back** (in same window, no copy-paste)
   - When it responds, we swap the placeholders back with the real values. You get a complete, useful answer — and the AI never saw your private data.
   - Internally, we log metadata (timestamp, user ID, redaction count - NO raw PII)
   - Where TBD (Supabase?)

### Technical Architecture (High-Level):
```
[User] → [Lovable UI] → [Bubble form] → [n8n webhook] 
  → [Text Parser (regex)] → [Redaction logic] → [Display results]
  → [User clicks "Send to AI"] → [n8n OpenAI node] → [Stream response]
  → [Log anonymized data to Supabase] → [Return to UI]
```

### Privacy Guarantees:
- **Ephemeral processing:** Data deleted after response (no server storage)
- **Local-first where possible:** Regex runs server-side but no persistence
- **Anonymized logs:** Store counts (e.g., "3 emails redacted") NOT actual PIIs
- **No AI in detection layer:** Regex = deterministic, no risk of LLM hallucination

---

## 4. MVP SCOPE (Must-Have for Demo)

### Must-Have Features

**Simple Web UI:**
- Built in TBD (Lovable, Bubble, etc.)
- Mobile-responsive
- Clear CTA: "Paste your prompt below"
- Progress indicator: "Scanning..." → "Safe!" → "AI answering..."

**Prompt Input Box/ File Upload (Support for Multiple File Formats):**
- Prompts/Queries
- Documents (Docs)
- PDFs (both digital and scanned)
- Text files
- Excel files
- Images/JPEGs
- Camera? Or only pre-taken images?
- Prompt character limit? File MB limit?

**OCR (Optical Character Recognition):**
- Required to handle scanned PDFs, images (medical reports, bank statements), and other non-digital documents
- Supports multiple formats: PDF, images, Excel

**Two-Layer PII Filtering:**
- First layer: Regex pattern matching
- Second layer: Presidio (additional filtering)
- User confirmation before redaction when ambiguity arises

**User Confirmation/Verification Step:**
- Before any redaction happens, the system asks the user to confirm
- Ensures nothing gets redacted unless confirmed by the user
- Helps achieve 99% accuracy with user consent

**One-Click AI Integration:**
- Button: "Send to LLM"
- n8n node routes cleaned text to LLM API
- Stream response back to UI

**Basic Logging:**
- Store in Supabase: {user_id, timestamp, pii_count, status}
- NO raw PII stored
- Confidence scores
- Detection counts
- Simple table view (admin only)

### To Be Decided Features

**Display "Before/After" view:**
- Would be nice for demo day to display effectiveness of PrivaSend
- Show summary: "6 items redacted: 4 emails, 2 phones"

### Nice-to-Have Features

**Voice Dictation/Voice Input:**
- Decided to skip for MVP to keep it simple
- Can leverage existing tools like Whisper AI for future versions
- Concern: unstructured PII may not be easy for regex to parse

**Multilingual Support:**
- MVP will focus on English only
- Regional languages (Hindi, Devnagari script, etc.) deferred to future versions
- Regex doesn't support non-Latin scripts well currently

**Third-Layer LLM Integration:**
- Decided NOT to use a cloud LLM as a third filter layer
- Reasons: 30-50 second delay, increased latency, privacy breach risk, cost
- Instead: Ask user directly for ambiguous items

### DEFERRED Features
- Browser extension
- Real-time streaming redaction
- Custom PII type training
- Persistent user sessions
- Advanced analytics dashboard

### Explicitly Out-of-Scope (For 6 Weeks):
- User authentication / multi-tenancy
- Persistent storage / database (MVP uses ephemeral)
- Computer vision / robotics
- Compliance certification (GDPR/HIPAA certified)

---

## 5. TECHNICAL ARCHITECTURE

### Two Detection Layers Explained:

#### LAYER 1 — REGEX (Pattern Matching)
- **The fastest, most reliable layer**
- Catches structured patterns with known formats
- Examples: Email addresses, phone numbers, SSNs, credit cards, API keys, Aadhaar, PAN

#### LAYER 2 — PRESIDIO + spaCy (AI/NER)
- **Named Entity Recognition (understands language)**
- Catches context-dependent PII that regex cannot
- Examples: Person names, addresses, organizations, locations, medical conditions

#### LAYER 3 — LOCAL LLM (Llama 3) - DISABLED FOR MVP
- **Uncertainty Resolver (the double-checker)**
- Originally planned for 0.50-0.85 confidence entities
- **DECISION: Disabled for MVP** - replaced with user confirmation
- Reasons: Privacy risk, latency (30-50s), cost

### How the layers work together:
1. Run regex (instant, <10ms)
2. Run Presidio/spaCy (100-200ms)
3. Merge results (deduplicate overlapping spans)
4. Bucket by confidence:
   - ≥0.85: High confidence (pre-checked in UI)
   - 0.50-0.85: Medium confidence (show for user review)
   - <0.50: Low confidence (ignore)
5. User reviews and confirms medium-confidence items
6. Redact confirmed items
7. Send to LLM via OpenRouter
8. De-redact response

---

## 6. WHAT PII DO WE CATCH?

### Regex Patterns (Layer 1):
- Email addresses
- Phone numbers (US, India, International)
- SSN (US Social Security Numbers)
- Credit card numbers
- API keys (various formats)
- Aadhaar (India)
- PAN (India)
- Passport numbers
- Driver's license numbers
- IBAN (International Bank Account Numbers)
- Bank account numbers
- Date of birth
- Medical record numbers
- IP addresses (IPv4, IPv6)
- MAC addresses
- VIN (Vehicle Identification Numbers)
- URLs with credentials
- UPI IDs (India)
- Username:password combinations
- Crypto wallets (BTC, ETH)
- UK National Insurance numbers
- Canadian SIN
- US EIN
- Vehicle plates
- SWIFT/BIC codes

### NER Detection (Layer 2 - Presidio/spaCy):
- Person names
- Street addresses
- Organizations
- Locations
- Medical conditions

---

## NOTES FROM DISCUSSION

**Changes from Old Architecture:**
1. LLM validation layer → User confirmation (privacy-first)
2. n8n backend → Direct Python/FastAPI (performance)
3. Supabase logging → To be decided (privacy concerns)
4. Single LLM (OpenAI) → OpenRouter (user choice: GPT-4o, Gemini, Claude)

**Key Decisions Needed:**
1. UI framework: Lovable vs Bubble vs custom
2. Logging destination: Supabase vs self-hosted vs none
3. Market: India vs US (affects PII patterns)
4. OCR priority: Must-have for scanned documents

**Technical Stack:**
- Backend: Python 3.11+, FastAPI
- PII Detection: Regex + Microsoft Presidio
- NER Model: spaCy en_core_web_lg
- PDF extraction: pdfplumber
- DOCX extraction: python-docx
- OCR: pytesseract + Tesseract
- LLM: OpenRouter API (OpenAI, Google, Anthropic)
- Frontend: Vanilla HTML/CSS/JS (current) or Bubble/Lovable (future)

---

**Document Source:** Google Docs
**Imported:** 2026-02-06
**Status:** Active PRD v2.0
