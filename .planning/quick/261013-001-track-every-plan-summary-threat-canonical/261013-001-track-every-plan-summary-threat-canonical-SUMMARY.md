---
phase: quick-261013-001
plan: "01"
subsystem: workflow
tags: [threat-tracking, templates, structural-validation]
requires: []
provides:
  - Canonical safe threat issue lifecycle and linked producer/coordinator review seams
  - Offline template/step mutation and real issue-validator regression evidence
affects: [planning, execution, quick, shipping]
actuals:
  tokens: 14438
  tasks: 3
  commits: 3
tech-stack:
  added: []
  patterns: [canonical risk identity, coordinator issue reconciliation]
key-files:
  created: [tests/test_threat_tracking_contract.py]
  modified: [".ai/references/git-workflow.md",".ai/templates/issue.md",".ai/templates/pull-request.md",".ai/templates/phase-prompt.md",".ai/templates/summary.md",".ai/agents/phase-preparer.md",".ai/agents/coder.md",".ai/agents/phase-checker.md",".ai/agents/verifier.md",".ai/workflows/plan-phase.md",".ai/workflows/execute-phase.md",".ai/workflows/quick.md",".ai/workflows/ship.md",".ai/runtime/TEMPLATE-CONTRACT.md","tests/test_issue_format.py"]
key-decisions:
  - "Follow approved threat-specific scope; generic phase issue lifecycle and approval-gate work belongs to separate PR84."
patterns-established:
  - "Workers carry safe findings; coordinator owns semantic issue reconciliation and publication."
requirements-completed: []
acceptance: [QT-01, QT-02, QT-03, QT-04, QT-05, QT-06]
documentation: [".ai/references/git-workflow.md",".ai/templates/issue.md",".ai/templates/pull-request.md",".ai/templates/phase-prompt.md",".ai/templates/summary.md",".ai/agents/phase-preparer.md",".ai/agents/coder.md",".ai/agents/phase-checker.md",".ai/agents/verifier.md",".ai/workflows/plan-phase.md",".ai/workflows/execute-phase.md",".ai/workflows/quick.md",".ai/workflows/ship.md",".ai/runtime/TEMPLATE-CONTRACT.md"]
coverage:
  - id: D1
    description: Canonical lifecycle plus PLAN/SUMMARY and coordinator/reviewer/ship contracts
    verification:
      - {kind: other, ref: "python -m unittest discover -s tests -p test_threat_tracking_contract.py -v", status: pass}
      - {kind: other, ref: "python -m unittest discover -s tests -p test_workflow_links.py -v", status: pass}
    human_judgment: false
  - id: D2
    description: Security risk heading/order enforcement with honest structuralOnly boundary
    verification:
      - {kind: unit, ref: "python -m unittest discover -s tests -p test_issue_format.py -v", status: pass}
      - {kind: integration, ref: "python -m unittest discover -s tests -p test_todo_issues.py -v", status: pass}
    human_judgment: false
duration: "At least 12 minutes measured authoring; initial inspection unmeasured"
completed: 2026-10-13
status: complete
plan_head_before: 6c2a0d5b3250a7486addaf1a2608b6d5953e584a
implementation_head: 0134e93ed75fb4b8c614c66c31af7a0d70268201

---

# Phase quick-261013-001 Plan 01: Canonical threat tracking Summary

Every identified PLAN/SUMMARY threat now reaches a shared safe canonical issue
procedure with carried identity/lifecycle fields and mandatory coordinator review.

## Performance

3/3 tasks; 16 implementation paths plus this SUMMARY. Initial inspection was not
timestamped; first SUMMARY creation 18:55:20Z and final preparation 19:08:03Z
establish a 12-minute authoring floor on 2026-10-13. Context usage unavailable.
Actuals measure base 6c2a0d5b3250a7486addaf1a2608b6d5953e584a through implementation
head 0134e93ed75fb4b8c614c66c31af7a0d70268201: 14438 tokens, rounded-up
characters/4 over the text Git diff, no binary/generated files. Commit count 3
covers this same range, including the SUMMARY then; final metadata is separate.

Root: D:/Codex Projects/ai-engineering-template/.worktrees/261013-001-track-every-plan-summary-threat-canonical-144851397.
Branch: phase-261013-001-track-every-plan-summary-threat-canonical-144851397.

