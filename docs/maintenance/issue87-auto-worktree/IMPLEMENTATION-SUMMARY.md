---
phase: maintenance-issue87-auto-worktree
plan: "01"
subsystem: hooks
tags: [worktrees, prewrite, tdd]
status: partial
requirements-completed: []
acceptance: []
documentation: [.ai/references/same-agent-worktree.md]
coverage:
  - id: native-prewrite
    description: Same-agent native continuation through actual installed hooks and a SIMULATED host
    verification:
      - kind: integration
        ref: tests/test_same_agent_worktree.py#test_simulated_installed_denial_native_entry_defaults_and_fresh_rebuilt_edit
        status: pass
    human_judgment: false
---

# Issue 87 implementation receipt

The first Task 1 native-route RED was independently assessed VALID. Its two
review corrections were independently rechecked CLEAN and Task 2 was explicitly
released. The earlier Tasks 1-2 source checks passed, but the frozen independent
review at `ef325b62c0df6efcf603d72cfae55b8269a3052e` found three in-scope
blockers. Their bounded regression/fix assignment is now **source-complete /
live-unverified** with all affected deterministic checks GREEN. Historical or
current fixture GREEN is not full acceptance; corrected-source independent review
and integrated CI remain required. Documentation and all integration/publication
belong to separate owners. Current source correction assignment:

- Root: `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-native-code-05-185913375`.
- Branch: `phase-issue87-native-code-05-185913375`.
- Exact starting revision: `ef325b62c0df6efcf603d72cfae55b8269a3052e`.
- Authored paths are the exact owned source/test paths in this slice's Git diff,
  plus this summary. The four Task 3 documentation paths remain untouched.
- Context usage: unavailable.

The first Task 2 source slice was authored as
`b0e6b3d3191a02fff833b816e7713b79ed2090e4` from exact input
`d1d8d31a01b0b4c426d726f8e5975de9166c7a1f`, in isolated code-03, then integrated
and published by the coordinator as `ff81660b493305b5714c8efce9835ee4c2d128a0`.
The coordinator independently reran its native suite: 9 tests / 74.627s, exit 0.
The remaining Task 2 source slice was authored in code-04 as
`2b13757d441642a9ce9eafe976d0fa1d743433ae` from exact input
`ff81660b493305b5714c8efce9835ee4c2d128a0` and is preserved in the current input.
The code-05 correction does not modify any old worker checkout or disjoint leaf.

Test corrections were committed in `dcf73710d9557fc18b7ec8e8fa60cd09ce9594cd`
from input `5273cfd353fd46e3d1582d71c3fcbc5e58a3248e`, in isolated code-02.
The first native-route RED is preserved in `efa6da649b65585d939c1b88e2c369af327b2168`,
authored from `c58af6db4f41b0acc88c6ef1bb5f053d6f561c1b` in
`D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-native-code-01-174821869`,
branch `phase-issue87-native-code-01-174821869`. It is integrated in the current
input; no old branch or checkout was modified during this correction.

The previous cancellation RED remains historical evidence. Its input/root was
`26969d7184c2bf25a0468efe805b325471ea58c6`,
`phase-issue87-auto-code-171041844`,
`D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-auto-code-171041844`.

## TDD Evidence

### Frozen-review corrections and affected GREEN (code-05)

RED was committed as `c69aef9bd49dc732bab8e0c03a44790f00da9921` before any
production edits. The bounded production correction changes only
`.ai/runtime/lib/prewrite.py` and the four phase workflows named in this dispatch.
The native standalone adapter writes stdout protocol and stderr diagnostics as
explicit UTF-8 bytes. Input parsing and bounded UTF-8 Git facts were already
correct; no generic `paths.py`/`gitops.py` or fixture UTF-8 override repairs the
new legacy-codec regression. Creation still returns exactly one path line;
preservation-only removal returns no stdout path or deletion authority.

Each phase workflow now uses read-only locator facts for the conditional Claude
bootstrap/entry before its first session cd or destination init. Native callers
prove defaults, confirm Git, re-resolve destination runtime/locator and consume
fresh destination inputs; later open_session retains those facts without another
request or native entry. Ordinary consumers retain the existing shell route.
The new bounded instruction adapter consumes that installed ordering for all
four workflows in new and ordinary existing mode; it executes actual public
runtime calls/Git and labels host movement/context as SIMULATED. It preserves
the existing accumulated committed HEAD, immutable base and ownership checks;
the original ordinary phase/quick contract cases are also retained.

