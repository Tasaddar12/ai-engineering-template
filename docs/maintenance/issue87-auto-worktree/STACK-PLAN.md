# PR97 bounded native/planning stack reconciliation

This is the execution/dependency record for PLAN Task 4. Same-agent maintenance
acceptance, conditional Claude support, note boundaries, essential native lifetime
preservation and the unverified live-host requirement are unchanged. The user
authorized preserving prior work through distinct adjustments/stacked drafts.
Coordinator dependency reconciliation is routine work under that authorization;
no new human approval, PR merge or frozen-head rewrite is requested.

## Pinned inputs and ownership

| Input | Exact revision / status |
|---|---|
| Preparation root | issue87-native-stack-plan-190605907, branch phase-issue87-native-stack-plan-190605907, clean base 92a221241a2e0bf191fccd981f944c1862029288 |
| Frozen PR93 parent | 47593a3d3f71739bd146a6c2c3590798d7c73c2e; already depends on frozen PR92 |
| Frozen PR92 ancestor | d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6 |
| Native review | ef325b62c0df6efcf603d72cfae55b8269a3052e; REVIEW-01 and VERIFICATION report gaps, not acceptance |
| Current correction prerequisite | Code-05 owns CR-01 UTF-8 native output, CR-02 four complete workflow orderings, CR-03 failed external Git discovery. Integrate its committed corrections first; do not inspect/edit its active checkout. DOC-01 correction is already in preparation base. |
| Original-six local composition baseline | e464c73dd0ae8dc0a139faee0144917b04029ead; not a dependency to merge into PR97 |
| Disposable combined prototype | 9060df58033452483961d9eb1d7113cca10b0b4a in issue87-native-composition-190322437; local-only composition, not a publication branch or final GREEN |

Task 4 worker owns exactly .ai/runtime/phase.py, .ai/install.py, .ai/RULES.md
(Hooks and validation only), .ai/hooks/README.md, tests/test_same_agent_worktree.py
and tests/test_install.py, plus its own STACK-SUMMARY.md in this maintenance
directory. No new test file or harness is required. Frozen dependency helpers and
tests are consumed, not rewritten. All overlapping source/doc workers finish and
their commits integrate before Task 4 dispatch. Coordinator owns local merges,
conflict materialization, actual PR base change, frozen-head checks and publication.

## Concrete incompatibility and narrow interface

Inspected native phase.py passes workspace=None for native adapters to avoid
generic locale-sensitive root discovery and an extra lookup outside their bounded
deadline. Frozen PR93 run_verb snapshots canonical records unconditionally after
handler lookup; planning_integrity.snapshot reads workspace.root. Textually keeping
both produces snapshot(None), so merely resolving imports does not preserve the
two behaviors. Imports, registration and exception payloads also overlap.

The coordinator's installed test on disposable9060 reached a real native denial
and ticket, then failed its no-Traceback assertion when installed prewrite.begin
called run_verb line91 -> planning_integrity.snapshot(None) line231 -> AttributeError
NoneType.root. Reported command: Python3.13 -m unittest discover -s tests -p
test_same_agent_worktree.py -k
simulated_installed_denial_native_entry_defaults_and_fresh_rebuilt_edit -v.
Reported result: one test, 15.981s, exit1, named assertion failure. This is the
coordinator's joined regression receipt, not a test run by this preparer; its
COMPOSITION record will hold the exact executable/working-root/revision output.
Other prototype checks still running are not claimed passed.

Task 4 must preserve that evidence and obtain the same behavioral RED on the
intended corrected97 plus frozen93 join before its compatibility fix. Add targeted
test-only assertions/commit before changing adapter behavior. A missing import,
failed install or test setup crash cannot replace the installed native failure.

