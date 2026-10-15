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
`8ac55ee` corrected registered-junction RED. The GREEN commit is the subsequent
implementation commit; its exact identity will be recorded after creation.

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
