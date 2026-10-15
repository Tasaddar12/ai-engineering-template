---
phase: maintenance-issue87-auto-worktree
plan: "01"
type: tdd
wave: 1
depends_on: []
autonomous: true
requirements: [ISSUE87]
acceptance: [AW-01, AW-02, AW-03, AW-04, AW-05, AW-06, AW-07, AW-08]
files_modified:
  - .ai/hooks/source-prewrite.sh
  - .ai/hooks/source-prewrite.test.sh
  - .ai/runtime/lib/prewrite.py
  - .ai/runtime/lib/worktrees.py
  - .ai/runtime/phase.py
  - .ai/install.py
  - tests/test_prewrite.py
  - tests/test_install.py
  - tests/test_install_update.py
  - .ai/hooks/README.md
  - .ai/references/worktree-sessions.md
  - .ai/runtime/README.md
files_deleted: []
documentation:
  - .ai/hooks/README.md
  - .ai/references/worktree-sessions.md
  - .ai/runtime/README.md
resources: [issue87-source-worker-checkout, issue87-disposable-git-fixtures]
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_prewrite.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_session_delivery.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install_update.py, -v]
  - [bash, .ai/hooks/source-prewrite.test.sh]
  - [bash, .ai/hooks/worktree-guard.test.sh]
  - [bash, .ai/hooks/worktree-location.test.sh]
user_setup: []
must_haves:
  truths:
    - A first source edit with a trustworthy actor/unit identity prepares or selects one isolated checkout and cancels the original mutation; ambiguous identity cancels with explicit coordinator preparation instructions.
    - Repeated and concurrent attempts for the same repository, host and actor/unit reuse the same validated unit without primary synchronization or additional checkouts.
    - The session must explicitly enter the selected root and reread destination files before rebuilding its mutation; creation never counts as host binding.
    - Ordinary untracked scratchpad create/update operations warn and continue without preparation, including when session identity is absent.
    - All existing primary tracked, staged, untracked and ignored bytes and index state survive preparation, failed preparation and retries.
    - Malformed or ambiguous source requests and stale or cross-root targets cannot become successful old-root edits through the supported hook.
    - Both actual installed host hook pipelines exercise the new component while the existing advisory script stays byte-identical.
  artifacts:
    - path: .ai/runtime/lib/prewrite.py
      provides: Strict classification, session-keyed preparation journal, Git validation, and native host cancellation adapter.
    - path: .ai/hooks/source-prewrite.sh
      provides: Registered stdin-preserving launcher for the selected host adapter.
    - path: tests/test_prewrite.py
      provides: Disposable real-Git preservation, reuse, recovery, path and concurrency evidence.
    - path: .ai/hooks/source-prewrite.test.sh
      provides: Native hook input, cancellation and allowed-note fixture behavior.
    - path: .ai/references/worktree-sessions.md
      provides: Actionable host/coordinator continuation and explicit supported-host evidence gate.
  key_links:
    - from: .ai/install.py hook_settings(host)
      to: .ai/hooks/source-prewrite.sh
      via: Second handler of the existing editing-tool PreToolUse group, after the advisory handler.
    - from: .ai/hooks/source-prewrite.sh
      to: .ai/runtime/lib/prewrite.py handle_event
      via: Explicit installed host argument and original stdin, without shell interpolation of payload fields.
    - from: .ai/runtime/lib/prewrite.py prepare
      to: .ai/runtime/lib/worktrees.py open_session
      via: Explicit full committed base, sync=False, deterministic request identity and validated matching unit.
    - from: Hook cancellation reason
      to: .ai/references/worktree-sessions.md source-prewrite continuation
      via: Exact selected root, branch, base and preparation key, with instructions to enter, reread and rebuild.
---

<objective>
Deliver one source-sensitive prewrite preparation and handoff feature. A first
source edit with trustworthy actor/unit identity can create/select isolation once, then cancels
the old-root edit and routes continuation into an explicit host/coordinator root
handoff. It must not become another repeated hard-halt loop.

This maintenance plan is kept outside the unfilled adoption skeleton. ISSUE87 is
the maintenance issue identifier, not an invented adopting-project requirement.
The assigned PLAN.md filename is an explicit maintenance exception to phase-local
numbering. It is not registered as an adoption phase.

The deliverable can establish automatic **checkout preparation**. No trustworthy
installed Codex/Claude release or live same-session transition is available here.
Automatic **session entry** remains unproven: neither documented pretool response
binds cwd/session, and updatedInput only replaces input. Never rewrite the pending
mutation's paths, replace it with a purported native tool call, or advertise full
automatic context switching without the separate live proof below. A remaining
manual/native handoff is an explicit limitation, not a passed end-to-end claim.
Codex PreToolUse documents only the parent's session_id for subagents, so an
unbound Codex actor cannot safely receive a session-only automatic checkout.
This is a second explicit partial-support limit: Codex requires a coordinator's
per-request named-unit preparation, while a present valid Claude agent_id can
distinguish actor-local automatic preparation. An absent Claude agent_id is
insufficient to distinguish a coordinator from a missing field: it also takes
the explicit coordinator route. Both hosts still cancel unbound
source mutation attempts through their registered pipeline.
</objective>

