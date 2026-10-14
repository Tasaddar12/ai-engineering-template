---
phase: quick-261013-001
plan: "01"
status: complete
requirements-completed: []
acceptance: [HANDOFF-01, PUBLICATION-01, PR-01, RECONCILE-01, AUTHORITY-01]
documentation:
  - .ai/workflows/execute-phase.md
  - .ai/workflows/ship.md
  - .ai/references/git-workflow.md
  - .ai/runtime/README.md
issue_refs: []
coverage:
  - id: D1
    description: Declared phase issue publication and handoff gate
    verification:
      - kind: integration
        ref: tests/test_phase_issues.py plus tests/test_todo_issues.py
        status: pass
    human_judgment: false
  - id: D2
    description: Phase PR body gates and verified folded TODO reconciliation
    verification:
      - kind: integration
        ref: tests/test_phase_issues.py plus tests/test_session_delivery.py
        status: pass
    human_judgment: false
  - id: D3
    description: Normal and early handoff producers and post-merge procedures
    verification:
      - kind: other
        ref: tests/test_workflow_links.py
        status: pass
    human_judgment: false
---
# Phase issue handoff and delivery enforcement

Execution SUMMARY declarations now gate supported handoffs/completion and phase
PR bodies. Publication reuses the existing TODO duplicate/recovery helpers;
folded TODO retirement waits for matching MERGED/CLOSED readback.

## Identity and commits

- Root: `D:/Codex Projects/ai-engineering-template/.worktrees/phase-issue-code-150554588`.
- Branch: `phase-phase-issue-code-150554588`.
- Base: `21eeed1e6c5c7f215689d3ace0c2090659abc6a2`.
- Task 1 RED: `efc66d9fbf20687a798790c51c3ec30421bfc736`.
- Task 1 GREEN: `a3a5ad1c7c881b98b40bb32ee04362f0c1b3928e`.
- Task 2 RED: `5b601e8cbdd404d967fa40f768acf12892505fc8`.
- Declaration-producer RED: `4354fb9b89e845320c26915b6145968625a115fd`.
- Task 2 GREEN: `8dfeb6ec559448360373c4072a74e0b9744b0839`.
- Task 3: this documentation/SUMMARY commit; final SHA returned to the coordinator.

## Changes

1. Added phase_issues entry adapter and locked handoff/declaration/preview/publish/
   update verbs. Explicit reviewed [] passes; missing/malformed/unlinked problems
   fail before completion writes. Provider failure preserves attempted intent as
   retryable blocked-publication. Publication/update preserves selected issue kind.
2. Phase pr.open automatically binds the existing session, pins phase calls to
   origin, validates the effective body and publishes its exact validated bytes.
   Deferred/pending-human followups cannot use closing references. Remote pending
   UAT cannot be made resolving through a forged local claim. Merge command success
   is verified only by matching number/URL/head MERGED readback. Reconciliation
   selects exact Folded Todos and the session PR; open/unknown/CLOSED-but-pending-UAT
   and stale records remain pending. Retry is idempotent and creates/closes no issue.
3. Wired normal/deferral/blocked/halted/early execution handoffs to coordinator
   leftover review and runtime declarations. Necessary issue tracking uses existing
   execution authority. Removed execution-time TODO retirement; ship reconciles
   after verified merge and records TODO-only changes through existing planning
   policy. Documented fields, argv, provider boundary and semantic limits.

## Checks and TDD evidence

All checks used fake providers and temporary Git repositories; no live network,
publication or merge was used. Runs occurred at the named RED HEAD plus the owned
implementation/test diff subsequently committed as GREEN; commit content was
preserved. Task 3 checks ran at `8dfeb6e` plus the owned documentation/test diff.

| Check | Observed result |
| --- | --- |
| Task 1 RED: unittest discover test_phase_issues.py | 3 tests, 3 intended failures, exit 1: missing declarations passed phase.complete; phase.handoff absent |
| Task 1 GREEN: unittest discover test_phase_issues.py | 20 tests passed, 50.903s |
| unittest discover test_todo_issues.py | 34 tests passed, one existing platform skip, 157.141s |
| unittest discover test_phase_runtime.py | 162 tests passed, 246.760s |
| Task 2 RED: test_phase_issues.py -k phase_session | 1 intended failure, exit 1: omitted phase still edited undeclared PR |
| Task 2 RED: test_session_delivery.py -k matching_merged_readback | 1 test, 7 intended failures, exit 1: false merged success on unknown/mismatched readback |
| Producer RED: test_phase_issues.py -k declaration_setter | 1 intended missing-verb failure, exit 1 before setter implementation |
| Task 2 GREEN: unittest discover test_phase_issues.py | 32 tests passed, 95.957s |
| Final affected/new phase cases: -k closing_keyword, -k effective_body, -k changed_todo | Each passed 1 test; current file has 34 cases, full combined run remains coordinator-owned |
| unittest discover test_session_delivery.py | 60 tests passed, 125.113s |
| unittest discover test_workflow_links.py | 4 tests passed, 1.641s |
| git diff --check; phase.py query help | Passed; documented verbs registered |

Commands use `python -m unittest discover -s tests -p <named file>` with the shown
`-k` selectors for affected cases. Negative coverage maps SEC-01 to private-source/
diagnostic separation, SEC-02 to traversal/link/stale-record and retirement guards,
and SEC-03 to origin/number/URL/session/remote-kind/MERGED/CLOSED/pending-UAT guards.
Windows symlink checks execute when link privilege is available; the existing TODO
suite reports its platform skip. No separate REFACTOR commit was needed.

## Deviations and resolved authoring mistakes

- Added bounded phase.issue-declare after the coordinator identified the existing
  SUMMARY producer gap. It uses a whole-record digest and preserves publication
  identity/kind; no ledger or provider extension was added.
- Initial test discovery imported the TODO TestCase; corrected before valid Task 1
  RED. Initial merge fixture lacked config; corrected before valid Task 2 RED.
- A Windows default decode changed original Unicode assertions in the first runtime
  run (162 tests, two failures). Restored their original UTF-8 bytes; affected
  PlanRegistration20 then the named full162 file passed. No assertion was weakened.

## Remaining and limits

No implementation blocker or actionable unresolved author finding remains. The
coordinator owns integration, combined final tests/CI, independent code/document/
outcome review and draft delivery. No worker push, merge, branch switch or cleanup
was performed. Context usage: unavailable.

Runtime validates declared records, source paths, selected kinds/format and observed
provider fields. It cannot discover omitted prose, prove semantic issue type or real
human acceptance, or intercept arbitrary direct gh/API edits. issue.validate remains
structuralOnly and planning.validate warn-only. Templates, issue_format, threat roles/
methods and PR 80 threat architecture are unchanged. PR 80 remains separate additive
work requiring coordinator overlap reconciliation; PR 78's base behavior is preserved,
and held PRs 76/77 are not dependencies.
