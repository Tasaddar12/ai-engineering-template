---
phase: template-maintenance-parallel-pipeline
plan: runtime
subsystem: runtime
tags: [python, git, snapshots, receipts, scheduling]
requires:
  - phase: parallel-pipeline-plan
    provides: independently approved implementation contract at aa0b044
provides:
  - paired immutable reviewer and test snapshots
  - pre-dispatch dependency, ownership and resource routing
  - observed check receipts and explicitly imported structured reviews
  - serialized atomic common-repository chunk state
affects: [execute-phase, verify-work, coordinator-dispatch]
actuals:
  tokens: 13343
  tasks: 3
  commits: 1
tech-stack:
  added: []
  patterns: [detached Git snapshots, OS file locks, atomic JSON replacement]
key-files:
  created: [.ai/runtime/lib/pipeline.py, tests/test_parallel_pipeline.py]
  modified: [.ai/runtime/phase.py]
key-decisions:
  - "The coordinator dispatches agents; runtime executes configured argv checks only."
  - "Check reuse is exact-revision and requires matching complete execution provenance."
  - "Imported review provenance explicitly says runtime did not observe reviewer execution."
patterns-established:
  - "Chunk gates are provisional; final integrated verification remains separate."
requirements-completed: []
acceptance: []
documentation: []
coverage:
  - id: runtime-pipeline
    description: immutable snapshots, dependency and conflict gates, structured evidence and atomic shared state
    verification:
      - kind: integration
        ref: python -m unittest discover -s tests -p test_parallel_pipeline.py -v
        status: pass
    human_judgment: false
  - id: legacy-runtime
    description: existing phase verbs and verification.run-checks retain their contract
    verification:
      - kind: integration
        ref: python -m unittest discover -s tests -p test_phase_runtime.py
        status: pass
    human_judgment: false
duration: startup timestamp not captured
completed: 2026-10-08
status: complete
plan_head_before: aa0b0443aa3e583e8a60370928c44b5edc9463c6
work_branch: phase-parallel-runtime
work_root: D:/Codex/2026-10-08/task-3/runtime-worker
---

# Parallel runtime pipeline summary

Committed chunks now freeze reviewer and test worktrees at the same full SHA,
and only current passing evidence plus Git-proven integration releases dependent
work. Independent coding can continue while checks and review use frozen trees.

## Performance

Three tasks completed in four owned files: runtime enforcement, CLI wiring, and
real Git/subprocess regression coverage with this maintenance record. Startup
time was not captured, so duration is an evidence gap rather than an estimate.
The implementation measurement is 53,371 characters / 4, rounded to 13,343,
from the assigned base's phase.py diff plus new pipeline/test source bytes;
this SUMMARY and binary/generated files are excluded. There was no plan estimate.

## Accomplishments

- Register resolves base/head, validates ancestry, identifiers, acceptance/check
  lists, exact ownership, declared committed deletions and linked paths.
- Prepare creates separate detached snapshots and checks their common Git
  identity, exact SHA and clean state. Author advancement leaves snapshots pinned.
- Route persists coordinator task declarations and reports ready/wait/blocked
  with dependency, ownership and named resource reasons. Unregistered future
  prerequisites wait; planned cycles block only related tasks. Independent
  pending tasks remain ready. The coordinator supplies the complete task inventory
  and uses the result before dispatch; the runtime never launches agents.
- Dependency release requires integration ancestry, prerequisite passing current
  check/review gates, and a dependent registered base containing the prerequisite
  chunk. A SUMMARY is never consulted as completion evidence.
- Tests execute explicit argv with a timeout in the test snapshot. Receipts retain
  attempts, full logs, hashed inputs/stat identity, environment hash and explicit
  identity, executable bytes/path, runtime/OS identity and the exact tested SHA.
  Intact passing receipts may reuse only on that same contract and SHA.
  `--no-reuse` forces execution for volatile external state; a reusable external
  check requires a stable explicit environment identity. Empty, failed, partial,
  stale, corrupt and timed-out check evidence cannot pass.
- Review import requires exact assignment/chunk/base/head, complete acceptance and
  scope coverage, explicit status, findings, evidence and attributed provenance.
  Passed reports reject high/critical/blocking findings and explicit blocking
  flags. Import is distinguished from runtime-observed command execution.