<execution_context>
@.ai/agents/coder.md
@.ai/templates/summary.md
@.ai/references/methods/tdd.md
@.ai/runtime/TEMPLATE-CONTRACT.md
</execution_context>

<context>
@docs/maintenance/issue87-auto-worktree/CONTEXT.md
@docs/maintenance/issue87-auto-worktree/RESEARCH.md
@AGENTS.md
@.ai/RULES.md
@.ai/references/worktree-sessions.md
@.ai/references/git-workflow.md

Input revision: e87f49debbd64daf25157da0b693d328ad3dd531. Research inspected
77b5668f2003bea60127d87e8785469286abafb3; the consumed definitions below were
inspected again at this plan's input revision. Preparation authoring runs only in
the assigned phase-issue87-auto-plan-164901267 worktree. Implementation, tests,
integration and publication belong to separately dispatched owners.

Decision aliases used here refer to the existing CONTEXT bullets, without
inventing new user replies: D-01 = separate draft, never merge; D-02 = source/note
distinction and scratchpad warnings without retry loop; D-03 = preserve dirty
state and prevent old-root writes after claimed handoff; D-04 = six frozen drafts,
73/74, live infrastructure, installation and cleanup excluded. The latest actual
user constraints recorded by the coordinator satisfy the discussion prerequisite.
No extra approval is needed at internal preparation transitions.

Granularity: Standard. One feature, one TDD plan, three sequential tasks. Task 1
produces independent behavioral expectations; Task 2 consumes its real RED and
implements the complete hook-to-Git-to-cancellation slice; Task 3 consumes the
implementation and receipts to document truthful continuation. Same source worker
may own Tasks 1-2; coordinator assigns Task 3's exact documentation paths to a
doc-writer after integration. No concurrent writers share these paths.
</context>

## Acceptance and scope

| ID | Observable acceptance | Producer / evidence |
|---|---|---|
| AW-01 | Primary source mutation with trustworthy actor/unit identity prepares exactly one checkout from local committed HEAD, or reuses the explicitly selected valid unit; original mutation is cancelled. Codex parent-only identity cancels with explicit preparation route and no inferred unit. | Task 2; real-Git and installed-pipeline fixtures |
| AW-02 | Deterministic identity, explicit binding precedence, concurrency and uncertain-outcome recovery prevent selection of another unit and duplicate checkout creation. | Task 2; distinct-session, race and timeout fixtures |
| AW-03 | Scratchpad-only create/update remains warning/continue without identity or worktree creation; delivered records and mixed operations are source. | Tasks 1-2; false-positive fixtures plus old advisory suite |
| AW-04 | Existing tracked/staged/untracked/ignored bytes, primary branch/HEAD and index are unchanged; no fetch, primary sync, stash, reset, clean or bulk copy. | Tasks 1-2; full preservation snapshots and offline fixtures |
| AW-05 | Strict input/path handling refuses unsupported or ambiguous source mutations, stale paths, cross-checkout requests and unsafe note exceptions. | Tasks 1-2; independent bypass matrix |
| AW-06 | Both installed hosts run the new component in their existing editing group; advisory handler remains first and its script is byte-identical. | Tasks 1-2; actual installed-launcher aggregate fixtures and upgrade tests |
| AW-07 | Cancellation supplies a concrete continuation; real destination Git facts, fresh reads and rebuilt edits are required. Remaining unsupported native transition is reported explicitly. | Tasks 2-3; fixture flow plus documentation review |
| AW-08 | Test-only RED precedes fixes, same target passes GREEN, independent reviews assess preservation/bypasses, and live-host proof is distinguished from fixtures. | Tasks 1-3; TDD receipts, independent review and live evidence gate |

Excluded: editing `.planning/` adoption records; changing old
`.ai/hooks/worktree-guard.sh` bytes; six other drafts; provider 73/74; provider
changes by workers; live infrastructure, installing/upgrading a host, cleanup,
merges; arbitrary shell-command parsing; external writers; existing exec-session
input; specialized tools that do not run these hooks; a universal sandbox; a
general workflow engine; automatic dirty-content migration or copying. New
preparation metadata and a newly created worktree are expected additions; no
existing ignored primary files may be rewritten or removed.

## Inspected producer/consumer map