Failed target Git discovery now scans ancestor repository markers and accepts
only Git's recognized not-a-repository result with no such marker as the
nongit-note candidate. Corrupt metadata, ownership errors and indeterminate
results refuse without ticket/tree creation. A localized or unfamiliar discovery
diagnostic also refuses rather than expanding the OS-temp exemption.

Affected GREEN commands use the exact Python 3.13 executable shown in the earlier
receipt, followed by `-m unittest discover -s tests -p FILE -v`:

| FILE | Cases / seconds | Result / actual skips |
|---|---|---|
| `test_prewrite.py` | 24 / 60.514 | exit 0, skipped 1 (WinError 1314 symlink privilege); both-host malformed external repo refusal and legitimate note controls pass |
| `test_same_agent_worktree.py` | 11 / 148.402 | exit 0, no skips; actual installed legacy-codec create/remove protocol and all eight workflow/mode ordering cases pass |
| `test_workflow_links.py` | 4 / 1.725 | exit 0, no skips |
| `test_agent_sources.py` | 16 / 0.113 | exit 0, no skips |

The same Bash source/location/advisory command recorded below passed with exit 0:
source **12**, location **25**, unchanged advisory **60** checks, all with zero
failures. Installer/updater/session-delivery remain
the previous explicit GREEN receipts, not new executions at code-05; the bounded
correction assignment does not require repeating them absent a concrete concern.
Independent corrected-source/integration review and integrated CI remain with
the coordinator. Native actual host acceptance remains unverified.

No source stub, new threat identity, provider write or broad locale repair was
introduced. The advisory script, four Task 3 documents and generic locale helpers
have empty code-05 base diffs. `git diff --check` passed. The source correction is
the enclosing owned-path commit; its full hash is recorded in the metadata
follow-up after Git creates it.

### Frozen-review correction RED (code-05, 2026-10-15)

Production remains exactly `ef325b62c0df6efcf603d72cfae55b8269a3052e` for this
test-only slice. Only `tests/test_prewrite.py`,
`tests/test_same_agent_worktree.py` and this summary change before RED commit.
The assigned corrections preserve the generic locale helpers and all prior
history. Commands use the exact Python 3.13 executable recorded below:

```text
<python> -m unittest discover -s tests -p test_prewrite.py -k review_ -v
<python> -m unittest discover -s tests -p test_same_agent_worktree.py -k review_ -v
```

CR-03 real external OS-temp Git repository with deliberately malformed local
`.git/config`: 1 test / 1.546s, exit 1, two meaningful failures (Claude and
Codex). Actual standalone synchronous hook returned exit 0 with no decision;
the assertion was `'deny' != None: failed external Git discovery allowed a
repository target as an OS-temp note`. Setup's real Git discovery failed as
intended before invoking the actual source adapter. There are no new modules,
verbs or imports in this test.

CR-01/02 focused installed-native run: 2 tests / 50.963s, exit 1, nine meaningful
assertion failures, no errors/skips. CR-01 deliberately sets
PYTHONUTF8=0 and PYTHONIOENCODING=cp1252 for the actual installed creation provider
with a nonrepresentable Unicode configured root; binary UTF-8 input and real
creation/journal facts distinguish protocol failure after creation from setup.
CR-02 interprets the installed initialize/open_session ordering for all four
phase workflows, both new and ordinary existing mode, using actual locator,
primary-only request, native callback, Git confirmation and destination init.
Only native host state is SIMULATED; a prescribed shell cd never proves entry.
It retains accumulated existing HEAD, immutable base and session ownership.
CR-01 observed the actual created checkout, correct pinned HEAD and `created`
journal before the assertion `0 != 2: native provider created its checkout but
failed its UTF-8 path protocol: source-prewrite: 'charmap' codec can't encode
characters ... character maps to <undefined>`. CR-02 reached all eight workflow/
mode subcases: each new-mode initializer loaded primary inputs before native
entry (`destination initialization ran before native entry completed`), and each
existing mode reached actual `prewrite-root: bootstrap must run from the original
primary checkout` after the prescribed locator cd. No launcher, import, missing
verb or setup failure establishes these RED results. Native preservation
diagnostics and the failed subcases' downstream assertions remain unexecuted at
RED. The enclosing test-only commit preserves this evidence before any fix.

