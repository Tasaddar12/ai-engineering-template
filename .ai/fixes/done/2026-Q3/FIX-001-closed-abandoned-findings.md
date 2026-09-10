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

Index current open reports and completed record IDs before importing receipt
findings. FIX records in `done/` and promoted/abandoned INTAKE records suppress
stale receipt copies regardless of their originating track's status. Resolve
current open reports by ID, including renamed files, and preserve saved reports
and source worktrees for unclosed abandoned findings without a current report.

## Proof

The final cold reviewer reproduced the defect in an isolated Git repository:

```text
closed record exists: True
open target record exists: False
queued FIX IDs: ['FIX-001']
```

The post-PLAN correction added two real-Git regressions in
`tests/test_runtime_recovery.py`:

- `test_closed_abandoned_reports_are_not_resurrected_from_receipts` closes
  records under new filenames and checks both the abandoned originating run
  and a later run importing its saved receipt.
- `test_abandoned_findings_use_current_open_reports` checks preservation of
  unclosed abandoned findings and selection of a renamed current report while
  retaining the abandoned worktree and receipt evidence.

Before the source change at base `1f3f6d6cbb4a98c95809e5328648da8007ed01ca`,
`python -m unittest discover -s tests -p test_runtime_recovery.py -k abandoned -v`
failed in both runs for both tests:

```text
AssertionError: Lists differ: ['FIX-001'] != []
Ran 2 tests in 20.904s
FAILED (failures=4)
```

The other failed assertion selected the receipt's
`.git/orchestration/ORCH-001/deferred/a/.ai/fixes/open/FIX-001-review.md`
instead of the current `.ai/fixes/open/FIX-001-current-evidence.md`.

After the source change, the same command returned:

```text
Ran 2 tests in 20.724s
OK
```

The full recovery module,
`python -m unittest discover -s tests -p test_runtime_recovery.py -v`, returned:

```text
Ran 20 tests in 158.321s
OK (skipped=1)
```

The existing directory-symlink check was skipped because this Windows host
cannot create directory symlinks. The regression and all other recovery checks
passed. Commands used the bundled Python executable. The template's
`verification.commands` is empty; the coordinator runs the repository-wide
suite before delivery. `git diff --check` also passed.

## Contract

The record's directory owns its lifecycle stage, as established by
`.ai/truth-map.md`. The existing runtime regression
`test_closed_reports_are_not_resurrected_from_receipts` establishes that a
closed report must not be restored from a receipt; extend that guarantee to
abandoned origins. No documentation or contract change is needed.

- Related documentation/contract INTAKE: none