| Existing owner / entrypoint | Proposed connection and exact owned path |
|---|---|
| `.ai/install.py:430-468` MANAGED_HOOKS/HOST_HOOKS and `hook_settings(host)` | Keep the one editing matcher group; append `.ai/hooks/source-prewrite.sh` after the existing advisory handler, passing the explicit host. Include the new script in managed installation/update ownership. Preserve unrelated user hooks. |
| `.ai/hooks/worktree-guard.sh:147-262` file-tool advisory | Unchanged reference consumer. Keep warning behavior and its existing tests; new component handles source preparation separately. |
| `.ai/hooks/worktree-location.sh:91-112` Claude WorktreeCreate | Read-only dependency; still a location hook, not an arbitrary edit trigger or session registration. Do not edit it. |
| `.ai/runtime/lib/worktrees.py:71-115,621-653,747-832` | Reuse common_dir, worktree_root, listing, load_sessions, open_session/put_session. Add only deterministic request identity support necessary for crash recovery; preserve ordinary open_session defaults. Do not rely on session_for's first-match/missing-entry mutation as proof of safe reuse. |
| `.ai/runtime/phase.py` `verb_session_open` and verb registry | Add only `prewrite.prepare`, delegating to `lib.prewrite.prepare`; existing session.open keeps its existing default sync semantics. |
| `.ai/hooks/lib/handoff-io.sh` Python probe/native-path pattern | Read-only pattern; source-prewrite launcher has a strict failure/cancellation contract and must not inherit this helper's fail-open behavior. |
| `tests/test_session_delivery.py` SessionCase/SessionLifecycle/PhaseLocate | Read-only disposable-repository/subprocess pattern and regression command. New feature cases live in `tests/test_prewrite.py`. |
| `tests/test_install.py:666-733` installed launcher and scratchpad cases | Extend the actual generated host settings pipeline; retain exactly one matching editing group and advisory first. New note case must work with no session_id. |
| `.ai/references/worktree-sessions.md:68-102` explicit root transition | Add one source-prewrite continuation section to this existing shared routing reference; no new workflow/skill/command catalog. |

## Bounded contract

`lib.prewrite.prepare(workspace, host, session_id, agent_id=None, tool_use_id=None,
kind=None, label=None, base=None)` is shared by the hook and one runtime verb:
`phase.py query prewrite.prepare --host <codex|claude> --session-id <opaque-id>`.
An optional explicit unit uses both `--kind <existing-session-kind>` and
`--label <unit>` plus `--base <full-commit-id>`; partial selection is an error.
For Codex and Claude events lacking a valid agent_id, all of that explicit unit
selection plus the captured `--tool-use-id` is required, binding only that request
to the named unit. For Claude subagents include `--agent-id`. Do not create a
Codex unit from session_id alone, even when just one session exists. A missing
tool_use_id in the explicit route cancels with the existing named session.open
route using --base and --no-sync, followed by isolated dispatch/entry; it never
authorizes inventing a request identity.
The runtime emits its usual JSON result. Direct hook execution uses
`source-prewrite.sh --host <codex|claude>`, reads the native event on stdin, and
invokes `lib/prewrite.py`'s hook adapter from that installed runtime. Keep host
output serialization separate from runtime JSON envelopes. Do not pass raw tool
arguments through shell interpolation or evaluate payload strings.

**Identity and automatic unit:** trust only the installed registration's explicit
host, the native nonempty bounded string session_id, actual process cwd/Git facts,
and the repository's existing runtime bookkeeping. A payload cwd must resolve to
the actual process root/subdirectory; a disagreement is not permission to operate
there. Canonicalize the Git common directory using filesystem identity rules.
Claude with a present valid agent_id hashes `(canonical common directory, host,
exact opaque session_id, agent_id)` with SHA-256 for a filesystem-safe preparation key.
Codex explicit preparation additionally binds the captured tool_use_id to the
coordinator-selected kind/label; the unit identity, not changing request IDs,
determines checkout reuse. Never scrub session IDs
into colliding filenames. Do not use transcript contents, prompt text, tool paths,
current branch name or newest session to infer a work unit.

A previously explicit, valid actor/request mapping takes precedence. For Claude
only, when its documented native actor identity is available, otherwise
derive `kind=quick`, `label=auto-<full-preparation-key>` and capture the calling
checkout's full local `HEAD^{commit}` before creation. This is a technical
session-local work identity, not a guessed phase or a new planning record. Create
with that explicit base and `sync=False`; no origin/remote assumption or network
call. Codex PreToolUse has session_id, cwd, hook_event_name, tool_name, tool_input,
tool_use_id and turn_id, but its subagents share the parent session_id and no actor
field is documented. Neither turn_id nor tool_use_id establishes exclusive work
ownership; do not invent such a use. An unbound Codex event therefore cancels
without creation and gives the coordinator the captured request identity for one
explicit prepare-and-handoff operation. The coordinator names the work unit under
existing authorization; it must not resubmit the denied edit in the old root.
Claude includes agent_id for subagents; root/coordinator events may omit it, but
absence alone cannot distinguish a real coordinator from a missing/malformed
identity field. Only a present valid native actor ID enables unbound automatic
creation; otherwise require the explicit named-unit/request route. Validate its
type when present. Missing session identity, ambiguous/mismatched explicit mappings, unsupported
host or unavailable Git/commit cannot auto-create. Cancel the source call with
the exact missing fact and the one-time coordinator preparation/entry instruction.
Note-only calls do not require this identity.

**Storage and idempotence:** keep only the key, source repository/root, host/unit,
full base, selected branch/root and preparation state under
`common_dir/ai-phase/prewrite/<key>.json`; no source payloads or transcript text.
Use an OS-released exclusive repository-level preparation lock with at most one second wait,
then atomic journal writes. Recheck mapping and Git registration after acquiring
the lock. Journal deterministic branch/path ownership before creating; add an
optional `request_id` to open_session solely to stabilize its normal branch/path
token for this caller. All ordinary callers retain existing behavior. Validate
duplicate session records, existing branch ownership, common-dir identity,
configured ignored root, immediate-child destination, actual registration,
expected branch and recorded base before reuse. A crash after worktree creation
but before session registration must be recoverable only from this exact journal
and matching Git facts. Timeout/uncertain outcomes require inspection before retry;
never delete an uncertain tree, create a new random alternative, steal a stale
lock by age, or fall back to the primary checkout. Conflicting/stale records remain
preserved and return an actionable error. Concurrency coverage is for cooperating
prewrite callers; arbitrary external Git writers are outside the lock guarantee.