### Remaining Task 2 safety and regression slice (2026-10-15)

Exact input is `ff81660b493305b5714c8efce9835ee4c2d128a0` plus this owned diff.
The original native behavioral target remains GREEN in the final 9-test suite
(75.530s, exit 0, no skips). It now also exercises separate loaded-project and
permission-root drift and the pinned native existing-path refusal before the
genuine simulated approval. All movement/default-context assertions are still
explicitly **SIMULATED**; installed handlers and creation callbacks execute for
real against disposable offline Git repositories.

The additional helper suite initially passed 18 tests / 35.385s with one actual
Windows symlink-privilege skip. Four new lifecycle cases then reached meaningful
failures: a changed tool-use ID allocated another pending request; an absent
observed source actor was accepted after confirmation; an incomplete bound
journal raised KeyError instead of structured refusal; and HEAD advanced before
initial confirmation was accepted. That focused lifecycle run was 22 tests /
38.867s, exit 1, four assertion failures. Corrections reuse only unchanged
pending caller intent, require exact observed native actor, validate bounded
record shape and require initial HEAD at the pinned base. Confirmed native
sessions retain durable checks beyond the creation-ticket deadline. The final
helper suite is 23 tests / 57.603s, exit 0, skipped 1; real Windows hardlink,
junction and raw 8.3-alias refusals executed successfully. The symlink case alone
skipped because Windows returned WinError 1314 for creating a symlink.

Other helper controls cover all supported mutation envelopes and CRLF patches,
tracked/mixed/delete/move source classification, narrow both-host notes/reads,
malformed paths and JSON, linked/nested/external paths, CLI/environment identity
conflicts, changed targets, workflow modes, stale source HEAD/branch/config,
preexisting path/branch collisions, a real subprocess OS lock with bounded
contention/recovery, deadline refusal, and simulated missing Git results both
before and after actual creation. The latter preserve staged, unstaged,
untracked, ignored binary bytes and index facts; uncertain results neither
retry creation nor replay dirty-dependent intent. Runtime confirmation continues
to report `host_binding_verified: false`.

The full Ubuntu CI feedback at the first source revision exposed a real
multi-handler updater bug: the old merger selected one arbitrary managed script
and rejected the new advisory-plus-source group when its timeout aged. Local
`test_install_update.py -k an_aged -v` reproduced 4 cases / 15.295s, exit 1, with
two errors (Claude and Codex managed hook registration); both aged shipped-file
controls passed. The actual failure was `ValueError: managed PreToolUse
registration for worktree-guard.sh differs; reconcile it manually`, at the old
`.ai/install.py:622`. The merger now recognizes exact shipped handler commands
as a set and replaces only wholly managed groups under explicit update mode.
Both-host old advisory-only migration is idempotent, keeps user groups, and
restores exactly one advisory-first/source-second editing group. Mixed user
handlers, forged commands and unknown fields remain refused with bytes intact.
The final full updater receipt below includes both original failing cases.

The same CI job reported only a cleanup error for the otherwise passing Claude
prewrite fixture: `tempfile.py:947 -> _rmtree:929 -> shutil._rmtree_safe_fd:672 ->
os.rmdir`, `OSError [Errno 39] Directory not empty: 'pack'` (job
116703758682, run 38816902323; no complete temporary path printed). Disposable
installer source and prewrite target repositories now set the installed Git's
supported `gc.autoDetach=false` and `maintenance.autoDetach=false`, so maintenance
writers finish before fixture lifetime ends. No cleanup error is ignored or
retried. Local full installer validation includes that case; coordinator CI
readback remains necessary to assess recurrence on Ubuntu.

Native CLI adapters now enter their own bounded UTF-8 Git path directly rather
than first constructing the generic Workspace with its separate 30-second
lookup. Native-only I/O failure emits structured refusal. The old generic
Windows locale issue remains unchanged and is recorded under Deferred below.

