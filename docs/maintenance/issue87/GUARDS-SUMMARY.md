---
phase: issue87-maintenance
plan: guards
status: in_progress
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 14e8bd97481524c306d853ebb21249b6da57f60f
---

# Guard implementation

Assigned branch: `phase-issue87-guards`; approved source base `77b5668`.
Only GUARDS-PLAN is being implemented. Cleanup and publication remain coordinator owned.

## TDD Evidence

RED command: `python -m unittest discover -s tests -p test_destructive_guard.py -v`.
Python 3.13.14 on Windows; exit 1, Ran 3 tests, 45 failing subtest assertions,
zero skips. Named `test_registered_pipeline_denies_primary_switch` expected
registered refusal for Codex exec_command/shell_command/shell and Claude Bash;
actual pipeline contained no matching handlers and allowed each command (`[]`).
The 41 attack assertions likewise observed allow; precision matrix passed.
No command under assessment was executed. An earlier discovery attempt imported
the installer TestCase into this module; it was interrupted and corrected and is
not counted as RED evidence.

GREEN: pending implementation.

## Threat Outcomes

GUARDS-PLAN I87-G-T1/T2: implementation pending; canonical threat issue readback
remains coordinator owned. I87-G-T3 belongs to dependent cleanup.

## Remaining

Implementation, focused checks and final commit IDs pending.
