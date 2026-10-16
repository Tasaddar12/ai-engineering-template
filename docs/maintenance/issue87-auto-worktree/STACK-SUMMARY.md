---
phase: maintenance-issue87-auto-worktree
plan: "01"
task: 4
status: partial
requirements-completed: []
acceptance: []
documentation: [.ai/RULES.md, .ai/hooks/README.md]
---

# PR97 native/planning stack implementation receipt

Task 4 is **source-complete / live-unverified**. Genuine installed RED preceded
the minimal compatibility fix, and all seven approved checks are GREEN. This is
a bounded source compatibility result, not full issue87 acceptance or live host
evidence. Fresh independent joined review, composition and CI remain coordinator
obligations. Context usage: unavailable.

## Identity and dependency boundary

- Root: `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-native-code-06-203146625`.
- Branch: `phase-issue87-native-code-06-203146625`.
- Immutable input: `a14a0fe2e64eba9d93579f6e29942ab3261f5b62`.
- Corrected native97 first parent: `5714d1d53df054ce06585c1726dae20b5a879afd`.
- Task4 RED commit: `e0204a89f9d7191d5e70256441354573c09625bf`.
- Task4 source fix: `9ae9e119495783e9a9e22404ef18627db59e3e50`.
- Frozen PR93 dependency: `47593a3d3f71739bd146a6c2c3590798d7c73c2e`.
- Frozen PR92 ancestor: `d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6`.
- Coordinator materialized the corrected native97/frozen93 merge before dispatch;
  this worker does not merge, switch, publish, change PR bases or frozen heads.
- Ownership: `.ai/runtime/phase.py`, `.ai/install.py`, `.ai/RULES.md` Hooks and
  validation only, `.ai/hooks/README.md`, `tests/test_same_agent_worktree.py`,
  `tests/test_install.py`, plus this summary. Dependency helpers/tests remain
  read-only. No original-six composition tree is imported.

The approved [PLAN Task 4](PLAN.md), [STACK-PLAN](STACK-PLAN.md), and clean
[independent stack-plan review](STACK-PLAN-REVIEW.md) govern the assignment.
Earlier code-05 correction commits and receipts remain in
[IMPLEMENTATION-SUMMARY](IMPLEMENTATION-SUMMARY.md). The coordinator's prototype
`9060df58033452483961d9eb1d7113cca10b0b4a` receipt (one installed native test /
15.981s, snapshot(None) failure) is
historical composition evidence, not the corrected input's execution receipt.

## TDD Evidence

Production stayed exactly at the immutable input for the RED slice. Only the two
owned existing test files and this summary changed; no new test file/harness or
production stub was introduced.

PowerShell command, run from the assigned root:

```text
& 'C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe' -m unittest discover -s tests -p test_same_agent_worktree.py -k simulated_installed_denial_native_entry_defaults_and_fresh_rebuilt_edit -k stacked -v
```

Observed **3 tests / 16.523s, exit 1, two assertion failures, no errors/skips**.
The original installed native target reached actual install, source denial and
request ticket, then `prewrite.begin -> run_verb:91 ->
planning_integrity.snapshot:231` raised `AttributeError: 'NoneType' object has no
attribute 'root'`. The named assertion was `installed prewrite.begin must preserve
the native/planning dispatch boundary`, failing its no-Traceback requirement.
This is an actual joined behavioral defect, not a missing import/verb/setup error.

The additional installed dispatch fault case also reached snapshot(None) before
its expected structured native OSError result. Its later three-adapter, unknown
and future-prefix boundary assertions remain unexecuted at RED. The real ordinary
`roadmap.update-plan-progress` success/error warning control passed, retaining
its unrelated authored sentinel and exact real index bytes. Native new/existing
phase/quick execution and full required regressions remain GREEN obligations.

The installer test extensions check the actual union registrations, timeout
precedence, Python/runpy Windows status, one advisory-first/source-second editing
group, distinct advisory dispatch identity, preserved user hooks, malformed
canonical commit denial, exact index bytes and authored sentinels. Runtime help
must retain both planning.integrity and all three native adapter verbs.

## Checks

RED was committed as `e0204a89f9d7191d5e70256441354573c09625bf` before source
edits. One exact `NATIVE_ADAPTERS` set contains only the three registered native
adapters. `main` uses it for Workspace selection and native OSError handling;
`run_verb` validates the handler, then uses it for the snapshot/warning exception.
Ordinary PR93 snapshots, success/error warnings, registration and init dispatch
remain unchanged. No generic helper or global snapshot(None) handling changed.

The materialized `.ai/install.py` union was inspected and retained byte-identical:
Python/runpy hooks120, source-prewrite30, other shared shell hooks10, Claude
creation/removal180/60. The stronger installed fixture verifies both hosts'
unique managed identities, advisory-first/source-second editing group and user
hook retention. Narrow RULES Hooks and validation and hooks README explain this
boundary together with destructive/canonical/native controls; no PR91/94 prose
was imported. These are local union clarifications, not a broader guide rewrite.

All commands below run from the assigned root on the RED commit plus the exact
owned production/docs diff. Python is the exact executable recorded in TDD
Evidence, invoked as `-m unittest discover -s tests -p FILE [FILTER] -v`.