**Source/note policy:** preserve existing `.planning/scratchpads/**` ordinary
untracked file create/update behavior. Also allow create/update in the ignored
`.planning/handoffs/<preparation-key>/scratch/**` namespace when identity exists.
The whole operation must stay inside the selected note namespace, with every
ancestor resolved inside the same real checkout, no symlink/junction/reparse
traversal, nested repository, tracked file or existing hard-linked target.
Malformed paths, tracking ambiguity, deletion, rename/move, or any non-note member
make the entire operation source. A source file with a Markdown extension remains
source; delivered `.planning/` records are source for these editing tools. The
existing named runtime planning-record exception remains unchanged and outside
this hook's tool coverage. These explicit scratch namespaces are a note exception,
not an attempt to infer semantic source from file contents. The old advisory
continues to warn on ordinary scratchpad writes. Read-only tools are quiet and
create no bookkeeping.

**Input/path handling:** structurally parse the whole native JSON object and
supported tool input; no jq/text fallback that silently loses fields. Cover Write,
Edit, MultiEdit, NotebookEdit and apply_patch's documented Add/Update/Delete/Move
operations, with each source and destination included. Require complete recognized
patch framing and operation headers; reject unrecognized or malformed captured
mutations rather than classifying an empty path set as allowed. Do not parse
general shell scripts. Resolve relative paths against actual cwd, handle nested
cwd, CRLF, spaces, Unicode, Windows drive/case/separator variants and Git Bash
native path conversion. Reject drive-relative paths, unsafe UNC/device forms,
traversal, alternate streams and cross-repository/root targets; unsupported path
forms get an explicit cancellation. Use real nearest existing ancestors for new
files and inspect filesystem links, not lexical prefix tests alone. No path is
silently translated into the selected worktree.

**Cancellation and continuation:** synchronous successful denial uses exit 0 and
the exact JSON shape `hookSpecificOutput: {hookEventName: "PreToolUse",
permissionDecision: "deny", permissionDecisionReason: "..."}` on both hosts.
Use documented blocking exit 2 plus stderr when the wrapper cannot parse/execute
safely. Never emit `continue:false` or `stopReason`. Pin native envelopes and exit behavior in fixtures;
unsupported stop fields, a generic runtime error envelope or an exit-1 hook error
are not cancellation. Successful preparation always cancels the pending source
mutation. Its reason contains the preparation key, selected root/branch/base when
prepared, or the exact one-time preparation command and missing identity otherwise,
and the existing reference's exact continuation section. Repeated old-root calls
remain cancelled and refer to the same destination without another creation.
For Codex, an unbound new request is never routed using a different request's
mapping merely because session_id matches; refer to the coordinator route rather
than invent an actor. Bound per-request retries reuse their unit.
Record a digest of the captured request identity, operation and targets alongside
an explicit request binding; changed targets/operation under the same tool_use_id
cancel as a mismatch. Such binding authorizes only selecting/preparing the unit,
never executing the original payload. A later unrelated/retried call with a new
request identity gains no permission from it. The coordinator continues directly
to isolated dispatch/entry and fresh destination reads under existing authority;
there is no blanket new approval prompt or old-root resubmission step.

Register the new synchronous handler with a 30-second host timeout. From adapter
startup use a monotonic 15-second cumulative budget, one-second lock wait and Git
subprocess bounds no longer than the remaining budget (at most five seconds per
call), reserving time to serialize denial. A large/slow creation can time out;
preserve its journal and inspect actual Git state before the next attempt. Test
deadline/uncertain outcome behavior and never wait until the outer hook timeout
to return a decision. This bounds cooperating subprocess work, not failure to
launch the hook. Codex missing/crashed/malformed/timed-out hooks may allow the
call; background hooks cannot cancel, and cloud orchestration is unsupported.
Claude onFailure:"block" is documented only from 2.1.295; do not inject that
configuration without confirmed host compatibility. Installed versions remain
unknown. Neither host's outer failure behavior is made safe merely by these
internal deadlines or fixtures.

The coordinator/host must next enter the selected checkout through a supported
native operation or explicitly bind a fresh executor there, using existing
authorization. The continuation verifies actual cwd, common-dir, Git registration,
branch and base; reloads instructions/planning inputs from that root; rereads every
destination file and every rename/delete source; and rebuilds the edit there.
Dirty-primary content is not transferred. If intent depends on absent dirty or
untracked content, surface that dependency and preserve both trees. A later
supported source call is allowed only when its actual root and all targets match
the validated destination (or an already independently valid assigned linked
worktree); stale absolute primary paths remain cancelled. A JSON intended-root
marker alone never authorizes a write. Do not treat a changed subprocess directory,
checkout attachment, updatedInput, or printed path as host/session entry.

