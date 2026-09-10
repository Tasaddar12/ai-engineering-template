---
tier: plan
authority: agent
id: FIX-001
title: Closed findings from abandoned tracks return to the deferred queue
found: 2026-09-10
found_by: final cold review of PR 11
severity: major
violates: none
links: []
deferred_until: all-other-plans-complete
---

# FIX-001: Closed findings from abandoned tracks return to the deferred queue

## Symptom

A blocked worker produces a code FIX, its track is abandoned, and a later
correction carries that FIX into `.ai/fixes/done/` with proof. The next
deferred queue still includes the abandoned track's stale copy and can audit
its preserved old source even though the current FIX is closed.

## Root cause

`Runner.followup_queue()` in `.ai/runtime/orchestrate.py` checks whether a
report remains open only for `merged` receipts. Abandoned receipts always
append their saved finding. Closure must be recognized by record ID across
receipts, while unclosed abandoned findings remain actionable.

## The change

Deferred at the second review under the autonomous review limit. Handle this
code-only correction after the other PLAN work and live pilot finish.

## Proof

The final cold reviewer reproduced the defect in an isolated Git repository:

```text
closed record exists: True
open target record exists: False
queued FIX IDs: ['FIX-001']
```

Add a regression covering both closed and still-open findings from abandoned
tracks before closing this FIX.

## Contract

The record's directory owns its lifecycle stage, as established by
`.ai/truth-map.md`. The existing runtime regression
`test_closed_reports_are_not_resurrected_from_receipts` establishes that a
closed report must not be restored from a receipt; extend that guarantee to
abandoned origins. No documentation or contract change is needed.

- Related documentation/contract INTAKE: none