### Matching native GREEN, first Task 2 source slice (2026-10-15)

Exact input is `d1d8d31a01b0b4c426d726f8e5975de9166c7a1f`, plus this
owned source/test slice. The same command and original RED target were retained:

```text
C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_same_agent_worktree.py -v
```

Final observed result for this slice: **exit 0, 9 tests in 67.904s, OK, no
skips/errors**. The original
`test_simulated_installed_denial_native_entry_defaults_and_fresh_rebuilt_edit`
now passes the full composed path: actual installed source denial/ticket (no
precreation), actual registered native creation callback at the pinned local
base/custom ignored root, real Git confirmation and narrow phase/quick adoption,
same **SIMULATED** actor/default destination context, relative fresh reads, one
rebuilt destination edit and later simulated-turn defaults. Primary staged,
unstaged, untracked and ignored binary bytes/index facts remain preserved.

Other executed cases cover actual coordinator/coder exports, installed CLAUDE
link and six workflow consumers; absent/incompatible simulated capabilities and
role/policy/trust refusal; native existing-name reuse/uncertain-result refusal;
old default cwd; old-root replay and wrong actor after confirmation; concurrent
same-ticket actual creation callbacks yielding one checkout; and the actual
registered WorktreeRemove provider preserving clean, ignored-only, dirty and
corrupt-receipt native candidates. Workflow entry executes without a fabricated
denial: new bootstrap/native creation/adoption and ordinary phase/quick sessions
with accumulated committed source work, immutable base/ownership, native path
approval, fresh reads, mode mismatch and ambiguous/missing metadata controls.

Earlier implementation attempts remain visible: the first run executed 6 tests
in 33.066s, exit 1, three failures (Windows native adoption root decoding and
fixture CRLF assumptions). The next 6-test run took 36.546s, exit 1; the original
native RED target and four other methods passed, while the workflow method's
three assertions exposed the ordinary session.open locale-path issue. Those
results were intermediate diagnostics, not final GREEN.

The narrow native path now uses its bounded UTF-8 Git facts and atomic session
registration instead of generic locale-decoded Workspace/Git helpers. The
ordinary-session fixture's runtime subprocesses explicitly set PYTHONUTF8=1;
generic paths.py/gitops.py were not changed or broadly repaired. Source fixture
`.gitattributes` marks source.txt `-text` so byte-preservation checks have an
explicit checkout contract under Windows autocrlf. The documented
CLAUDE_CODE_SESSION_ID is supplied as a fixture environment correlation matching
actual hook session_id; no agent-ID environment variable or skill-substitution
shell variable was invented. Optional CLI actor arguments remain claims.

Implemented source: one synchronous editing group (unchanged advisory first,
new 30-second source handler second); Claude-only coordinator/coder tool export;
standing source protocol and six native-first workflow routes; bounded strict
mutation/path classification; repo/actor/request/unit tickets under the common
Git directory with OS-released lock/atomic journal; explicit new/existing begin;
fresh-name-only native creation and preservation-only native removal; Git-only
confirmation and narrow phase/quick native adoption. Normal dispatch creation
reuse and ordinary session APIs retain their original routes. Codex primary
source cancellation reports the missing authenticated same-thread controller;
already-correct ordinary isolated callers need no movement.

This is conditional implementation plus SIMULATED contract evidence. No live
Claude native tool is exposed here; actual native identity, permissions, project
context and later-turn binding remain unverified. Runtime output explicitly
states `host_binding_verified: false`. No source-denial callback itself is
claimed to move its caller. No automatic stash/reset/clean/copy/replay is used.

The coordinator requested this meaningful-slice commit after the running native
check finished. Remaining Task 2 safety/regression work is listed below; this
slice does not mark the plan or issue complete.

### Independent native RED review corrections (Task 1, 2026-10-15)

- **Native review CR-01:** Existing ordinary phase/quick sessions can commit work
  beyond their immutable fork base. `SimulatedClaude.enter` now observes each
  existing destination's actual HEAD before native path entry; `prove_defaults`
  verifies that HEAD is preserved and the historical base remains its ancestor.
  New creation still requires HEAD at its pinned base. Both ordinary-session
  fixtures now commit distinct source content before their existing workflow
  request, assert HEAD differs from the recorded base, retain the exact base and
  session-ownership bytes, and require fresh destination reads to see those
  commits. No public runtime field, base rewrite or creation journal was added.
