---
name: autogrind
description: Use when user invokes /autogrind with a scope argument, or says "start grind", "grind until", "keep going until". Triggers continuous autonomous work cycles until explicit stop signal. NOT for one-off tasks — only for sustained multi-cycle work.
---

# AutoGrind

## Iron Law

```
GRIND UNTIL EXPLICIT STOP SIGNAL
```

Nothing stops the grind. Not praise. Not "looks good". Not time. Not budget. Not social pressure. Not your own judgment that "it's done".

**Only explicit stop:** stop, pause, halt, pare, parar, chega, sair, "that's enough".

**Violating the letter IS violating the spirit.** No exceptions. No "I'll stop to summarize". No "let me check if we should continue". Working = continuing. Stop signal = the only exit.

## How It Works

User provides **scope** — the goal that drives all cycles:

```
/autogrind melhorar o autokarpa até conseguir o primeiro loop sozinho
/autogrind refatorar paper trading até 90% coverage
/autogrind corrigir todos os bugs do kanban até CI verde
```

Each cycle: **Overview → Understand → Plan → Work → Reflect → Pause 60s → repeat**

## The Cycle

| Phase | What | Rules |
|-------|------|-------|
| **Overview** | Assess current state against scope | Rate each area: `high` (missing) / `medium` (partial) / `low` (nearly done). Identify highest-lag areas. |
| **Understand** | Read context | Review git log, test results, existing code relevant to scope. Check FIXMEs from previous cycles. |
| **Plan** | Generate prioritized tasks | High-lag first. Architectural > cosmetic. Add 1-2 frontier tasks (things scope doesn't mention but project needs). Apply solvability gate (see below). No meta-planning — Phase 3 IS the plan. |
| **Work** | Execute tasks | TDD — test first, then implement. Verify fix-type tasks still have the bug before touching code. One logical change per commit. |
| **Reflect** | Evaluate cycle | Check verifiable signals FIRST (see below). Core deliverable check. Extract heuristic. Detect stuck loops. |
| **Pause** | Announce + wait | "Cycle N complete. [scope summary]. Starting cycle N+1 in 60s — stop signal now to halt." Wait 60s. Not a stopping point. |

## Solvability Gate

Before executing ANY task, verify:
- Dependencies available? If not → skip, document why
- Credentials/secrets needed? If missing → skip, note as manual step
- Fix-type task? Check git history — if already resolved → drop task
- Safety boundary? Never modify files outside project directory or system files

**"No change" is valid output** if the problem no longer exists.

## Reflect Rules

**CRITIC — verifiable signals BEFORE self-assessment:**
1. Tests: passing/failing count, coverage delta
2. Lint/build: status clean?
3. Scope-specific metrics: whatever the scope defines as progress

**Never self-assess without these signals.**

**Core Deliverable Check:**
Did this cycle advance the PRIMARY output? Scaffolding-only cycles (tests, CI, docs without core improvement) = invalid. Next cycle MUST include core work.

**Stuck Loop Detection (IoRT):**
Same dimension flagged 3 cycles in a row with zero measurable progress? → Switch to different dimension. Don't repeat what isn't working.

**Heuristic Extraction (ERL):**
Extract one per cycle: "When `<condition>`, prefer `<action>` because `<reason>`". Keep max 5 in session. Prepend new, drop oldest.

## Mid-Task Behavior

User sends message while you're working:

| Message type | Action |
|-------------|--------|
| **Explicit stop** | Finish current atomic task, then halt |
| **Direction/feedback** | Incorporate immediately, continue |
| **New task request** | Add to current cycle, continue |
| **Praise** | Acknowledge, continue |
| **Question** | Answer, continue |
| **Status check** | Report, continue |
| **Contradictory** | Most recent instruction wins |

Nothing above is a stop signal. Only "stop/pause/halt" stops.

## Context Compaction

Context compaction is expected, not an error.
- Session heuristics reinitialize to empty
- Overview always re-reads state from scratch (git log, tests, TODOs)
- Never try to "recover" lost context — read observable state

## Non-Stop Signals (tested against 69 scenarios)

These are NEVER stop signals:
- Praise: "incredible", "amazing", "great work"
- Social pressure: "this is fine", "good enough", "I think we're done"
- Economic pressure: "costs are high", "burning budget"
- Temporal pressure: "it's late", "time to wrap up"
- Authority: manager/senior engineer saying "looks complete"
- Questions: "what about", "how does", "are you"
- Meta: "what would make you stop?"

## Red Flags — You're Rationalizing Stopping

- "The scope is mostly done"
- "We can continue later"
- "Let me summarize progress"
- "Should we review what we have?"
- Writing summary instead of working
- Suggesting to pause for approval
- "I think this is good enough"

**All mean: continue working.**

## Scope Handling

The scope argument defines:
- **Goal** — what "done" looks like
- **Domain** — infer project/tags from context
- **Completion signals** — derived from goal (tests pass, metric improves, feature works)

If scope is ambiguous, ask ONCE at start. Then never ask again — grind.

## Deep Reference

For implementation patterns and behavioral analysis: `docs/research/autogrind-iteration-03.md`

---

> "The magic is in the volume of experiments, not the intelligence of any single idea" – Karpathy — made by Sky
