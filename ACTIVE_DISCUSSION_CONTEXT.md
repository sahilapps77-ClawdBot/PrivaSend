# Active Discussion Context
> **Date:** 2026-02-06
> **Time:** ~8:00 PM IST
> **Status:** Ongoing - Awaiting user input

## Current Discussion Topic
**Comparing PRD v2.0 vs Current Implementation** - Deciding what to change/keep

---

## Key Points Under Discussion

### 1. UI Framework (MAJOR DECISION PENDING)
| Option | PRD v2.0 | Current | Status |
|--------|----------|---------|--------|
| **Lovable/Bubble** | ✅ Required | ❌ Not using | Need decision |
| **Custom HTML/JS** | ❌ Not preferred | ✅ Built & working | Need decision |

**Context:**
- PRD v2.0 wants no-code solution (Lovable/Bubble)
- We have working custom HTML/JS frontend
- User said: "we shall discuss these points in a while"
- **NOT DECIDED YET** - Waiting for Sahil's input

---

### 2. Backend Architecture (DECISION PENDING)
| Option | PRD v2.0 | Current | My Recommendation |
|--------|----------|---------|-------------------|
| **n8n workflow** | ✅ Required | ❌ Not using | Switch? |
| **FastAPI Python** | ❌ Not preferred | ✅ Built & working | Keep? |

**Context:**
- PRD wants n8n for visual workflow
- We have FastAPI (better performance, testing)
- User acknowledged FastAPI might be better
- **NOT DECIDED YET** - Waiting for Sahil's input

---

### 3. User Confirmation Flow (MUST IMPLEMENT)
**PRD v2.0 Requirement:**
- Show ambiguous items (0.50-0.85 confidence) to user
- User reviews and confirms before redaction
- Helps achieve 99% accuracy

**Current Status:**
- ❌ NOT IMPLEMENTED
- Planned in MVP_ARCHITECTURE_PIVOT.md Phase 3-4
- This is a **must-have for MVP per PRD**

**Decision:** NEED TO BUILD THIS

---

### 4. LLM Integration (RECOMMEND KEEPING OPENROUTER)
| Option | PRD v2.0 | Current Plan | Status |
|--------|----------|--------------|--------|
| **OpenAI only** | ✅ Required | ❌ Not preferred | PRD wants this |
| **OpenRouter** | ❌ Not mentioned | ✅ Planned | Better choice |

**Context:**
- PRD v2.0: OpenAI via n8n only
- We planned: OpenRouter (multi-LLM: GPT-4o, Gemini, Claude)
- OpenRouter gives user choice
- **NOT DECIDED YET** - Need Sahil's preference

---

### 5. Logging (DECISION PENDING)
| Option | PRD v2.0 | Current | Privacy Risk |
|--------|----------|---------|--------------|
| **Supabase** | ✅ Required | ❌ None | Medium |
| **Self-hosted** | ❌ Not mentioned | ❌ None | Low |
| **No logging** | ❌ Not preferred | ✅ Current | None |

**Context:**
- PRD wants logging for analytics
- Privacy risk storing any data
- Current: No logging (ephemeral)
- **NOT DECIDED YET** - Need Sahil's call

---

## What's Already Aligned ✅

| Feature | PRD v2.0 | Current | Status |
|---------|----------|---------|--------|
| PII Detection | Regex + Presidio | Regex + Presidio | ✅ Aligned |
| OCR | Required | Implemented | ✅ Aligned |
| File Upload | PDF, DOCX, Images | PDF, DOCX, Images | ✅ Aligned |
| Two-Layer Filtering | Required | Implemented | ✅ Aligned |
| No Cloud LLM | Disabled | Disabled | ✅ Aligned |
| English Only | MVP Scope | Implemented | ✅ Aligned |

---

## Pending User Decisions

User said: "we shall discuss these points in a while"

**Waiting for Sahil to decide:**
1. ❓ UI: Switch to Lovable/Bubble or keep custom?
2. ❓ Backend: Switch to n8n or keep FastAPI?
3. ❓ LLM: OpenAI only or keep OpenRouter?
4. ❓ Logging: Add Supabase or stay ephemeral?

---

## My Recommendations (For Discussion)

1. **Keep FastAPI** - Better than n8n for this use case
2. **Keep OpenRouter** - User choice is valuable
3. **Build User Confirmation UI** - PRD requirement, improves accuracy
4. **Defer Logging** - Privacy risk, not core to demo
5. **UI Decision** - Either works, custom is ready now

---

## Next Steps (Per User)
1. ✅ Saved PRD v2.0 to project
2. ✅ Analyzed gaps
3. ⏳ **WAITING:** User wants to discuss points
4. ⏳ **THEN:** Decide on changes
5. ⏳ **THEN:** Begin implementation with Kimi K2.5

---

## Context Preservation Confirmation

**Sahil asked me to:**
- ✅ Keep all conversation context
- ✅ Not forget what we're talking about
- ✅ Confirm back to him

**I confirm:**
- I have saved PRD v2.0 to `/home/node/clawd/projects/PrivaSend/PRD_v2.0.md`
- I have documented all discussion points in this file
- I understand we are deciding: UI framework, backend architecture, LLM choice, logging
- I am waiting for your input before proceeding
- I will use Kimi K2.5 for coding once decisions are made

**Ready when you are to continue discussion.**