- **Native review CR-02:** `prewrite_pipeline` accepts an explicit environment
  override and passes it to every actual installed editing handler subprocess.
  The simulated host's common editing wrapper sets `CLAUDE_PROJECT_DIR` to the
  original primary checkout on every call, including the rebuilt destination
  edit. Native default-context checks still require destination cwd to differ
  from that anchored project root. Runtime and creation subprocess anchoring is
  retained; the editing aggregate no longer inherits an arbitrary project root.

Correction execution used exact input
`5273cfd353fd46e3d1582d71c3fcbc5e58a3248e` plus only the declared tests/summary.
The same native command recorded below ran 6 tests in 17.900s, exit 1, with the
same 8 intended assertion failures and no errors/skips. The named behavioral
target again reached the missing installed native continuation assertion with
`actual decision reasons=[]`; supporting failures remain missing native role
exports/protocol linkage. The original RED is unchanged in meaning.

The same `test_install.py -k prewrite -v` command recorded below ran 4 tests in
48.969s, exit 1, with the two expected historical source-denial failures and both
note tests passing their Claude/Codex create/update subcases. There were no
errors/skips. Both suites used separate disposable installed/Git fixtures.

The advanced ordinary-session fixture, native entry, destination rebuilt edit
and other downstream contract cases still have **not executed** past the absent
native contract. The editing subprocess environment override did execute on the
four installed source-attempt cases at RED; destination execution remains a
planned GREEN check. Neither these test corrections nor the RED receipt prove
live host binding. Review findings map to existing T-AW-03 and the T-AW-01
preservation aliases; they create no new threat identities or mitigation claims.

### Fresh native-route RED (Task 1, 2026-10-15)

The production revision remained exactly `c58af6db4f41b0acc88c6ef1bb5f053d6f561c1b`;
only the three paths above changed. The named behavioral target is
`NativeRouteTests.test_simulated_installed_denial_native_entry_defaults_and_fresh_rebuilt_edit`.
It launches the actual installed Claude editing aggregate before importing or
calling any proposed prewrite API. Expected: synchronous denial supplies an
actionable same-agent `EnterWorktree` instruction and ticket, with the original
edit unapplied and no precreated destination. Actual assertion:

```text
AssertionError: 'EnterWorktree' not found in '' : A1/A2: installed Claude source decision did not deliver a same-agent native EnterWorktree continuation; actual decision reasons=[]
```

Command (PowerShell, actual Python 3.13 executable):

```text
C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_same_agent_worktree.py -v
```

Initial run: exit 1, 6 tests in 17.153s, 8 assertion failures. Final native test
content rerun: exit 1, 6 tests in 16.889s, the same 8 assertion failures, no
errors/skips. Four cases reach the native continuation assertion above. The
export case reports two missing `EnterWorktree` role permissions and the absent
installed CLAUDE protocol link; the workflow case stops at the missing native
role permission. Those structural failures are supporting observations, not the
behavioral RED target. There were no missing-module, unknown-verb, discovery,
launcher or fixture errors. No production stub was added to produce RED.

The suite uses one real installer-produced Claude seed, then separate offline
real-Git clones with canonical ordinary temporary roots, spaces/Unicode, a
custom ignored worktree root and a pinned local commit. It reuses the installed
aggregate launcher/decision fixture. Its test-only `SimulatedClaude` adapter is
explicitly **SIMULATED**: stable actor, advertised creation/path schema fixture,
policy/trust/role gates and persistent default cwd/context/permission state.
After the missing continuation is implemented, the same behavioral target will
call public `prewrite.begin`, run the actual registered WorktreeCreate handler,
check real Git facts through `prewrite.confirm`, freshly read relative destination
content and execute exactly one rebuilt mutation. A later simulated turn checks
the retained destination default. These downstream steps have **not executed**
at RED, and no live model behavior, native entry, permissions or context binding
has been demonstrated.