| FILE / FILTER | Cases / seconds | Actual result |
|---|---|---|
| `test_same_agent_worktree.py` | 13 / 133.214 | exit 0, no skips; matching installed native tracer, all three exact adapters, new/existing phase/quick, native OSError and unknown/future-prefix boundaries, ordinary warning controls pass |
| `test_install.py -k registered_hooks_run_planning_integrity_from_installed_hosts` | 1 / 30.906 | exit 0, no skips; both hosts' union and canonical/index/authored controls pass |
| `test_install.py -k installed_runtime_answers_its_verb_contract` | 1 / 23.841 | exit 0, no skips; both installed namespaces retain native/planning verbs and unknown-verb result |
| `test_install_update.py` | 66 / 395.173 | exit 0, skipped 4 (two Windows symlink-privilege cases and two Claude instances of Codex-only settings checks) |
| `test_planning_integrity.py` | 47 / 67.598 | exit 0, no skips; imported canonical schema/commit/index/authored guard and ordinary warning cases pass |
| `test_phase_runtime.py` | 162 / 219.832 | exit 0, no skips; ordinary dispatch, canonical/authored mutations, configuration, registration and isolation controls pass |
| `test_session_delivery.py` | 60 / 100.123 | exit 0, no skips; ordinary session ownership/base/selection and delivery controls pass |

The suites use independent disposable offline repositories. All seven approved
checks passed with no failures/errors; no deterministic GREEN was repeated.
No original-six suite or benchmark is run in this worker assignment.

The matching original tracer now passes actual installed source cancellation and
ticket, prewrite.begin, actual registered WorktreeCreate, real Git confirmation
and native session adoption, then relative fresh reads and one rebuilt edit under
the same SIMULATED host actor/default context. Primary staged/unstaged/untracked/
ignored data, exact index facts and canonical STATE/ROADMAP bytes remain intact.
Workflow fixtures cover no-edit request bootstrap, native new phase/quick creation
and ordinary existing phase/quick entry with accumulated HEAD, immutable fork base
and unchanged ownership. No request or runtime confirm claims authenticated host
movement, permissions or loaded project context.

## Threat Outcomes

| Owning PLAN threat | Canonical issue | Current outcome and state | Evidence |
|---|---|---|---|
| T-AW-01 | [issue98 target confinement](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | Deterministic joined preservation GREEN; independent/integrated verification pending; OPEN per coordinator, no worker provider read/write | Ordinary success/error warnings, unrelated authored sentinel and exact index control; installed both-host canonical malformed commit denial; full imported integrity47 and ordinary runtime162 GREEN |
| T-AW-02 | [issue98 unit identity](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | Prior native lifecycle retained and focused GREEN; OPEN per coordinator, no worker provider read/write | New/existing phase/quick, accumulated HEAD/immutable base/ownership and exact actor/session controls pass; no lifecycle expansion |
| T-AW-03 | [issue98 host transition proof](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | Installed dispatch join corrected with matching GREEN; live unverified; OPEN per coordinator | Named installed native RED passes through creation/confirm/rebuilt edit; exact three-adapter OSError and unknown/future-prefix controls pass; source is not native host binding proof |

No new canonical threat identity is introduced by the exact adapter exception.

## Scope and deferred work

The input-to-worker diff is limited to the owned source, two existing tests,
the narrow RULES section, hooks README and this summary. `.ai/install.py`,
`planning_integrity.py`, its imported tests, native protocol helper/workflows,
advisory guard, cleanup policies and generic locale helpers have empty input
diffs. No paths are deleted. No PR91 guard-workflow or PR94 cleanup introduction
is copied into this bounded patch. Coordinator still owns the full
`47593a3d3f71739bd146a6c2c3590798d7c73c2e..final97` own-change inspection and
actual PR target metadata.

No new out-of-scope defect was discovered. The earlier generic Windows locale
follow-up remains in IMPLEMENTATION-SUMMARY Deferred; this adapter correction
does not repair it. Root-reported pre-join CI and code-05/doc review results do
not substitute for final joined CI/review. No new decision, approval or shared
adoption-record update is proposed.

## Remaining / coordinator reconciliation

- Assigned source, tests, narrow shared documentation and seven required checks
  are complete. Source commit `9ae9e119495783e9a9e22404ef18627db59e3e50` includes
  this summary; this metadata-only follow-up records its generated full hash
  without changing tested behavior.
- Coordinator obtains fresh source/integration/narrow-doc review at the integrated
  result, checks frozen93..final97 scope, then runs/reviews the separate disposable
  original-six composition. Earlier prototype/six-only evidence is insufficient.
- Native host/default context remains explicitly SIMULATED over installed hooks
  and real Git. Live same-agent permissions, context and later-turn binding remain
  unverified; Codex still lacks this template's authenticated same-thread controller.
- Keep PR97 draft and issue87 open; no PR merge, installation, provider action,
  real cleanup, shared status mutation or approval request belongs to this worker.

| Coordinator operation | Supplied result / proposed reconciliation |
|---|---|
| Integrate component / record session | Task4 source-complete on immutable a14 input; exact commits returned, clean worker HEAD |
| Progress / roadmap | Record bounded Task4 source completion after integration; do not infer phase/goal completion |
| Decisions / requirements | No new human decision or adoption requirement completion; AW03/05/06/08 deterministic join evidence only |
| Metrics / checks | Seven commands and actual counts/durations/skips above; dependency/input identities pinned |
| Blockers / next action | Fresh joined source/integration/narrow-doc review, disposable original-six composition/review and final CI; live acceptance remains unmet |

## Self-Check: PASSED

Root, branch and immutable input were verified before writes; exact root/branch/
HEAD and owned paths are rechecked for each commit. RED exists as
`e0204a89f9d7191d5e70256441354573c09625bf`. The matching original native tracer
and every required nonempty check passed after the repair. `git diff --check`
passes, imported helper/tests and installer/advisory bytes are unchanged, and
there are no deletions, new source stubs or new threat identities. This author
self-check does not replace independent review or native live observation.
