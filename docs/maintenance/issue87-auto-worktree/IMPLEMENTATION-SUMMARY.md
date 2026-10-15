---
phase: maintenance-issue87-auto-worktree
plan: "01"
subsystem: hooks
tags: [worktrees, prewrite, tdd]
status: blocked
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
released. Task 2 is now **in progress**: this meaningful native source slice is
committed for coordinator integration/publication, with remaining safety checks
and full regression work still required. Frontmatter remains blocked because
the assigned plan is unfinished. Task 3 documentation and all integration/
publication belong to separate owners. Current source-slice assignment:

- Root: `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-native-code-03-180817570`.
- Branch: `phase-issue87-native-code-03-180817570`.
- Exact starting revision: `d1d8d31a01b0b4c426d726f8e5975de9166c7a1f`.
- Authored paths are the exact owned source/test paths in this slice's Git diff,
  plus this summary. The four Task 3 documentation paths remain untouched.
- Context usage: unavailable.

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
| [PLAN T-AW-01](PLAN.md#threat_model) | [T-AW-01](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | partial implementation; not finally verified | OPEN per coordinator input; no worker readback | composed source cancellation/dirty preservation GREEN; helper/path matrix and full regressions remain |
| [PLAN T-AW-02](PLAN.md#threat_model) | [T-AW-02](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | partial implementation; not finally verified | OPEN per coordinator input; no worker readback | ticketed creation reuse/concurrency/uncertain-result controls GREEN; additional failure/identity checks remain |
| [PLAN T-AW-03](PLAN.md#threat_model) | [T-AW-03](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | conditional route implemented; live unverified | OPEN per coordinator input; no worker readback | matching SIMULATED native tracer GREEN; actual same-agent host transition remains unverified |

## Remaining

Task 2 remains in progress at the coordinator's requested meaningful-slice
integration boundary; no new human approval is required to resume its existing
authorization. Next source assignment must finish focused helper/path/link/
mutation/identity/deadline/stale-request/before-and-after-creation failure cases,
including dirty-dependent intent and legitimate isolated controls; add the new
test_prewrite.py and source-prewrite.test.sh suites and extend ordinary location
regressions as needed. Inspect journal tamper/corrupt/changed-target handling and
unknown outcomes without duplicate creation or data loss. Run every PLAN check:
native, prewrite, install, install_update, session_delivery, agent_sources,
workflow_links, Bash source-prewrite/location/advisory suites. Only the native
suite has final GREEN for this source slice; the full source implementation is
not finally verified and remaining case gaps are not waived. The advisory script
base diff remains empty, and git diff --check passes for this slice. Task 3 and
independent final source/doc/integration review and CI remain separate later
assignments. Conditional target Claude
support is documented by the capability research; a live supported host/version
and actual same-existing-agent transition remain unverified in this executor.
Codex still lacks the authenticated same-thread controller. Hooks cannot guarantee
enforcement for outer failures, cloud orchestration, existing exec sessions,
opaque shell/external writers or opted-out specialized tools. No provider
writes, merge, installation or real cleanup performed.
