# Planner Source Audit & Authority Limits

Reference for [phase-preparer](../../agents/phase-preparer.md) — extended rules for multi-source coverage audits and planner authority constraints.

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
3. **RESEARCH** — Technical approaches and discovered constraints in RESEARCH.md that affect the approved outcome. Research recommends and supplies evidence; it cannot add required product scope or defer an approved requirement.
4. **CONTEXT** — Every D-XX decision from CONTEXT.md `<decisions>` section.

### What is NOT a Gap

Do not flag these as MISSING:
- Items in `## Deferred Ideas` in CONTEXT.md — developer chose to defer these
- Items scoped to a different phase via `phase_req_ids` — not assigned to this phase
- Research suggestions outside approved scope, after checking the actual phase decisions; a researcher's label alone cannot defer required acceptance

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

   Continue corrections already authorized. Request a decision only when scope or a missing human choice blocks dependent planning.
```

If every required row is COVERED and each non-required suggestion has a recorded disposition → return `## PLANNING COMPLETE` as normal.

---

## Authority Limits — Constraint Examples

The planner's only legitimate reasons to split or flag a feature are **constraints**, not judgments about difficulty:

**Valid (constraints):**
- ✓ "Account creation and invoice export are separate component outcomes — assign each its own PLAN and preserve both acceptance mappings"
- ✓ "No API key or endpoint is defined in any source artifact — need developer input"
- ✓ "This feature depends on the auth system built in Phase 03, which is not yet complete"

**Invalid (difficulty judgments):**
- ✗ "This is complex and would be difficult to implement correctly"
- ✗ "Integrating with an external service could take a long time"
- ✗ "This is a challenging feature that might be better left to a future phase"

Apply phase-preparer `estimate_scope` for component splits. Missing information
and unmet dependencies must identify the blocked task and required fact or
artifact. File counts and advisory token estimates alone do not require a split.
Every required feature retains a plan or an explicit unresolved coverage gap;
difficulty never authorizes its removal.
