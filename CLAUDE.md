# Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
```

**Core principle:** Local files are just for processing. Anything I need to see or use lives in cloud services. Everything in `.tmp/` is disposable.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.

---

## The Agentic Bible — Discipline Layer

The WAT framework handles *what* to do. The Bible handles *how* to do it right.

### The Three Laws

1. **AI reasons. Code executes.** Use deterministic tools (tests, linters, CLIs) for execution. Never do manually what a tool can do reliably.
2. **Evidence before assertions.** Never claim something works without proof. Run the test. Check the output. "It should work" is not acceptable.
3. **Simplicity over cleverness.** Minimum complexity for the current task. Don't engineer for hypothetical futures.

### The Workflow

```
DISCOVER → PLAN → EXECUTE → VERIFY → SHIP
```

For trivial changes (<20 lines, obvious fix): Quick Mode — understand, change, verify, commit.

### Verification Protocol

Before marking ANY task complete, verify all three levels:

| Level | Question | Check |
|-------|----------|-------|
| Exists | Did I create the file/feature? | File exists |
| Substantive | Is it real code, not stubs? | No TODO/FIXME/HACK |
| Wired | Is it connected to the system? | Something imports/calls it |

**Verification checklist:**
```bash
# Run before claiming "done"
pytest tests/ -v                    # All tests pass
grep -r "TODO\|FIXME\|HACK" tools/  # No placeholders
```

### Commit Standards

Use conventional commits. One logical change per commit.

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `refactor:` | Code restructuring |
| `test:` | Adding/updating tests |
| `docs:` | Documentation |
| `chore:` | Config, dependencies |

**Format:** `type: short description of what and why`

Examples:
```
feat: add GSTIN detection for Indian tax IDs
fix: reduce false positives in DATE_TIME regex
test: add adversarial cases for address detection
```

### Context Management

Context degrades over long sessions. Manage it:

1. **Clear between unrelated tasks** — Don't let old context pollute new work
2. **Use subagents for investigation** — Research in isolated context, report back summary
3. **Document progress in STATE.md** — Write findings, clear context, resume fresh
4. **Fresh context for execution** — Each task benefits from clean context

**Signs of degraded context:**
- Repeating earlier decisions
- Forgetting previous instructions
- Quality drops compared to session start
- Introducing contradictory patterns

**Fix:** Clear and restart with focused prompt + written summary.

### AI Discipline Checklist

Before writing code, verify:
- [ ] I've READ the files I'm about to modify
- [ ] I'm NOT hallucinating APIs/libraries (checked docs)
- [ ] I'm NOT over-engineering (solving only what's asked)
- [ ] I'm NOT leaving dead code (no unused imports/files)
- [ ] I'm NOT adding unnecessary dependencies

### Quick Reference

```
WORKFLOW:    Discover → Plan → Execute → Verify → Ship
COMMITS:     feat: | fix: | refactor: | test: | docs: | chore:
VERIFY:      Exists? → Substantive? → Wired? → Tests pass?
CONTEXT:     Clear between tasks. Subagents for research. Document progress.
```
