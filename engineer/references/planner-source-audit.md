# Planner Source Audit & Authority Limits

Reference for `agents/planner.md` — extended rules for multi-source coverage audits and planner authority constraints.

## Multi-Source Coverage Audit Format

Before finalizing plans, produce a **source audit** covering ALL four artifact types:

```
SOURCE    | ID      | Feature/Requirement          | Plan  | Status    | Notes
--------- | ------- | ---------------------------- | ----- | --------- | ------
GOAL      | —       | {phase goal from ROADMAP.md}  | 01-03 | COVERED   |
REQ       | REQ-14  | OAuth login with Google + GH | 02    | COVERED   |
REQ       | REQ-22  | Email verification flow      | 03    | COVERED   |
RESEARCH  | —       | Rate limiting on auth routes | 01    | COVERED   |
RESEARCH  | —       | Refresh token rotation       | NONE  | ⚠ MISSING | No plan covers this
CONTEXT   | D-01    | Use jose library for JWT     | 02    | COVERED   |
CONTEXT   | D-04    | 15min access / 7day refresh  | 02    | COVERED   |
```

### Four Source Types

1. **GOAL** — The `goal:` field from ROADMAP.md for this phase. The primary success condition.
2. **REQ** — Every REQ-ID in `phase_req_ids`. Cross-reference REQUIREMENTS.md for descriptions.
3. **RESEARCH** — Recommendations and current-source evidence relevant to approved scope. Research cannot add or defer an obligation; return a consequential conflict to the coordinator.
4. **CONTEXT** — Every D-XX decision from CONTEXT.md `<decisions>` section.

### What is NOT a Gap

Do not flag these as MISSING:
- Items in `## Deferred Ideas` in CONTEXT.md — developer chose to defer these
- Items scoped to a different phase via `phase_req_ids` — not assigned to this phase
Confirm findings against current source and approved scope; research recommendations do not override a user decision.

### Handling MISSING Items

If ANY row is `⚠ MISSING`, do NOT finalize the plan set silently. Return to the orchestrator:

```
## ⚠ Source Audit: Unplanned Items Found

The following items from source artifacts have no corresponding plan:

1. **{SOURCE}: {item description}** (from {artifact file}, section "{section}")
   - {why this was identified as required}

   Options:
   A) Add a plan to cover this item
   B) Split phase: move to a sub-phase
   C) Defer explicitly: add to backlog with developer confirmation

Use outcome and dependency evidence rather than an arbitrary context percentage to propose a split.
```

Research cannot add or defer scope. Report the exact conflict and evidence to the coordinator.

---

## Authority Limits — Constraint Examples

The planner's only legitimate reasons to split or flag a feature are **constraints**, not judgments about difficulty:

**Valid (constraints):**
Preserve authorized corrections already in progress; only dependent missing decisions block work.
- ✓ "No API key or endpoint is defined in any source artifact — need developer input"
- ✓ "This feature depends on the auth system built in Phase 03, which is not yet complete"

**Invalid (difficulty judgments):**
- ✗ "This is complex and would be difficult to implement correctly"
- ✗ "Integrating with an external service could take a long time"
- ✗ "This is a challenging feature that might be better left to a future phase"

Split only at coherent outcomes or actual dependencies after coordinator review. `estimate_scope` and context estimates inform a proposal; they do not authorize adding, dropping or deferring approved scope.
