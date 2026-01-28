# Presidio + n8n Integration Guide for PrivaSend MVP

**Date:** January 27, 2026  
**Decision:** Include Presidio/NER layer in MVP (not post-MVP)  
**Expected Accuracy:** 90-95% (up from 85-90% regex-only)

---

## 1. What is Presidio?

**Microsoft Presidio** is an open-source SDK for PII detection and anonymization. It uses:
- **Named Entity Recognition (NER)** - ML models to identify names, locations, organizations
- **Pattern Recognizers** - Regex patterns (like what you'd write manually)
- **Custom Recognizers** - Add your own detection logic

### Why Presidio Over Pure Regex?

| Capability | Regex Only | Presidio |
|------------|------------|----------|
| Email detection | ✅ 95%+ | ✅ 95%+ |
| Phone detection | ✅ 75-85% | ✅ 90%+ |
| SSN detection | ⚠️ 70-80% | ✅ 90%+ (context aware) |
| **Name detection** | ❌ 20-40% | ✅ 85%+ |
| **Address detection** | ❌ 30-50% | ✅ 80%+ |
| **Organization names** | ❌ 10% | ✅ 75%+ |
| Date vs SSN confusion | ❌ High | ✅ Resolved |

---

## 2. Architecture Options

### Option A: Self-Hosted Presidio API (Recommended for MVP)
```
[Lovable UI] → [n8n Webhook] 
                    ↓
              [Code Node: Regex Layer 1]
                    ↓
              [HTTP Request: Presidio API]  ← Docker container
                    ↓
              [Merge Results]
                    ↓
              [Response to UI]
```

**Pros:** Full control, no external API costs, privacy-compliant  
**Cons:** Need to host Docker container (Render, Railway, or local)

### Option B: Presidio as Python Script in n8n
```
[Lovable UI] → [n8n Webhook] 
                    ↓
              [Execute Command Node: Python + Presidio]
                    ↓
              [Parse Output]
                    ↓
              [Response to UI]
```

**Pros:** No separate service to maintain  
**Cons:** n8n must have Python + Presidio installed (complex setup)

### Option C: Hybrid Cloud (Use Azure Text Analytics)
```
[Lovable UI] → [n8n Webhook] 
                    ↓
              [Code Node: Regex Layer 1]
                    ↓
              [HTTP Request: Azure PII Detection API]
                    ↓
              [Merge Results]
                    ↓
              [Response to UI]
```

**Pros:** No hosting, managed service  
**Cons:** API costs (~$1 per 1000 requests), data leaves your control

---

## 3. Recommended Setup: Self-Hosted Presidio API

### 3.1 Deploy Presidio API (One-Time Setup)

**Option 1: Docker Locally (for development)**
```bash
# Pull Presidio images
docker pull mcr.microsoft.com/presidio-analyzer
docker pull mcr.microsoft.com/presidio-anonymizer

# Run analyzer API on port 5001
docker run -d -p 5001:3000 mcr.microsoft.com/presidio-analyzer

# Run anonymizer API on port 5002
docker run -d -p 5002:3000 mcr.microsoft.com/presidio-anonymizer
```

**Option 2: Deploy to Render.com (free tier, for demo)**
```yaml
# render.yaml
services:
  - type: web
    name: presidio-analyzer
    env: docker
    dockerfilePath: ./Dockerfile.analyzer
    envVars:
      - key: PORT
        value: 3000
```

**Option 3: Deploy to Railway (simple, $5/mo)**
```bash
# One-click deploy from Docker image
railway login
railway init
railway up --image mcr.microsoft.com/presidio-analyzer
```

### 3.2 Presidio API Endpoints

#### Analyze Endpoint (Detect PII)
```
POST http://localhost:5001/analyze

Request Body:
{
  "text": "John Smith's email is john@example.com and SSN is 123-45-6789",
  "language": "en",
  "entities": ["PERSON", "EMAIL_ADDRESS", "US_SSN", "PHONE_NUMBER", "CREDIT_CARD"]
}

Response:
[
  {"entity_type": "PERSON", "start": 0, "end": 10, "score": 0.85},
  {"entity_type": "EMAIL_ADDRESS", "start": 22, "end": 38, "score": 0.95},
  {"entity_type": "US_SSN", "start": 51, "end": 62, "score": 0.90}
]
```

#### Anonymize Endpoint (Redact PII)
```
POST http://localhost:5002/anonymize

Request Body:
{
  "text": "John Smith's email is john@example.com",
  "analyzer_results": [
    {"entity_type": "PERSON", "start": 0, "end": 10, "score": 0.85},
    {"entity_type": "EMAIL_ADDRESS", "start": 22, "end": 38, "score": 0.95}
  ],
  "anonymizers": {
    "PERSON": {"type": "replace", "new_value": "[PERSON]"},
    "EMAIL_ADDRESS": {"type": "replace", "new_value": "[EMAIL]"}
  }
}

Response:
{
  "text": "[PERSON]'s email is [EMAIL]"
}
```

---

## 4. Updated n8n Workflow (Regex + Presidio)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PrivaSend n8n Workflow (Hybrid)                           │
└─────────────────────────────────────────────────────────────────────────────┘

[1] Webhook (Trigger)
        │
        ▼
[2] IF Node (Check input type: text vs file)
        │
        ├──── Text ────► [3a] Set Node (extract text)
        │
        └──── File ────► [3b] Extract from File → [3c] Merge
        │
        ▼
[4] Code Node (LAYER 1: Fast Regex Pre-scan)
        │    - Catches obvious patterns quickly
        │    - Emails, credit cards, API keys
        │
        ▼
[5] HTTP Request Node (LAYER 2: Presidio NER)
        │    - POST to Presidio /analyze
        │    - Catches names, addresses, context-dependent PII
        │
        ▼
[6] Code Node (Merge Results)
        │    - Combine regex + Presidio findings
        │    - De-duplicate overlapping matches
        │    - Apply redaction placeholders
        │
        ▼
[7] Set Node (Format response: original, redacted, stats, confidence)
        │
        ▼
[8] IF Node (User clicked "Send to AI"?)
        │
        ├──── No ────► [9a] Respond to Webhook (redacted text only)
        │
        └──── Yes ───► [9b] OpenAI Node → [10] Supabase Log → [11] Respond
```

---

## 5. Implementation Code

### Node 4: Layer 1 - Fast Regex Pre-scan
```javascript
// Quick regex layer - catches obvious patterns
const inputText = $json.text;

const patterns = {
  email: {
    regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,
    type: 'EMAIL_ADDRESS'
  },
  credit_card: {
    regex: /\b(?:\d{4}[-\s]?){3}\d{4}\b/g,
    type: 'CREDIT_CARD'
  },
  api_key: {
    regex: /\b(?:sk-|pk-|api[_-]?key[_-]?)?[A-Za-z0-9_-]{20,}\b/gi,
    type: 'API_KEY'
  }
};

const regexResults = [];

for (const [name, pattern] of Object.entries(patterns)) {
  let match;
  const regex = new RegExp(pattern.regex.source, pattern.regex.flags);
  
  while ((match = regex.exec(inputText)) !== null) {
    regexResults.push({
      entity_type: pattern.type,
      start: match.index,
      end: match.index + match[0].length,
      score: 0.95,  // High confidence for regex
      source: 'regex'
    });
  }
}

return {
  text: inputText,
  regexResults: regexResults
};
```

### Node 5: HTTP Request to Presidio
```json
{
  "method": "POST",
  "url": "http://your-presidio-host:5001/analyze",
  "body": {
    "text": "{{ $json.text }}",
    "language": "en",
    "entities": [
      "PERSON",
      "EMAIL_ADDRESS", 
      "PHONE_NUMBER",
      "US_SSN",
      "CREDIT_CARD",
      "LOCATION",
      "ORGANIZATION",
      "DATE_TIME",
      "NRP",
      "MEDICAL_LICENSE",
      "US_DRIVER_LICENSE"
    ],
    "score_threshold": 0.5
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Node 6: Merge Results & Apply Redaction
```javascript
const text = $('Node 4').first().json.text;
const regexResults = $('Node 4').first().json.regexResults;
const presidioResults = $json; // Array from Presidio

// Combine results
let allResults = [...regexResults];

// Add Presidio results (avoid duplicates)
for (const pResult of presidioResults) {
  const isDuplicate = allResults.some(r => 
    Math.abs(r.start - pResult.start) < 5 && 
    Math.abs(r.end - pResult.end) < 5
  );
  
  if (!isDuplicate) {
    allResults.push({
      ...pResult,
      source: 'presidio'
    });
  }
}

// Sort by position (descending) for safe replacement
allResults.sort((a, b) => b.start - a.start);

// Apply redactions
let redactedText = text;
const stats = {};

for (const result of allResults) {
  const placeholder = `[${result.entity_type}]`;
  const original = text.substring(result.start, result.end);
  
  redactedText = 
    redactedText.substring(0, result.start) + 
    placeholder + 
    redactedText.substring(result.end);
  
  stats[result.entity_type] = (stats[result.entity_type] || 0) + 1;
}

// Calculate weighted confidence
const avgConfidence = allResults.length > 0
  ? allResults.reduce((sum, r) => sum + r.score, 0) / allResults.length
  : 1.0;

return {
  original: text,
  redacted: redactedText,
  stats: stats,
  totalRedactions: allResults.length,
  confidenceScore: Math.round(avgConfidence * 100),
  detectionDetails: allResults.map(r => ({
    type: r.entity_type,
    confidence: Math.round(r.score * 100) + '%',
    source: r.source
  }))
};
```

---

## 6. Supported Entity Types (Presidio Built-in)

| Entity Type | Description | Example |
|-------------|-------------|---------|
| `PERSON` | Full names | John Smith, Dr. Jane Doe |
| `EMAIL_ADDRESS` | Email addresses | john@example.com |
| `PHONE_NUMBER` | Phone numbers (international) | +1-555-123-4567 |
| `US_SSN` | US Social Security Numbers | 123-45-6789 |
| `CREDIT_CARD` | Credit/debit card numbers | 4111-1111-1111-1111 |
| `LOCATION` | Addresses, cities, countries | 123 Main St, New York |
| `ORGANIZATION` | Company/org names | Microsoft, Acme Corp |
| `DATE_TIME` | Dates (distinguishes from SSN!) | January 15, 2024 |
| `NRP` | Nationality, religion, politics | American, Catholic |
| `US_DRIVER_LICENSE` | Driver's license numbers | D123-456-789 |
| `US_PASSPORT` | Passport numbers | 123456789 |
| `US_ITIN` | Individual Tax ID | 912-34-5678 |
| `MEDICAL_LICENSE` | Medical license numbers | MD12345 |
| `IP_ADDRESS` | IPv4/IPv6 addresses | 192.168.1.1 |
| `IBAN_CODE` | International bank accounts | DE89370400440532013000 |

---

## 7. Adding Custom Recognizers (India-Specific)

### Aadhaar Number Recognizer
```python
# custom_recognizers.py (add to Presidio deployment)
from presidio_analyzer import Pattern, PatternRecognizer

aadhaar_recognizer = PatternRecognizer(
    supported_entity="IN_AADHAAR",
    name="Aadhaar Recognizer",
    patterns=[
        Pattern(
            name="aadhaar_pattern",
            regex=r"\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b",
            score=0.85
        )
    ]
)

# PAN Card Recognizer
pan_recognizer = PatternRecognizer(
    supported_entity="IN_PAN",
    name="PAN Recognizer",
    patterns=[
        Pattern(
            name="pan_pattern",
            regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
            score=0.90
        )
    ]
)
```

---

## 8. Performance Considerations

### Latency Breakdown
| Operation | Time |
|-----------|------|
| Network: UI → n8n | ~50ms |
| Regex processing | ~5ms |
| Presidio NER | ~100-200ms |
| OpenAI API (if used) | ~500-1500ms |
| Network: n8n → UI | ~50ms |
| **Total (without AI)** | **~200-300ms** |
| **Total (with AI)** | **~700-1800ms** |

### Optimization Tips
1. **Run regex first** - filter obvious patterns before Presidio
2. **Set score_threshold** - 0.5 catches more, 0.7 reduces false positives
3. **Limit entities** - only scan for relevant types
4. **Cache Presidio model** - warm startup the first request

---

## 9. Error Handling

### Presidio Unavailable Fallback
```javascript
// In n8n Code Node after HTTP Request
try {
  const presidioResults = $json;
  // Process normally
} catch (error) {
  // Fallback to regex-only mode
  console.log('Presidio unavailable, using regex fallback');
  
  return {
    warning: 'Advanced detection temporarily unavailable. Using basic patterns.',
    results: $('Regex Layer').first().json.regexResults,
    fallbackMode: true
  };
}
```

---

## 10. Updated Accuracy Expectations

| PII Type | Regex Only | Regex + Presidio |
|----------|------------|------------------|
| Email | 95% | 98% |
| Phone | 75-85% | 92% |
| SSN | 70-80% | 93% |
| Credit Card | 90% | 95% |
| **Names** | 20-40% | **85%** ⬆️ |
| **Addresses** | 30-50% | **82%** ⬆️ |
| **Organizations** | 10% | **78%** ⬆️ |
| **Overall** | **85-90%** | **90-95%** ⬆️ |

---

## 11. Hosting Recommendations for Demo Day

| Platform | Cost | Ease | Stability |
|----------|------|------|-----------|
| **Render.com** | Free tier | Easy | Good for demo |
| **Railway** | $5/mo | Very easy | Better uptime |
| **Local Docker** | Free | Medium | Risk of laptop issues |
| **Azure Container** | Pay-as-go | Medium | Production-ready |

**Recommendation for MVP:** Deploy to **Railway** - simple, reliable, $5/mo is worth the stability for Demo Day.

---

## 12. Summary: What Changes with Presidio

| Aspect | Before (Regex Only) | After (Regex + Presidio) |
|--------|---------------------|--------------------------|
| **Accuracy** | 85-90% | 90-95% |
| **Name detection** | ❌ Poor | ✅ Good |
| **Context awareness** | ❌ None | ✅ Yes (date vs SSN) |
| **Latency** | ~50ms | ~200-300ms |
| **Complexity** | Low | Medium |
| **Hosting needs** | n8n only | n8n + Presidio container |
| **MVP achievable?** | ✅ Yes | ✅ Yes (with Docker) |

---

## 13. Next Steps for You (Sahil)

1. **Week 1:** 
   - Set up local Docker with Presidio (test the API)
   - Build n8n workflow with HTTP Request node
   
2. **Week 2:**
   - Deploy Presidio to Railway/Render
   - Connect Lovable UI to n8n endpoint
   
3. **Week 3:**
   - Add custom recognizers (Aadhaar, PAN if needed)
   - Tune score_threshold for optimal accuracy

---

*This document updated based on team decision to include Presidio in MVP.*
