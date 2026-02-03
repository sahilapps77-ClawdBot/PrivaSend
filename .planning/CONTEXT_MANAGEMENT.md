# Context Management Guide

> How to maintain AI agent performance during long development sessions

## The Problem

AI agents have limited context windows. As conversations grow:
- Earlier instructions get pushed out
- Quality degrades
- The agent starts contradicting itself
- Responses become slower and more generic

**The math:** If each decision in a long chain is 90% accurate, after 10 decisions you're at 35% accuracy. Context management prevents this decay.

## The Solution: Strategic Context Clearing

### 1. Clear Between Unrelated Tasks

When you finish one task (e.g., "add email detection") and start another (e.g., "build API endpoint"), **start a new conversation**.

**Why:** The context from email regex patterns is irrelevant to FastAPI endpoint design. Keeping it just adds noise.

**How in Claude Code:**
```
# Option 1: Start new conversation
/clear

# Option 2: Compact context (summarize and continue)
/compact
```

### 2. Use Subagents for Investigation

When you need to explore/research (read many files, search codebase, review docs), delegate to a subagent.

**Example prompt to agent:**
```
Use a subagent to investigate how Presidio handles custom recognizers.
Report back: (1) How to create one, (2) How to register it, (3) Example code.
```

**Why:** The subagent explores in its own context. You get a clean summary without 50 file reads polluting your main context.

### 3. Document Progress Before Clearing

Before clearing context on a complex task:

1. **Write current state to STATE.md:**
   ```markdown
   ## Session: 2026-02-03 - Adding GSTIN Detection

   ### Completed
   - Added regex pattern to config.py
   - Created 5 test cases

   ### In Progress
   - Need to handle edge case: GSTIN with lowercase letters

   ### Blockers
   - None

   ### Next Steps
   1. Add lowercase normalization
   2. Run full evaluation
   3. Update workflow docs
   ```

2. **Clear context**

3. **Start fresh with focused prompt:**
   ```
   Read STATE.md for context. Continue work on GSTIN detection.
   Current task: Add lowercase normalization for GSTIN patterns.
   ```

### 4. One Task Per Context Window

For multi-task plans, execute each task in a fresh context:

```
Task 1: Add regex pattern → Clear →
Task 2: Write tests → Clear →
Task 3: Update docs → Clear →
Task 4: Final verification
```

Each task gets full context attention instead of sharing a degraded context.

## When to Clear

| Situation | Action |
|-----------|--------|
| Finished a feature, starting new one | Clear |
| Agent repeating itself | Clear |
| Quality noticeably dropped | Clear |
| Conversation > 50 turns | Consider clearing |
| Need to research/explore extensively | Use subagent |
| Complex debugging session | Document findings, clear, resume |

## Context Budget Guidelines

Think of context as a budget:

| Activity | Context Cost |
|----------|--------------|
| Reading a file | Medium |
| Searching codebase | High |
| Writing code | Low |
| Running tests | Low |
| Research/exploration | Very High |

**Strategy:** Do high-cost activities (research) via subagents. Keep main context for low-cost activities (writing, testing).

## Signs of Context Degradation

Watch for these symptoms:

1. **Repetition** — Agent suggests something it already tried
2. **Contradiction** — Agent uses patterns it explicitly rejected earlier
3. **Forgetting** — Agent asks questions already answered
4. **Slowdown** — Responses take longer, feel more generic
5. **Regression** — Code quality drops compared to session start

## The STATE.md Pattern

Use `STATE.md` as your persistent memory across context clears:

```markdown
# Project State

## Current Focus
What we're working on right now

## Recent Decisions
- 2026-02-03: Chose regex over ML for GSTIN (deterministic, faster)
- 2026-02-02: Using spaCy en_core_web_lg for NER

## Blocked Items
Things waiting on external input

## Session Log
Brief notes from each session

### 2026-02-03
- Added GSTIN detection
- Fixed false positives in DATE_TIME
- Next: Address detection improvements
```

## Quick Commands

```bash
# Start fresh conversation
/clear

# Compact context (summarize)
/compact

# Check context usage
/cost
```

## Summary

```
RULE 1: Clear between unrelated tasks
RULE 2: Subagents for research/exploration
RULE 3: Document before clearing
RULE 4: One task per context for complex work
RULE 5: Watch for degradation signs
```

Context is your most valuable resource. Manage it like you'd manage a limited budget.
