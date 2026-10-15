---
phase: issue87-maintenance
plan: cleanup
status: complete
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 4c35d27436add6867934c85eb9e853bd2fc3052e
requirements-completed: [ISSUE87-CLEANUP, ISSUE87-RED]
acceptance: [I87-A2, I87-A3]
documentation:
  - .ai/hooks/README.md
  - .ai/references/destructive-operations.md
  - .ai/commands/cleanup.md
  - .ai/workflows/cleanup.md
  - .agents/skills/cleanup/SKILL.md
  - .ai/commands/README.md
---

# Cleanup implementation evidence

Assigned root: `repo/.worktrees/issue87-cleanup-145722566`.
Branch: `phase-issue87-cleanup`. Guard parent tip and own-change boundary start:
`4c35d27436add6867934c85eb9e853bd2fc3052e`.

Guard implementation source is `e5af9bd16d6c81dbd161f952886808baf85b8a10`;
the parent above also contains its completed evidence summary. Child commits:
`c488678` initial RED, `d4ed3aa` expanded matrix/junction attempt,
`8ac55ee` corrected registered-junction RED. GREEN source commit:
`f277d8ae7c092c36eca8152eade12348881e39ef`. This subsequent summary-only commit
pins that identity; no source changed after the final checks. Own-change boundary:
`4c35d27436add6867934c85eb9e853bd2fc3052e..f277d8ae7c092c36eca8152eade12348881e39ef`;
the evidence-only tip adds this summary update. Working tree clean after GREEN,
no tracked deletions, and only the nine source paths plus owned plan/summary differ
from the parent.

## Accomplishments

The same source/installed-host hook exposes explicit cleanup-preview and
cleanup-apply subcommands. Preview uses shared guard evidence and the existing
session/wave/listing record formats, preserving open/unknown, unique unintegrated,
dirty/ignored/untracked, protected/current/primary, detached, locked and unowned
work. It disables optional Git index writes. Operations pin repository/common-dir,
branch/base OIDs, full ownership, provider remote/project/record/state/head and
backup payload digests. Raw Git registration paths are checked before canonical
resolution so Windows junctions cannot hide behind their referents.

Apply requires the complete deterministic snapshot/list and the actual human
approval text/reference, validates before mutation and again under a shared
Git-common-dir cleanup lock, consumes a single-use operational receipt, then
refreshes evidence and approval payload before every item. Worktree removal is
non-force; readback must prove absence before expected-OID local ref deletion.
Backups are separate exact entries under owned .workflow-backups roots, with
content hashes, ancestor/overlap/alias boundaries and bounded traversal. No
remote ref deletion, provider mutation, runtime manifest edit, merge or prune.
Partial failure stops later operations and returns fresh final target and
preserved-target state, including unknown readback.

Command and mirrored skill route to one workflow, which displays exact operations,
waits for a real new human reply and reports actual results. Docs distinguish
unchanged legacy cleanup contracts, backup classification, offline behavior,
approval provenance limits and concurrency limits. These feature gates do not
request repeated implementation authorization.

## TDD Evidence

RED: `python -m unittest discover -s tests -p test_destructive_guard.py -k cleanup -v`.
Exit 1, Ran 8 tests in 5.956s, 14 failing assertions, no errors or skips.
`test_cleanup_preview_is_readonly_and_lists_distinct_operations` expected explicit
worktree_remove and branch_delete rows; the existing hook instead returned its
normal malformed-payload refusal (no cleanup mode/schema). Apply/approval tests
likewise failed on the missing snapshot assertion, before attempting mutation.
Source and installed CLI test expected exit 0 but observed exit 2. Earlier first
run had two KeyErrors in assertion fallback; those were corrected before this
valid RED observation. Production source remains unchanged at this slice.

Fixtures are temporary Git repositories with offline GitHub/GitLab evidence.
No actual project cleanup, install, push, publication or merge ran.
RED commit: `c488678f5c75663b040cfd7e7aafa2f66a2f2921`.

Interim GREEN (uncommitted implementation): full destructive-guard suite passed
21 tests in 95.807s; actual registered installed-host hook test passed 1 test in
25.942s; advisory guard passed 60 checks. No skips. A final boundary inspection
found raw registered junction paths could be hidden by the parent's canonical
listing. Added cleanup-only regression before repair:
`python -m unittest discover -s tests -p test_destructive_guard.py -k raw_registered -v`
initially exited 1, Ran 1 test in 1.160s, `EvidenceError not raised`. Inspection
showed Git canonicalizes aliases during worktree add: that fixture did not
establish the intended raw-registration boundary. The first attempted repair's
22-test run therefore still failed that one assertion (102.019s). This is not
accepted as valid boundary RED/GREEN evidence.