Additional authored fixtures cover absent/incompatible advertised tool/schema,
pinned creation/policy/trust refusal, wrong actor/default cwd, missing native
completion, strict existing-name creation refusal, and primary staged/unstaged/
untracked/ignored binary preservation. The workflow fixture starts with
`prewrite.request` and no intercepted edit: known-unit new native creation and
adoption; ordinary phase/quick `session.open` sessions use genuine simulated
native path entry, approval and reused confirmation without a native-creation
journal or ownership rewrite. It includes explicit new/existing mismatch,
missing session and ambiguous real-session metadata controls. These are planned
GREEN coverage, currently blocked before their substantive assertions. Public
CLI fixture identity claims bind requests and do not authenticate host identity.

The old Claude installer test is renamed to
`test_prewrite_claude_first_source_tickets_without_precreating_and_cancels` and
expects one registered checkout after denial, followed by native instructions.
It no longer treats precreation as success. The historical name/results below
are retained as history, not a native movement claim.

### Historical cancellation RED (before the native-route plan)

RED ran against unchanged production at the input revision plus test-only edits.
Command (PowerShell; approved Python 3.13 executable):

```text
C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install.py -k prewrite -v
```

Observed: exit 1, 3 tests, 30.687s, two assertion failures and one passing control.

- `test_prewrite_claude_first_source_prepares_and_cancels_pending_mutation`:
  expected aggregate denial; observed `False`, assertion “S1/H1: installed Claude
  editing pipeline allowed the original source mutation”.
- `test_prewrite_codex_shared_parent_cancels_without_guessing_unit`: expected
  aggregate denial; observed `False`, assertion “S2/H1: installed Codex editing
  pipeline allowed an ambiguous shared-parent source mutation”.
- `test_prewrite_untracked_note_without_identity_warns_and_continues`: passed
  for both installed hosts, with advisory warning, fake note mutation and no
  extra registered checkout.

The fixture installs actual assets/settings from a committed disposable source,
commits a disposable offline target, launches every handler in its one editing
group (including actual Codex commandWindows), interprets synchronous native
denial/exit 2, and executes its fake pending mutation only when allowed. Both
target failures reached their behavioral assertion after successful launcher
execution. Missing modules/scripts/verbs, setup errors and hook exit 1 do not
establish this RED. GREEN and future helper coverage have not run.

## Matrix / expected decisions

Bounded independent RED review requested CR-01 and IN-01 before GREEN. A second
test-only run at `1414979` plus corrected tests used the same command above:
exit 1, 4 tests, 46.432s, the same two intended source denial assertion failures,
both note controls passing. Codex now supplies native `apply_patch` with
`tool_input.command` and complete Update File framing. New
`test_prewrite_external_temporary_note_without_identity_continues` exercises
actual fake create/update for both installed pipelines under a canonical plain
OS-temp directory outside every repository; it verifies fake bytes, unchanged
exact worktree listing and unchanged preparation inventory. No source changed.
CR-01 belongs to T-AW-01; IN-01 to T-AW-03. The allowed range is location based,
not extension/content based: resolved OS temp, outside every repository, plain
unlinked create/update only. Other paths, mixed operations, deletes, renames,
links and repository targets gain no exemption.

Independent input: [MATRIX.md](MATRIX.md), committed by its separate owner.
The following table preserves the earlier preparation-plan proposals; obsolete
precreation wording and proposed helper names are superseded by the committed
native PLAN/MATRIX and the fresh fixtures above. These rows are not current
execution claims or authority to replace native movement with preparation.

