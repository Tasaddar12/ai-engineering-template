---
phase: maintenance-issue87-auto-worktree
plan: "01"
task: 4
status: blocked
requirements-completed: []
acceptance: []
documentation: [.ai/RULES.md, .ai/hooks/README.md]
---

# PR97 native/planning stack implementation receipt

Task 4 is in progress: genuine installed RED is preserved before production
changes. This is a bounded source compatibility assignment, not full issue87
acceptance or live host evidence. Context usage: unavailable.

## Identity and dependency boundary

- Root: `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-native-code-06-203146625`.
- Branch: `phase-issue87-native-code-06-203146625`.
- Immutable input: `a14a0fe2e64eba9d93579f6e29942ab3261f5b62`.
- Corrected native97 first parent: `5714d1d53df054ce06585c1726dae20b5a879afd`.
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
9060 receipt (one installed native test / 15.981s, snapshot(None) failure) is
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

RED command/result above is complete. All seven approved Task 4 GREEN commands
remain pending before production repair; they will be recorded here with actual
counts, durations, skips and exit status.

## Threat Outcomes

| Owning PLAN threat | Canonical issue | Current outcome and state | Evidence |
|---|---|---|---|
| T-AW-01 | [issue98 target confinement](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | Required preservation remains under review; OPEN per coordinator, no worker provider read/write | Ordinary success/error warnings, authored sentinel/index control passed at RED; installed canonical commit guard and native preservation GREEN pending |
| T-AW-02 | [issue98 unit identity](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | Prior native lifecycle retained; OPEN per coordinator, no worker provider read/write | New/existing phase/quick and exact actor/session controls remain required; no lifecycle expansion |
| T-AW-03 | [issue98 host transition proof](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | Actual installed dispatch join broken at RED; live unverified; OPEN per coordinator | Named installed native failure reaches canonical snapshot(None); exact registered adapter repair and matching GREEN required |

No new canonical threat identity is introduced by the exact adapter exception.

## Remaining / coordinator reconciliation

- Implement the minimal registered three-adapter exception after this RED commit,
  preserve ordinary snapshots/warnings/error payloads and imported planning guards.
- Run all seven approved Task 4 checks and commit source/docs/this receipt.
- Coordinator obtains fresh source/integration/narrow-doc review at the integrated
  result, checks frozen93..final97 scope, then runs/reviews the separate disposable
  original-six composition. Earlier prototype/six-only evidence is insufficient.
- Native host/default context remains explicitly SIMULATED over installed hooks
  and real Git. Live same-agent permissions, context and later-turn binding remain
  unverified; Codex still lacks this template's authenticated same-thread controller.
- Keep PR97 draft and issue87 open; no PR merge, installation, provider action,
  real cleanup, shared status mutation or approval request belongs to this worker.