Native entry may require host approval or be unavailable. Report that dependent
transition plainly and preserve the prepared checkout. Do not reinstall tools,
invent APIs, loop the denied mutation, or claim the user has approved a different
permission boundary. Codex create/attach leaves its caller in the original checkout;
the exposed handoff tool cannot move its caller. Claude WorktreeCreate does not
trigger merely because an arbitrary file edit was attempted.

<feature>
  <name>Source-sensitive one-time checkout preparation with explicit continuation</name>
  <files>.ai/runtime/lib/prewrite.py, .ai/runtime/lib/worktrees.py, .ai/runtime/phase.py, .ai/hooks/source-prewrite.sh, .ai/install.py, tests/test_prewrite.py, .ai/hooks/source-prewrite.test.sh, tests/test_install.py, tests/test_install_update.py</files>
  <behavior>Native first source event -> one prepared isolated root plus cancellation; same event retries/concurrency -> same root plus cancellation; permitted notes/read-only -> no creation; destination-local rebuilt mutation -> allowed; stale/cross-root/malformed mutation -> cancelled; uncertain creation -> exact recovery or preserved actionable error.</behavior>
  <implementation>Implement the bounded contract above only after observed test-only RED. Reuse existing Git/session/install surfaces; add no dependencies, generalized command parser or new workflow engine.</implementation>
</feature>

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Commit native-hook and real-Git behavioral RED</name>
  <files>tests/test_prewrite.py, .ai/hooks/source-prewrite.test.sh, tests/test_install.py, tests/test_install_update.py</files>
  <read_first>docs/maintenance/issue87-auto-worktree/CONTEXT.md, docs/maintenance/issue87-auto-worktree/RESEARCH.md, .ai/runtime/lib/worktrees.py, .ai/runtime/phase.py, .ai/install.py, tests/test_session_delivery.py, tests/test_install.py, tests/test_install_update.py, .ai/hooks/worktree-guard.test.sh, .ai/references/methods/tdd.md</read_first>
  <action>Per D-01 through D-04, build the independent bypass/false-positive matrix below before production changes. Start with a real installed-pipeline Claude first-source event carrying session_id and agent_id in a disposable Git repository, expecting a prepared checkout and a cancelled fake pending mutation. Add the Codex parent-only identity case expecting cancellation without guessed checkout creation. Existing registration currently permits these edits; require assertions about that missing behavior to fail. Build the harness so missing new code is not the failure reason. Use a test executor that runs the fake mutation only when the aggregate native hook result permits it, and assert primary bytes never change when denied. Capture command, named test, actual assertion, expected/observed value, exit status and input revision; commit only tests plus the worker summary with RED evidence before Task 2. A syntax/import/setup crash, zero tests, unavailable Bash, wrong fixture or unrelated failure is INVALID_RED. Do not create a stub production hook or alter production behavior to manufacture RED.</action>
  <behavior>Clean primary source request must fail the current allowed-write behavior; notes remain allowed, read-only stays quiet, and the fixture checks actual Git worktree registration and bytes rather than success wording.</behavior>
  <acceptance_criteria>AW-01 through AW-06 and AW-08 have named cases; genuine test-only target assertion failure is recorded and committed before fixes; ordinary note and advisory expectations remain intact.</acceptance_criteria>
  <verify><automated>python -m unittest discover -s tests -p test_install.py -k prewrite -v</automated><fails_when>At RED, no named target assertion fails for missing checkout preparation/cancellation, zero tests run, or setup/import/launcher errors cause the nonzero exit.</fails_when></verify>
  <done>A committed test-only RED proves the original supported mutation can currently proceed without preparation, and an independent matrix states expected allowed and cancelled outcomes.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement and register the complete preparation/cancellation slice</name>
  <files>.ai/hooks/source-prewrite.sh, .ai/runtime/lib/prewrite.py, .ai/runtime/lib/worktrees.py, .ai/runtime/phase.py, .ai/install.py, tests/test_prewrite.py, .ai/hooks/source-prewrite.test.sh, tests/test_install.py, tests/test_install_update.py</files>
  <read_first>docs/maintenance/issue87-auto-worktree/PLAN.md, tests/test_prewrite.py, .ai/hooks/source-prewrite.test.sh, tests/test_install.py, tests/test_install_update.py, .ai/hooks/lib/handoff-io.sh, .ai/runtime/lib/worktrees.py, .ai/runtime/lib/gitops.py, .ai/runtime/phase.py, .ai/install.py, .ai/hooks/worktree-guard.sh</read_first>
  <action>Implement the bounded contract, consuming Task 1's actual RED. Lead with its first source-event tracer across installed registration, strict adapter, real Git preparation and cancellation; then cover the matrix. Keep the existing advisory script byte-identical. Append the new handler in the existing editing matcher group after advisory on both hosts; do not add a duplicate editing group. Preserve user hooks and test reinstall/update idempotence. The generated Codex commandWindows launcher must preserve cancellation exit status, spaces and Unicode, and use the already supported Git Bash discovery pattern. Include the new script in installer management. Use local committed base and deterministic identity, validated journal recovery, bounded lock and no-sync session creation; never copy dirty content. Preserve ordinary session.open callers. Test a rebuilt destination operation after actual fixture cwd/root transition; never replay the original payload. Record GREEN command/results at the implementation revision, then commit source/tests and summary. Refactor only changed owned code when necessary and rerun affected checks.</action>
  <behavior>Every bounded-contract outcome and matrix case below is exercised through either actual generated launchers or real disposable Git subprocesses; the old source mutation never executes after successful preparation.</behavior>
  <acceptance_criteria>AW-01 through AW-07 pass fixture evidence; AW-08 has matching RED/GREEN history. Primary index/dirty snapshots match; repeated/concurrent calls have one selected destination; no native-binding claim is made from a fixture.</acceptance_criteria>
  <verify><automated>python -m unittest discover -s tests -p test_prewrite.py -v</automated><fails_when>Nonzero exit, zero tests, preservation mismatch, duplicate destination, or any bypass/false-positive matrix case has the wrong decision.</fails_when><automated>python -m unittest discover -s tests -p test_install.py -v</automated><fails_when>Nonzero exit, zero tests, wrong editing-group/handler order, absent registered cancellation, or installed-launcher fixture fails.</fails_when><automated>bash .ai/hooks/source-prewrite.test.sh</automated><fails_when>Nonzero exit, no executed cases, a native envelope/exit is misread, or a denied fake mutation executes.</fails_when></verify>
  <done>The registered bounded feature passes the same target that failed RED, preserves dirty state, and routes explicit continuation. Fixture completion does not satisfy the live-host automatic-entry gate.</done>
