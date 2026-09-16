# Chunked Mode Return Formats

Use when the coordinator explicitly assigns bounded outline-only or single-plan
preparation. This method keeps worker context focused; it does not install
chunking flags or automatic dispatch settings. Only the coordinator starts workers.

## Modes

### outline-only

Write **only** `{PHASE_DIR}/{PADDED_PHASE}-PLAN-OUTLINE.md`. Do not write any PLAN.md files.
Return:

```markdown
## OUTLINE COMPLETE

**Phase:** {phase-name}
**Plans:** {N} plan(s) in {M} wave(s)

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|-----------|-------------|
| {padded_phase}-01 | [brief objective] | 1 | none | REQ-001, REQ-002 |
| {padded_phase}-02 | [brief objective] | 1 | none | REQ-003 |
```

The coordinator reviews the outline and assigns one bounded plan per worker when
useful. Dependencies, ownership and available capacity govern assignment order;
wave numbers are a descriptive view, not a global barrier.

### single-plan

Write **exactly one** `{PHASE_DIR}/{plan_id}-PLAN.md`. Do not write any other plan files.
Return:

```markdown
## PLAN COMPLETE

**Plan:** {plan-id}
**Objective:** {brief}
**File:** {PHASE_DIR}/{plan-id}-PLAN.md
**Tasks:** {N}
```

The worker commits its assigned plan and SUMMARY. The coordinator checks the
actual content, integrates the commit and continues with ready assignments.

## Resume Behaviour

If the orchestrator detects that `PLAN-OUTLINE.md` already exists (from a prior interrupted
run), it inspects the outline and existing plans against the current inputs and revision.
Existing files alone do not establish completion; assign remaining or stale work.
