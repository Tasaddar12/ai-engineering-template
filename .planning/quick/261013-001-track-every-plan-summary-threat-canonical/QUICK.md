---
title: Track every PLAN and SUMMARY threat with a canonical Git issue and PR/MR lifecycle
  links
status: complete
created: 2026-10-13 14:33:30
completed: '2026-10-13T17:26:08'
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
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-REVISION-SUMMARY.md
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-SUMMARY.md
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-VERIFICATION.md
- .planning/quick/261013-001-track-every-plan-summary-threat-canonical/QUICK.md
- tests/test_issue_format.py
- tests/test_threat_tracking_contract.py
---

# Quick: Track every PLAN and SUMMARY threat with a canonical Git issue and PR/MR lifecycle links

## Task

Track every PLAN and SUMMARY threat with a canonical Git issue and PR/MR lifecycle links

## Verification

Requested correction verified at ee2ccc3: original coder/preparer/checker threat blocks preserved against b475037; per-PLAN content and concise linked outcomes retained. Focused checks: 12 threat-contract, 17 issue-format and 3 workflow-link tests passed. Independent correction diff review clean, zero findings. Issues 81/82 read back OPEN/unresolved. Required final CI recorded in PR80; keep both PR80/84 unmerged.

## Changes

Files touched, filled on completion.
