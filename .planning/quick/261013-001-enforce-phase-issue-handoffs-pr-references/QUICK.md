---
title: Enforce phase issue handoffs, PR references and post-merge TODO reconciliation
status: complete
created: 2026-10-13 14:46:32
completed: '2026-10-13T16:12:34'
files:
- .ai/references/git-workflow.md
- .ai/runtime/README.md
- .ai/runtime/lib/delivery.py
- .ai/runtime/lib/phase_issues.py
- .ai/runtime/lib/phases.py
- .ai/runtime/lib/todo_issues.py
- .ai/runtime/lib/todos.py
- .ai/runtime/phase.py
- .ai/workflows/execute-phase.md
- .ai/workflows/ship.md
- .planning/quick/261013-001-enforce-phase-issue-handoffs-pr-references/261013-001-enforce-phase-issue-handoffs-pr-references-PLAN.md
- .planning/quick/261013-001-enforce-phase-issue-handoffs-pr-references/261013-001-enforce-phase-issue-handoffs-pr-references-PREPARER-SUMMARY.md
- .planning/quick/261013-001-enforce-phase-issue-handoffs-pr-references/261013-001-enforce-phase-issue-handoffs-pr-references-REPAIR-SUMMARY.md
- .planning/quick/261013-001-enforce-phase-issue-handoffs-pr-references/261013-001-enforce-phase-issue-handoffs-pr-references-SUMMARY.md
- .planning/quick/261013-001-enforce-phase-issue-handoffs-pr-references/QUICK.md
- tests/test_phase_issues.py
- tests/test_phase_runtime.py
- tests/test_session_delivery.py
- tests/test_workflow_links.py
---

# Quick: Enforce phase issue handoffs, PR references and post-merge TODO reconciliation

## Task

Enforce phase issue handoffs, PR references and post-merge TODO reconciliation

## Verification

Local verification passed 5/5 at 5f289549a50da5a447943cb0db342ceed2c8a121: integrated phase tests 38 passed with one explicit symlink skip; workflow checks 4 passed; code review clean and documentation 4 PASS. Earlier runtime162, TODO34 and delivery60 evidence retained; final callback completion6 passed. Required remote CI is pending final draft delivery; no merge authorized.

## Changes

Files touched, filled on completion.