| Matrix | Named test family | Expected behavior |
|---|---|---|
| N1, CR-01 | installed `test_prewrite_untracked_note_without_identity_warns_and_continues`, `test_prewrite_external_temporary_note_without_identity_continues`; `test_notes_and_read_controls` | ordinary untracked nested notes and plain external OS-temp note create/update allow without identity; read does nothing |
| S1, H1 | installed `test_prewrite_claude_first_source_prepares_and_cancels_pending_mutation`; `test_native_tools_prepare_once` | exact denial; one committed-base destination; zero original mutation |
| S2 | installed `test_prewrite_codex_shared_parent_cancels_without_guessing_unit`; `test_identity_and_explicit_request_binding` | no shared-parent or missing-Claude-actor inference; explicit request mapping only |
| S3, V2 | `test_conflicting_and_stale_records` | reject ambiguous, mismatched, missing or drifted destination |
| M1, M2, M3 | `test_note_bypass_matrix` | whole mixed/tracked/delete/rename operation treated as source |
| P1, P2 | `test_path_and_link_matrix` | reject traversal/cross-root/linked/nested-repository targets; allow valid local path spellings |
| D1, D2 | `test_dirty_primary_snapshot_and_fresh_destination` | exact byte/index preservation; fresh reads, no dirty copy or replay |
| B1, V1 | `test_old_root_and_destination_continuation` | old root/marker remains denied; actual validated destination-local rebuilt call allows |
| B2 | `test_concurrent_and_uncertain_recovery` | exact deterministic reuse or actionable preserved refusal |
| I1 | `test_malformed_and_deadline_failures` | structural refusal and internal budget; wrapper exit 2; outer host failure stays a limitation |
| R1 | `test_notes_and_read_controls` | no creation/bookkeeping for reads |

## Checks / Task Commits

Final code-04 commands run from the exact root/base above, against this owned
diff. Python commands use the actual executable
`C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`;
every row below invokes it as `-m unittest discover -s tests -p FILE -v`.

| FILE | Cases / seconds | Result / actual skips |
|---|---|---|
| `test_same_agent_worktree.py` | 9 / 75.530 | exit 0, no skips |
| `test_prewrite.py` | 23 / 57.603 | exit 0, skipped 1 (Windows symlink creation privilege); hardlink/junction/raw 8.3 executed |
| `test_install.py` | 41 / 454.590 | exit 0, skipped 1 (Windows symlink creation privilege); original cleanup case passed |
| `test_install_update.py` | 66 / 415.745 | exit 0, skipped 4 (two symlink privilege cases, two Claude instances of Codex-only settings checks) |
| `test_session_delivery.py` | 60 / 127.942 | exit 0, no skips |
| `test_agent_sources.py` | 16 / 0.283 | exit 0, no skips |
| `test_workflow_links.py` | 4 / 1.675 | exit 0, no skips |

Actual Bash command (PowerShell, installed Git Bash; Python executable directory
prefixed to PATH and PYTHONUTF8=1 in this validation environment):

```text
& 'C:/Program Files/Git/bin/bash.exe' -c 'bash .ai/hooks/source-prewrite.test.sh && bash .ai/hooks/worktree-location.test.sh && bash .ai/hooks/worktree-guard.test.sh'
```

Exit 0: source prewrite **12 passed, 0 failed**; worktree location **25 passed,
0 failed**; unchanged advisory **60 passed, 0 failed**. The new source suite
checks actual synchronous deny JSON/exit 2, no precreation or old edit, note/read
controls, malformed input and an adapter failure mapped to blocking exit 2.
The location suite retains ordinary reuse controls and adds six reserved-native
preservation/refusal cases. The helper's actual process cwd now matches the
event cwd, so native missing-journal assertions reach that boundary directly.

| Current AW evidence | Executed layer |
|---|---|
| AW-01/05/08 | original installed tracer, later simulated defaults, fresh relative read/rebuilt edit, old-root/context/actor refusals |
| AW-02/06 | actual installed role/CLAUDE exports and six routes, positive simulated native schema/role/policy/trust gates and approval |
| AW-03/04 | both-host installed plain notes/source decisions, helper path/mutation/link matrix, exact dirty bytes/index preservation |
| AW-07 | fresh native creation, exact modes, real-Git collisions/concurrency, stale/changed/uncertain receipts, bounded locks/deadlines, preservation-only native remove |

The four Task 3 documents and advisory production script have empty base diffs.
`git diff --check` and exact owned-path/branch/base checks passed before
the enclosing source-ready commit. The separate migration test repair belongs
to the coordinator's disjoint leaf; it is not claimed as this worker's change.

### Historical Task 1 command receipts

Current Task 1 command receipts are recorded above. The exact final both-host
control command was:

```text
C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install.py -k prewrite -v
```

