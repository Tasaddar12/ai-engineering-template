---
phase: issue87-maintenance
plan: guards-preparer
subsystem: planning
tags: [guards, cleanup, git, github, gitlab, maintenance]
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
requires: []
provides:
  - Executable guard plan and genuinely dependent cleanup child plan
affects: [issue87-guards, issue87-cleanup, planning-integrity]
actuals:
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [bounded command parsing, evidence-based refusal, pinned cleanup approval]
key-files:
  created:
    - docs/maintenance/issue87/GUARDS-PLAN.md
    - docs/maintenance/issue87/CLEANUP-PLAN.md
    - docs/maintenance/issue87/GUARDS-PREPARER-SUMMARY.md
  modified: []
key-decisions:
  - Guard first; coordinator creates cleanup child from returned guard implementation tip.
  - Standalone Python hook entrypoint owns cleanup-preview/cleanup-apply; no phase.py or worktrees.py edits.
  - Unknown provider evidence preserves work; closed-unmerged unique commits remain preserved.
  - Approval envelope records a real exact-list human instruction but does not prove human provenance cryptographically.
patterns-established: []
requirements-completed: []
acceptance: []
documentation:
  - docs/maintenance/issue87/GUARDS-PLAN.md
  - docs/maintenance/issue87/CLEANUP-PLAN.md
coverage:
  - id: guards-plan
    description: Guard implementation assignment with bounded parser attack matrix and intentional RED-first registration test
    verification:
      - kind: other
        ref: Python YAML/section/task structural validation
        status: pass
    human_judgment: false
  - id: cleanup-plan
    description: Dependent cleanup assignment with exact state/list approval and final-state reporting
    verification:
      - kind: other
        ref: Python YAML/section/task/dependency structural validation
        status: pass
    human_judgment: false
completed: 2026-10-15
status: complete
---

# Issue87 guard and cleanup preparation

**Prepared separate guard and cleanup implementation plans with explicit source ownership, provider refusal behavior and exact deletion approval.**

## Performance

- Tasks: two plan artifacts and this handoff.
- Files created: three maintenance documents.
- No implementation, publication, adoption record or real cleanup operation performed.

## Accomplishments

- GUARDS-PLAN defines a separate blocking Python hook, installed-host registration, read-only provider evidence, primary-checkout switching refusal, legitimate path restore allowance and bounded shell grammar. PR86's advisory worktree guard remains unchanged.
- CLEANUP-PLAN depends on the actual guard implementation commit, extending the shared library/test paths sequentially. Preview preserves unknown/open/dirty/unowned and closed-unmerged unique work; apply requires exact approved list/state and fresh evidence.
- Required tests start with an intentional behavior assertion against the current registered hook pipeline, so missing-module crashes cannot be mistaken for RED.
- Both plans include source audits, task verification/failure signals and local threat registers pending coordinator canonical-risk reconciliation.

## Task Commits

- One documentation commit contains this summary and both plans; its hash is returned with the handoff. No source code commit is claimed.

## Checks

- Inspected revision: 77b5668f2003bea60127d87e8785469286abafb3, branch phase-issue87-guards; initial worktree was clean.
- Read-only Python/YAML validation exited 0. Both plans passed required metadata, full section set, task fields and automated/fails_when pair counts. Cleanup dependency resolved to guards. Exact overlapping sequential ownership was .ai/hooks/README.md, .ai/hooks/destructive-git-guard.py, .ai/references/destructive-operations.md, .ai/runtime/lib/destructive_guard.py and tests/test_destructive_guard.py.
- Implementation test commands are grounded in existing unittest discovery and registered-hooks test conventions. Future destructive_guard tests are assigned for creation; no implementation tests were run or claimed passed during preparation.
- Source evidence inspected: worktrees.cleanup_wave, close_session, session_merged/listing; delivery.gh/view; installer MANAGED_HOOKS/hook_settings; registered launcher tests and hook documentation.
- rg is unavailable; bounded PowerShell reads/Select-String were used. One attempted read of tests/test_hooks.py found no file; no plan relies on that path.
- Staged path inspection confirmed only these three assigned files. The first staged whitespace check found an extra blank EOF line in CLEANUP-PLAN.md; it was removed before the final repeated check.

## Files Created/Modified

- docs/maintenance/issue87/GUARDS-PLAN.md — guard ownership, parser/evidence contract and fail-first implementation instructions.
- docs/maintenance/issue87/CLEANUP-PLAN.md — guard-dependent cleanup child with exact approval and final-state contract.
- docs/maintenance/issue87/GUARDS-PREPARER-SUMMARY.md — preparation evidence and coordinator handoff.

## Decisions Made

- Coordinator explicitly approved standalone entrypoint/library cleanup rather than a new runtime facade. No phase.py interface is required for these plans.
- Coordinator expanded assigned deliverables to add CLEANUP-PLAN.md and requires the cleanup worktree be created only after the guard returns.
- command_segments(payload) is the proposed reusable read-only parse interface for the later planning-integrity hook: supported/unsupported status, reason_code and ordered effective-cwd/literal-argv segments. That hook and its later installer registration remain outside these plans.

## Deviations from Plan

- Original two-file preparer assignment expanded by coordinator to three files so guard and cleanup can be delivered as a real parent/child stack.
- Maintenance-local identifiers substitute for absent adopting-project roadmap IDs; skeleton records remain untouched.

## Issues Encountered

- No blocking missing design choice remains for preparation. Installed gh/glab argv/schema is deliberately grounded by implementers against actual read-only CLI help and pinned in offline fixtures; unknown/incomplete evidence always refuses destruction.
- New hook registration is a real ownership dependency for the later planning-integrity installer change. Coordinator must sequence .ai/install.py writers after GUARD, and prevent overlapping library/test writers during CLEANUP.

## Threat Outcomes

| PLAN/ID | Issue | Outcome | Git state | Evidence |
|---|---|---|---|---|
| GUARDS I87-G-T1/T2/T3 | Pending coordinator canonical-risk dedup/readback | Mitigation planned, unresolved | Planning only | Guard task, parser matrix and evidence/approval boundaries |
| CLEANUP I87-C-T1/T2 | Pending coordinator canonical-risk dedup/readback; possible parent aliases declared | Mitigation planned, unresolved | Planning only | Exact-list state pinning, race handling and final-state task |

No threats are claimed resolved or closed. Approval provenance and external-process filesystem races remain explicit limits for independent review.

## Next Phase Readiness

Send both plans to independent phase-checker. On acceptance, execute GUARDS first under the existing user implementation authority. After the committed guard result is integrated, create CLEANUP's child checkout at that implementation tip, then execute its assigned overlapping paths sequentially. Coordinator owns publishing drafts, risk reconciliation and shared CONTEXT updates. Never merge or close issue87.