## Accomplishments

- Canonical identity/aliases, open/closed semantic review, uncertain-create
  recovery, safe public/restricted-detail reporting and evidence-based closure.
- Security risk/PR fields plus PLAN/SUMMARY carry-forward fields; concise links
  across producers, reviewers and phase/quick/ship coordinator seams.
- Mandatory reconciliation outside optional quick check_plan/verify.
- Actual validator tests enforce security headings/order and installed schemas,
  while invalid field values deliberately pass structuralOnly.

## Task Commits

1. 4baf5982dc8a690499792e8586f555a716ee251a: lifecycle/templates.
2. 3aeb811514f9509dee20f7ae7827825f827cf310: producer/coordinator seams.
3. 0134e93ed75fb4b8c614c66c31af7a0d70268201: edges and validator limits.

Final SUMMARY metadata is a separate commit returned to the coordinator.

## Checks

Elevated local Python 3.13.14; no remote service contact. Checks ran on working
changes before their slice commits, then relevant source/tests were committed
unchanged. Observed HEADs: Task 1 base 6c2a0d5, Task 2 4baf598, Task 3 3aeb811.

| Exact command | Actual result |
|---|---|
| python -m unittest discover -s tests -p test_issue_format.py -v | Task 1:16 passed / 2.628s; final 17 passed / 2.653s |
| python -m unittest discover -s tests -p test_threat_tracking_contract.py -v | Task 2:8 passed / 2.717s; final 11 passed / 2.435s |
| python -m unittest discover -s tests -p test_workflow_links.py -v | Task 2:3 passed / 1.214s; final 3 passed / 0.674s |
| python -m unittest discover -s tests -p test_todo_issues.py -v | 34 ran:33 passed,1 skipped/134.252s |
| git diff --check | Passed after each slice |

TODO skip: test_ambiguous_name_and_symlink_escape_are_refused, symlink creation
unavailable on Windows. The Windows junction test passed. No skipped execution
was represented as passing. The initial Task 3 mutation test errored by matching
an earlier numbered Git action; its test-only boundary was corrected and 11 tests
passed / 2.550s, then passed again after preparer example restoration.

## Files Created/Modified

All 14 assigned documentation paths are named exactly in frontmatter.

| Scope | Change |
|---|---|
| Git reference, Security risk and PR templates | Canonical procedure, ordered assessment heading and neutral/eligible risk references |
| PLAN/SUMMARY templates and preparer/coder agents | Full carry-forward fields, ownership, self-check and preserved illustrative STRIDE rows |
| Checker/verifier and plan/execute/quick/ship workflows | Finding/link/evidence review and mandatory coordinator reconciliation |
| TEMPLATE-CONTRACT.md | Additive fields, ownership and structuralOnly boundary |
| tests/test_issue_format.py | Real template/installed-schema behavior and deliberately passing invalid assessment values |
| tests/test_threat_tracking_contract.py | File Template/step parsing, temporary mutations, alias handoff and declared review obligations |

No runtime implementation, CI, entrypoints, shared QUICK/STATE/PLAN or adoption
skeleton changed. issue_format.py and test_todo_issues.py remain unchanged.
No deletion, branch switch, integration, push, publication or merge performed.

## Acceptance Coverage

QT-01/02: every-occurrence tracking, identity/aliases and mandatory phase/both
quick-mode hooks. QT-03/04: assessment/lifecycle/evidence fields and neutral links
until mitigation plus existing closure authority. QT-05: both private-reporting
instructions reconciled. QT-06: linked producer/checker/verifier/ship seams and
meaningful artifact/step mutations. Provider semantics remain review obligations.

## Decisions Made

Followed the approved threat-specific PLAN. Generic execution-issue enforcement,
approval-gate removal and same-execution generic issue exceptions belong to
separate PR84; the all-threats requirement still includes already mitigated,
accepted and deferred findings. Overlapping Git/execute/ship edits remain narrow.

## Deviations from Plan

Rule1, Task 3: restored useful preparer examples removed during Task 2 table
modernization, now with lifecycle/Pending fields; contract/link checks rerun in
0134e93. Test-only mutation repair above changed no product behavior/scope.

## Issues Encountered

