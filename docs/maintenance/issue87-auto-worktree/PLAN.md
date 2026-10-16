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
  - .github/workflows/validate.yml
  - AGENTS.md
  - .ai/install.py
  - .ai/hooks/source-prewrite.sh
  - .ai/hooks/source-prewrite.test.sh
  - .ai/hooks/worktree-location.sh
  - .ai/hooks/worktree-location.test.sh
  - .ai/runtime/phase.py
  - .ai/runtime/lib/prewrite.py
  - .ai/runtime/lib/worktrees.py
  - .ai/references/same-agent-worktree.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
  - tests/test_prewrite.py
  - tests/test_same_agent_worktree.py
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - .ai/hooks/README.md
  - .ai/references/worktree-sessions.md
  - .ai/runtime/README.md
  - .ai/RULES.md
files_deleted: []
documentation:
  - .ai/references/same-agent-worktree.md
  - .ai/hooks/README.md
  - .ai/references/worktree-sessions.md
  - .ai/runtime/README.md
  - .ai/RULES.md
resources: [issue87-source-worker-checkout, issue87-disposable-native-fixtures]
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_same_agent_worktree.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_prewrite.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install_update.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install_migration.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_session_delivery.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_planning_integrity.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_phase_runtime.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, registered_hooks_run_planning_integrity_from_installed_hosts, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, installed_runtime_answers_its_verb_contract, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_agent_sources.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_workflow_links.py, -v]
  - [bash, .ai/hooks/source-prewrite.test.sh]
  - [bash, .ai/hooks/worktree-location.test.sh]
  - [bash, .ai/hooks/worktree-guard.test.sh]
user_setup: []
must_haves:
  truths:
    - An eligible Claude agent cancels its first old-root source edit, invokes its own available native EnterWorktree creation tool, and continues as the same existing agent in the destination.
    - Subsequent tools use destination cwd, permission and repository context by default; shell cd, argument retargeting and replacement children never count as movement.
    - The cancelled mutation is never replayed; destination files are freshly read and a rebuilt edit executes once after native and Git checks.
    - Missing tool/schema, ineligible role, policy refusal, untrusted hook or uncertain movement yields a precise unsupported or pending result without repeated edit retries or approval bypass.
    - Scratchpad and narrow ordinary OS-temp notes remain allowed without session identity or worktree creation; source, mixed and unsafe paths retain their required decisions.
    - Dirty staged, unstaged, untracked and ignored data remain preserved and accounted for; creation never silently copies, discards or replays them.
    - Actual installed hooks, Claude role exports and workflow consumers connect this route; simulated contract evidence and live native movement are reported separately.
  artifacts:
    - path: .ai/references/same-agent-worktree.md
      provides: Standing same-agent native capability gate, creation/entry sequence and default-context proof protocol.
    - path: .ai/runtime/lib/prewrite.py
      provides: Strict request classification, bounded ticket/name lifecycle, native creation callback and Git-only confirmation.
    - path: .ai/hooks/source-prewrite.sh
      provides: Registered synchronous native source denial with actionable same-agent continuation.
    - path: .ai/hooks/worktree-location.sh
      provides: Dedicated ticketed native creation branch without existing-name reuse; unchanged ordinary dispatch branch semantics.
    - path: tests/test_same_agent_worktree.py
      provides: Explicitly simulated same-agent native contract harness composed with real installed exports/hooks and disposable Git.
    - path: .ai/RULES.md
      provides: Narrow Hooks and validation policy consistent with integrated implementation and verified documentation.
  key_links:
    - from: .ai/install.py hook_settings and render_asset
      to: Installed source hook, coordinator/coder tool exports and CLAUDE.md
      via: One editing group, advisory first, source handler second; Claude-only native tool permission and standing contract link.
    - from: Source denial and six source-session workflows
      to: .ai/references/same-agent-worktree.md
      via: Same caller reads protocol, gates actual native tool/schema and invokes it without a child/fork.
    - from: Native EnterWorktree creation
      to: .ai/hooks/worktree-location.sh ticketed branch
      via: Host WorktreeCreate event, exact reserved name, pinned local base and validated creation journal.
    - from: Native completion and subsequent default-root tools
      to: prewrite.confirm and worktrees.adopt_native_session
      via: Same-actor host observation plus real Git checks; new native units are adopted, existing ordinary sessions are confirmed without creating/adopting them again. Runtime never certifies host binding.
---

<objective>
Implement the conditional Claude path that actually moves the same existing agent,
as required by the human: "This time we actually move the agent itself."
Synchronous denial is the trigger for instruction-driven native orchestration,
not fulfillment. The same model next invokes its own available EnterWorktree
creation operation; after completion it proves default destination context, reads
the destination afresh and rebuilds the intended edit.

The earlier preparation/manual-handoff plan is replaced. Do not create a checkout
in PreToolUse and call that movement; do not use shell cd, per-call cwd/path
overrides, attachment, a replacement executor or a new task/fork as fulfillment.
Native creation through the trusted existing WorktreeCreate provider is supported
conditionally on the target Claude host. This selected executor lacks the native
tool, so live demonstration is unavailable here; that does not prevent authoring
the gated supported-target implementation.

Codex same-agent automatic movement is unsupported by the observed template
integration: there is no authenticated same-thread host controller. Its source
hook may cancel and explain that exact limitation, but neither cancellation nor
creation counts as movement. Do not add an unverified controller, invoke idle CLI
commands from a running hook, or claim Codex products cannot move conversations.
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
@docs/maintenance/issue87-auto-worktree/SAME-AGENT-CAPABILITIES.md
@docs/maintenance/issue87-auto-worktree/MATRIX.md
@docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md
@docs/maintenance/issue87-auto-worktree/RED-REVIEW.md
@AGENTS.md
@.ai/RULES.md
@.ai/references/git-workflow.md

Fresh source/decision input: 206deb7578ca51e3bbea0caa75beed1769a08363, including
the updated actual human/parent decisions and source-map packet. Final preparation
input 4f978af0521b2ba960750545ba36f01268f3cbff additionally contains only the
coordinator's native MATRIX A1-A7 update. The prior source boundary RED
at 38b7b1c changed only tests; no production implementation has been released.
Keep that honest historical evidence but require fresh native-route RED below.
Do not reinterpret prior plan approval or source-denial RED as native fulfillment.

Decision aliases: D-01 separate PR97 draft, never merge; D-02 source versus notes
and no denial/retry loop; D-03 preserve dirty data and stop old-root edits; D-04 six
original drafts frozen, 73/74, live infrastructure/install/cleanup excluded; D-05
same existing agent/session moves natively; D-06 actual availability/role/policy/
trusted-hook gate with no existing-path approval bypass; D-07 Codex lacks the
observed controller, and live smoke is distinct from simulated contract evidence.
These summarize actual CONTEXT decisions, not invented discussion or approval.

One feature, one TDD plan, three original tasks plus bounded Task 4 for the
same-phase dependency join and configuration-only Task 5 after observed CI timeout.
Coordinator dispatches one
isolated source worker for Tasks 1-2, then an isolated doc-writer for Task 3 after
source integration. Sources and docs have disjoint ownership below. Task 4 follows
integrated code-05 corrections and the coordinator's local non-rewriting PR93
dependency merge; overlapping source/doc paths are serial, never assigned to
concurrent writers. Task 4 preparation owned this PLAN, CONTEXT, STACK-PLAN and
PREPARER-SUMMARY. Task 5 preparation owns only PLAN, CONTEXT, CI-PLAN and
PREPARER-SUMMARY; no code, tests or provider writes run in this assignment.
</context>

