# n8n + Regex Architecture Evaluation for PrivaSend

**Date:** January 27, 2026  
**Author:** Technical Architecture Review  
**Purpose:** Inform architecture decisions for PII redaction workflow

---

## 1. End-to-End Workflow Design

### 1.1 Trigger Type: Webhook (HTTP POST)

**Why Webhook:**
- User-initiated actions (paste text, upload file) require **synchronous request-response**
- Schedule-based triggers make no sense for on-demand processing
- Event-based triggers (e.g., database changes) add unnecessary complexity

**Webhook Configuration:**
```
Method: POST
Path: /api/redact
Response Mode: "Respond to Webhook" (not "Last Node")
Authentication: API Key header or Bearer token
```

### 1.2 Complete n8n Workflow (Node by Node)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PrivaSend n8n Workflow                          │
└─────────────────────────────────────────────────────────────────────────┘

[1] Webhook (Trigger)
        │
        ▼
[2] IF Node (Check input type: text vs file)
        │
        ├──── Text ────► [3a] Set Node (extract text field)
        │
        └──── File ────► [3b] Extract from File Node (PDF/DOCX → text)
                                │
                                ▼
                         [3c] Merge Node (unify text output)
        │
        ▼
[4] Code Node (Regex Processing - CORE LOGIC)
        │
        ▼
[5] Set Node (Format response: original, redacted, stats)
        │
        ▼
[6] IF Node (User clicked "Send to AI"?)
        │
        ├──── No ────► [7a] Respond to Webhook (return redacted text only)
        │
        └──── Yes ───► [7b] OpenAI Node (send redacted text)
                                │
                                ▼
                         [8] Supabase Node (log anonymized metadata)
                                │
                                ▼
                         [9] Respond to Webhook (return AI response)
```

### 1.3 Detailed Node Configuration

#### Node 1: Webhook
```json
{
  "httpMethod": "POST",
  "path": "redact",
  "responseMode": "responseNode",
  "options": {
    "rawBody": true  // Preserve file binary data
  }
}
```

#### Node 2: IF Node (Input Type Check)
```javascript
// Condition: Check if file was uploaded
{{ $json.file !== undefined && $json.file !== null }}
```

#### Node 3b: Extract from File
- **Node Type:** "Extract from File"
- **Supported formats:** PDF, DOCX, TXT
- **Output:** Plain text string
- **Error handling:** Catch corrupted files, return user-friendly error

#### Node 4: Code Node (Regex Engine) - THE CORE
```javascript
// Input: raw text from previous node
const inputText = $json.text || $json.extractedText;

// Define patterns with named groups for easier debugging
const patterns = {
  email: {
    regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,
    placeholder: '[EMAIL]',
    category: 'email'
  },
  phone_us: {
    regex: /(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}/g,
    placeholder: '[PHONE]',
    category: 'phone'
  },
  ssn: {
    regex: /\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g,
    placeholder: '[SSN]',
    category: 'ssn'
  },
  credit_card: {
    regex: /\b(?:\d{4}[-\s]?){3}\d{4}\b/g,
    placeholder: '[CREDIT_CARD]',
    category: 'credit_card'
  },
  api_key: {
    regex: /\b(?:sk-|pk-|api[_-]?key[_-]?)?[A-Za-z0-9_-]{20,}\b/gi,
    placeholder: '[API_KEY]',
    category: 'api_key'
  }
};

// Process and count redactions
let redactedText = inputText;
const stats = {};
const matches = [];

for (const [name, pattern] of Object.entries(patterns)) {
  const found = inputText.match(pattern.regex) || [];
  if (found.length > 0) {
    stats[pattern.category] = found.length;
    matches.push(...found.map(m => ({ type: pattern.category, value: m })));
    redactedText = redactedText.replace(pattern.regex, pattern.placeholder);
  }
}

// Calculate confidence score
const totalRedactions = Object.values(stats).reduce((a, b) => a + b, 0);
const confidenceScore = totalRedactions > 0 ? 98 : 100; // Simplified for MVP