- Repository-common JSON uses a digest envelope, serialized OS locking and atomic
  replacement. Missing evidence state, partial records and corruption fail closed.
  Failed attempts and partial snapshots are retained. Checks run outside the state
  lock; same-chunk review imports can overlap test execution.

## Task Commits

The runtime implementation, tests, CLI wiring and this SUMMARY form one completed
slice, committed together with `feat(runtime): enforce immutable parallel chunk gates`.
The exact resulting hash is recorded in Git and supplied in the worker return.

## Checks

- **Tested input:** assigned base aa0b044 plus the owned final implementation diff.
- **Command:** `python -m unittest discover -s tests -p test_parallel_pipeline.py -v`.
- **Result:** 18 tests passed in 93.288 seconds; one native filesystem symlink test
  skipped because this Windows host lacks symlink privilege. Committed Git symlink
  refusal is tested independently without requiring native privilege.
- **Scenarios:** paired snapshots and author advancement; same-chunk overlapping
  checks/review; dependent integration and current gates; registered-base ancestry;
  named resources and ownership routing; future/cyclic task prerequisites;
  malformed/stale/failed reviews; failed/timeout/empty checks; exact receipt reuse
  and forced execution; environment identity changes; mutation, log/state
  corruption, partial receipts, missing state, concurrent subprocess registrations,
  and path escape/committed symlink rejection.
- **Command:** `python -m unittest discover -s tests -p test_phase_runtime.py`.
- **Result:** 158 tests passed in 177.662 seconds. Existing verification.py is
  unchanged and its legacy API remains covered.
- **Command:** `git diff --check`. **Result:** passed.

An earlier focused rerun rejected a receipt after this worker changed runtime
source while checks were active. Runtime identity invalidation worked as intended;
the final passing run held runtime source unchanged. Initial Windows Store Python
alias hashing failed because an execution alias cannot be read as executable bytes;
the runtime now binds that alias to the current interpreter's installed binary.

## Files Created/Modified

- `.ai/runtime/lib/pipeline.py`: runtime state, snapshots, routing and evidence gates.
- `.ai/runtime/phase.py`: pipeline verbs and agreed lazy evidence-module CLI wiring.
- `tests/test_parallel_pipeline.py`: real Git and subprocess regression fixtures.
- `.ai/maintenance/parallel-runtime-SUMMARY.md`: this output.

## Decisions Made

Kept all process execution in the deterministic runtime tester. Added pre-coding
routing and strict same-revision receipt reuse after coordinator clarification of
the approved scope. Windows Python aliases retain both launcher and binary identity.

## Deviations from Plan

No scope deviation. The maintenance PLAN has prose acceptance outcomes but no bare
acceptance or requirement IDs; metadata lists remain empty rather than invent IDs.
The evidence cache module is owned by the sibling worker; phase.py imports it
lazily and calls its agreed store/lookup/invalidate APIs through `--spec` JSON.

## Issues Encountered

Default shell execution was unavailable; scoped approved escalated commands ran
successfully. `rg` was unavailable; native PowerShell searches were used. Native
filesystem symlink privilege is absent; that one regression is skipped explicitly.

## Remaining

Coordinator integration must validate evidence CLI wiring with sibling commit
e415dab, run the repository aggregate and hooks on the final integrated revision,
and obtain fresh independent review/verification. Linux/Windows CI and final
correctness, security, documentation/integration and aggregate gates remain
separate. No publication or merge was performed by this worker.

Runtime snapshots and failed attempts intentionally have no automatic destructive
cleanup. A process killed during checks leaves a running attempt for coordinator
inspection instead of silently claiming success. Duration measurement is missing
because startup was not captured. No heavy engine, Docker or model benchmark ran.

## Known Stubs

None. Explicitly initialized empty collections are state containers, not product
placeholders. The adopting project's `.planning` skeleton and PR56 remain untouched.

## Next Phase Readiness

Coordinator can integrate this tested slice, reconcile required documentation with
the documented CLI, then run final verification and review before delivery. No
adoption STATE/ROADMAP/REQUIREMENTS updates are proposed for template maintenance.

## Self-Check: PASSED

All four assigned output paths exist; source/test verification passed as above.
The slice commit is restricted to the assigned worktree and branch, and its exact
hash is provided in the worker's completion response.
