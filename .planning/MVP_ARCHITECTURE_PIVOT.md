# PrivaSend MVP Architecture Pivot — Implementation Plan

> **Created:** 2026-02-03
> **Status:** Ready for implementation
> **Estimated scope:** 5 phases across tools/, server/, and frontend

## Summary

Implement the new MVP architecture:
1. Disable LLM validation layer (keep code, feature-flagged)
2. Add confidence bucketing with user review UI
3. Add "Send to AI" via OpenRouter API (ChatGPT, Gemini, Claude)

---

## Architecture Overview

```
User Input
    ↓
PII Detection (Regex + Presidio/spaCy) — LLM DISABLED
    ↓
Confidence Bucketing
    ├── >= 0.85: High (pre-checked in UI)
    ├── 0.50-0.85: Medium (shown for review)
    └── < 0.50: Low (ignored)
    ↓
User Review Panel
    ├── Category toggles (Names, IDs, Addresses, etc.)
    ├── Individual entity checkboxes
    └── Preferences (session / persistent / reset)
    ↓
Output Options
    ├── "Redact Only" → copy to clipboard
    └── "Send to AI" → OpenRouter API → ChatGPT/Gemini/Claude
```

---

## Phase 1: Backend Configuration

### 1.1 Update `tools/config.py`

Add new settings:

```python
# Confidence bucketing thresholds
CONFIDENCE_HIGH = 0.85          # >= this: pre-checked in UI
CONFIDENCE_LOW = 0.50           # < this: ignored

# LLM validation toggle (disabled for MVP)
USE_LLM_VALIDATION = os.getenv("USE_LLM_VALIDATION", "false").lower() == "true"

# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
```

### 1.2 Create `tools/pii_categories.py` (new file)

```python
"""PII type to category mapping for UI grouping."""

from tools.detect_pii import PIIType

PII_CATEGORIES = {
    "Names": [PIIType.PERSON],
    "Contact": [PIIType.EMAIL, PIIType.PHONE, PIIType.UPI_ID],
    "IDs": [PIIType.SSN, PIIType.AADHAAR, PIIType.PAN, PIIType.PASSPORT,
            PIIType.DRIVERS_LICENSE, PIIType.UK_NI_NUMBER, PIIType.CANADIAN_SIN,
            PIIType.US_EIN, PIIType.MEDICAL_RECORD],
    "Addresses": [PIIType.ADDRESS, PIIType.LOCATION],
    "Financial": [PIIType.CREDIT_CARD, PIIType.IBAN, PIIType.BANK_ACCOUNT, PIIType.SWIFT_BIC],
    "Credentials": [PIIType.API_KEY, PIIType.USERNAME_PASSWORD, PIIType.CREDENTIAL,
                    PIIType.URL_WITH_CREDENTIALS, PIIType.CRYPTO_WALLET],
    "Technical": [PIIType.IP_ADDRESS, PIIType.MAC_ADDRESS, PIIType.VIN, PIIType.VEHICLE_PLATE],
    "Other": [PIIType.DATE_OF_BIRTH, PIIType.DATE_TIME, PIIType.ORGANIZATION, PIIType.MEDICAL_CONDITION],
}

# Reverse lookup
def get_category(pii_type: PIIType) -> str:
    for cat, types in PII_CATEGORIES.items():
        if pii_type in types:
            return cat
    return "Other"
```

### 1.3 Update `tools/detect_pii.py`

Add bucketing function:

```python
def bucket_entities(entities: list[DetectedEntity]) -> dict:
    """Group entities by confidence: high (>=0.85), medium (0.50-0.85), low (<0.50)."""
    from tools.config import CONFIDENCE_HIGH, CONFIDENCE_LOW
    return {
        "high": [e for e in entities if e.confidence >= CONFIDENCE_HIGH],
        "medium": [e for e in entities if CONFIDENCE_LOW <= e.confidence < CONFIDENCE_HIGH],
        "low": [e for e in entities if e.confidence < CONFIDENCE_LOW],
    }
```

Update `detect()` to respect `USE_LLM_VALIDATION` flag:

