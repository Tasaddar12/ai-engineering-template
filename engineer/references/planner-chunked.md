# Chunked Mode Return Formats

Use when the coordinator assigns bounded outline or single-plan work. It is a dispatch strategy, not a mode that relaxes planning contracts or user authorization. Each assignment carries repository, branch, revision, exact owned outputs and required checks.

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

The coordinator assigns one bounded plan per worker. Actual groups follow `depends_on`, exact file/deletion overlap and shared `resources`; wave labels are advisory. Dispatch independent plans only within host capacity and confirmed ownership. Wait for all assigned workers before integrating or repairing their outputs.

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

After each return, the coordinator reads the produced contract, checks required fields and scope, commits the assigned artifacts and records their evidence. File existence alone is insufficient.

## Resume Behaviour

On resume, inspect the outline and each existing plan's content, metadata, assignment revision and disposition. A filename alone does not prove completion. Preserve complete unaffected plans; return missing or stale contracts for bounded correction. Never redispatch onto paths an existing worker may still own.
