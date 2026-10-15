---
phase: issue87-maintenance
plan: orchestration
subsystem: workflow
tags: [parallel-status, security-tracking, issue-audit]
issue_refs: []
requires: []
provides:
  - Coordinator-owned actual-wave status and bounded stall decisions
  - Per-risk planned checklist routing and standalone distinct unplanned tracking
  - Independent semantic/provider issue-link audit before merge eligibility
affects: [execution, planning, shipping]
actuals:
  tokens: 0
  tasks: 3
  commits: 3
plan_head_before: 54d0558b65e18da108586d438a31054397d5f527
tech-stack:
  added: []
  patterns: [single-owner instruction contracts]
key-files:
  created: [.ai/references/parallel-status.md, tests/test_parallel_status_contract.py]
  modified: [.ai/workflows/execute-phase.md, .ai/agents/coordinator.md, .ai/references/git-workflow.md, .ai/workflows/plan-phase.md, .ai/templates/issue.md, tests/test_threat_tracking_contract.py, .ai/agents/verifier.md, .ai/workflows/ship.md]
key-decisions: []
patterns-established: [bounded host observations preserve active worker ownership]
requirements-completed: [ISSUE87-6, ISSUE87-7]
acceptance: [ISSUE87-6, ISSUE87-7]
documentation: [.ai/references/parallel-status.md, .ai/references/git-workflow.md]
coverage:
  - id: D1
    description: Actual-wave assignment status and bounded stalled decisions
    requirement: ISSUE87-6
    verification:
      - kind: unit
        ref: python -m unittest discover -s tests -p test_parallel_status_contract.py -v
        status: pass
    human_judgment: false
  - id: D2
    description: Planned per-risk checklist identity and standalone distinct unplanned routing
    requirement: ISSUE87-7
    verification:
      - kind: unit
        ref: tests/test_threat_tracking_contract.py#test_planned_checklist_real_structure_and_each_field_mutation
        status: pass
      - kind: unit
        ref: tests/test_threat_tracking_contract.py#test_planned_unplanned_routing_duties_and_mutations
        status: pass
    human_judgment: false
  - id: D3
    description: Independent issue-link audit scope, evidence and currentness at actual workflow seams
    requirement: ISSUE87-7
    verification:
      - kind: unit
        ref: tests/test_threat_tracking_contract.py#test_independent_audit_duty_mutations
        status: pass
      - kind: unit
        ref: tests/test_threat_tracking_contract.py#test_each_actual_audit_step_and_verifier_hook_is_required
        status: pass
    human_judgment: false
duration: unavailable (wall-clock start was not captured)
completed: 2026-10-15
status: complete
---

# Phase issue87 Plan orchestration: Status, tracking and audit Summary

**Actual-wave status preserves worker ownership; per-risk security checklists and an independent issue-link audit preserve tracking and closure evidence.**

## Performance

- Started: 2026-10-15, assigned base 54d0558b65e18da108586d438a31054397d5f527.
- Tasks: 3/3, locally implemented and checked; coordinator integration/review remains pending.
- Files: ten implementation paths, assigned PLAN reconciliation and this required summary.
- Actuals tokens: Pending final chars/4 measurement over assigned-base diff; zero above is provisional, not a measured claim.

## Accomplishments

- Added per-wave assignment columns, honest unavailable states, progress evidence and lifecycle refresh seams.
- Required a recorded decision after two bounded waits without progress/state change; preserved join, handoff, continuation and termination safeguards.
- Added focused structure and mutation regressions for real workflow steps and the canonical status reference.
- Added individually addressable planned checklist entries, reuse of existing canonical issues and standalone tracking for distinct unplanned risks; retained per-PLAN registers, safe disclosure and evidence/closure duties.
- Added independent audit scope, evidence packet and freshness rules with actual reviewer/verifier and ship seams. Missing links/readback and stale evidence cannot establish merge eligibility.

## Task Commits

1. Task 1: bounded wave reporting - `cfc5255`.
2. Task 2: planned security tracking - `55f4c81`.
3. Task 3: independent issue-link audit - current implementation slice; hash returned from Git.

## Checks

