# Sahil Mehta - Role & Responsibilities for PrivaSend

**Document Created:** January 27, 2026  
**Team Meeting:** January 28, 2026

---

## 🎯 Project Overview: PrivaSend

**PrivaSend** (formerly SafePrompt) is a **runtime prompt governance system** designed to protect SMBs from accidentally leaking sensitive data (PII) when using AI tools like ChatGPT.

### The Problem It Solves
- **57% of employees leak sensitive data** into LLMs (per TELUS survey)
- Average data breach costs **$4.45M** (IBM)
- SMBs can't afford enterprise DLP tools ($10K-100K+)

### How It Works
1. User pastes text or uploads a file (PDF/DOCX)
2. **Regex-based redaction** detects and replaces PII (emails, SSNs, phone numbers, API keys, credit cards) with placeholders like `[EMAIL]`, `[SSN]`
3. Shows user what was hidden (transparency)
4. **One-click "Send to ChatGPT"** button routes cleaned text to OpenAI
5. Streams AI response back - completing the entire workflow
6. Logs anonymized metadata (no raw PII stored)

### Tech Stack
| Component | Tool |
|-----------|------|
| **Frontend** | Lovable |
| **Backend Logic** | n8n (workflow automation) |
| **Detection** | Regex (n8n Text Parser) |
| **Database** | Supabase |
| **LLM Integration** | OpenAI API |

---

## 👤 Your Role: Sahil Mehta

Based on the PRD, you have been assigned as a **core technical member** focusing on:

### Primary Responsibilities

| Task | Timeline |
|------|----------|
| **Build n8n workflows** (webhook → parser → response) | Week 1 (Jan 28 - Feb 2) |
| **Connect Lovable to n8n** (webhook integration) | Week 2 (Feb 3-9) |
| **Add OpenAI node** (one-click AI feature) | Week 2 (Feb 3-9) |

### Your Strengths Identified
- **Automation expertise**
- **n8n experience**
- **AgriTech/HealthTech background**

### What This Means Practically
You are the **n8n backend architect**. Your job is to:
1. Create the webhook that receives data from the Lovable frontend
2. Build the text parsing/redaction logic using regex patterns
3. Integrate with OpenAI API for the "Send to AI" feature
4. Ensure the cleaned text flows properly between UI → n8n → OpenAI → back to UI

---

## 📅 Key Dates to Remember

| Date | Milestone |
|------|-----------|
| **Jan 28, 2026** | Tomorrow's team meeting - finalize roles, 3-min pitch ready |
| **Feb 5** | Rewatch assigned n8n sessions (18, 21, 24) |
| **Feb 23** | **FEATURE FREEZE** - only bug fixes after this |
| **Late Feb** | Product Qualifiers (present MVP to mentors) |
| **March 28** | Demo Day in Bangalore |

---

## 📺 Sessions You Should Rewatch (High Priority)

1. **Session 18** - Text Parser & Regex (core detection logic)
2. **Session 21** - HR Recruitment (file handling, PDF upload, "Extract from File" node)
3. **Session 24** - Webhooks & Serverless (Lovable → n8n integration - **critical for you**)
4. **Session 15** - HTTP Request Node (calling OpenAI API)
5. **Session 19** - JSON Structured Output (clean OpenAI responses)

---

## 🤝 Collaboration Partners

- **Fareed**: Works with you on n8n logic (Week 1) and OpenAI node (Week 2)
- **Naveli**: Designs the Lovable UI you'll connect to
- **Hina**: Helps with regex patterns

---

## ❓ Key Questions for Your Meeting

1. **Clarify with the team:** Will you use self-hosted n8n or cloud n8n? (Privacy implications)
2. **Ask Naveli:** What endpoints/webhooks should the Lovable UI call?
3. **Ask Fareed:** How will you coordinate on the test corpus - who tests what?

---

## 📊 Technical Architecture Reference

```
[User] → [Lovable UI] → [Bubble form] → [n8n webhook] 
  → [Text Parser (regex)] → [Redaction logic] → [Display results]
  → [User clicks "Send to AI"] → [n8n OpenAI node] → [Stream response]
  → [Log anonymized data to Supabase] → [Return to UI]
```

---

## 🔧 Regex Patterns You'll Be Working With

```javascript
// Email
const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;

// US Phone (multiple formats)
const phonePattern = /(\d{3}[-.]?\d{3}[-.]?\d{4})|(\(\d{3}\)\s?\d{3}[-.]?\d{4})/g;

// US SSN
const ssnPattern = /\d{3}-\d{2}-\d{4}/g;

// Credit Card (simple 16-digit with optional dashes)
const cardPattern = /\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}/g;

// API Key (heuristic: 20+ alphanumeric)
const apiKeyPattern = /\b[A-Za-z0-9_-]{20,}\b/g;
```

---

## ✅ Success Metrics

- ≥95% redaction accuracy on test corpus
- <10% false positives
- Working demo by Product Qualifiers (late Feb)
- 3-minute pitch ready by Jan 28

---

*Good luck at tomorrow's meeting, Sahil! 🚀*