```python
def detect(text: str, use_presidio: bool = True, use_llm: bool | None = None) -> list[DetectedEntity]:
    # If use_llm not explicitly set, use config flag
    if use_llm is None:
        from tools.config import USE_LLM_VALIDATION
        use_llm = USE_LLM_VALIDATION
    # ... rest of function
```

---

## Phase 2: OpenRouter Integration

### 2.1 Create `tools/openrouter.py` (new file)

```python
"""OpenRouter API client for sending redacted prompts to AI models."""

import httpx
from tools.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

MODELS = {
    "openai/gpt-4o-mini": "GPT-4o Mini",
    "openai/gpt-4o": "GPT-4o",
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
    "google/gemini-pro": "Gemini Pro",
}

async def send_prompt(prompt: str, model: str, api_key: str | None = None) -> str:
    """Send prompt to OpenRouter, return AI response text."""
    key = api_key or OPENROUTER_API_KEY
    if not key:
        raise ValueError("No OpenRouter API key configured")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "https://privasend.app",
                "X-Title": "PrivaSend",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
```

---

## Phase 3: New API Endpoints

### 3.1 Update `server/main.py`

Add new Pydantic models:

```python
class ReviewResponse(BaseModel):
    entities: list[EntityOut]
    categories: dict[str, list[int]]  # category name -> list of entity indices
    elapsed_ms: float

class RedactSelectedInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    selected_indices: list[int]

class SendToAIInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    selected_indices: list[int]
    model: str = "openai/gpt-4o-mini"
    prompt: str
    api_key: str | None = None

class AIResponse(BaseModel):
    redacted_input: str
    ai_response: str
    model_used: str
    elapsed_ms: float
```

Add new endpoints:

```python
@app.post("/api/analyze-for-review", response_model=ReviewResponse)
async def api_analyze_for_review(body: TextInput):
    """Detect PII and return grouped by category for user review."""
    from tools.pii_categories import get_category

    entities = detect(body.text, use_presidio=True, use_llm=False)

    # Group entity indices by category
    categories = {}
    for i, e in enumerate(entities):
        cat = get_category(e.pii_type)
        categories.setdefault(cat, []).append(i)

    return ReviewResponse(
        entities=[EntityOut(...) for e in entities],
        categories=categories,
        elapsed_ms=...,
    )

@app.post("/api/redact-selected", response_model=RedactResponse)
async def api_redact_selected(body: RedactSelectedInput):
    """Redact only user-selected entities."""
    entities = detect(body.text, use_presidio=True, use_llm=False)
    selected = [entities[i] for i in body.selected_indices if i < len(entities)]
    result = redact(body.text, selected)
    return RedactResponse(...)

@app.post("/api/send-to-ai", response_model=AIResponse)
async def api_send_to_ai(body: SendToAIInput):
    """Redact selected entities, send to AI via OpenRouter."""
    from tools.openrouter import send_prompt

    # 1. Detect and filter to selected
    entities = detect(body.text, use_presidio=True, use_llm=False)
    selected = [entities[i] for i in body.selected_indices if i < len(entities)]

    # 2. Redact
    result = redact(body.text, selected)

    # 3. Build prompt with redacted text
    full_prompt = f"{body.prompt}\n\n---\n\n{result.redacted_text}"

    # 4. Call OpenRouter
    ai_response = await send_prompt(full_prompt, body.model, body.api_key)

    return AIResponse(
        redacted_input=result.redacted_text,
        ai_response=ai_response,
        model_used=body.model,
        elapsed_ms=...,
    )
```

---

## Phase 4: Frontend Redesign

### 4.1 Update `server/static/index.html`

**New flow:**
1. User pastes text → clicks "Analyze"
2. Review panel appears with category toggles + entity checkboxes
3. High-confidence items are pre-checked
4. User can toggle categories or individual items
5. User clicks "Redact Only" or "Send to AI"

**Key HTML additions:**