## Acceptance, ownership and exclusions

| ID | Required observable result | Owner / evidence |
|---|---|---|
| AW-01 | Eligible target Claude: source denial leads to the same existing agent's native creation call, completed movement and subsequent default destination tools. | Task 2; composed SIMULATED contract, plus separate live gate |
| AW-02 | Positive actual native tool/schema, eligible role, permitted policy, trusted creation hook and unambiguous work identity gate; unsupported cases are precise. Existing outside-path approval is honored. | Tasks 1-2; installed export and capability/refusal fixtures |
| AW-03 | Untracked .planning/scratchpads/** create/update warns/continues; plain unlinked OS-temp note create/update outside every repository allows without identity/ticket/creation. Other external and unsafe targets gain no exemption. | Tasks 1-2; both-host installed aggregate controls |
| AW-04 | Every pre-existing staged, unstaged, untracked and ignored change remains preserved/recoverable at its documented location. Selected custom native creation preserves primary bytes/index; any observed legitimate host relocation is separately accounted for. No blind copy/replay. | Task 2; disposable dirty Git snapshots; live gate |
| AW-05 | Strict source/target confinement, mixed/rename/delete handling and identity checks; original pending call always cancelled, fresh reads precede exactly one rebuilt edit. | Tasks 1-2; bypass matrix and composed contract |
| AW-06 | Actual installed hook pipeline, Claude native tool exports, standing instructions, six workflow consumers and native creation callback are connected. Phase/quick session adoption does not create a second checkout or sync primary. | Task 2; installed/real-Git/export tests |
| AW-07 | Bounded ticket/creation lifecycle, concurrent separation, uncertain native outcome and retry handling avoid duplicate creation, double edits or creation-name approval bypass. Already-correct worktree is a no-movement control. | Tasks 1-2; failure/race/recovery cases |
| AW-08 | Fresh genuine behavioral native-route RED before fixes, GREEN of same case, independent source/docs/integration review, honest live evidence and completion status. | All tasks; receipts and independent verification |

Source worker (Tasks 1-2) owns every files_modified path except Task 5's
`.github/workflows/validate.yml`, the bounded Task 2
migration subassignment below and these Task 3
doc-writer paths: `.ai/hooks/README.md`, `.ai/references/worktree-sessions.md`,
`.ai/runtime/README.md`, `.ai/RULES.md`. The shared operational protocol
`.ai/references/same-agent-worktree.md` is source-worker-owned executable workflow
instruction, covered by contract tests; doc-writer reads and explains it without
editing it. Coordinator explicitly delegates only the standing native-route link
in AGENTS and the narrow Hooks and validation section in RULES to their respective
owners. Other shared policy and adoption skeleton sections stay untouched.
Task 4 is a later isolated integration assignment with exactly its six listed
paths; it supersedes no active writer's ownership. Its overlaps are permitted only
after earlier commits integrate and writers finish. It owns the automatic summary
docs/maintenance/issue87-auto-worktree/STACK-SUMMARY.md.

Task 5 is a later isolated repair after the independent timeout diagnosis and
plan check join. Its exact ownership is `.github/workflows/validate.yml` plus its
automatic `docs/maintenance/issue87-auto-worktree/CI-SUMMARY.md` receipt. Only the
platform job budget and its adjacent explanation may change: Windows45 minutes,
Ubuntu30. This is the sole provider-workflow exception; no earlier worker gains
that path. CI-PLAN.md supplies the observed RED, bounded checks and handoff.

Bounded Task 2 CI-regression subassignment at published source input
ff81660b493305b5714c8efce9835ee4c2d128a0: coordinator assigns isolated targeted-fixer
only `tests/test_install_migration.py` plus its own
`docs/maintenance/issue87-auto-worktree/MIGRATION-SUMMARY.md`. This leaf may run
concurrently with main source coder04 because those paths are disjoint; coder04
retains all other Task 2 ownership. No installer or production edits belong to
the leaf. Ubuntu full CI reported 644 tests, one failure and three errors; the
named migration failure at test_install_migration.py:357 compares raw event-group
counts and observes 3 != 2 after intended editing-group coalescing. This is an
actual regression receipt, not a setup/missing-test RED. Replace that count-only
assumption with meaningful managed-script identity and preserved-user-hook
assertions: exactly one editing group contains advisory first and source second,
each managed registration identity (event, matcher, script) occurs once after
relocation, and original user hooks remain. The advisory script's intentional
dispatch and editing registrations are distinct identities, not duplicates.
Do not merely change the expected count or weaken behavior. If the assertions
expose a production defect, return it to coder04/coordinator rather than editing
the installer. Run `python -m unittest discover -s tests -p test_install_migration.py -v`;
nonzero exit or zero executed cases fails the focused check. Record actual revision/results
and commit the test plus MIGRATION-SUMMARY. Coordinator integrates this disjoint
repair and checks its receipt before final verification; unrelated CI errors stay
with the currently assigned source worker.

Excluded: edits to original six draft heads; GitHub/GitLab/provider workflow changes
except Task 5's exact validation-job budget/comment; provider
73/74; live infrastructure, installations, cleanup and merges; generalized command
parsing; shell/external writers; existing exec-session input; cloud hooks; new
Codex controller; whole-host sandbox claims; broad role/tool or workflow rewrites.
Keep `.ai/hooks/worktree-guard.sh` byte-identical and its warning preference intact.
No automatic stash/reset/clean, dirty-file bulk copy, path rewriting or old-input
replay. Worker lifecycle/integration/publication remain coordinator-owned. The
explicit Task 4 exception imports frozen PR93 (already on frozen PR92) as a
non-rewriting local dependency merge into PR97; it does not merge either PR,
change either frozen head or import the original-six umbrella into PR97. See
STACK-PLAN.md for the exact stack, own-change boundary and composition evidence.

## Inspected source map and precise integration

| Producer/consumer at fresh input | Required change / retained contract |
|---|---|
| `.ai/install.py:128-145,188-198` render_asset/destination_path; Claude roles copied verbatim | Add a bounded Claude-only export adjustment granting EnterWorktree in restrictive coordinator/coder tools metadata; preserve all other tool restrictions, role bodies and Codex TOMLs. Source-tree roles without that export still require actual native availability. Skill allowed-tools grants preapproval, not availability; do not add context:fork or blanket privileges. |
| `AGENTS.md` installed as CLAUDE.md; coordinator/coder read it | Add a standing same-existing-agent source-denial rule linking the new protocol. A returned deny reason names the installed protocol, so ad-hoc source edits also reach it. |
| `.ai/install.py:430-468,479` hook registrations | Append source-prewrite after unchanged advisory in the single existing editing PreToolUse group on both hosts; keep actual Windows launcher and user-hook behavior. Claude WorktreeCreate remains worktree-location. |
| `.ai/hooks/worktree-location.sh:27-45,91-112`; ordinary .test.sh:52-85 | Add only the dedicated reserved `wf-entry-` ticket branch. Validate journal and pinned base; create fresh destination or return explicit uncertain/refusal. Never reuse a registered destination/branch through this creation branch. Ordinary dispatch name reuse/custom-root/calling-HEAD behavior remains covered unchanged. |
| `.ai/runtime/lib/worktrees.py:766-832` open_session | Do not use it to precreate the Claude native destination; retain its defaults and existing callers. Reuse existing common_dir/root/listing/session helpers where sufficient. |
| `.ai/runtime/lib/worktrees.py:835-893` phase-only session.adopt | Add narrowly scoped adopt_native_session for verified native-created phase/quick units with exact journal base/root/branch. Do not broaden ordinary session.adopt or infer a remote base/phase from recency. |
| `.ai/runtime/phase.py` registry and normal JSON envelopes | Add prewrite.request, prewrite.begin and prewrite.confirm adapters to lib.prewrite. request bootstraps a known workflow unit without an intercepted edit; begin resolves explicit new/existing target mode; confirm branches between new native adoption and existing-session validation. None certifies host binding or invokes native tools. |
| quick:127-140, discuss:236-253, plan:127-144, execute:178-195, verify:132-149, ship:90-98 | Add a conditional Claude native-route branch before shell session.open/cd routing. New unit uses native creation then adoption. Existing session uses the actual native existing-path operation with eligibility/policy/approval checks. Reload locate/init from post-native default root. Shell cd remains ordinary runtime guidance, never native movement proof. |
| `tests/test_install.py:682-780` aggregate and note/source tests | Preserve valid cancellation/note controls; replace obsolete Claude precreated-second-checkout expectation with denial ticket followed by native creation contract. Codex refusal remains unsupported-control evidence, not the new native-route RED. |
| `tests/test_session_delivery.py`, `.ai/hooks/worktree-location.test.sh`, `tests/test_agent_sources.py` | Existing real-Git/session, ordinary location reuse and role/export regression checks remain. New native behavior cases live in new test_same_agent_worktree.py and test_prewrite.py. |

## Same-agent operational contract

1. **Classify and cancel.** Strictly parse the synchronous native event and full
   mutation. Source requests from primary produce a bounded local ticket and deny;
   they do not create a worktree. Use exit 0 plus
   `hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",
   permissionDecisionReason:"..."}`; internal parse/adapter failure uses blocking
   exit 2/stderr. Never use continue:false, stopReason or generic runtime JSON as
   host cancellation. Denial identifies ticket, original committed HEAD, source
   root and the installed same-agent protocol. The same agent follows that next;
   it must not resubmit the pending mutation or silently rewrite its arguments.

2. **Gate in the same model's standing protocol.** The hook cannot inspect the
   tool pool. The actual caller checks that its advertised native tool pool/schema
   exposes EnterWorktree creation, that its current role is eligible/unpinned,
   policy allows it and the installed creation hook is trusted/registered.
   Use the host-advertised creation argument field, including a name only when the
   schema actually supplies it. No guessed minimum version, guessed JSON schema,
   config flag or marker can manufacture availability. A restrictive installed
   creation schema that cannot safely carry the reserved creation identity is an
   unsupported adapter case; do not invent a field or invoke unnamed creation.
   A restrictive installed
   role must actually permit the tool; preapproval alone is insufficient. Missing
   schema/tool, pinned creation restriction, policy denial or untrusted hook ends
   this attempt precisely as unsupported, with the edit unapplied. The selected
   executor's missing tool is a live-smoke limit, not a target-host veto.

3. **Bootstrap and choose target mode explicitly.** Intercepted source events
   produce denial requests as in step 1. Separately, each of the six workflow
   entrypoints can call `prewrite.request <phase|quick> <label> --mode <new|existing>`
   before any edit/session.open/cd. This known-unit bootstrap validates actual
   repository/root and explicit workflow kind/label, captures local committed HEAD
   for new mode, and returns a workflow request ID with origin=workflow. It has
   no denied mutation or source-target digest: never fabricate an intercepted edit
   or require one to start a workflow. For existing mode it resolves exactly one
   open kind/label session and validates its recorded root/branch/base against real
   Git registration; missing, conflicting or ambiguous metadata refuses. No
   arbitrary external path or newest-session selection is accepted. Bootstrap
   records a request, not native capability, identity or movement proof.

   `prewrite.begin <request> <phase|quick> <label> --mode <new|existing>` accepts
   either the exact intercepted request or the workflow request. It validates
   repository/session/actor/request linkage and explicit unit/mode; intercepted
   requests additionally retain target/operation confinement. For workflow requests
   mode/kind/label must match their bootstrap. New mode requires no existing unit
   and the pinned local commit; existing mode requires the exact validated open
   session and returns its actual destination with no creation name/base fiction.
   New/existing disagreement refuses instead of switching modes implicitly.
   Only new mode reserves one safe fresh
   `wf-entry-<opaque-token>` name under the configured ignored immediate-child
   worktree root. Store minimal unit/root/base/name/state/digests under
   common_dir/ai-phase/prewrite; no source contents or transcript text. Use a bounded
   OS-released common-repository lock and atomic journal. Stable actor identity is
   Claude session_id plus agent_id when present; omitted agent_id alone never
   proves main-agent eligibility. Native role/tool/context checks establish the
   caller's route; a request-specific unit binding avoids guessing ownership.
   Known workflow kind/label takes precedence; an ad-hoc call uses an explicit
   ticket-local quick label returned by begin, not newest session/branch/transcript.
   Conflict or ambiguous ownership refuses, never shares a unit implicitly.
   Reserve exact branch `worktree-wf_<opaque-token>` so the native-created unit
   satisfies the existing isolation branch namespace; do not infer its branch
   from an unrelated session or relax existing branch checks.

4. **Native entry is the next operation.** In new mode the same existing model invokes its
   own advertised EnterWorktree creation form with the reserved creation identity.
   The host fires WorktreeCreate; the dedicated location-hook branch consumes the
   exact journal name/source/base and creates the checkout from that pinned local
   commit without fetch/sync. Return only its validated destination as the host's
   creation provider. No worktree exists merely because begin succeeded. Existing
   registered destination, branch/name collision, stale journal, wrong base or
   uncertain prior creation cannot be returned as "new" creation. Refuse and
   inspect/preserve, or use the genuine native existing-path route if its schema,
   eligibility and required approval allow it. Never disguise reuse to evade
   outside `.claude/worktrees/` approval. Preserve ordinary dispatch hook reuse.
   In existing mode the same agent invokes the actual advertised native
   existing-path form for the returned session root, subject to its eligibility,
   policy and required approval. It does not call creation or WorktreeCreate and
   does not need a native-creation journal. Failure leaves the existing session
   untouched; no new-unit fallback or approval bypass is allowed.

5. **Prove post-entry defaults.** Native completion must be observed for the same
   existing session/agent. Subsequent tools, without explicit cwd overrides or
   prefixed cd, must report actual destination cwd/Git root, registration, named
   branch and pinned base; a relative read must come from the destination. Reload
   the destination CLAUDE.md/AGENTS and relevant instructions/project configuration,
   re-resolve runtime and all locate/init inputs there, and confirm destination
   write permissions. The original project-directory environment variable stays
   anchored on Claude; do not use it as the post-entry cwd. `prewrite.confirm
   <request>` verifies actual Git/request facts in its default cwd. In new mode it
   requires the matching native creation journal, then registers the phase/quick
   unit through adopt_native_session without another checkout or primary sync.
   In existing mode it validates the original open session's kind/label/root/
   branch/base and registration against current Git and the request, returning
   reused=true without adopt_native_session, a fabricated creation receipt or
   rewriting session ownership. No native-creation journal is required for an
   ordinary existing phase/quick session. Native/default-context proof is still
   mandatory in both modes and is separate from these Git checks. Its output
   explicitly says Git facts verified, host
   binding not certified by runtime. Intended-root state, self-reported tool lists,
   a child process cwd or confirm success alone are not host movement proof.

6. **Fresh reconstruction and continuation.** Re-read every destination file,
   including rename/delete sources; rebuild the intended mutation against those
   reads, and apply once in the destination. Do not reuse old absolute paths,
   old content offsets or the cancelled pending call. If intent depends on dirty
   primary content absent there, surface the dependency and keep data preserved;
   no automatic copy/replay. A later source hook validates current root/unit/targets
   and rejects stale paths or drift. Already correctly isolated callers need no
   native move. Wrong-root/already-worktree/pinned callers may use only the actual
   permitted native path form with its restrictions; no replacement child counts.

7. **Failure and retry.** Register synchronous source handler timeout 30 seconds;
   ticket work has a 15-second cumulative internal budget, at most one-second lock
   wait and bounded Git subprocesses, reserving time for valid denial. Native
   creation uses the existing WorktreeCreate timeout and explicit bounded child
   Git calls shorter than that outer deadline. On timeout/unknown native outcome,
   inspect same-session native state, journal and actual registration before any
   next call; no new random tree, repeated EnterWorktree, second edit or cleanup.
   Actual movement may have completed despite missing result: prove it or leave
   pending/unverified. Old-root source remains denied. Explicit request bindings
   do not authorize later unrelated calls or changed targets under the old ID.

8. **Preserve native-session lifetime.** In the existing WorktreeRemove handler,
   recognize a native-entry-owned path only through its exact common-repository
   journal/Git identity, and preserve that checkout rather than removing it. This
   applies to clean, dirty, ignored-only and uncertain native-owned state; retain
   journal/branch and report preservation. No new cleanup is authorized. A prefix
   or missing/corrupt journal cannot authorize deletion: a reserved native-entry
   candidate with missing/corrupt identity must be preserved/refused, never fall
   through to ordinary dispatch removal. Test the actual registered
   removal callback with ignored-only native data and uncertain outcomes. Preserve
   all ordinary dispatch WorktreeRemove behavior and its separate tests. If a
   target host does not honor the trusted custom removal provider, report that
   lifecycle unsupported/unverified rather than promising data preservation.

Existing native session paths are never shell-cd fulfillment: use the real native
path form, honor host approval and role restrictions, then perform steps 5-6.
If unavailable, the exact same-agent route is unsupported; do not create a new
unit to evade that condition. Prior shell-based runtime routes are not relabeled
as movement. Do not remove ordinary session.open semantics for unrelated callers.

## Classification and preservation boundaries

Preserve untracked create/update under `.planning/scratchpads/**` as advisory
without identity. The ignored `.planning/handoffs/<ticket>/scratch/**` may hold
session-local create/update notes under the same safety checks. Plain unlinked
create/update under resolved Python tempfile.gettempdir(), proven outside every
Git/nested repository, is an allowed ordinary temporary artifact without identity,
ticket or creation. Use real containment/ancestor/Git facts, no lexical temp prefix,
extension or content guessing. Non-temp external targets are unsupported; no
arbitrary external exemption. Tracked notes, mixed note/source, delete/rename/move,
symlink/junction/reparse traversal, existing hardlinks, nested repositories and
ambiguous paths receive source/unsupported handling for the whole operation.

Parse complete Write/Edit/MultiEdit/NotebookEdit and native apply_patch Add/Update/
Delete/Move input structurally, collecting all source/destination targets. Unknown
captured mutation, malformed JSON/patch or empty path set must not silently allow.
Resolve actual default cwd with Windows drives/case/separators, spaces, Unicode,
CRLF and Git Bash native conversion. Reject unsafe traversal, drive-relative,
device/UNC/alternate-stream forms and cross-repository targets; no broad shell
parsing. Read-only tools create no tickets or worktrees. Keep named runtime-owned
planning-record exceptions unchanged; editable delivered Markdown is source.

The chosen custom creation hook creates a fresh committed checkout and preserves
primary staged/unstaged/untracked/ignored bytes, index, branch and HEAD. Snapshot
them in disposable tests before denial/native creation/failure/retry. If a real
host legitimately relocates existing data, record each change's before/after
location, recoverability and conflict behavior separately; do not silently treat
missing primary data as success or impose byte-identical primary state on a
documented relocation. No automatic stash/reset/clean/remove or dirty bulk-copy.

Outer Codex missing/crashed/malformed/timed-out hooks may fail open; background
hooks cannot cancel, cloud orchestration and existing exec-session inputs are not
covered. Claude onFailure:block requires confirmed compatible host support; do not
invent an installed version or add unverified config. These are optional hooks
with bounded coverage, not a universal filesystem enforcement boundary.

<feature>
  <name>Same-existing-agent conditional Claude native worktree entry</name>
  <files>.ai/references/same-agent-worktree.md, .ai/runtime/lib/prewrite.py, .ai/hooks/source-prewrite.sh, .ai/hooks/worktree-location.sh, .ai/install.py, tests/test_same_agent_worktree.py</files>
  <behavior>Supported caller: deny old edit -> positive native gate -> same-agent native creation -> default destination context proof -> fresh read -> rebuilt edit once. Unsupported/uncertain caller: precise unapplied/pending outcome, never simulated fulfillment. Notes/read-only remain controls.</behavior>
  <implementation>Implement only this route and its bounded existing-session/workflow connections after fresh target behavioral RED. Reuse existing Git/session/install surfaces; no new host controller or workflow engine.</implementation>
</feature>

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Commit fresh native-route behavioral RED and installed contract controls</name>
  <files>tests/test_same_agent_worktree.py, tests/test_prewrite.py, tests/test_install.py, tests/test_install_update.py, .ai/hooks/source-prewrite.test.sh, .ai/hooks/worktree-location.test.sh</files>
  <read_first>docs/maintenance/issue87-auto-worktree/CONTEXT.md, docs/maintenance/issue87-auto-worktree/SAME-AGENT-CAPABILITIES.md, docs/maintenance/issue87-auto-worktree/MATRIX.md, docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md, docs/maintenance/issue87-auto-worktree/RED-REVIEW.md, .ai/install.py, .ai/hooks/worktree-location.sh, .ai/hooks/worktree-location.test.sh, .ai/runtime/lib/worktrees.py, tests/test_install.py, tests/test_install_update.py, tests/test_session_delivery.py, .ai/references/methods/tdd.md</read_first>
  <action>Per D-01 through D-07, retain valid historical 38b7b1c refusal/note evidence but update its obsolete Claude precreated-tree assertion: first denial must produce a native continuation ticket and no checkout until the native creation event. Add a fresh installed export/orchestration contract suite using an explicitly SIMULATED host/session adapter with stable actor identity, advertised creation schema fixture and default tool cwd. Drive the actual generated source pipeline, continuation ticket/contract, native operation simulation, actual registered WorktreeCreate launcher, real disposable Git confirmation and subsequent default-cwd relative read/rebuilt mutation exactly once. A test-supplied host adapter models native movement; it does not prove a live host or model follows instructions. The target RED must reach an assertion about absent same-agent native continuation/export/default-context contract, not just the old Codex/source refusal, missing new module or test setup. Add the independent matrix below, preserving ordinary dispatch name reuse tests separately. Record command, named target, expected/actual assertion, exit, revision and case count, then commit only tests plus implementation summary before any production fix. Setup/import/syntax errors, zero tests or unrelated failures are INVALID_RED; do not create a production stub to manufacture RED.</action>
  <behavior>Native-capable simulated caller must preserve identity and use destination defaults after the registered creation sequence. Missing capability, path-only/pinned policy, untrusted hook, cancelled or uncertain transition, stale request and forbidden existing-name reuse cannot pass as native success. Both host note controls remain allowed.</behavior>
  <acceptance_criteria>AW-01/02/06/07/08 have a genuine fresh target assertion RED at a test-only commit; AW-03 controls pass; native contract assertions are independent of implementation internals and explicitly labeled SIMULATED.</acceptance_criteria>
  <verify><automated>python -m unittest discover -s tests -p test_same_agent_worktree.py -v</automated><fails_when>At RED, no named native-route behavior assertion fails, zero cases run, or setup/import/launcher faults cause the nonzero result.</fails_when></verify>
  <done>A fresh committed native-route RED exists with legitimate controls; historical cancellation RED is preserved without being relabeled movement evidence.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Wire the same-agent native route, creation provider and session consumers</name>
  <files>AGENTS.md, .ai/install.py, .ai/hooks/source-prewrite.sh, .ai/hooks/source-prewrite.test.sh, .ai/hooks/worktree-location.sh, .ai/hooks/worktree-location.test.sh, .ai/runtime/phase.py, .ai/runtime/lib/prewrite.py, .ai/runtime/lib/worktrees.py, .ai/references/same-agent-worktree.md, .ai/workflows/quick.md, .ai/workflows/discuss-phase.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md, tests/test_prewrite.py, tests/test_same_agent_worktree.py, tests/test_install.py, tests/test_install_update.py, tests/test_install_migration.py</files>
  <read_first>docs/maintenance/issue87-auto-worktree/PLAN.md, docs/maintenance/issue87-auto-worktree/SAME-AGENT-CAPABILITIES.md, Task 1 tests and committed RED summary, AGENTS.md, .ai/install.py, .ai/agents/coordinator.md, .ai/agents/coder.md, .ai/hooks/worktree-guard.sh, .ai/hooks/worktree-location.sh, .ai/runtime/phase.py, .ai/runtime/lib/worktrees.py, .ai/runtime/lib/gitops.py, .ai/workflows/quick.md, .ai/workflows/discuss-phase.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md, tests/test_install_migration.py</read_first>
  <action>Consume the actual fresh RED and implement the operational contract above. Lead with the installed-source-deny to same-model native instruction to trusted creation callback to Git-confirmed destination slice, then complete refusal/retry/path/dirty cases. Source hook never precreates; native WorktreeCreate owns fresh pinned-base creation. Add the dedicated wf-entry name branch, ticket lifecycle and narrow phase/quick native adoption without changing normal dispatch reuse/session defaults. Add Claude-only EnterWorktree permission to actual restrictive coordinator/coder exports, the standing AGENTS/installed CLAUDE link, and the six conditional workflow branches so Claude does not reach shell session.open/cd as its movement mechanism. Actual availability, role, schema and policy remain positive model-side gates. Existing-session entry uses genuine native path form and honors required approval; no name-reuse bypass. Preserve user hooks, Windows Unicode/spaces/status propagation, one editing group with advisory first, and the old advisory bytes. Codex returns precise unsupported movement rather than claiming a controller. Finish matching GREEN, record all actual commands/results and commits in the implementation summary, and commit source/test slice. Refactor only changed owned code if needed, with affected checks rerun.</action>
  <behavior>AW-01 through AW-07 hold through composed installed/export/real-Git fixtures, including the matrix below. Test-only host simulation is always identified; runtime Git confirmation is never labeled host binding proof.</behavior>
  <acceptance_criteria>The same fresh RED target passes GREEN; native creation is causally after denial and same-agent capability gate; default context/fresh reads/rebuilt edit are required; preservation and unsupported controls pass; no preparation-only/manual-child substitute or inferred live success remains.</acceptance_criteria>
  <verify><automated>python -m unittest discover -s tests -p test_same_agent_worktree.py -v</automated><fails_when>Nonzero exit, zero cases, stale actor/default-cwd contract, missing gate, creation-name reuse bypass, or double edit/creation.</fails_when><automated>python -m unittest discover -s tests -p test_install.py -v</automated><fails_when>Nonzero exit, zero cases, missing actual role/hook exports, pipeline denial failure or note false positive.</fails_when><automated>python -m unittest discover -s tests -p test_prewrite.py -v</automated><fails_when>Nonzero exit, zero cases, wrong path/identity/dirty-state decision or broken ticket/native-session confirmation.</fails_when><automated>bash .ai/hooks/worktree-location.test.sh</automated><fails_when>Nonzero exit, no executed cases, ticketed reuse bypass, wrong pinned base or changed ordinary dispatch reuse behavior.</fails_when></verify>
  <done>Conditional native route and precise unsupported paths are implemented with matching GREEN and committed evidence. The isolated migration-test subassignment has meaningful script-identity/user-hook assertions, a passing focused receipt and committed MIGRATION-SUMMARY before final verification. Live native smoke remains a separate unmet acceptance layer in this executor.</done>
</task>

<task type="auto">
  <name>Task 3: Reconcile guides and shared policy with actual native movement behavior</name>
  <files>.ai/hooks/README.md, .ai/references/worktree-sessions.md, .ai/runtime/README.md, .ai/RULES.md</files>
  <read_first>docs/maintenance/issue87-auto-worktree/PLAN.md, docs/maintenance/issue87-auto-worktree/SAME-AGENT-CAPABILITIES.md, docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md, .ai/references/same-agent-worktree.md, .ai/hooks/README.md, .ai/references/worktree-sessions.md, .ai/runtime/README.md, .ai/RULES.md, .ai/install.py, .ai/hooks/source-prewrite.sh, .ai/hooks/worktree-location.sh, .ai/runtime/lib/prewrite.py</read_first>
  <action>Coordinator dispatches doc-writer after integrated Task 2 evidence. Document the supported conditional Claude same-existing-agent sequence, actual capability gate and native creation/session adoption; explain that shell cd, cancellation, prepared roots and replacement children do not fulfill movement. Preserve existing ordinary dispatch reuse and note warnings; explain the strict wf-entry no-reuse/approval boundary, narrow OS-temp notes, dirty-data accounting and unsupported Codex controller. Coordinator explicitly delegates only RULES Hooks and validation reconciliation: distinguish advisory hooks from the new supported source denial, native continuation requirement and honest coverage limits; preserve all other sections. Update the three guides against exact implemented commands and installed paths, including ordinary session.open versus native creation/adoption. State fixture results as SIMULATED and live smoke unavailable here without misrepresenting target Claude support. Commit all four documentation paths and summary; coordinator integrates before final verification. Do not edit source-worker-owned operational protocol.</action>
  <acceptance_criteria>All four paths accurately explain integrated behavior, notes, existing-path approval and unsupported hosts. The narrow RULES section has an owner, committed completion point and independent check. No preparation-only fallback or simulated/live conflation appears.</acceptance_criteria>
  <verify><manual>At the integrated source/docs revision, independent doc-verifier checks all four exact paths, explicitly RULES Hooks and validation, against actual native protocol, exports, creation callback and receipts. Missing, failed or required unverifiable claims prevent conclusive coverage; a native live claim requires separate observed host evidence.</manual></verify>
  <done>Four-path documentation is integrated before final verification with explicit per-document/section review evidence and the real live-smoke limitation preserved.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: Join the native adapters to frozen PR93 planning integrity without weakening either control</name>
  <files>.ai/runtime/phase.py, .ai/install.py, .ai/RULES.md, .ai/hooks/README.md, tests/test_same_agent_worktree.py, tests/test_install.py</files>
  <read_first>docs/maintenance/issue87-auto-worktree/STACK-PLAN.md, docs/maintenance/issue87-auto-worktree/CONTEXT.md, docs/maintenance/issue87-auto-worktree/REVIEW-01.md, docs/maintenance/issue87-auto-worktree/VERIFICATION.md, docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md, .ai/runtime/phase.py, .ai/runtime/lib/prewrite.py, .ai/runtime/lib/planning_integrity.py, .ai/install.py, .ai/RULES.md, .ai/hooks/README.md, tests/test_same_agent_worktree.py, tests/test_install.py, tests/test_install_update.py, tests/test_planning_integrity.py, tests/test_phase_runtime.py, tests/test_session_delivery.py</read_first>
  <precondition>Coordinator has integrated code-05's CR-01/02/03 correction commits and joined doc correction DOC-01, then locally merged frozen PR93 into PR97 without rewriting either history; all earlier writers on these six paths have finished. PR93 dependency supplies planning_integrity.py and its tests. No test is run against a worker's uncommitted checkout.</precondition>
  <action>Implement only the shared-interface reconciliation detailed in STACK-PLAN. First preserve the coordinator's genuine installed-native composition RED receipt; on the intended corrected-native plus frozen93 joined input, run the same installed tracer before the fix and record the actual native-query failure. Extend the existing native/installed suites for three exact adapters, new and existing ordinary phase/quick sessions, unknown prewrite-prefixed verbs, native OSError output, ordinary handler success/error integrity_warnings, malformed canonical planning commit refusal, authored-record sentinels and unchanged real index. A named assertion after successful installation/denial/ticket dispatch is RED; missing imports/files, zero tests or setup crashes are invalid. Commit test-only additions/receipt before adapter fixes. Add no new harness/file: existing tests/test_same_agent_worktree.py and tests/test_install.py can exercise the join, while imported planning tests retain their own behavior. In phase.py preserve both imports, planning.integrity registration, ordinary registered-verb snapshot/mutation_warnings behavior and VerbError integrity_warnings emission, together with native bounded UTF-8 discovery and native OSError handling. Validate handler existence before a bypass. Use one exact registered adapter set containing only prewrite.request, prewrite.begin and prewrite.confirm for workspace=None selection, canonical snapshot bypass and native OSError boundary; no startswith exemption, unknown-verb bypass, removal of planning validation or blanket disabling of integrity warnings. These three handlers write journal/session metadata in Git common-dir, not canonical .planning records; future planning-mutating verbs do not inherit the exception. Keep initializer routing and all ordinary behavior from PR93. Resolve installer union with destructive-git-guard.py and planning-integrity.sh retained, one advisory-first/source-second editing group, user hooks and registration identities preserved; Python hooks use Python/runpy launchers and timeout120, source-prewrite timeout30, other managed hooks10, existing host-specific timeouts unchanged. Retain source shell/native exit propagation and Unicode launchers. Reconcile only RULES Hooks and validation plus hooks README to describe destructive, canonical-planning and conditional native controls together, including Python entrypoints/adapters and limits. Do not copy PR91 guard-workflow prose or PR94 cleanup introduction from the disposable all-six composition into PR97. Run matching GREEN and the focused checks below, commit only six assigned files plus STACK-SUMMARY, and return exact dependency/integration/test revisions and remaining live limits. The coordinator owns Git merge/base/publication and final local combined-original-six checks; workers do not alter frozen heads.</action>
  <behavior>Installed native request/begin/confirm complete Git-only new and existing phase/quick paths without snapshot(None), while canonical malformed planning still blocks and ordinary success/error warnings preserve authored records. Both hosts retain all intended managed registrations/order/timeouts and user hooks. Runtime confirm still cannot certify live host binding.</behavior>
  <acceptance_criteria>AW-03/05/06/08 integration remains intact at the joined stack: handler-validated exact native exception, all ordinary PR93 snapshot/warning/error/commit controls preserved, no index/authored-byte loss, actual installed pipeline and timeout union verified, no unrelated PR91/94 changes in the PR97 own-change diff. Genuine installed RED precedes corresponding GREEN; code-05 defects and live movement are not declared resolved by this task alone.</acceptance_criteria>
  <verify><automated>python -m unittest discover -s tests -p test_same_agent_worktree.py -v</automated><fails_when>Nonzero exit, zero cases, snapshot(None), native/ordinary-session regression, unknown-verb bypass or simulated behavior labeled live.</fails_when><automated>python -m unittest discover -s tests -p test_install.py -k registered_hooks_run_planning_integrity_from_installed_hosts -v</automated><fails_when>Nonzero exit, zero cases, missing canonical-planning denial or changed real index/authored bytes.</fails_when><automated>python -m unittest discover -s tests -p test_install.py -k installed_runtime_answers_its_verb_contract -v</automated><fails_when>Nonzero exit, zero cases, missing native/planning verb or incorrect structured result.</fails_when><automated>python -m unittest discover -s tests -p test_install_update.py -v</automated><fails_when>Nonzero exit, zero cases, lost/duplicated managed or user hook, wrong launcher/order/timeout or damaged installed records.</fails_when><automated>python -m unittest discover -s tests -p test_planning_integrity.py -v</automated><fails_when>Nonzero exit, zero cases, malformed canonical commit allowed, absent success/error warning or lost authored/index data.</fails_when><automated>python -m unittest discover -s tests -p test_phase_runtime.py -v</automated><fails_when>Nonzero exit, zero cases or ordinary runtime verb regression.</fails_when><automated>python -m unittest discover -s tests -p test_session_delivery.py -v</automated><fails_when>Nonzero exit, zero cases, changed phase/quick session ownership/base or unintended checkout/sync.</fails_when></verify>
  <done>The exact frozen93-on92/native97 join has passing focused receipts and committed STACK-SUMMARY; independent code, integration and narrow documentation reviews confirm both controls survive. The coordinator then performs the separate disposable original-six composition check/review, without publishing it or altering those heads. Live native movement remains unverified unless separately observed.</done>
</task>
<task type="auto">
  <name>Task 5: Give the observed Windows validation workload a bounded 45-minute job budget</name>
  <files>.github/workflows/validate.yml</files>
  <read_first>docs/maintenance/issue87-auto-worktree/CONTEXT.md, docs/maintenance/issue87-auto-worktree/CI-PLAN.md, docs/maintenance/issue87-auto-worktree/CI-DIAGNOSIS.md, docs/maintenance/issue87-auto-worktree/COMPOSITION.md, .github/workflows/validate.yml, .ai/runtime/requirements.txt, captured run38832833234 logs/metadata</read_first>
  <precondition>Coordinator has joined the independent diagnosis of run38832833234 and obtained an independent check of this amendment, then assigns a fresh isolated targeted-fixer or coder the exact workflow path and CI-SUMMARY. Earlier source writers have finished; the intended implementation input and workflow bytes are captured.</precondition>
  <action>Under D-01/D-04 and the bounded CI exception recorded in CONTEXT, preserve the real job-timeout RED at production21488ca: Windows Python746 passed, tier10 and advisory60 passed, context was canceled and location skipped; aggregate validate failed. Change only jobs.platform.timeout-minutes to the existing matrix.os conditional expression specified in CI-PLAN, yielding integer45 for windows-latest and30 for ubuntu-latest, with an adjacent comment grounded in observed duration. Keep the matrix, job names, triggers, permissions, Python3.11, action versions, dependency install, full Python command, all four Bash commands/order, per-test limits and aggregate failure semantics identical. This is configuration-only recovery, so the existing observed timeout is the RED; no new test, benchmark, harness, shard, cache, infrastructure or action upgrade is needed. Parse and inspect the YAML and scoped diff, record actual results in CI-SUMMARY, and commit only that receipt and the workflow. Coordinator integrates and publishes the changed CI input for a fresh run; a manual rerun of a healthy unchanged job is not the repair. Fresh bounded independent review and final verifier reconciliation must cover the actual new revision.</action>
  <acceptance_criteria>AW-08 retains honest evidence: Windows budget45/Ubuntu30 with unchanged required coverage and fail-closed aggregate; fresh CI completes Python and all four Bash suites on both platforms and validate succeeds at the new source/config revision. Source preservation/composition receipts remain scoped to their unchanged input boundaries. AW-01/AW-04 live-host gaps remain unverified/human_needed, PR97 stays draft based on93, issue87 stays open and all six original heads remain frozen.</acceptance_criteria>
  <verify><automated>python -c "import pathlib, yaml; d=yaml.load(pathlib.Path('.github/workflows/validate.yml').read_text(encoding='utf-8'), Loader=yaml.BaseLoader); print(d['jobs']['platform']['timeout-minutes'])"</automated><fails_when>Nonzero exit, YAML parse error, absent job budget, or printed expression differs from CI-PLAN's exact Windows45/Ubuntu30 expression on inspection.</fails_when><automated>git diff --check</automated><fails_when>Nonzero exit or whitespace diagnostics.</fails_when><manual>Compare the parsed workflow and scoped Git diff against the captured input as specified in CI-PLAN: only the platform timeout/comment differs, both matrix values resolve to their required integer budgets and every command/aggregate/protection remains identical. Coordinator then observes the new CI run: either platform incomplete/canceled/non-success, any missing Python or Bash result, or non-success validate prevents GREEN.</manual></verify>
  <done>Workflow and CI-SUMMARY are committed with structural/diff receipts; coordinator obtains fresh actual CI GREEN, independent bounded review and revision-specific verifier reconciliation. No canceled or skipped suite is labeled passed and live acceptance is not waived.</done>
</task>
</tasks>

## Independent behavioral matrix and evidence layers

Consume coordinator-owned MATRIX A1-A7 as the native acceptance rows, plus
retained controls N1-N2, S1-S3, M1-M3, P1-P2, D1-D2, B1-B2, V1-V2, I1, H1 and
R1. Native A1-A7 are committed in the final preparation input. Prior matrix preparation wording is not authority
to drop same-agent movement. Task 1 and fresh reviewers assess these native cases:

| Family | Required case and legitimate control |
|---|---|
| Native positive | Actual installed denial -> actionable same-model protocol/ticket -> advertised schema fixture -> simulated native creation using actual registered WorktreeCreate -> same stable simulated actor/default destination cwd -> relative fresh read -> rebuilt edit once. Test subsequent simulated turn defaults too. Label SIMULATED. |
| Actual exports/consumers | Installed Claude coordinator/coder permit EnterWorktree while unrelated restrictions remain; installed CLAUDE protocol link and six workflow routes consume it. Skill allowed-tools is not mistaken for tool availability, and context:fork is never used. |
| Workflow request / ordinary existing sessions | Real-Git plus simulated native contract covers workflow entry with no prior write/denial: known-unit new bootstrap -> fresh native creation -> adoption, and existing ordinary phase and quick sessions with no native-creation journal -> actual native path entry/default-context proof -> reused confirmation without creation/adoption/metadata rewrite. Missing/ambiguous session and new/existing mode mismatch refuse. No fake denied edit or retroactive creation journal. |
| Capability/refusal | Missing tool, missing/incompatible creation schema, ineligible/pinned/already-worktree role, policy refusal, untrusted/missing creation hook, unsupported Codex and absent/ambiguous identity. No workaround child, shell cd or guessed invocation. Correct isolated control proceeds without movement. |
| Creation/approval | Explicit local pinned base; custom ignored root; offline; registered/unregistered existing destination or branch collision; ordinary dispatch reuse control. wf-entry creation refuses existing-name reuse; actual existing-path operation preserves approval and role restrictions. |
| Context/identity | Native completion missing, old-root default cwd, only explicit cwd override works, wrong actor, branch/base/root/context drift, intended-root marker without host action, original environment project dir still old. Reject native completion claims; verify destination-local control separately. |
| Failure/concurrency | Denied native call; timeout before/after creation; missing native result; same-ticket concurrent calls; different units; stale ticket; changed targets; repeated old edit. Inspect native/journal/Git before retries; no duplicate tree, second edit or cleanup. |
| Dirty data | Staged/unstaged/untracked/ignored/binary bytes and index preservation through chosen fresh custom creation, error/retry; dirty-dependent intent not copied/replayed. Any legitimate host relocation has full per-change accounting, never inferred from missing primary bytes. Registered WorktreeRemove preserves native-owned clean/dirty/ignored-only/uncertain checkout and journal; ordinary dispatch removal remains unchanged. |
| Classification | Both hosts ordinary in-repo notes and resolved-OS-temp plain nongit create/update without identity; read-only no ticket; source Markdown, mixed, rename/delete/Move all source; Windows/Unicode/CRLF/relative/absolute paths, symlink/junction/hardlink/nested-repo/traversal/cross-root/malformed controls. |
| Cancellation/pipeline | Exact native synchronous deny JSON/exit2, one installed editing group advisory first; Windows actual launcher status; original pending mutation never executes. Outer host launch/error/timeout failures are reported limitations, never proof of enforcement. |

Native A-row coverage: A1 = AW-01/05/06; A2 = AW-02/06; A3 = AW-02/07;
A4 = AW-01/05/08; A5 = AW-05/07; A6 = AW-03/04; A7 = AW-02/08.

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Native event to local ticket/Git operation | Input/paths/identity claims must match actual process/Git facts; installed host selection is explicit, not inferred from payload. |
| Model instruction to native host transition | Only actual available native tool/schema and eligible same caller can move itself; runtime markers do not certify host identity, permissions or default context. |
| Creation journal to WorktreeCreate and session registration | Exact reserved new name/base/root controls creation; existing-name reuse cannot bypass native existing-path approval. |
| Primary dirty state to fresh destination | No silent transfer/replay or data loss; destination reads are fresh and any legitimate native relocation is separately accounted for. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| [T-AW-01](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | Tampering / Elevation of Privilege | Source classification, old mutation and dirty-data boundary | high | mitigate | Tasks 1-2 AW-03/04/05: strict all-target decisions, narrow notes, original denial, no blind copy/replay, fresh reads and dirty snapshots; real-Git/native pipeline cases. |
| [T-AW-02](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | Spoofing / Tampering / Denial of Service | Ticket, work identity, native creation and retry | high | mitigate | Tasks 1-2 AW-02/06/07: exact actor/request/unit linkage, bounded lock/journal, pinned base, fresh name, refusal on existing-name collision, uncertain-result inspection; race/reuse/approval-bypass tests. |
| [T-AW-03](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | Spoofing / Tampering | Same-agent native availability/entry and installed orchestration | high | mitigate | All tasks AW-01/02/06/08: positive schema/role/policy/trusted-hook gate, actual native call and default-context proof, no child/cd substitute, actual exports, explicit SIMULATED fixtures and separate live acceptance. |

Canonical keys remain `Tasaddar12/ai-engineering-template/source-prewrite/` plus
`target-confinement`, `unit-identity`, `host-transition-proof`; issue 98 is OPEN,
all three unresolved and unimplemented. No new identities or mitigation claims.
Coordinator reconciles the changed same-agent acceptance within those entries;
workers make no provider writes. Distinct from issues 95/96. L2 review applies to
these changed trust boundaries; storing no payload/transcript contents bounds
disclosure, and exact receipts support review without claiming audit authentication.
Task 4 carries these same risks across the dependency join: T-AW-01 requires
canonical planning/authored/index preservation, and T-AW-03 requires actual
installed native/planning routing and exception output. The exact-set adapter
exception is not a new canonical risk identity or a verified mitigation.
</threat_model>

<verification>
No tests, source implementation, provider writes or native operations run in this
preparer assignment. Future check commands are grounded in existing suites or the
new files Task 1 creates. Existing source-denial RED38b7b1c is historical boundary
evidence; fresh native-route RED and matching GREEN are mandatory before claiming
the new implementation. Zero-case/setup errors are not evidence. Record revision,
command, case count, assertion/result, commits and actual skips in summaries.

Run every frontmatter command after implementation, in the implementation root.
Nonzero exit, zero required cases, preservation mismatch, forbidden reuse or
missing native-route wiring is a gap. Inspect implementation-base diff of
.ai/hooks/worktree-guard.sh: any byte change violates scope. Fresh code-reviewer
assesses source/tests and threat boundaries; integration-checker traces installed
role/CLAUDE exports, six routes, ticket/denial, native gate/call contract, actual
creation callback/adoption and fresh rebuilt edit. Independent doc-verifier checks
the four doc-writer paths, explicitly the narrow RULES section, after integration.
Verifier reconciles AW-01 through AW-08 and all evidence layers.
Task 4 additionally requires independent review of the exact stacked integration
revision and the separate disposable final97/original-six composition described
in STACK-PLAN. Earlier e464 original-six checks and uncorrected9060 RED are inputs,
not final native97 composition GREEN. No composition branch is published.

Live native smoke is UNAVAILABLE HERE and remains required for a conclusive actual
same-agent movement claim. On an available eligible target Claude host record its
actual version/tool schema, hook trust/policy, same session/actor identity, original
cwd/root/branch/base and dirty inventory. Trigger source denial and show the old
mutation did not run; the same existing agent invokes its advertised native
creation tool; observe native completion. Subsequent tools without cwd overrides,
including a later turn, must use destination defaults, permissions and loaded
project context. Freshly read and rebuild the edit once, verify only the intended
destination changed, and account for all initial staged/unstaged/untracked/ignored
data. Exercise denied/uncertain/native-existing-path approval and offline cases.
No hook output, runtime confirm or simulated host adapter proves these live facts.

The lack of that live tool in this executor does not block writing/reviewing the
conditionally supported Claude implementation. Keep its code/fixture status
distinct from actual live acceptance. Without observed smoke, report live native
entry unverified and keep PR97 draft/issue87 open; never call the user's same-agent
goal completely verified. Codex movement remains unsupported by current plumbing,
not fulfilled by cancellation or an unrelated host product feature.
</verification>

## Four-source coverage audit

| Source | ID | Required outcome / boundary | Coverage / disposition |
|---|---|---|---|
| GOAL | ISSUE87 | Actually move same existing agent after source attempt | Tasks 1-3; conditional Claude native route, live smoke explicitly unverified |
| REQ | ISSUE87 | Maintenance acceptance outside adoption skeleton | AW-01..08; no invented adoption phase/requirements |
| CONTEXT | D-01/D-04 | Separate draft, never merge; frozen six/73/74/providers/infrastructure excluded | Ownership/exclusions and coordinator delivery |
| CONTEXT | D-02 | Source versus notes, no retry loop | AW-03/05/07; narrow notes, next native action or precise unsupported |
| CONTEXT | D-03 | Preserve data and stop old-root edit | AW-04/05; snapshots/accounting, original denial and fresh rebuild |
| CONTEXT | D-05 | Same existing agent and subsequent default context | AW-01/08; native contract plus distinct live proof; no cd/child substitute |
| CONTEXT | D-06 | Positive availability/role/policy/trusted creation gate, no approval bypass | AW-02/06/07; installed exports, fresh-name-only provider, real path approval |
| CONTEXT | D-07 | Codex unsupported controller; simulation is not live | Objective, capability cases and live gate |
| RESEARCH | Native capabilities | Official target Claude semantics support instruction-driven native route | Implement gated route; this executor's missing tool limits live observation only |
| RESEARCH | Source map | Restrictive role exports, six shell routes, creation reuse and phase-only adopt | AW-06; exact producer/consumer changes above |
| RESEARCH | Prior RED/matrix | Cancellation/note cases useful but preparation-only assertions insufficient | Task 1 fresh native-route RED; preserve valid controls and historical receipts |
| RESEARCH | Actual CI timeout | Run38832833234 exhausts Windows30-minute job budget after Python GREEN | Task 5 / CI-PLAN; Windows45, Ubuntu30, unchanged coverage and fresh CI required |
| CONTEXT | D-01/D-04 CI exception | Existing implementation/recovery authority, only validate job budget/comment added | Task 5 exact ownership; other provider, frozen-head and live-host boundaries retained |

Hardest constraint is real native same-agent default context, addressed by the
first tracer and not deferred to docs. Pre-mortem controls: unavailable/schema
tool -> positive gates; approval bypass through reused creation name -> dedicated
refusal; apparently moved agent still writing old root -> default-cwd/context and
fresh-read tests plus live gate. No complexity/deadline-based scope reduction.

<success_criteria>
Source and docs implement the conditional native same-agent route, required
deterministic checks pass at the reported integrated revision with fresh genuine
RED/GREEN, and independent reviewers confirm actual export/creation/workflow
wiring and data safety. Task 5 additionally requires the new CI input's complete
both-platform Python/four-Bash and aggregate GREEN; prior partial run is RED.
Actual same-agent fulfillment is verified only with live
native evidence. If unavailable, return implemented/fixture-verified conditional
behavior and live acceptance unverified; no preparation/manual-child fallback is
presented as fulfillment. Keep PR97 draft, issue87 open and never merge.
</success_criteria>

<output>
Source worker updates docs/maintenance/issue87-auto-worktree/IMPLEMENTATION-SUMMARY.md
with new native-route commits, TDD Evidence, Checks, AW coverage, explicitly
SIMULATED contract results, live gaps and issue98 Threat Outcomes. Doc-writer owns
docs/maintenance/issue87-auto-worktree/DOCUMENTATION-SUMMARY.md. Summaries belong
to assigned authors. Task 4 returns
docs/maintenance/issue87-auto-worktree/STACK-SUMMARY.md with exact frozen parents,
joined input/output tips, real RED/GREEN and focused receipts, preservation and
scope-diff evidence, review obligations and unverified live behavior. Task 5 returns
docs/maintenance/issue87-auto-worktree/CI-SUMMARY.md with observed timeout RED,
input/output revision, exact workflow-only delta, structural/diff receipts, and
pending or actual fresh CI/review results; never invent future GREEN. Coordinator
records the separate disposable composition evidence and keeps all frozen heads
unchanged. Coordinator integrates source before docs, commits/reconciles
native MATRIX and canonical issue98 scope, obtains independent plan recheck before
source release and independent final reviews, and owns publication. No adoption
roadmap/status mutation, provider worker writes or merge is proposed.
</output>
