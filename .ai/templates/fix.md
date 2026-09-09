---
id: FIX-{{ nnn }}
title: {{ title }}
status: open
intake: null
plan: null
specs: []
approval: pending
---
# {{ title }}

## Confirmed defect

Expected and observed behavior; affected scope; reproduction or other confirming
evidence, revision and environment. Link original intake or research without
duplicating its evidence. State uncertainty about cause separately from confirmation.

## Repair scope and acceptance

Smallest proposed repair, exclusions, affected specs and observable acceptance.
Record exact execution and delivery authority when received. If a PLAN is linked,
it owns execution tasks and approval; reference it instead of copying its checklist.

- [ ] T01: Bounded repair and acceptance condition, unless owned by a linked PLAN.

## Validation and delivery

Agreed checks, actual commands/results and subject revision; use test-result.md for
evidence. Record review, user acceptance and authorized delivery references before done.
A failed, stale or unrun required check keeps the fix open.

## Remaining work and links

Remaining work, blocker/owner/resume condition if any, and related records.
When complete, state what closed the defect and link a successor for later recurrence.