</task>

<task type="auto">
  <name>Task 3: Document the concrete continuation and evidence boundary</name>
  <files>.ai/hooks/README.md, .ai/references/worktree-sessions.md, .ai/runtime/README.md</files>
  <read_first>docs/maintenance/issue87-auto-worktree/PLAN.md, docs/maintenance/issue87-auto-worktree/RESEARCH.md, .ai/hooks/README.md, .ai/references/worktree-sessions.md, .ai/runtime/README.md, .ai/hooks/source-prewrite.sh, .ai/runtime/lib/prewrite.py, .ai/install.py, docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md</read_first>
  <action>Coordinator dispatches doc-writer after Task 2's integrated implementation summary exists. Explain first-source automatic preparation, deterministic auto-unit and explicit unit override, note policy, errors/recovery and the supported entrypoints exactly as implemented. Add the source-prewrite continuation section named by denial output to worktree-sessions: enter/bind through the supported host or coordinator, verify actual Git root/branch/base, reload context and reread destination before rebuilding, and report dirty dependencies. Retain ordinary workflow source-session routing and named runtime planning exceptions. Explain that native/manual transition is still required unless independently demonstrated on a supported host; list shell/external/cloud-orchestration/hook-error coverage limits and fail-open host behavior. Correct blanket all-hooks-advisory wording only in these owned guides; return any required shared RULES wording change to coordinator rather than editing RULES. Record actual fixture evidence and the pending live proof without turning unavailable live evidence into user approval or success.</action>
  <acceptance_criteria>AW-03, AW-07 and AW-08 are explained against implementation; exact continuation is actionable; creation, fixture pass and live automatic entry remain distinct facts; the existing advisory policy is preserved.</acceptance_criteria>
  <verify><manual>Doc-verifier traces every new command/option and hook continuation reference to implemented entrypoints, compares note/error behavior with receipts, and confirms no assertion of live host binding or universal enforcement.</manual></verify>
  <done>Required guides describe implemented behavior and the remaining host transition limitation; doc-writer returns committed documentation summary and doc-verifier reports evidence.</done>
</task>
</tasks>

## Independent bypass / false-positive matrix

Task 1 owns expected decisions; the fresh code-reviewer and verifier must assess
this matrix independently rather than accept a copied implementation checklist.
Before source dispatch the coordinator supplies its independently scouted
`docs/maintenance/issue87-auto-worktree/MATRIX.md` at a committed revision and
obtains phase-checker approval. Task 1 consumes that packet and maps named test
cases to N1, S1-S3, M1-M3, P1-P2, D1-D2, B1-B2, V1-V2, I1, H1 and R1; no
case may disappear because an implementation chooses a different internal shape.
The scout performed no execution and supplied no implementation correctness
verdict. This is an additional committed input, not a new preparer-owned file.