return {
  original: inputText,
  redacted: redactedText,
  stats: stats,
  totalRedactions: totalRedactions,
  confidenceScore: confidenceScore,
  isSafe: totalRedactions > 0
};
```

#### Node 7b: OpenAI Node
```json
{
  "model": "gpt-4-turbo",
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.redacted }}"
    }
  ],
  "temperature": 0.7,
  "maxTokens": 2000
}
```

#### Node 8: Supabase Node (Anonymized Logging)
```json
{
  "table": "redaction_logs",
  "data": {
    "user_id_hash": "{{ $json.userIdHash }}",
    "timestamp": "{{ $now }}",
    "redaction_counts": "{{ JSON.stringify($json.stats) }}",
    "status": "success"
  }
}
```

---

## 2. Role of Regex in This Workflow

### 2.1 Problems Regex Solves

| Problem | How Regex Solves It |
|---------|---------------------|
| **Pattern Recognition** | Emails, SSNs, phone numbers follow predictable formats |
| **Deterministic Output** | Same input → same output (no AI hallucination risk) |
| **Speed** | Regex processes thousands of characters in <10ms |
| **No API Dependency** | Works offline, no latency, no cost per call |
| **Transparency** | Users can audit exactly what patterns are matched |

### 2.2 Why Regex is Appropriate Here

**Regex is the RIGHT choice when:**
- ✅ Data has **known, structured patterns** (emails = `*@*.*`)
- ✅ You need **100% reproducibility** (compliance requirement)
- ✅ **Latency matters** (real-time user interaction)
- ✅ **Cost must be zero** for detection (ML APIs charge per call)
- ✅ **False negatives are worse than false positives** (better to over-redact)

**Regex is the WRONG choice when:**
- ❌ Data is unstructured (e.g., "John's social is the digits after the letter")
- ❌ Context matters (e.g., "Apple" as company vs. fruit)
- ❌ You need semantic understanding

### 2.3 Pattern Examples with Trade-offs

#### Email Pattern
```regex
/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi
```
- **Catches:** `john@example.com`, `user.name+tag@sub.domain.co.uk`
- **False positive risk:** Low (@ symbol is distinctive)
- **False negative risk:** Obfuscated emails like `john [at] example [dot] com`

#### SSN Pattern (US)
```regex
/\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g
```
- **Catches:** `123-45-6789`, `123 45 6789`, `123456789`
- **False positive risk:** HIGH - dates like `12-31-2024` match this pattern!
- **Mitigation:** Add date exclusion logic

```javascript
// Improved SSN detection with date exclusion
const ssnPattern = /\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g;
const datePattern = /\b(0?[1-9]|1[0-2])[-\/](0?[1-9]|[12]\d|3[01])[-\/]\d{4}\b/g;

// First find all dates, then exclude them from SSN matches
const dates = text.match(datePattern) || [];
let ssns = text.match(ssnPattern) || [];
ssns = ssns.filter(ssn => !dates.includes(ssn));
```

#### API Key Pattern (Heuristic)
```regex
/\b(?:sk-|pk-|api[_-]?key[_-]?)?[A-Za-z0-9_-]{20,}\b/gi
```
- **Catches:** `sk-abc123...`, `AKIAIOSFODNN7EXAMPLE` (AWS), generic long strings
- **False positive risk:** MEDIUM - UUIDs, base64 strings, random IDs
- **Mitigation:** Whitelist known safe patterns (e.g., file hashes)

---

## 3. Critical Evaluation: Is n8n Necessary?

### 3.1 Value n8n Adds

| Value | Explanation | PrivaSend Relevance |
|-------|-------------|---------------------|
| **Visual Debugging** | See data flow between nodes | HIGH - debugging regex outputs |
| **No-Code Modifications** | Non-developers can tweak workflows | MEDIUM - team has mixed skills |
| **Native Integrations** | OpenAI, Supabase nodes pre-built | HIGH - saves development time |
| **Error Handling** | Retry logic, error branches built-in | HIGH - API failures handled gracefully |
| **Webhook Management** | Auto-generates endpoints, handles CORS | HIGH - Lovable integration |
| **Logging & Monitoring** | Execution history, performance metrics | MEDIUM - useful for debugging |
| **Scalability** | Queue management, parallel execution | LOW - MVP doesn't need scale |

### 3.2 Scenarios Where n8n is OVERKILL

| Scenario | Why n8n is Too Much | Better Alternative |
|----------|---------------------|-------------------|
| **Single-step processing** | Just regex on text, return result | Serverless function (Vercel, AWS Lambda) |
| **High throughput (>1000 req/sec)** | n8n adds ~50-100ms latency per workflow | Direct API with compiled regex |
| **Simple CRUD operations** | No orchestration needed | Direct Supabase SDK |
| **Batch processing** | n8n optimized for event-driven, not batch | Python script with multiprocessing |
| **Cost-sensitive deployment** | n8n cloud = $20-50/mo; self-hosted = server costs | Vercel Edge Functions (free tier) |

### 3.3 Alternative Architectures

#### Option A: Pure Serverless (Vercel Edge Functions)
```
[Lovable UI] → [Vercel Edge Function] → [Supabase]
                      ↓
               [OpenAI API]
```
**Pros:**
- Zero cold start (edge runtime)
- Free tier handles MVP traffic
- Single codebase (TypeScript)
- Lower latency (~20ms vs ~100ms)

**Cons:**
- No visual debugging
- Harder for non-developers to modify
- Must build retry logic manually

#### Option B: Backend-Only (Express.js / FastAPI)
```
[Lovable UI] → [Express.js API] → [PostgreSQL]
                      ↓
               [OpenAI SDK]