Corrected fixture: move the already registered temporary directory within its
verified temporary root, then replace its original path with an actual Windows
junction. Remove the attempted raw-reader override and rerun the same focused
command before restoring it: exit 1, Ran 1 test in 1.083s, intended
`EvidenceError not raised` assertion. Parent grammar/ownership readers unchanged.
The corrected fixture passed with raw-reader repair (1 test in 0.507s).
Final GREEN/check table below covers the frozen implementation. No separate
refactor was needed.

## Checks

Python 3.13.14 and existing PyYAML 6.0.3; no installation. All deletion and
provider-matrix scenarios use disposable temporary repositories and injected
offline provider evidence. The initial CLI wiring fixture could attempt a
read-only gh lookup against a fake owner/repo because subprocess CLI mode cannot
inject a runner. This limitation was found and corrected: its origin now uses an
unsupported .invalid host, which reaches no provider subprocess. The corrected
CLI-only run passed 1 test in 2.783s; the final full suite uses that exact fixture.
No real cleanup/deletion, provider write, installation into a user's project,
push, publication or merge was performed by this worker.

| Check | Observed result |
|---|---|
| Full guard/cleanup suite before final test-only matrix expansion | Exit 0, 22 tests in 102.749s, zero skips |
| Expanded cleanup provider matrix | Exit 0, 1 test in 15.461s, zero skips; both-provider terminal/open/unknown, fork/mixed/missing/partial/recordless, valid complete pagination and closed/merged unique tips |
| `python -m unittest discover -s tests -p test_destructive_guard.py -v` final full guard/cleanup suite | Exit 0, 22 tests in 100.706s, zero skips; exact final offline CLI and expanded provider fixture revision |
| `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v` | Exit 0, 1 test in 25.951s, zero skips; actual Codex Windows and Claude Git Bash launchers, registered refusal, advisory scratchpads/dispatch |
| `C:/Program Files/Git/bin/bash.exe .ai/hooks/worktree-guard.test.sh` | Exit 0, 60 passed, 0 failed; unchanged advisory source |
| Installer render_asset trace for cleanup command/skill/workflow | Both host namespaces passed; identical source command/skill, installed workflow and hook paths |
| PyYAML maintenance frontmatter parse and required-field/path assertions | CONTEXT, CLEANUP-PLAN and CLEANUP-SUMMARY passed; pinned base, nine source paths, issue_refs and empty deletion scope verified |
| `git diff --check` | Exit 0 |

Acceptance I87-A2 is covered by the 14 cleanup tests, including exact-list
refusal, both-provider open-after-preview refusal, ownership/ref/content staleness,
lock preservation, per-item revalidation, readback, partial failure, consumed
receipt, ignored/unowned/detached preservation and actual Windows junctions.
I87-A3 has committed intended RED evidence before implementation and the corrected
junction RED before restoring that boundary repair. The 8 inherited guard tests
and installed/advisory checks preserve parent's behavior. Independent review and
final verification remain coordinator owned; this summary is worker evidence.

## Deviations

Reused the parent's strict shared Evidence/_ownership readers and existing
worktree/session/wave formats rather than calling worktrees.load_sessions or
load_manifest wrappers: those collapse malformed records into empty state.
No worktrees.py or provider adapter changed. Backups require an explicit opt-in
`backups` array in an eligible ownership record; absent/ambiguous ownership
preserves them. No runtime manifest is written to manufacture that ownership.
The fixture correction and its failed attempt are recorded above rather than
misrepresented as successful TDD evidence.

## Threat Outcomes

I87-C-T1 (alias parent I87-G-T2): exact identity/list/snapshot, required human
text/reference and stale evidence refusal mitigate the assigned approval boundary;
an envelope does not prove human provenance. I87-C-T2 (alias parent I87-G-T3):
common-dir locking, pre-item refresh, expected-OID compare-delete, non-force
removal, backup hashes/alias checks, consumption and truthful readback constrain
staleness and partial failure. Coordinator owns canonical issue95 linkage/readback
and independent acceptance; no risk closure is inferred.

## Remaining

No implementation blocker remains for the assigned child delta after checks pass.
Coordinator must propagate the independently reviewed parent guard repairs
(including malformed ownership-root handling), then perform independent child
review/verification before readiness. This worker did not pull, merge or duplicate
parent repairs. The own-change boundary remains the exact supplied parent above.