| Family | Required cases / expected observable result |
|---|---|
| Allow without creation | Read-only; ordinary scratchpad create/update with and without session_id; safe nested note paths; assigned valid linked checkout with relative targets. Existing advisory warnings preserved. |
| Prepare then cancel | Clean primary Write/Edit/MultiEdit/NotebookEdit and each supported patch operation; dirty primary; offline/no remote; nested cwd; Claude actor identity and explicitly bound Codex request. One selected checkout, zero original mutations. Unbound Codex cancels without guessed unit. |
| Reuse and identity | Same native actor retries; different host/session/Claude agent IDs; same Codex parent session with two indistinguishable unisolated workers; omitted/malformed Claude agent_id cannot establish coordinator identity; explicit per-request mapping precedence; changed targets under old tool_use_id; new unrelated/retried request ID; valid existing unit; two possible units; absent/empty/non-string/oversized identity; equivalent Windows spellings; conflicting repository. Codex shared session never proves ownership. Missing/ambiguous identity cancels without guessing. |
| Note bypass attempts | Tracked notes; deleted/renamed note; mixed note/source; source Markdown; traversal; symlink/junction/reparse ancestor; hard-link target; nested repo; missing/unresolvable ancestors; misleading prefix. Source policy/cancellation applies. |
| Input and paths | Malformed JSON/object/type/patch; empty path set; all rename source/destination pairs; Delete File; CRLF; Unicode/spaces; absolute primary path from selected tree; unrelated checkout; drive-relative/UNC/device/alternate-stream path; unsupported aliases/shapes. No unsafe allow or input rewrite. |
| Preservation | Before/after file bytes plus file inventory for tracked, staged, unstaged, untracked and pre-existing ignored content; binary/NUL-sensitive index snapshot including staged rename/delete entries; primary branch and HEAD. Failed/repeated/offline preparation preserves the same snapshot. |
| Concurrency/recovery | Simultaneous first events; lock contention/timeout; crash after Git creation before metadata registration; uncertain subprocess outcome; deleted/unregistered destination; wrong branch/base/common-dir; existing unowned path/branch; stale journal. One safe reuse or preserved actionable cancellation, never random retry creation. |
| Actual registration | Both hosts install/reinstall/update; one editing matcher group, advisory first, new handler second; user hooks retained; commandWindows cancellation status; non-ASCII nested root; exact native denial envelope and exit 2; allowed notes without session_id; internal deadline versus outer timeout. Aggregate pipeline must cancel even though advisory exits 0. Explicitly simulate outer failure as a limitation, never a passing enforcement case. |
| Explicit continuation | Fixture actually changes executor cwd, verifies Git facts, freshly reads destination then builds a new edit; absolute old-root input stays cancelled. Missing dirty source yields dependency, not bulk copy. Original pending input never executes. |

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Host event to privileged Git/filesystem operation | Payload paths, identity, shape and cwd claims are untrusted until checked against installed host argument and actual process/Git facts. |
| Primary checkout to isolated destination | Dirty source and index bytes stay owned by the primary; local metadata cannot authorize path translation or movement. |
| Session journal to Git registration / concurrency | Persisted intended roots and units are claims; reuse/recovery requires exact Git and ownership verification under a bounded lock. |
| Hook result to active host context | Only supported cancellation is claimed by fixtures; native session binding and permissions require separate host evidence. Hooks are optional and not a sandbox. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-AW-01 - Pending: coordinator canonical prewrite-target-confinement linkage | Tampering / Elevation of Privilege | prewrite path classifier and pending mutation | high | mitigate | Tasks 1-2, AW-03/04/05: reject mixed, linked, stale and cross-root targets; cancel original; no input rewriting or dirty-byte movement. Verify real-Git snapshots and native bypass fixtures. |
| T-AW-02 - Pending: coordinator canonical prewrite-unit-identity linkage | Spoofing / Tampering / Denial of Service | prepare journal, lock and worktree selection | high | mitigate | Tasks 1-2, AW-01/02/04: Claude actor tuple, Codex explicit request/unit binding, no shared-parent ownership inference, deterministic unit/base, bounded lock, journal-before-create and exact recovery. Verify distinct actors, ambiguity, concurrent first requests and uncertain outcomes. |
| T-AW-03 - Pending: coordinator canonical prewrite-host-transition-proof linkage | Spoofing / Tampering | installed host pipeline and continuation | high | mitigate | Tasks 1-3, AW-06/07/08: actual registered denial, destination Git verification, fresh reads, never claim updatedInput binds cwd, live evidence gate. Verify aggregate pipeline and independent integration trace; no automatic-entry advertisement without real proof. |

Review depth: L2 for the changed input-to-filesystem boundary. Applicable
information disclosure is bounded by storing no tool contents or transcripts;
repudiation is bounded by key/root/branch/base receipts without claiming audit-grade
authentication. These are aspects of the three scoped findings above, not separate
untracked risk claims. External writers and hook opt-outs remain documented host
coverage boundaries, not accepted guarantees of isolation.

Coordinator safe linkage requests (no worker provider writes):

- Repository: `Tasaddar12/ai-engineering-template`; canonical surface/control:
  `source-prewrite/target-confinement`; failure/remediation scope: unsafe source
  target or dirty-byte movement through note/path classification.
- Repository: `Tasaddar12/ai-engineering-template`; canonical surface/control:
  `source-prewrite/unit-identity`; failure/remediation scope: wrong/duplicate unit
  selection or uncertain worktree creation through session/journal/concurrency.
- Repository: `Tasaddar12/ai-engineering-template`; canonical surface/control:
  `source-prewrite/host-transition-proof`; failure/remediation scope: old-root
  mutation or false automatic-entry claim through cancellation/transition wiring.

All are unresolved Pending semantic dedup, sanitized checklist publication and
readback by coordinator. These scopes differ from issue 95's updater/destructive
command/provider/cleanup risks and issue 96's planning-commit prospective bytes.
Do not invent equivalence, URLs, closure or mitigation outcomes. Reuse a verified
full-scope canonical match when coordinator finds one, otherwise create scoped
tracking under existing authority. Pending linkage is a coordinator dependency,
not another user approval gate.
</threat_model>