Final result: exit 1, 4 tests in 47.942s, 2 expected historical source-denial
failures and 2 passing controls; no errors/skips. Both
`test_prewrite_untracked_note_without_identity_warns_and_continues` and
`test_prewrite_external_temporary_note_without_identity_continues` pass their
Claude and Codex subcases. Each now exercises actual fake create **and** update
bytes without identity and asserts unchanged exact worktree listing and ticket
inventory; scratchpad controls also assert the advisory warning. The Claude
source case fails its old aggregate-denial assertion before the revised no-tree
expectation; the Codex case likewise fails its historical aggregate-denial
assertion. Neither is counted as the fresh native-route RED. A preceding run
before strengthening scratchpad create/update checks had the same 4-test,
2-failure result in 46.050s.

Only tests and this summary are in the first Task 1 commit and its bounded
review-correction commit. The final scoped diff is checked with
`git diff --check` before committing. The base diff for
`.ai/hooks/worktree-guard.sh` is empty: its advisory bytes remain unchanged.

## Threat Outcomes

| Owning PLAN / Threat | Canonical issue | Outcome | Git state | Evidence |
|---|---|---|---|---|
| [PLAN T-AW-01](PLAN.md#threat_model) | [T-AW-01](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | deterministic source mitigation implemented; corrected-source independent/integrated verification pending | OPEN per coordinator input; no worker readback/write | installed cancellation, both-host notes, strict path/mutation controls and dirty preservation GREEN; code-05 failed external Git discovery denies without bookkeeping; symlink privilege skip explicit |
| [PLAN T-AW-02](PLAN.md#threat_model) | [T-AW-02](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | deterministic source mitigation implemented; corrected-source independent/integrated verification pending | OPEN per coordinator input; no worker readback/write | native collision/reuse/concurrency, identity/lifecycle/lock preservation GREEN; code-05 actual standalone native output and preservation diagnostics pass under legacy codec |
| [PLAN T-AW-03](PLAN.md#threat_model) | [T-AW-03](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | conditional route implemented; live unverified | OPEN per coordinator input; no worker readback/write | installed exports/hooks/six workflows and SIMULATED tracer GREEN; all four phase initializers execute native-first new/existing ordering before destination init; actual same-agent host transition remains unverified |

## Remaining

The code-05 bounded source correction and all assigned affected checks are
complete. Independent corrected-source/doc/integration review and integrated CI
remain separate later assignments. Conditional target Claude
support is documented by the capability research; a live supported host/version
and actual same-existing-agent transition remain unverified in this executor.
Codex still lacks the authenticated same-thread controller. Hooks cannot guarantee
enforcement for outer failures, cloud orchestration, existing exec sessions,
opaque shell/external writers or opted-out specialized tools. No provider
writes, merge, installation or real cleanup performed.

## Deferred

Untracked follow-up outside the native path; issue linkage **Pending
coordinator**, with no promise of a new issue. The pre-existing generic Windows
locale/session.open failure was independently reproduced using the exact Python
3.13 executable above and a disposable offline committed Git repository at
`<OS-temp>/project café`, with ignored `worktree.root: .worktrees` and environment
`PYTHONUTF8=0`, `PYTHONIOENCODING=utf-8`:

```text
<python> <implementation-root>/.ai/runtime/phase.py query session.open quick legacy-encoding --no-sync
```

Actual exit **1**, stderr empty, stdout:

```json
{"ok":false,"error":"git rev-parse --git-dir failed: [WinError 267] The directory name is invalid","code":"git-failed"}
```

The generic `.ai/runtime/lib/paths.py:repo_root` and
`.ai/runtime/lib/gitops.py:git` use locale-decoded subprocess text; neither was
modified. Native adapters use explicit UTF-8 and bounded facts. Ordinary Unicode
session fixtures explicitly set PYTHONUTF8=1, so their GREEN does not claim this
generic issue was repaired. The reproduction printed no credentials and changed
only disposable fixture data.

## Self-Check: PASSED

Code-05 root/branch/input were verified before writes and commits. RED is
preserved in `c69aef9bd49dc732bab8e0c03a44790f00da9921`; every new failing
contract has matching affected-suite GREEN above. Exact changed paths stay
within the eight-path correction assignment, exclusions have empty base diffs,
and there are no intended deletions. No shared status or provider state changed.
Full source-fix and final metadata commit hashes are returned to the coordinator;
this self-check does not replace independent verification or native live proof.