Provider availability is covered with offline fixtures; no live GitLab execution
is claimed. Enterprise-host/fork ambiguity and squash-merged unique work preserve.
Backup evidence is limited to 10,000 entries/100 MiB; approval/receipt reads to
1 MiB and receipt inventory to 10,000. Cross-provider/filesystem transactions
are unavailable; uncooperative processes can race inspection despite the shared
lock. A crash can leave a lock/consumed receipt requiring coordinator inspection.
No automatic stale-lock breaking, opaque-script sandbox or cryptographic proof
of human approval is claimed. Canonical parent risk linkage and draft94 updates
are coordinator owned. No real cleanup is authorized by these implementation tests.

## Independent review repair CR01 / CR02

Repair input: `4370fb18853cf842fbb40845da0c54c7cd1d0e6f` on the same assigned
branch/root. Ownership is limited to the child library/tests/summary, plus the
existing local-ref deletion sentence in destructive-operations.md. Parent guard
repair and synchronization are separate coordinator work; no parent pull/merge.

Observed RED before production repair:
`python -m unittest discover -s tests -p test_destructive_guard.py -k cleanup_review -v`
exited 1, Ran 9 tests in 53.006s, 5 intended assertion failures, zero errors/skips.
The unchanged library still made a symbolic candidate eligible; a same-OID
direct-to-symbolic swap retained approval and reported complete; mutation-time
aliasing deleted the disposable protected main referent; dangling alias readback
falsely reported absence; and nested-backup/two-worktree cleanup stopped partial
after its own first three removals. Expected results were preservation/refusal,
referent survival, truthful existing-alias state, and all five approved operations
completing with the ancestor group retained.

Passing controls in that same run: normal direct branch deletion, moved-OID
compare-delete refusal, real Git --no-deref deletion semantics and nested dirty/
provider-open/changed-owner drift. The latter has three independent disposable
subcases and must remain stale after the repair. Git is 2.49.0.windows.1;
`git update-ref --no-deref -d REF OLD_OID` actually removed a named symbolic probe
while preserving its protected referent, and removed a normal direct probe.

Fixture correction before accepted RED: the original second branch name sorted
before the backup owner, so it did not reproduce owner-first container drift.
Renamed it phase-z-other, preserving original provider records after local ref
removal. The corrected nested-only run had 2 tests/1 expected happy-path failure
in 35.887s; the complete nine-test run above is the accepted coherent evidence.
No production file changed for this RED matrix. RED commit:
`a357e507247ee1a818639f66f8a421f777cd94f1`. Independent matrix review accepted
both reproductions and requested a bounded additional control: introduce an
unrelated unowned backup sibling after the first owner's branch deletion and
require the next operation to stop before touching the second worktree. The
adjusted happy-path assertion also requires the retained group container in the
original preview and final readback. Dirty/provider/ownership controls now assert
the stale reason and absence of a second-tree mutation, preventing a fallback
command failure from masquerading as the freshness check.

Adjusted RED: same cleanup_review command, exit 1, Ran 10 tests in 51.215s,
5 intended assertion failures, zero errors/skips; all five control tests pass,
including the new unrelated-unowned-sibling control. The nested happy case now
fails at the stronger initial retained-container assertion. Production unchanged.
Adjusted RED commit: `02270a815740fcbe30bac55b1fd3b524053370a7`.
Prior completion statements above describe the original delivered slice; the
following evidence owns this repair's current result.

CR01 repair records direct/symbolic/missing identity of the exact named ref,
including dangling symbolic refs. Explicit symbolic-ref status 1 means "not
symbolic"; other failed evidence remains unknown. Direct candidate identity is
part of the pinned operation and is compared again immediately before mutation.
`git update-ref -d --no-deref REF EXPECTED_OID` binds deletion to the approved
name even if an external writer aliases it after that inspection. Actual Git
controls prove named aliases can be removed without deleting their referents,
while moved-OID refs survive. Readback uses exact identity rather than treating
for-each-ref omission of dangling aliases as absence.

CR02 repair lists each retained root-level backup container in preserved rows
unless that container is itself the exact owned backup removal target. Owning a
nested child grants no ancestor removal approval. The group's preserved row is
therefore stable before and after our own approved removals. The existing full
preserved-list and remaining-operation equality checks are unchanged; genuine
dirty/provider/ownership/unrelated-unowned-sibling changes still stop before the
second tree. The five-operation success case leaves the unapproved group and
reports it in final preserved readback.

| Repair check | Observed result |
|---|---|
| `python -m unittest discover -s tests -p test_destructive_guard.py -k cleanup_review -v` | Exit 0, 10 tests in 69.860s, zero skips; all attack/false-positive/drift controls passed |
| `python -m unittest discover -s tests -p test_destructive_guard.py -v` full repaired suite | Exit 0, 32 tests in 170.226s, zero skips; includes CLI/replay regressions and the accepted review matrix |
| `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v` | Exit 0, 1 test in 27.107s, zero skips; actual installed host launchers |
| `C:/Program Files/Git/bin/bash.exe .ai/hooks/worktree-guard.test.sh` after repair | Exit 0, 60 passed, 0 failed |
| `git diff --check` | Exit 0 |