<verification>
No implementation or test execution is authorized in this preparer assignment.
The commands in frontmatter and Tasks are future implementation checks, grounded
in existing suites or the new test files explicitly produced by Task 1. No result
is implied. Empty adoption verification.commands is unchanged; coordinator owns
explicit maintenance checks and independent review.

After implementation, run every frontmatter check in the isolated implementation
checkout. A nonzero exit, zero-case run, skipped required environment or preservation
mismatch is a gap; record exact command, revision, case counts and result. Also
inspect `git diff <implementation-base> -- .ai/hooks/worktree-guard.sh`: any output
violates the byte-preservation acceptance. Independent code-reviewer reviews source
and test adequacy; integration-checker traces the generated host settings through
the launcher, preparation, denial, explicit root transition and rebuilt mutation;
doc-verifier checks the guides; verifier reconciles AW-01 through AW-08 and the TDD
receipts. Test-only RED must precede source changes in Git and recorded execution.

Live-host evidence gate: only in an available, identified, supported installed host
with hooks enabled/trusted and appropriate orchestration, use a disposable repo to
show the first source attempt is cancelled, one checkout is prepared, a real native
or coordinator-supported operation binds subsequent work to its actual root and
permission context, destination reads are fresh, and a rebuilt destination mutation
succeeds while primary bytes stay intact. Record host/version, mode, revision,
observed operation and results separately from fixtures. No installed version or
supported same-session transition has been verified here. If unavailable, leave
live automatic entry unverified and keep the PR draft with an explicit manual/native
handoff limitation; fixture results may establish preparation/cancellation only.
</verification>

## Multi-source coverage audit

| Source | ID | Outcome / constraint | Plan coverage | Disposition |
|---|---|---|---|---|
| GOAL | ISSUE87 | User's first source-write isolation request and another separate PR | Tasks 1-3, AW-01/07/08 | Covered for preparation/handoff; automatic native entry expressly gated on live evidence |
| REQ | ISSUE87 | Maintenance assignment, not adoption placeholder requirements | All tasks | Covered; no roadmap/requirement mutation proposed |
| CONTEXT | D-01 | Separate draft, never merge | Scope and coordinator output | Covered; publication owned by coordinator |
| CONTEXT | D-02 | Notes/source distinction and avoid retry loop | Contract, Tasks 1-3, AW-03/07 | Covered |
| CONTEXT | D-03 | Preserve dirty state; prevent old-root writes | Contract, Tasks 1-2, AW-01/04/05 | Covered |
| CONTEXT | D-04 | Frozen drafts, 73/74, infrastructure/install/cleanup excluded | Scope and exact ownership | Excluded as required |
| RESEARCH | R-01 | updatedInput replaces input but cannot bind session | Objective, cancellation contract, AW-07/08 | Covered; no blind path rewrite |
| RESEARCH | R-02 | Existing session.open can sync primary by default | Explicit base and sync=False, AW-04 | Covered; ordinary defaults preserved |
| RESEARCH | R-03 | Unknown/mixed/Windows/rename paths and note policy | Contract and matrix, AW-03/05 | Covered |
| RESEARCH | R-04 | Reuse, concurrency, offline and uncertain creation; Codex shared parent identity | Journal, Claude actor identity and explicit Codex request/unit binding, AW-02/04 | Covered; unbound Codex automatic preparation is unsupported |
| RESEARCH | R-05 | Native fixtures and actual installer registration are distinct from live host | Tasks 1-3 and live gate, AW-06/08 | Covered; live proof remains unavailable |
| RESEARCH | R-06 | Shell/external writers prevent universal enforcement | Scope and required guides | Explicit unsupported boundary; no broad parser added |

Hardest constraint: an actual host/session root transition is not supplied by
pretool output. It is addressed up front by always cancelling and routing explicit
continuation; it cannot be hidden in the last documentation step. Pre-mortem:
wrong unit -> identity/race cases; dirty edit lost -> primary snapshots and fresh
reads; hook silently allows -> aggregate native cancellation cases and live gate.
All required behaviors have owners; unproven live entry is a named evidence gap,
not a reduced acceptance represented as complete.

<success_criteria>
One bounded feature is implemented with genuine RED/GREEN evidence, all required
fixture checks pass at the reported revision, existing advisory bytes and primary
state remain preserved, and independent reviewers confirm the actual wiring and
documented limits. Automatic session entry is advertised only with real supported
transition evidence. Otherwise report automatic preparation plus the remaining
manual/native handoff, with live entry explicitly unverified. Keep the separate
tracking PR draft and never merge.
</success_criteria>

<output>
Tasks 1-2 return `docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md`
with actual task commits, Checks, TDD Evidence, AW coverage and Threat Outcomes.
Task 3's doc-writer returns
`docs/maintenance/issue87-auto-worktree/DOCUMENTATION-SUMMARY.md`. These summaries
are automatically owned by their assigned authors. Coordinator integrates isolated
workers, reconciles Pending canonical links, arranges independent checks/reviews,
and owns the separate draft PR. No adoption roadmap/status update is proposed.
</output>