```html
<!-- Review Panel (hidden initially) -->
<div id="review-panel" class="glass card" style="display:none;">
  <h3>Review Detected PII</h3>
  <p class="hint">High-confidence items are pre-selected. Uncheck items you don't want to redact.</p>

  <!-- Category sections (dynamically generated) -->
  <div id="categories-container"></div>

  <!-- Preference controls -->
  <div class="pref-controls">
    <label><input type="checkbox" id="persist-prefs"> Remember my preferences</label>
    <button class="btn-link" id="reset-prefs">Reset to defaults</button>
  </div>

  <!-- Action buttons -->
  <div class="btn-row">
    <button class="btn-primary" id="btn-redact-only">Redact Only</button>
    <button class="btn-secondary" id="btn-send-ai">Send to AI</button>
  </div>
</div>

<!-- AI Modal -->
<div id="ai-modal" class="modal" style="display:none;">
  <div class="modal-content glass">
    <h3>Send to AI</h3>

    <label>Select AI Model</label>
    <select id="ai-model">
      <option value="openai/gpt-4o-mini">GPT-4o Mini (Fast)</option>
      <option value="openai/gpt-4o">GPT-4o (Best)</option>
      <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
      <option value="google/gemini-pro">Gemini Pro</option>
    </select>

    <label>Your Prompt</label>
    <textarea id="ai-prompt" rows="4" placeholder="What would you like the AI to do?"></textarea>

    <details>
      <summary>Use your own API key (optional)</summary>
      <input type="password" id="user-api-key" placeholder="OpenRouter API key">
    </details>

    <div class="btn-row">
      <button class="btn-primary" id="btn-submit-ai">Send</button>
      <button class="btn-secondary" id="btn-cancel-ai">Cancel</button>
    </div>
  </div>
</div>

<!-- AI Response Panel -->
<div id="ai-response-panel" class="glass card" style="display:none;">
  <h3>AI Response</h3>
  <div id="ai-response-content"></div>
</div>
```

**Key JavaScript additions:**

```javascript
// State management
const state = {
  text: '',
  entities: [],
  selected: new Set(),  // indices of selected entities
  prefs: JSON.parse(localStorage.getItem('privasend_prefs') || '{}'),
};

// Apply smart defaults
function applyDefaults() {
  state.selected.clear();
  state.entities.forEach((e, i) => {
    // Pre-check high confidence (>= 0.85)
    if (e.confidence >= 0.85) {
      state.selected.add(i);
    }
    // Apply saved category preferences
    const cat = getCategory(e.pii_type);
    if (state.prefs[cat] === false) {
      state.selected.delete(i);
    } else if (state.prefs[cat] === true && e.confidence >= 0.50) {
      state.selected.add(i);
    }
  });
}

// Analyze flow
async function handleAnalyze() {
  const text = document.getElementById('input-text').value.trim();
  if (!text) return;

  state.text = text;
  showLoading();

  const resp = await fetch('/api/analyze-for-review', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text}),
  });
  const data = await resp.json();

  state.entities = data.entities;
  applyDefaults();
  renderReviewPanel(data.categories);
  hideLoading();
}

// Category toggle
function toggleCategory(cat, checked) {
  state.entities.forEach((e, i) => {
    if (getCategory(e.pii_type) === cat) {
      if (checked) state.selected.add(i);
      else state.selected.delete(i);
    }
  });

  // Save preference if user opted in
  if (document.getElementById('persist-prefs').checked) {
    state.prefs[cat] = checked;
    localStorage.setItem('privasend_prefs', JSON.stringify(state.prefs));
  }

  renderReviewPanel();
}

// Reset to defaults
function resetPrefs() {
  state.prefs = {};
  localStorage.removeItem('privasend_prefs');
  applyDefaults();
  renderReviewPanel();
}

// Redact Only
async function handleRedactOnly() {
  const resp = await fetch('/api/redact-selected', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text: state.text,
      selected_indices: [...state.selected],
    }),
  });
  const data = await resp.json();

  // Copy to clipboard
  await navigator.clipboard.writeText(data.redacted_text);
  showNotification('Redacted text copied to clipboard!');

  // Also show in results
  renderResults(data);
}

// Send to AI
async function handleSendToAI() {
  const model = document.getElementById('ai-model').value;
  const prompt = document.getElementById('ai-prompt').value;
  const apiKey = document.getElementById('user-api-key').value || null;

  if (!prompt.trim()) {
    alert('Please enter a prompt');
    return;
  }

  showLoading();
  closeModal('ai-modal');

  const resp = await fetch('/api/send-to-ai', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text: state.text,
      selected_indices: [...state.selected],
      model,
      prompt,
      api_key: apiKey,
    }),
  });
  const data = await resp.json();

  hideLoading();
  renderAIResponse(data);
}
```