The primary .venv launcher failed to locate pyvenv.cfg before edits/tests through
it; the working Python alias was used. rg unavailable; used Select-String.
No credentials, provider calls or package installation needed.

## Known Stubs

None in delivered behavior. Reusable template prompts/fictional examples are
intentional scaffolding; Pending evidence below is an actual review dependency.

## Threat Flags

Both findings carry the [PLAN STRIDE register](261013-001-track-every-plan-summary-threat-canonical-PLAN.md#stride-threat-register).
The coordinator supplied verified issue readback and exact keys; this worker
performed no fresh provider readback.

| Threat ID / key and aliases | Category / scope | Severity / assessment | Disposition / mitigation | Owner / status | Canonical issue | Resolution evidence |
|---|---|---|---|---|---|---|
| T-QT-01 / workflow-publication-restricted-detail; source PLAN T-QT-01 | Information disclosure; publishable PLAN/SUMMARY/issue/PR text/links | high: broad public disclosure impact; possible agent error, no sensitive payload identified | mitigate; Tasks 1/2 safe-public/restricted-detail duties, focused checks, independent safe-content review | coordinator; unresolved | https://github.com/Tasaddar12/ai-engineering-template/issues/81 | 0134e93 instructions/fixtures and passes above; Pending independent review, offline checks do not prove live redaction |
| T-QT-02 / workflow-threat-identity-and-closure; source PLAN T-QT-02 | Tampering/Repudiation; identity/lifecycle/closing references | medium: duplicates/premature closure conceal work; prior shared lifecycle gap evidenced in PLAN | mitigate; Tasks 1/2 identity/carry-forward/ship duties, Task 3 mutations, independent lifecycle/closure audit | coordinator; unresolved | https://github.com/Tasaddar12/ai-engineering-template/issues/82 | 0134e93 instructions/fixtures and passes above; Pending independent review and current issue/PR readback |

No additional threats identified across owned changes, deviations or Remaining;
the two PLAN disclosure/status boundaries cover these changes. Instructions
alone do not justify marking either risk mitigated. No new issue/closure request.

## Remaining

- Coordinator integrates, reconciles changed main
  b475037dfcce9636d544b909255836b7be58ba6e (PR78 landed during execution), obtains
  fresh independent code/document/verification review and current provider/PR
  closure-reference readback. Worker stayed on assigned base.
- Preserve neutral 81/82 references and update evidence/status only after review.
  Keep [draft PR80](https://github.com/Tasaddar12/ai-engineering-template/pull/80)
  and [enhancement issue 79](https://github.com/Tasaddar12/ai-engineering-template/issues/79)
  current. Their publication/readback was supplied before test scripts. NEVER MERGE.
- Full required CI unrun locally by coordinator instruction: python -m unittest
  discover -s tests -v on Linux/Windows and bash .ai/hooks/ai-tier-notice.test.sh,
  bash .ai/hooks/worktree-guard.test.sh, bash .ai/hooks/context-handoff.test.sh,
  bash .ai/hooks/worktree-location.test.sh. Observe required validate on the
  pushed combined candidate; Pending/failure prevents readiness. Empty scaffold
  verification.commands is not evidence. Linux CI covers the Windows symlink skip.
- Offline tests prove structure, validator behavior and unchanged TODO subprocess
  behavior, not live redaction/dedup/publication/closure or GitLab publication.
  Runtime provider remains GitHub-only; other hosts need a verified authorized
  tool or explicit Pending blocker.

## User Setup Required

None for this implementation. Missing independent/remote evidence remains pending,
without invented human approval.

## Next Phase Readiness

Author tasks complete; integration, independent review and CI remain coordinator-owned.

| Reconciliation | Evidence/proposal |
|---|---|
| Position/progress/roadmap | Quick 3/3 author tasks; do not fill adoption scaffolds or infer delivery |
| Metrics | Immutable base/head, measured chars/4 and implementation count above |
| Decisions/session | Threat-specific scope; final owned SUMMARY commit; next integrate/review |
| Requirements/blockers | None assigned; QT-01 through QT-06 author coverage; review/CI/main reconciliation and skip retained |

## Self-Check: PASSED

All 16 implementation paths and this SUMMARY exist. Three implementation commits
exist on the assigned branch, with no deleted/out-of-scope paths. Root/branch
guards ran before writes/commits. Final metadata commit/clean status checked after commit.
