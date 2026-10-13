---
maintenance: entrypoint-git-routing
plan: "01"
subsystem: instructions
tags: [git-routing, entrypoints, installer, codex, claude]
requires: []
provides:
  - Mandatory shared Git routing for all issue and PR/MR writes
  - Real fresh-install regression coverage for both hosts
affects: [agent-entrypoints, delivery]
actuals:
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [shared-reference routing, real installer fixtures]
key-files:
  created:
    - tests/test_entrypoint_git_routing.py
    - .ai/maintenance/entrypoint-git-routing-SUMMARY.md
  modified:
    - AGENTS.md
    - .ai/install-assets/agent-entry.txt
key-decisions: []
patterns-established: []
requirements-completed: [entrypoint-git-routing]
acceptance: [ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04]
documentation: [AGENTS.md, .ai/install-assets/agent-entry.txt]
coverage:
  - id: D1
    description: Both source entrypoints mandate the shared Git reference for every issue and PR/MR creation or edit across providers, including templates and validation.
    requirement: entrypoint-git-routing
    verification:
      - kind: unit
        ref: tests/test_entrypoint_git_routing.py#test_source_entrypoints_require_complete_routing
        status: pass
    human_judgment: false
  - id: D2
    description: Fresh Codex and Claude installs retain the mandate and resolve their installed Git-reference and template links while preserving template contents after host mapping.
    requirement: entrypoint-git-routing
    verification:
      - kind: integration
        ref: tests/test_entrypoint_git_routing.py#test_fresh_codex_install_routes_to_installed_policy_and_templates
        status: pass
      - kind: integration
        ref: tests/test_entrypoint_git_routing.py#test_fresh_claude_install_routes_to_installed_policy_and_templates
        status: pass
    human_judgment: false
duration: 3min
completed: 2026-10-13
status: complete
plan_head_before: 6de80aa15b87b6b8f1a6245759eebcf9091d9e27
branch: codex/entrypoint-git-routing-worker
---

# Maintenance Plan 01: Entrypoint Git Routing Summary

**Both agent entrypoints require every issue and PR/MR creation or edit to follow the canonical Git reference, including its templates and validation requirements, regardless of provider.**

## Performance

- Implementation and checks started: 2026-10-13T15:47:12Z.
- Duration: approximately 3 minutes, excluding initial required source reading.
- Tasks: 1 completed; files: 4 owned paths.
- Context usage: unavailable. No token estimate was assigned.

## Accomplishments

- Replaced the source Delivery reference with one mandatory routing sentence and added the equivalent sentence to the installer entry asset.
- Kept the canonical Git reference as the detailed policy owner; no template sections, commands or provider rules were duplicated in either entrypoint.
- Added three focused tests: source contract, fresh Codex install and fresh Claude install. Real installations use a committed temporary Git source copied from the actual repository, reusing the existing installer fixture without inheriting its test suite.
- Verified host-specific reference/template navigation and full installed template contents after host mapping. Confirmed the source root has no CLAUDE.md.

## Task Commits

Task 1 and this SUMMARY form one exact-path implementation commit. Its immutable SHA is returned in the worker completion result; a commit cannot embed its own hash. Locate it from this record with `git log -1 --format=%H -- .ai/maintenance/entrypoint-git-routing-SUMMARY.md`.

## Checks

Tested input: `6de80aa15b87b6b8f1a6245759eebcf9091d9e27` plus the owned working-tree implementation changes. The final focused rerun includes installed-template content assertions; the SUMMARY was added afterward. The coordinator owns committed-candidate checks and independent review.

Python argv for each command below resolves to `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`.

| Exact command from repository root | Observed result |
|---|---|
| `python -m unittest discover -s tests -p test_entrypoint_git_routing.py -v` | 3 passed in 14.312s on the final focused rerun; both hosts installed successfully. Initial focused run also passed 3 in 14.391s. |
| `python -m unittest discover -s tests -p test_issue_format.py -v` | 13 passed in 2.009s. |
| `python -m unittest discover -s tests -p test_session_delivery.py -v` | 59 passed in 138.793s, including all 9 OpeningPullRequests cases. |
| `python -m unittest discover -s tests -p test_workflow_links.py -v` | 3 passed in 1.570s. |
| `git diff --check` | Passed; no whitespace errors. |
| `git diff --exit-code 6de80aa15b87b6b8f1a6245759eebcf9091d9e27 -- .ai/references/git-workflow.md .ai/templates/issue.md .ai/templates/pull-request.md .ai/install.py .ai/runtime tests/test_issue_format.py tests/test_session_delivery.py tests/test_workflow_links.py .planning` | Passed; policy, templates, installer/runtime, existing regressions and adopting-project skeleton unchanged. |

All four unittest commands exited 0 with no failures or skips. Root, branch and input revision matched the assignment before writes. Source/installed tests allow harmless line wrapping by normalizing whitespace.

## Files Created/Modified

- `AGENTS.md` - existing Delivery reference now requires all issue and PR/MR writes to follow shared policy.
- `.ai/install-assets/agent-entry.txt` - equivalent mandatory routing for both host entrypoints.
- `tests/test_entrypoint_git_routing.py` - source checks plus real fresh installations, resolving links and preserved template contents.
- `.ai/maintenance/entrypoint-git-routing-SUMMARY.md` - scope, evidence and coordinator handoff.

## Decisions Made

None - followed the assigned maintenance plan and its locked boundaries.

## Deviations from Plan

None. The coordinator clarified that installed template contents should be compared after host mapping; this strengthened planned preservation coverage without changing scope.

## Issues Encountered

The default Python alias and repository virtualenv were known broken. Used the coordinator-supplied working executable with sandbox escalation. `rg` was unavailable; bounded PowerShell reads and Select-String provided required source inspection. No checks failed and no credentials, servers or packages changed.

## User Setup Required

None - no external service configuration required.

## Remaining / Deferred

No implementation gaps, stubs, skipped checks or deferred defects. Coordinator integration, fresh independent review, committed-candidate checks and publication remain coordinator-owned. No worker push or publication occurred; tracking issue #75 and draft PR #78 remain coordinator-owned.

## Next Phase Readiness / Coordinator Reconciliation

- Advance position / progress / roadmap: one standalone maintenance task completed; no adopting-project phase or planning-record mutation is proposed.
- Metrics: 1 task, 4 owned paths, 1 atomic implementation-and-summary commit from the recorded base; approximately 3 minutes of implementation/check work.
- Decisions / requirements: no new decisions; maintenance requirement `entrypoint-git-routing` and ROUTE-01 through ROUTE-04 have author evidence. Independent acceptance remains coordinator-owned.
- Session continuity: last completed action is the exact-owned slice commit; integrate it, run candidate checks and assign independent review.
- Blockers: none.

## Self-Check: PASSED

The assigned implementation paths and SUMMARY exist. Required checks passed; declared immutable paths have no delta. The commit hash, exact changed-path list and deletion/clean-tree checks are verified and returned after committing this record.
