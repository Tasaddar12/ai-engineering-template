---
title: Track every PLAN and SUMMARY threat with a canonical Git issue and PR/MR lifecycle
  links
status: complete
created: 2026-10-13 14:33:30
completed: '2026-10-13T15:23:34'
files:
- .ai/agents/coder.md
- .ai/agents/phase-checker.md
- .ai/agents/phase-preparer.md
- .ai/agents/verifier.md
- .ai/references/git-workflow.md
- .ai/runtime/TEMPLATE-CONTRACT.md
- .ai/templates/issue.md
- .ai/templates/phase-prompt.md
- .ai/templates/pull-request.md
- .ai/templates/summary.md
- .ai/workflows/execute-phase.md
- .ai/workflows/plan-phase.md
- .ai/workflows/quick.md
- .ai/workflows/ship.md
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-PLAN.md
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-SUMMARY.md
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/QUICK.md
- tests/test_issue_format.py
- tests/test_threat_tracking_contract.py
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-VERIFICATION.md
---

# Quick: Track every PLAN and SUMMARY threat with a canonical Git issue and PR/MR lifecycle links

## Task

Track every PLAN and SUMMARY threat with a canonical Git issue and PR/MR lifecycle links

## Verification

Source acceptance QT-01 through QT-06 passed at 9dc8840; independent code review clean and all 14 documentation paths PASS. Local checks passed: 17 issue-format, 11 threat-contract, 3 workflow-link and 3 entrypoint tests; TODO: 33 passed, 1 Windows symlink skip. Canonical issues 81/82 read back OPEN/unresolved with neutral PR80 links. Required final CI checked separately; keep draft unmerged.

## Changes

Files touched, filled on completion.