- Tested tree: assigned base 54d0558b65e18da108586d438a31054397d5f527 plus Task 1 owned working diff.
- `python -m unittest discover -s tests -p test_parallel_status_contract.py -v`: Ran 5 tests, OK.
- Task 2 tree: `cfc5255` plus owned working diff.
- `python -m unittest discover -s tests -p test_threat_tracking_contract.py -v`: Ran 16 tests, OK. Initial added template-region extractor failed once; corrected its fence/heading handling and reran successfully.
- `python -m unittest discover -s tests -p test_phase_issues.py -v`: Ran 38 tests, OK (one skipped: Windows symlink creation privilege unavailable).
- `python -m unittest discover -s tests -p test_workflow_links.py -v`: Ran 4 tests, OK.
- Python 3.13.14 at `C:\Users\killi\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe`; PyYAML 6.0.3.
- No zero-test run accepted.

Task 3 source tree is `55f4c81` plus the exact owned audit/lifecycle diff committed
in the next task slice. Focused threat tracking: Ran 20 tests, OK. Final status
suite: Ran 5 tests, OK. Final workflow links: Ran 4 tests, OK. Phase issue rerun:
Ran 38 tests, OK (one skipped for Windows symlink privilege). Immutable
source-revision evidence will be recorded before final handoff.
`git diff --check` produced no whitespace errors.

## Files Created/Modified

- `.ai/references/parallel-status.md`: table, observations, bounded decisions and dispatch-to-join example.
- `tests/test_parallel_status_contract.py`: real-step structure and mutation checks.
- `.ai/workflows/execute-phase.md`: grouping/dispatch/join/integration/check hooks.
- `.ai/agents/coordinator.md`: execution owner link.
- `.ai/references/git-workflow.md`: planned checklist and distinct unplanned canonical routing.
- `.ai/workflows/plan-phase.md`: mandatory preparer-return routing choice.
- `.ai/templates/issue.md`: checklist guidance in existing Security risk variant; headings preserved.
- `tests/test_threat_tracking_contract.py`: per-entry columns, routing seams and mutation checks.
- `docs/maintenance/issue87/ORCHESTRATION-PLAN.md`: coordinator-authorized issue-template ownership reconciliation.
- `.ai/agents/verifier.md`: mandatory independent provider/link audit and gap reporting.
- `.ai/workflows/ship.md`: audit preflight/body/readback/currentness and merge gate.

## Decisions Made

None - followed the approved plan within assigned ownership.

## Deviations from Plan

The coordinator corrected the nonexistent compatibility suite name to `test_phase_issues.py` before dispatch. During execution, the coordinator explicitly added `.ai/templates/issue.md` and narrow PLAN ownership reconciliation; added existing-variant instructions without a new runtime variant. TEMPLATE-CONTRACT remains the planning worker's responsibility.

## Issues Encountered

`rg` is unavailable; native PowerShell reads/searches used. Installed Python and Git require approved elevated execution because WindowsApps sandbox access is blocked; no installation or hook change performed.

## User Setup Required

None.

## Threat Outcomes

None identified as a new product exploit. Inspected documentation/contract-test scope follows the PLAN boundaries: worker lifecycle, safe provider tracking and review/closure authority. No product endpoints, authentication, credentials, persistence schemas or provider adapters changed.

## Remaining / Deferred

- Coordinator owns final integration and independent review, TEMPLATE-CONTRACT risk-routing reconciliation after planning ownership ends, code-reviewer cross-reference and draft publication. The contract edit is intentionally not included until explicit sequential ownership handoff.
- Offline contracts check instruction structure and mutations, not provider behavior or a live PR audit. Actual PR89/readback audit remains independent coordinator work; no live issue was created, changed or closed here.
- One Windows symlink regression is skipped for missing host privilege; all other targeted checks execute. Full wall-clock duration is unavailable because start time was not captured.

## Next Phase Readiness

All three owned tasks are locally implemented. No phase completion, publication readiness or merge is claimed before integration and independent review.

## Coordinator Reconciliation

| Operation | Worker evidence / proposed reconciliation |
|---|---|
| Position/progress | Three owned tasks complete locally; integrate and independently verify before phase completion |
| Metrics | Final duration, diff chars/4 and commit count pending final summary |
| Decisions | None beyond approved plan |
| Session | Integrate owned commits, reconcile shared contract and code-reviewer link, obtain fresh review/audit |
| Roadmap/requirements | Keep shared adoption skeleton unchanged; no runtime mutations assigned |
| Blockers | No implementation blocker; independent integrated verification remains coordinator-owned |

## Self-Check: PASSED

Created reference/test and owned source paths exist. Focused suites and mutation checks pass, with the explicit host symlink skip. Exact task commit identities and final tested revision are reconciled at final metadata commit; no unrun provider audit is claimed.
