---
phase: issue87-maintenance
plan: workflow-preparation
subsystem: workflow
tags: [issue87, planning, guard-repair, authorization]
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
requires: []
provides:
  - Bounded workflow implementation plan with exclusive source ownership.
  - Guard repair matrix, RED/GREEN receipt contract and approval categories.
affects: [issue87-workflow]
tech-stack:
  added: []
  patterns: [fixture-copy removal regressions, independent guard repair cases]
key-files:
  created:
    - docs/maintenance/issue87/WORKFLOW-PLAN.md
    - docs/maintenance/issue87/WORKFLOW-PREPARER-SUMMARY.md
  modified: []
key-decisions:
  - One coder owns the source and tests; the narrow RULES reusable-source ownership exception was explicitly assigned by the coordinator.
  - Contract tests protect procedure reachability and meaningful removal cases; semantic review proves instruction completeness.
  - Reviewer issue-link audit points to existing canonical-threat-tracking anchor, preserving independent PRs.
patterns-established: []
requirements-completed: []
acceptance: []
documentation: [docs/maintenance/issue87/WORKFLOW-PLAN.md]
coverage:
  - id: PLAN-WORKFLOW
    description: Executable workflow plan prepared for independent phase-checker review.
    verification:
      - kind: manual_procedural
        ref: WORKFLOW-PLAN.md task-field, ownership and source-coverage audit
        status: pass
    human_judgment: false
duration: approximately 7min
completed: 2026-10-15
status: complete
---

# Issue 87 workflow preparation summary

**Prepared an exclusive workflow slice requiring independent guard cases,
genuine failing regressions and concise approval boundaries.**

## Performance

- Tasks: one preparation slice, two implementation tasks planned.
- Files created: two assigned maintenance records.
- Base and branch: 77b5668f2003bea60127d87e8785469286abafb3, phase-issue87-workflow.

## Accomplishments

- Planned a canonical guard-repair reference and narrow links from AGENTS,
  RULES, preparer, coder and reviewer instructions.
- Required paired bypass/false-positive cases for case, empty input, encoding,
  alternate methods/bodies, quoting/tokenization and supported parser differences.
- Specified observable RED before guard implementation, invalid-RED handling,
  the same GREEN checks, captured revisions and independent evidence review.
- Preserved PR86 advisory scratchpad behavior, existing phase authority,
  earlier explicit authorization and the user's no-merge limit.
- Defined bounded network/DNS/tunnel/infrastructure, install and new-scope
  approval categories without repeated internal phase-transition prompts.

## Task Commits

- Preparation PLAN and this SUMMARY: the current planning-slice commit.
- No source implementation or tests were written or published by the preparer.

## Checks

- Reviewed input revision: 77b5668f2003bea60127d87e8785469286abafb3.
- Confirmed clean starting status, assigned branch and worktree root with Git.
- Native PowerShell XML check: PASS; two tasks have required fields, all five
  automated task commands have immediate failure signals, issue_refs is present.
- git diff --check: PASS for the staged preparation artifacts before commit.
- An initial optional Python structural check could not launch because the
  sandbox resolves python to an inaccessible WindowsApps alias. Native XML
  validation replaced it. The coordinator reports Python 3.13.14/PyYAML 6.0.3
  work outside that sandbox; execution may use its approved environment route.
- Implementation suites were not run: the new test is deliberately assigned
  to the coder, and the coordinator explicitly requested no planner test run.
  The PLAN's unittest argv follow existing CI/scout evidence and are future
  execution checks, not claimed passing implementation evidence.

## Files Created/Modified

- WORKFLOW-PLAN.md: exact source ownership, sequential tasks, matrix,
  communication/approval boundaries and four-source coverage audit.
- WORKFLOW-PREPARER-SUMMARY.md: this preparation evidence and handoff.

## Decisions Made

The coordinator explicitly assigned the reusable .ai/RULES.md source edit to
the implementation coder; shared execution/planning status remains coordinator
owned. Keep source changes small and preserve complete role methods. For the
reviewer's issue-link audit duty, link to existing canonical-threat-tracking;
the orchestration owner maintains the canonical audit details separately.

## Deviations from Plan

None. This is the preparation assignment; its output is a maintenance PLAN,
not a numbered adopting-project phase or implementation completion.

## Issues Encountered

Optional Python invocation was unavailable inside the sandbox; a native
PowerShell structural check completed. No installation or escalation attempted.

## User Setup Required

None.

## Threat Outcomes

None identified in preparation-only scope. The PLAN changes guidance and
fixture-only reachability tests; implementation owners retain actual guard
boundary findings, canonical threat tracking and executable guard evidence.

## Next Phase Readiness

Ready for the coordinator's independent phase-checker review and bounded coder
dispatch under already-recorded authorization. Required implementation tests,
fresh code/document review and integrated verification remain future work.
No uncovered assigned acceptance or blocking human decision remains.