The sufficient fix is a handler-validated exact exception for the currently
registered prewrite.request, prewrite.begin and prewrite.confirm. Only these use
their own bounded native workspace discovery and skip canonical snapshot/warnings:
they mutate Git-common-dir journal/session metadata, not canonical .planning
records. Use the same exact set in main workspace selection and native OSError
handling; unknown prewrite-prefixed names must be rejected as unknown, not inherit
the exception. All ordinary PR93 registered-verb snapshot/mutation_warnings and
success/error integrity_warnings behavior remain. Keep planning.integrity,
canonical schema validation, commit-byte checks, initializer routing and authored
record safeguards; do not replace them with a global bypass or make snapshot
silently accept arbitrary None workspaces. Preserve native structured OSError
results and VerbError warnings in the joined exception path.

## Four shared-file union and scope fence

- phase.py: retain planning_integrity and prewrite imports/verbs, exact adapter
  exception, ordinary warnings and native structured errors.
- install.py: union destructive Python, planning shell and native source hooks;
  retain one editing group with advisory first/source second and preserved user
  hooks. Timeout precedence: .py120, source-prewrite.sh30, other managed scripts10;
  host-specific creation/removal timeouts remain unchanged. Python entries retain
  Python/runpy commandWindows support; shell entries retain Git Bash/status and
  Unicode behavior. Registration identity is event/matcher/script, not raw group
  count; intentional advisory dispatch/edit entries remain distinct.
- RULES Hooks and validation and hooks README: preserve destructive/planning
  controls together with conditional native behavior, Python entrypoints/adapters,
  notes and simulation/live limits. Do not copy PR91 guard-workflow or PR94 cleanup
  introductions from prototype9060; use frozen93 and corrected97 as union owners.
- No cleanup expansion, no new lifecycle mechanism, no policy weakening to excuse
  a code defect. Essential native preservation remains as already approved.

## Stack and own-change boundary

After independent plan approval and integration of code-05 corrections, coordinator
locally merges the exact frozen PR93 tip into the PR97 branch without rewriting
history. Materialize only the necessary two-owner conflict union, then dispatch
Task 4 for the proven interface repair. Do not merge prototype9060 or original-six
baselinee464 into PR97. Do not change PR93/92 heads, or PR89/91/94/88 heads/bases.

The intended stack is PR92 -> PR93 -> PR97. Only after checked plan, integrated
corrections, Task 4 checks and review does coordinator change PR97's actual target
to PR93's existing branch. Its own-change boundary is frozen93..final97, so review
the PR diff for native97 work and necessary join only. Imported93/92 work remains
their dependency history, not new PR97 edits. Record exact parent branch/tip,
final97 tip, Target, DependsOn and OwnChangeBoundary in the draft under canonical
Git workflow. This plan is no provider edit and no PR merge authorization.

## Required checks, review and composition

Task 4's executable commands/failure signals are in PLAN. Existing native suite
must cover request/begin/confirm, new and existing ordinary phase/quick sessions,
unknown prewrite names and native errors. Installed planning and runtime-verb
tests, full managed update suite, imported planning integrity suite, ordinary
phase-runtime and session suites must pass on the joined revision. Cover malformed
canonical planning commit refusal, real index preservation, authored-record
sentinels and ordinary success/error warnings. No blanket constant relaxation,
new benchmark or replacement mock-only harness is sufficient.

After all native corrections and Task 4 integrate, obtain fresh independent source
and integration review plus narrow shared-doc verification. Then coordinator
builds a new disposable local composition of the final native97 tip with all six
original frozen heads, using e464's provenance and explicit resolutions. Verify
all frozen tips remain exact, inspect the combined tree for lost controls, run the
focused native/install/planning/session checks and the existing configured
original-six checks recorded by that composition's owner, and obtain independent
composition review. Record actual input tips, conflicts, commands/results and
remaining gaps; no earlier six-only evidence or prototype RED is final97 GREEN.
Do not publish this composition branch or alter any original draft. Failed actual
preservation/composition behavior requires an in-scope repair, not deferral or a
passing label. Live native same-agent movement remains separately unverified.