The repair changes only the child library, tests and this SUMMARY plus the
specifically authorized existing local-ref deletion sentence in
destructive-operations.md. No hook registration, legacy runtime, RULES or parent
guard/parser/ownership function changed. All mutation scenarios are disposable
temporary Git repositories with offline evidence; no real cleanup/provider write.

Threat aliases remain the existing canonical
[I87-G-T2](https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t2)
for I87-C-T1 and
[I87-G-T3](https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t3)
for I87-C-T2. These repairs mitigate the reviewed identity/staleness paths; no new
risk issue or closure is inferred. Coordinator still owns parent propagation and
independent final child review after release. No parent pull/merge was attempted.

All assigned repair checks pass on frozen repair GREEN source
`1b5eb8a4ad3eb5c6026637be92687987042ff20a`. This subsequent SUMMARY-only commit
pins that identity; no production source changed after the full checks. Repair
own-change boundary is
`4370fb18853cf842fbb40845da0c54c7cd1d0e6f..1b5eb8a4ad3eb5c6026637be92687987042ff20a`;
it includes the observed RED/control commits above, library fix, narrow contract
sentence and evidence. The original full child boundary still begins at the
supplied guard parent `4c35d27436add6867934c85eb9e853bd2fc3052e`. Working tree
clean after GREEN, no tracked deletions. No source refactor was necessary.

## Coordinator canonical readback and final child review

Issue95 was read back OPEN with matching keys and aliases. The six-column PLAN
register now links I87-C-T1 to95#i87-g-t2 and I87-C-T2 to95#i87-g-t3.
Independent final correction review at e5cabcb178c141b2aa9167b6f8370d7c1531f9e8
found zero critical/warning/info findings. It verified direct reference identity,
non-dereferencing mutation/readback, nested five-operation completion and genuine
stale-state preservation. An additional retained-container probe preserved new
unowned content, consistent with the bounded contract.

The proposed child mitigation is locally checked and independently reviewed;
latest guard synchronization, final integrated checks and required CI are pending.
Issue95 stays OPEN; these unmerged changes grant no real cleanup or closure authority.

## Windows CI fixture portability correction

Input revision: `0f7cab53a7e29bcf221cf49e27080e8a72a0e55d`, including the
coordinator's canonical readback above. Prior provided CI run `38793499728`
reported Windows `Ran 659 tests in 1178.224s`, 1 failure, 39 errors and 2 skips.
The saved cleanup-ci-prior.log traces cleanup preview errors to
`_safe_path(repo_path)` / `EvidenceError: path-alias`, and CLI preview to expected
exit 0 versus actual refusal exit 2. The disposable fixtures constructed roots
from unnormalized TemporaryDirectory names. A Windows runner TEMP path can use
8.3 spelling while canonical resolution expands it, correctly triggering the
strict production alias check before the intended fixture behavior is exercised.

Correction is fixture-only: RegisteredGuardTests resolves its freshly created
temporary root; CleanupTests resolves one fresh temporary root and derives the
ordinary repo/worktree/approval/outside/detached/physical/second-tree paths from
it. Actual alias/junction operands remain raw. The raw registered worktree
junction is still formed after its normal fixture path exists and is still
expected to refuse. No production policy, hook, CLI, command or cleanup semantics
changed. This uses the observed CI failure as regression evidence; no fabricated
new RED cycle is claimed.

| Portability check | Observed result |
|---|---|
| `python -m unittest discover -s tests -p test_destructive_guard.py -v` full child suite | Exit 0, 32 tests in 173.763s, zero skips; includes actual raw-registration junction refusal |
| `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v` | Exit 0, 1 test in 24.818s, zero skips |
| Real Win32 8.3 TEMP probe | Exit 0, 3 tests in 5.544s, zero skips; primary-switch guard, read-only preview and real raw-registration junction rejection pass with tempfile.tempdir set to an actual GetShortPathNameW spelling |
| Strict production control within that probe | The unchanged `_safe_path` still rejects that actual raw short spelling as path-alias |
| `git diff --check` | Exit 0 |

The focused short-TEMP probe uses a freshly created disposable root, obtains its
real Windows short spelling, restores tempfile.tempdir afterward, and preserves
the actual junction operand in the protection test. No string-only alias mock is
used. Hosted CI rerun and parent integration remain coordinator-owned; these
local checks do not claim the hosted 659-test suite is green. No parent sync,
real cleanup, provider write, installation or publication was performed here.