```
**Pros:**
- Full control over logic
- Easy to unit test regex
- Standard deployment (Docker, Railway)

**Cons:**
- More code to write
- No visual workflow
- Team needs backend experience

#### Option C: Hybrid (Lovable + Supabase Edge Functions)
```
[Lovable UI] → [Supabase Edge Function] → [Supabase DB]
                      ↓
               [OpenAI API]
```
**Pros:**
- Stays within Lovable/Supabase ecosystem
- Edge functions = low latency
- Supabase handles auth, DB, functions

**Cons:**
- Edge functions have size limits
- Debugging is harder than n8n

---

## 4. Decision Guidance

### 4.1 When n8n is the RIGHT Choice

✅ **Choose n8n when:**
- Team has **mixed technical skills** (some non-coders)
- You need **rapid prototyping** (MVP in 6 weeks)
- Workflow involves **multiple integrations** (OpenAI, Supabase, potentially Slack/email)
- You want **visual debugging** for complex data flows
- You anticipate **frequent changes** to workflow logic
- **Error handling and retries** are important (API failures)

### 4.2 When n8n is the WRONG Choice

❌ **Avoid n8n when:**
- Processing is **simple and linear** (single function call)
- You need **<50ms latency** (n8n adds overhead)
- Budget is **extremely tight** (self-hosting has server costs)
- Team is **all experienced developers** (code is faster to write than configure nodes)
- You need **>1000 requests/second** (n8n not designed for high throughput)

### 4.3 Recommendation for PrivaSend

| Factor | Assessment | Points to n8n? |
|--------|------------|----------------|
| Team skills | Mixed (some n8n experience, some not) | ✅ Yes |
| Timeline | 6 weeks to MVP | ✅ Yes (faster prototyping) |
| Integrations | OpenAI + Supabase + Lovable | ✅ Yes (pre-built nodes) |
| Latency requirement | User-facing, but not real-time critical | ⚠️ Acceptable |
| Scale | Demo + small pilot (~100 users) | ✅ Yes (n8n handles this) |
| Debugging needs | High (regex tuning required) | ✅ Yes |
| Post-MVP extensibility | Slack bot, email alerts, audit logs | ✅ Yes |

**Verdict: n8n is APPROPRIATE for PrivaSend MVP**

The visual debugging, pre-built integrations, and rapid iteration capabilities outweigh the latency overhead for a demo-focused MVP. Post-MVP, consider migrating to serverless if latency becomes an issue.

---

## 5. Implementation Recommendations

### 5.1 Optimize Regex Performance

```javascript
// BAD: Recompile regex on every request
const result = text.match(/pattern/g);

// GOOD: Pre-compile regex patterns once
const PATTERNS = {
  email: new RegExp('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', 'gi'),
  // ... other patterns
};

// Then use pre-compiled patterns
const result = text.match(PATTERNS.email);
```

### 5.2 Handle Large Files

```javascript
// Limit processing to prevent n8n timeout (default 60s)
const MAX_CHARS = 50000; // ~10 pages of text

if (inputText.length > MAX_CHARS) {
  return {
    error: true,
    message: `Text too long (${inputText.length} chars). Maximum ${MAX_CHARS} characters.`
  };
}
```

### 5.3 Add Confidence Scoring

```javascript
// Pattern-based confidence
const patternConfidence = {
  email: 0.99,      // Very reliable pattern
  phone: 0.85,      // Some false positives possible
  ssn: 0.75,        // Date confusion risk
  api_key: 0.70,    // Heuristic-based
  credit_card: 0.95 // Luhn checksum could improve this
};

// Calculate weighted confidence
let totalWeight = 0;
let weightedConfidence = 0;

for (const [category, count] of Object.entries(stats)) {
  totalWeight += count;
  weightedConfidence += count * patternConfidence[category];
}

const overallConfidence = totalWeight > 0 
  ? Math.round((weightedConfidence / totalWeight) * 100) 
  : 100;
```

### 5.4 Error Handling Strategy

```
[Code Node] 
    │
    ├─── Success ────► Continue to next node
    │
    └─── Error ──────► [Error Handler Node]
                              │
                              ├── Regex Error ──► Return: "Invalid pattern"
                              ├── File Error ───► Return: "Corrupted file"
                              └── Timeout ──────► Return: "Processing took too long"
```

---

## 6. Summary

| Question | Answer |
|----------|--------|
| **Is n8n needed?** | Yes, for MVP. Provides rapid prototyping and visual debugging. |
| **Is regex appropriate?** | Yes. PII patterns are well-defined and deterministic. |
| **Main risk?** | False positives (dates → SSN, random strings → API keys) |
| **Main mitigation?** | Allow user override, add exclusion patterns, show confidence scores |
| **Post-MVP consideration?** | If latency becomes critical, migrate regex logic to Edge Functions |

---

*Document prepared for PrivaSend architecture review. Questions? Discuss with team during Jan 27 meeting.*
