# PrivaSend — AI Session Briefing

> **Copy-paste this entire document into any AI coding assistant (Gemini, ChatGPT, Copilot, etc.) at the START of every session working on this project.**

---

## How to restart a session

**For Claude Code:** Paste this as your first message:
> Read these files in order before doing anything: `CLAUDE.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `docs/architecture.md`. Then tell me where we left off and what's next.

**For Gemini / other AI:** Copy-paste this entire document as your first message, then say what you need.

---

## What is this project?

PrivaSend is a PII (Personally Identifiable Information) detection and redaction tool. Users paste text or upload files (PDF, DOCX, images). The system finds sensitive data (emails, names, phone numbers, credit cards, etc.), replaces them with placeholders like `[EMAIL_1]`, and optionally sends the safe version to ChatGPT.

## Tech stack

- **Backend:** Python 3.11+, FastAPI
- **PII Detection:** Regex patterns + Microsoft Presidio (with spaCy NER model)
- **File extraction:** pdfplumber (PDF), python-docx (DOCX), pytesseract (images)
- **AI integration:** OpenAI API
- **Frontend:** Vanilla HTML/CSS/JS (no framework)
- **Version control:** Git with feature branches

## Project structure

```
PrivaSend/
├── CLAUDE.md              # Framework instructions (DO NOT modify)
├── REQUIREMENTS.md        # Frozen scope and decisions (DO NOT modify without asking user)
├── ROADMAP.md             # Build phases and progress
├── STATE.md               # Session-by-session log (UPDATE after every session)
├── pyproject.toml         # Dependencies
├── .env                   # Secrets (never commit, never read, never display contents)
├── .gitignore
│
├── docs/
│   ├── architecture.md    # System design and data flow
│   └── reference/         # Original planning documents
│
├── tools/                 # Core logic scripts (WAT framework Layer 3)
│   ├── detect_pii.py      # PII detection engine (regex + Presidio)
│   ├── redact.py          # Reversible redaction with placeholder mapping
│   ├── extract_text.py    # File-to-text extraction (PDF, DOCX, OCR)
│   └── ai_proxy.py        # OpenAI proxy with de-redaction
│
├── workflows/             # Markdown SOPs describing how things work
│
├── server/                # FastAPI application
│   ├── main.py            # API routes
│   ├── config.py          # Settings
│   ├── models.py          # Pydantic schemas
│   └── static/
│       └── index.html     # Frontend
│
└── tests/                 # Pytest test suite
```

## Rules you MUST follow

### 1. Read before you write
Before modifying ANY file, read it first. Understand what is already there. Do not overwrite existing code with your own version.

### 2. Stay in scope
Only do what the user explicitly asks. Do not refactor code, add features, add comments, add docstrings, or "improve" things that were not requested.

### 3. Follow existing patterns
Look at how existing code is written — naming conventions, import style, error handling patterns. Match them exactly. Do not introduce a new style.

### 4. Git discipline
- NEVER commit directly to the `main` branch
- ALWAYS work on a feature branch (the user or primary AI will tell you which branch)
- NEVER run `git push --force`, `git reset --hard`, or any destructive git command
- If you are unsure about git, ask the user instead of guessing

### 5. Do not touch these files without explicit permission
- `CLAUDE.md` — framework instructions, never modify
- `REQUIREMENTS.md` — frozen scope, only the user can change this
- `docs/architecture.md` — system design, only update if you add a component
- `.env` — never read, display, or commit

### 6. Update STATE.md after every session
At the end of your session, add an entry to STATE.md with:
- Date
- What you did
- What changed (which files)
- Any problems encountered
- What should happen next

### 7. Small, testable changes
Make one change at a time. Test it. Confirm it works. Then move to the next change. Do not make 10 changes at once.

### 8. Security
- Never log, print, or display original PII values in production code
- Never send unredacted text to any external API
- Never store secrets outside of `.env`

## Architecture overview

```
User input (text or file)
    │
    ▼
File extraction (if file: PDF/DOCX/Image → plain text)
    │
    ▼
PII Detection Layer 1: Regex (fast, structured patterns)
    │
    ▼
PII Detection Layer 2: Presidio + spaCy (ML-based, names/addresses)
    │
    ▼
Merge results (deduplicate overlapping detections, keep highest confidence)
    │
    ▼
Reversible redaction (replace PII with [TYPE_N] placeholders, store mapping)
    │
    ▼
Output: redacted text + detection report
    │
    ▼ (optional)
Send redacted text to OpenAI → get response → de-redact → show to user
```

## Current state

**Read STATE.md for the latest status.** It contains what has been built, what is in progress, and what needs to happen next. Always read it before starting work.

## When in doubt

- Read REQUIREMENTS.md for what we are building
- Read ROADMAP.md for what phase we are in
- Read STATE.md for what was done last
- Read docs/architecture.md for how components connect
- If still unclear, ASK THE USER. Do not guess.