**CSS additions:**

```css
/* Review panel */
.category-section {
  margin-bottom: 1rem;
  border-left: 3px solid rgba(255,255,255,0.1);
  padding-left: 1rem;
}
.category-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}
.entity-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0;
  font-size: 0.9rem;
}
.entity-item.high { border-left: 3px solid #6ee7b7; padding-left: 0.5rem; }
.entity-item.medium { border-left: 3px solid #fcd34d; padding-left: 0.5rem; }

/* Modal */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  width: 90%;
  max-width: 500px;
  padding: 2rem;
}

/* Preference controls */
.pref-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1rem 0;
  padding: 0.5rem;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
}
```

---

## Phase 5: Configuration & Deployment

### 5.1 Update `.env.example`

```bash
# OpenRouter API (for Send to AI feature)
OPENROUTER_API_KEY=sk-or-v1-xxx

# LLM Validation (disabled for MVP)
USE_LLM_VALIDATION=false

# Legacy: Ollama (kept for future use)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
```

### 5.2 Deploy to VPS

```bash
# Copy files
scp -r tools/ server/ Dockerfile pyproject.toml root@72.61.171.205:/opt/privasend/

# Rebuild and restart with OpenRouter key
ssh root@72.61.171.205 "cd /opt/privasend && \
  docker stop privasend && \
  docker rm privasend && \
  docker build -t privasend . && \
  docker run -d --name privasend \
    -p 8100:8000 \
    -e OPENROUTER_API_KEY=sk-or-v1-xxx \
    -e USE_LLM_VALIDATION=false \
    privasend"
```

---

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `tools/config.py` | MODIFY | Add CONFIDENCE_*, USE_LLM_VALIDATION, OPENROUTER_* |
| `tools/pii_categories.py` | CREATE | PII type to category mapping |
| `tools/openrouter.py` | CREATE | OpenRouter API client |
| `tools/detect_pii.py` | MODIFY | Add bucket_entities(), update detect() |
| `server/main.py` | MODIFY | Add 3 new endpoints |
| `server/static/index.html` | REWRITE | Review panel, AI modal, new JS logic |
| `.env.example` | MODIFY | Add OPENROUTER_API_KEY |

---

## Verification Checklist

After each phase:

```bash
# 1. Run tests
pytest tests/ -v

# 2. Check for placeholders
grep -r "TODO\|FIXME\|HACK" tools/ server/

# 3. Manual test flow:
#    a. Paste text with various PII types
#    b. Click Analyze → verify review panel appears
#    c. Verify high-confidence items are pre-checked
#    d. Toggle a category OFF → verify entities uncheck
#    e. Click "Redact Only" → verify clipboard has redacted text
#    f. Click "Send to AI" → verify modal opens
#    g. Select model, enter prompt, click Send
#    h. Verify AI response is displayed
#    i. Check "Remember preferences" → toggle category → reload → verify persisted
#    j. Click "Reset to defaults" → verify preferences cleared
```

---

## Key Decisions (from team discussion)

1. **LLM validation disabled** — Regex + Presidio only for MVP
2. **All detections bucketed** — Even regex matches go through confidence scoring
3. **High confidence = pre-checked** — User can uncheck if needed
4. **OpenRouter for all AI providers** — Single integration point
5. **API keys** — Default provided + users can use own via UI
6. **Preferences** — Session-scoped by default, can persist to localStorage
7. **De-redaction out of scope** — MVP doesn't restore AI responses
