---
phase: maintenance-issue87-auto-worktree
plan: "06-codex"
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [ISSUE87]
acceptance: [CW-01, CW-02, CW-03, CW-04, CW-05, CW-06]
files_modified:
  - .ai/runtime/lib/codex_worktree.py
  - .ai/hooks/codex-worktree.py
  - tests/test_codex_worktree.py
  - .ai/install-assets/codex-worktree.py
  - .ai/install.py
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - .ai/references/same-agent-worktree.md
  - .ai/references/worktree-sessions.md
  - .ai/hooks/README.md
  - .ai/runtime/README.md
  - .ai/RULES.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
  - tests/test_same_agent_worktree.py
files_deleted: []
documentation:
  - .ai/references/same-agent-worktree.md
  - .ai/references/worktree-sessions.md
  - .ai/hooks/README.md
  - .ai/runtime/README.md
  - .ai/RULES.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
resources: [issue87-codex-native-temp-fixtures]
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_codex_worktree.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, codex_worktree_install, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, codex_worktree_native_generated_guard, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, selected_host_preserves_settings_instructions_and_worker_routes, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install_update.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install_migration.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_same_agent_worktree.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_prewrite.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_workflow_links.py, -v]
issue_refs:
  - id: ISSUE98
    summary: Preserve canonical source-confinement, unit-identity and host-transition risk tracking for the Codex addition.
    variant: Security risk
    state: unresolved
    relationship: followup
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/98
    issueNumber: 98
user_setup: []
must_haves:
  truths:
    - An explicitly selected phase or quick launch starts a new native Codex run with one validated runtime-owned destination as its default cwd and workspace root.
    - Primary and invalid-root supported tool operations are refused before acting; exact active runtime-owned plan workers remain usable, and structured mutation targets retain the established narrow note allowance.
    - Known disabled, untrusted, modified, missing or unlaunchable enforcement stops the launcher before any model run; user configuration and native trust remain authoritative.
    - The launcher never weakens effective sandbox or approval restrictions; a stricter, differing or ambiguous policy refuses startup instead of being replaced by workspace-write.
    - Fresh install, reinstall and managed update ship the same reachable launcher and synchronous guards without losing custom hooks, Claude behavior or model settings.
    - Actual installed Codex executes the generated guard and refuses both a shell and a patch attempt, separately from startup refusal and simulated fixtures.
    - Documentation distinguishes startup isolation, active-session limitations and transport/sandbox boundaries without waiving original AW acceptance.
  artifacts:
    - path: .ai/runtime/lib/codex_worktree.py
      provides: Bounded native launch preflight and Codex hook decisions using existing runtime-owned session selection.
    - path: .ai/hooks/codex-worktree.py
      provides: Synchronous generated Python adapter with normalized denial for supported events.
    - path: .ai/install-assets/codex-worktree.py
      provides: Thin installed .codex/codex-worktree.py entry point into the runtime launcher.
    - path: tests/test_codex_worktree.py
      provides: Real-Git behavioral regression coverage for launch selection, guard decisions and refusal preservation.
    - path: tests/test_install.py
      provides: Generated installed-adapter assertions and reproducible actual-native local-provider smoke.
    - path: .ai/references/same-agent-worktree.md
      provides: Canonical Codex startup instructions and unchanged conditional Claude movement contract.
  key_links:
    - from: Installed .codex/codex-worktree.py
      to: runtime/lib/codex_worktree.py launcher_main
      via: Existing session.open with explicit local base and no synchronization, exact destination validation, native --cd and invocation-scoped --enable hooks.
    - from: Native hooks/list for the selected cwd
      to: Generated required project guard registrations and handlers
      via: Exact enabled/eventName/sourcePath/matcher/command identity and trusted or managed state before model startup.
    - from: Codex PreToolUse, SessionStart and UserPromptSubmit registrations
      to: .codex/hooks/codex-worktree.py hook_main
      via: Installed synchronous platform launcher with preserved exit status and bounded runtime decisions.
    - from: Six workflows and installed guides
      to: Canonical startup protocol
      via: Short Codex-specific references; no child launch from an active caller as movement.
---

<objective>
Implement the supported Codex equivalent authorized in CONTEXT: select and
validate the worktree before starting a new native run, and install synchronous
guards for supported operations. This is Task 6 of the existing issue87
maintenance change, not a new adopting-project phase. The preparation input is
1ead8809a4df9047316ad80698520f4511687a5c; PR97 remains a draft on PR93, which
depends on PR92. The coordinator owns integration and publication.

Original AW-01..08 acceptance, historical RED/GREEN receipts and live
human_needed observations remain intact. Startup defaults and tool denial do not
prove relocation of an existing agent. No app-server controller product,
detached-worktree adoption, active-agent child substitute, data copy, implicit
sync/fetch, phase creation, cleanup, installation, benchmark or PR merge is added.
</objective>

<execution_context>
@.ai/commands/execute-phase.md
@.ai/templates/summary.md
@.ai/runtime/TEMPLATE-CONTRACT.md
@.ai/references/methods/tdd.md
</execution_context>

<context>
@docs/maintenance/issue87-auto-worktree/CONTEXT.md
@docs/maintenance/issue87-auto-worktree/CODEX-RESEARCH.md
@docs/maintenance/issue87-auto-worktree/PLAN.md
@docs/maintenance/issue87-auto-worktree/STACK-PLAN.md
@docs/maintenance/issue87-auto-worktree/CI-PLAN.md
@.ai/references/same-agent-worktree.md
@.ai/references/worktree-sessions.md
@.ai/runtime/lib/worktrees.py
@.ai/runtime/lib/prewrite.py
@.ai/install.py

PROJECT, STATE, ROADMAP and REQUIREMENTS are an unfilled teaching skeleton;
read them as instructed and leave them unchanged. ISSUE87 and CW-01..06 come
from this maintenance CONTEXT, not those example requirements. PR99's separate
model-routing changes are not a dependency to absorb or an owned checkout.
</context>

## Evidence and fixed interfaces

Installed Codex 0.162.0-alpha.17.2 actually demonstrated new-run destination
defaults and generic synchronous Bash denial. Its native --worktree produced a
detached checkout; use the existing phase/quick session contract instead. The
generic probe used temporary trust bypass and is not production enforcement or
GREEN for this addition. Confounded earlier probes remain recorded in research.

The generated app-server schema establishes read-only `hooks/list` with optional
`cwds: string[]`. Response `data[]` requires `cwd`, `hooks`, `warnings`, `errors`.
Each command hook requires `handlerType=command`, `command`, `enabled`,
`eventName`, `isManaged`, `key`, `source`, `sourcePath`, `timeoutSec`,
`trustStatus`, `currentHash`, `displayOrder`; matcher and statusMessage are
optional. Event metadata uses `preToolUse`, `sessionStart`, `userPromptSubmit`.
Trust is exactly `managed|untrusted|trusted|modified`. Error entries carry
`message` and `path`. Empty warnings/errors do not imply trust: the captured old
rpc probe had enabled=true/trustStatus=untrusted. Do not invent a
`hooksTrusted` flag, treat enabled as trust, use a trust bypass in production or
read/modify a private trust store directly.

Implement one bounded read-only preflight exchange with the installed native
app-server: initialize/initialized, hooks/list for the exact destination, then
close the helper. It starts no thread/turn and is not a controlling host. Use
the same --cd and invocation hook controls as the eventual run. Verify the
effective native command representation: the actual no-thread differential
probe reports commandWindows as metadata.command on Windows. Compare that
OS-selected generated command on Windows and the POSIX command on POSIX. Match native identity to the
parsed installed registration, event, matcher, source/config path and handler;
require every required handler enabled and trusted/managed, with no unresolved
load errors or relevant warnings. Missing schema/capability, ambiguity,
untrusted/modified, managed disable or timeout returns a visible setup error
before a model starts. Preserve the native review/trust process.

The capability directory is
`C:/Users/killi/AppData/Local/Temp/codex87-capability-5b752dbfe8894db38c2dd65872b1417f`.
It now holds `provenance-and-receipts.json`, `cli-receipts.json`,
`hooks-list-command-selection.json`, saved CLI help and schemas. The exact old
successful inline probe was saved afterward as
`successful-shell-probe.from-inline.py`; it was not rerun from that path.
`canned_guard_fixture.py` was AST/help checked only, never functionally executed.
Its reusable CLI requires --codex ABS, --output-dir FRESH_OS_TEMP,
--cwd TEMP_GIT_CHECKOUT, --hook-command EXACT_EMITTED_COMMAND,
optional --hook-command-windows EXACT_EMITTED_WINDOWS_COMMAND,
--expect-denial GENERATED_REASON, then either --tool shell --shell-command TEXT
or --tool patch --patch-input-file UTF8_PATCH. --test-trust-bypass is an explicit
temporary-fixture exception. B must execute both generated-adapter cases, not
count its AST/help check. Preserve this provenance when adapting its bounded
provider/server/process logic into the owned native test.

Actual `codex --enable hooks --disable plugins features list` exited0 and
reported hooks stable true/plugins stable false. Use that established native
feature control for fixtures; disabledPluginIds does not filter capabilities.
Closed loopback HTTP proxies bound proxy-aware auxiliary traffic, not all
operating-system network traffic. Claim no external model call only with the
captured local-provider requests; never claim a universal network boundary.

## Policy preservation correction: PC-06-codex-context_compliance-01

CONTEXT.md:105 forbids weakening native sandbox/approval policy. The original
Task6A action at line265 selected workspace-write unconditionally, so a configured
read-only policy could be weakened. This correction removes that selection.
The saved `cli-help.stdout` describes --sandbox as selecting policy, not merely
asserting an existing restriction. Production argv must contain no --sandbox,
--ask-for-approval, --approve-for-me, bypass flag or equivalent config override.

Extend the same bounded, no-thread native preflight with `config/read`, using
`{cwd: CALLER_ROOT, includeLayers: true}` and
`{cwd: DESTINATION_ROOT, includeLayers: true}`. The saved
`schemas/v2/ConfigReadParams.json` explicitly defines cwd as selecting the
effective config including project layers. `ConfigReadResponse.json` requires
`config` and `origins`; its actual config fields are `sandbox_mode` (line652),
`approval_policy` (line483), `sandbox_workspace_write` (line662) and
`approvals_reviewer`. No new config or trust keys are introduced.

Use a conservative supported route rather than inventing a policy ordering:
require both effective sandbox_mode values to be exactly workspace-write and
both approval_policy values to be present, non-null, schema-valid and
structurally identical. The schema's AskForApproval at line230 permits the
strings untrusted/on-request/never or its defined granular object; compare the
whole parsed policy without reducing granular settings to a string. Require
the sandbox_workspace_write and approvals_reviewer values to be structurally
identical across caller and destination as well, preserving every configured
writable-root, temp exclusion, network and reviewer setting; nullable values
are retained as reported, never interpreted as an additional permission grant.
Pass no policy values back as overrides: the native run loads the same effective
configuration with only --cd and invocation hook enabling. Preserve native
managed requirements and approval review without a config/requirements bypass.

If either root is read-only, refuse with a diagnostic that this source-writing
route requires workspace-write and will not relax read-only. Also refuse
danger-full-access, missing/null sandbox or approval policy, differing policy
objects/settings, unsupported schema/policy, read errors, timeout or unresolved
effective-policy ambiguity before a model starts. Do not guess native defaults,
rank approval modes, change user config or prompt for relaxation. Re-read the
policy immediately before launch; any change from the accepted snapshot refuses
startup. Later host/config races retain the plan's explicit external limits.

A's existing runtime suite must add regression cases for caller or destination
read-only (including attempted native promotion), null/unsupported policy,
differing project layers, granular approval mismatch and changed preflight
snapshot. Each must prove zero model-launch calls and unchanged configuration.
The positive matching workspace-write case proves original network/temp/root
and approval/reviewer settings survive with no policy override in native argv.
B's installed launcher tests exercise the same stricter-policy refusal and
unchanged argv/config through the generated entry point. C documents this
preservation/refusal prerequisite. Existing task checks cover these assertions;
no new worker, source ownership or verification command is added.

The existing runtime verb is `session.open KIND LABEL --base COMMIT --no-sync`.
Do not change its public contract or its normal sync default. New launches use
an explicitly resolved local commit; no origin refresh. Reuse retains the
recorded base and accumulated branch commits; validate base commit/ancestry,
not equality of current HEAD to an old base. A caller-supplied different base
must refuse rather than reset an existing unit. Phase selection first uses
existing phase.locate and must find the requested phase. Quick requires an
explicit unit label and does not create canonical quick/phase records.

## Worker compatibility correction: PC-06-codex-worker-compatibility-01

This coordinator finding arose during Task6A implementation, after the prior
independent plan checks; independent checking of this correction is pending.
Launcher selection remains restricted to ordinary phase/quick sessions. Hook
root validation has a wider existing caller set: either one exact valid open
phase/quick session or one exact active runtime-owned plan-worker wave entry.
Requiring every hook caller to appear in sessions.json would block the parallel
isolated executors created by the existing runtime.

The existing interfaces are worktrees.state_dir (worktrees.py:80),
manifest_path/load_manifest (:186/:191), and create (:253). state_dir resolves
the shared Git common directory's ai-phase metadata; manifests live under its
waves directory. Existing envelopes contain phase and entries. create records
entry.plan, nullable entry.phase, isolation=orchestrator-worktree, worktree,
branch, base, status=active, files, deletions and created_at (:292..304).
The envelope uses the requested phase string or current; the entry uses the
actual nullable phase representation. Validate those existing representations
and exact phase/plan identity without introducing a new manifest field/schema.

For hook validation only, inspect the actual common-root waves manifests through
the existing state_dir/load_manifest interfaces and admit exactly one matching
active orchestrator-worktree entry after validating the manifest envelope and
entry shape. load_manifest intentionally returns an empty envelope on malformed
input (:193..201); raw read/schema/error screening is required before relying
on that fallback, so malformed or ambiguous candidate ownership cannot silently
be treated as absence. Missing ownership, unreadable/malformed candidate state,
duplicate/conflicting path, branch or phase/plan ownership, non-active status,
foreign common root or any inconsistent identity refuses source execution.
Do not edit load_manifest, lifecycle helpers or the persisted schema.

Require the exact canonical registered worktree path, its same common Git
repository, actual non-detached isolated branch matching the stored branch,
captured base resolving to a commit and remaining an ancestor of accumulated
HEAD, and exact owning phase/plan entry. Validate the physical worker root as
an immediate child of the configured worktree root as create does. A normal
worker path is <sanitized-plan>-<token>, while its default branch is
phase-<sanitized-plan>-<token>; do not impose path-basename equals branch on a
worker. Registration plus an isolated-looking branch alone never grants access.
No Claude native-journal exception, arbitrary linked checkout, merged/closed,
blocked/cleaned/missing entry or stale historical worker is admitted. After
integration, corrections use a fresh coordinator-created active worktree rather
than broadening closed-entry admission. Preserve primary/index data and permit
legitimate worker source edits, shell tests and ordinary commits while active.

Preserve the existing ordinary phase adoption route as part of the same caller
compatibility correction. worktrees.adopt_session (:835) records an open
phase session for an already registered named checkout at its actual canonical
path; it need not have the generated session path/name. Validate the exact
stored path and branch against Git/common root, live isolated namespace,
captured base ancestry, unique ordinary session identity and expected phase/label
through existing phase.locate/phase facts where applicable. Do not infer unit
identity from a kind-label branch prefix, path-basename equals branch, or a
generated-path template. An authoritative ordinary session.adopt receipt must
remain valid with accumulated commits/data even at a differently named linked
path. This adds no adoption operation or origin field, grants no arbitrary
linked checkout access, and is distinct from the excluded Claude native journal
and detached-worktree adoption. Worker creation's configured-root path rule
above applies to its own wave receipt, not adopted ordinary phase sessions.

A's existing runtime suite adds real-Git positive source and shell cases for
an active worktrees.create worker with no phase/quick session, including two
distinct concurrent worker units and accumulated commits. It adds negative
unit/common-root/path/branch/base, detached, duplicate, malformed, non-active and
foreign-manifest cases without weakening the ordinary-session checks. B proves
the same active-worker allowance and refusal boundary through the generated
installed guard. C explains ordinary launcher sessions versus active worker
units. Existing checks and ownership remain unchanged. This is another
T-AW-02/unit-identity occurrence in existing issue98, not a new risk identity.
Both A and B also retain an adopted named phase session at a non-generated path,
with source/shell use and accumulated commits intact, and refuse wrong
unit/phase-label, branch or recorded-path variants. C documents that valid
ordinary adopted sessions use receipt/Git identity rather than naming inference.

The agreed producer API is `codex_worktree.launcher_main(argv=None)` and
`codex_worktree.hook_main(argv=None)`, backed by
`.ai/runtime/lib/codex_worktree.py`. A owns this module and the Python hook;
B's thin asset loads the adjacent installed runtime and calls launcher_main.
Do not add phase.py verbs or change worktrees.py/prewrite.py to duplicate
existing mechanisms. A may call their public helpers. Any needed change outside
owned paths returns a concrete interface finding to the coordinator.

## Execution and ownership

This is one supported Codex launch/guard outcome with three separately assigned
components. Each worker receives only its row, relevant read_first inputs,
approved interface and predecessor SUMMARY. All run in coordinator-created,
pinned isolated worktrees and commit only owned paths plus their SUMMARY.

| Component | Needs / creates | Exact ownership | Order |
|---|---|---|---|
| A: runtime and guard | Existing session and source classifiers; creates launcher_main/hook_main and behavioral tests | .ai/runtime/lib/codex_worktree.py; .ai/hooks/codex-worktree.py; tests/test_codex_worktree.py; CODEX-RUNTIME-SUMMARY.md in this maintenance directory | First |
| B: installation and native integration | A API and committed hook/module; creates reachable installed launcher, registrations, installer and actual-native evidence | .ai/install-assets/codex-worktree.py; .ai/install.py; tests/test_install.py; tests/test_install_update.py; tests/test_install_migration.py; CODEX-INSTALL-SUMMARY.md in this directory | Depends on integrated A |
| C: documentation consumers | Integrated A+B and actual results; creates accurate guides and six workflow references | All eleven documentation paths in frontmatter; tests/test_same_agent_worktree.py for documentation/export assertions only; CODEX-DOCUMENTATION-SUMMARY.md in this directory | Depends on integrated A+B |

Disjoint paths alone do not establish test independence. B's installed/native
checks consume A, so A -> B -> C is deliberate. Do not dispatch B against
unintegrated A and call broken fixtures RED or fabricate parallel GREEN. There
is no shared mutable native fixture across workers. Keep summaries distinct;
coordinator writes shared CONTEXT/MATRIX/VERIFICATION and the PR body. No worker
owns model tables, agent TOMLs, .planning/config.yaml, source-prewrite.sh,
worktree-guard.sh, .github, runtime lifecycle/cleanup or the six original drafts.

A names direct-runtime cases with `runtime` in their unittest method names.
First run `python -m unittest discover -s tests -p test_codex_worktree.py -k
installed_primary_shell_is_denied -v` against current registrations: require a
named assertion showing the primary mutation proceeded after successful setup,
then commit test-only. Keep that assertion active without skip/xfail throughout
A; its known pending B result is reported explicitly. A's `-k runtime` command
checks only the produced API/guard. B reruns the identical installed tracer on
joined registrations; only then can the full suite be GREEN. Do not place an
import of the not-yet-created module at suite load time and call that RED.

B's new Codex-only registrations are `PreToolUse` with matcher `*`, and
`SessionStart`/`UserPromptSubmit` without tool matchers, all command handlers
with timeout30 and synchronous behavior (`async` absent/default false or false,
never true). Preserve other script timeouts; the existing Python120 default
does not silently become this guard's bound. Native preflight rejects async
handlers and compares the known definition plus observed OS command without
inventing a trust-hash algorithm. A's bounded helper must distinguish its own
launch failure from a successful trust gate. Later host crash/timeout/config
change can still fail open and is documented as such. Lifecycle checks must not
erase the narrow PreToolUse note allowance or require worktree creation for
ordinary note-only operations; source enforcement belongs at the source tool
boundary and the explicitly selected startup route.

<tasks>
<task type="auto" tdd="true">
  <name>Task 6A: Enforce the validated Codex launch and supported-tool root contract</name>
  <files>.ai/runtime/lib/codex_worktree.py, .ai/hooks/codex-worktree.py, tests/test_codex_worktree.py</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/coder.md, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/references/methods/tdd.md, docs/maintenance/issue87-auto-worktree/CONTEXT.md, docs/maintenance/issue87-auto-worktree/CODEX-RESEARCH.md, this plan's fixed interfaces, .ai/runtime/lib/worktrees.py session_for/open_session/locate_phase, .ai/runtime/lib/prewrite.py facts/existing_session/classification/source_decision, .ai/runtime/phase.py verb_session_open, .ai/hooks/destructive-git-guard.py, tests/test_prewrite.py, tests/test_session_delivery.py, tests/test_same_agent_worktree.py fixture patterns</read_first>
  <precondition>Independent phase-checker has accepted this plan; coordinator supplies exact root/branch/base pins and research native schema/help evidence. No source implementation starts merely because preparation completed.</precondition>
  <behavior>The named test_codex_worktree_installed_primary_shell_is_denied exercises the current installed Bash-hook pipeline: installation/dispatch succeeds but the primary mutation proceeds, establishing behavioral RED before the new guard/registration. Missing new modules or scripts are setup errors, not RED. Retain that tracer unchanged through B's final registration GREEN. Real disposable Git fixtures cover one selected phase/quick destination, reuse without duplication, mismatched unit/common-root/branch/base, detached/unregistered/foreign worktree, preserved primary staged/unstaged/untracked/ignored data, missing destination installed inputs, disabled/untrusted guard setup, stricter/differing/ambiguous sandbox and approval settings, prelaunch policy changes and narrow note controls. A real worktrees.create active worker without a phase/quick session permits structured source edits, shell tests and ordinary commits; two distinct concurrent worker units and accumulated HEAD remain valid. An adopted ordinary named phase session at a non-generated path also passes source/shell use with accumulated commits; wrong phase/label, branch or recorded path refuses without relying on generated naming. Unit/common-root/path/branch/base, detached, duplicate, malformed, non-active and foreign-manifest cases refuse. A successful isolated shell operation such as tests or an ordinary commit stays usable.</behavior>
  <action>Implement CONTEXT's six Codex decisions and CW-01/02/04. Start with the retained installed-current Bash tracer and a test-only RED commit; fixture/import/syntax errors, missing new entry points and zero cases are invalid RED. A's direct-runtime tests then become GREEN, while the installed tracer intentionally awaits B; record that dependency and do not claim full Task6/CW acceptance at A's handoff. The first retained end-to-end slice selects a real runtime phase/quick worktree, validates it and records native launch argv/cwd through a child-process spy, then demonstrates refusal when that root or a structured mutation target is primary. This traces session selection through launch and guard; the spy is explicitly simulated native invocation, with actual native proof assigned to B. Complete the refusal matrix after that slice. Expose a bounded launcher CLI KIND LABEL with optional --base COMMIT, --prompt TEXT and --exec only; no arbitrary trailing native argv. Internally use supported native --cd DESTINATION and invocation-scoped --enable hooks, preserving configured model/effort and all effective sandbox/approval restrictions through the config/read preservation-or-refusal protocol in PC-06-codex-context_compliance-01 above. Pass no sandbox/approval override; stricter, differing or ambiguous effective policy must refuse before a model run. Reject every other argument, including cwd redirection, hook disable, configuration/requirements bypass, profile/config override, extra writable roots, resume/fork/worktree and sandbox/approval weakening. Treat prompt text as data in an argv element. The launcher is a startup entry point only; do not wire it as an active-agent recovery action or infer authenticated host identity from unverified environment names. Validate all known options before worktree creation. Resolve the selected unit through existing runtime helpers, create with explicit captured local base and sync=False only when absent, then independently validate exact registered canonical path/common Git repository, live non-detached isolated branch, unique open unit record, stored base and ancestry. Do not admit a linked tree solely because it is linked or apply Claude's native-journal exception to Codex. Validate both caller and destination installed runtime/configuration/guard files and handler launchability; missing committed installation at the selected base is a dependency, never permission to copy dirty files. Validate effective hooks via the read-only native exchange above before model startup. Known setup failures return bounded diagnostics/nonzero without running a model; preserve any prepared unit for coordinator inspection. Recheck the destination and required file identities immediately before launch. Do not rewrite global features.hooks=false or trust. Hook handling is synchronous, validates payload/default cwd agreement, and normalizes expected/unexpected adapter errors to denial exit2 with actionable stderr. Use existing prewrite classification for structured file/patch operations so tracked source, mixed targets, external/nested repositories, links/reparse/hardlinks and rename/delete retain their existing handling; ordinary allowed scratchpad/OS-temp create/update notes remain allowed without session identity. For hook handling only, validate either the exact unique open phase/quick session or exact unique active runtime-owned wave entry under PC-06-codex-worker-compatibility-01 above; preserve launcher selection as ordinary phase/quick only. Use existing worktrees.state_dir/load_manifest/create metadata, screen malformed input instead of silently accepting load_manifest's empty fallback, validate the actual worker path independently of branch spelling, and preserve active-worker source/shell/commit use without adding lifecycle or schema changes. For ordinary adopted phase sessions validate authoritative receipt/Git/phase identity rather than a generated path or kind-label branch naming rule; do not introduce a new adoption operation. For shell/opaque supported tool calls, apply default-root/unit validity and any actual structured cwd/workdir/path fields the native payload exposes. In primary/invalid roots, deny potentially source-changing or ambiguous actions; narrowly recognized read-only diagnostics may pass. In a validated isolated unit allow ordinary shell tests/commits under workspace-write policy without inventing a general shell-language analyzer. Treat unknown supported tool kinds conservatively at invalid roots. Never parse arbitrary shell text to promise universal target confinement. Startup/pre-prompt handlers revalidate the root and surface refusal according to the actual event contract; do not assume SessionStart has a hard-stop semantic it lacks. Launcher preflight owns the before-model guarantee, PreToolUse owns supported-tool cancellation. Persist no transcript/prompt/secret contents. Record RED/GREEN and any refactor in the owned runtime summary.</action>
  <acceptance_criteria>Public launcher and hook APIs exist; real Git selection/reuse and negative cases are assertion-tested; known unsafe setup/options never reach the native-launch spy. Supported source decisions refuse primary/invalid roots and structured cross-root mutations, allowed notes and isolated tests/commits remain functional, and primary bytes/index are preserved. Global/user models, trust, features and effective sandbox/approval restrictions are unchanged. Read-only, policy mismatch/ambiguity or snapshot drift produces zero model-launch calls; matching workspace-write retains all network/temp/root and granular approval/reviewer settings without policy argv overrides. Valid ordinary adopted named phase sessions remain usable at their recorded non-generated paths with no naming inference. Active runtime-owned workers without session records remain usable through exact wave identity; concurrent distinct workers pass, while malformed/ambiguous/non-active/foreign ownership and root/branch/base mismatches refuse without primary/index loss. The shell/opaque transport boundary is explicit.</acceptance_criteria>
  <verify>
    <automated>python -m unittest discover -s tests -p test_codex_worktree.py -k runtime -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, a required launch/refusal case skipped, unsafe setup or stricter/differing/ambiguous policy reaching the model-launch spy, policy-changing argv/config, a changed primary/index sentinel, legitimate active-worker source/shell/tests/commits blocked by a session-only rule, or invalid/ambiguous/non-active wave ownership admitted.</fails_when>
    <automated>python -m unittest discover -s tests -p test_prewrite.py -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, altered narrow-note/source classification or weakened Claude native identity/confirmation behavior.</fails_when>
  </verify>
  <done>A's test-only behavioral RED precedes source changes, direct-runtime checks pass, and public APIs/hook are committed with CODEX-RUNTIME-SUMMARY. The retained installed tracer is explicitly pending B, not reported GREEN; A's interface is ready for B, while Task6 acceptance remains pending. No actual native success is inferred from the spy. Coordinator integrates A before B.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 6B: Generate and verify the installed Codex launch and guard path</name>
  <files>.ai/install-assets/codex-worktree.py, .ai/install.py, tests/test_install.py, tests/test_install_update.py, tests/test_install_migration.py</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/coder.md, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/references/methods/tdd.md, docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md, docs/maintenance/issue87-auto-worktree/CODEX-RUNTIME-SUMMARY.md, .ai/runtime/lib/codex_worktree.py, .ai/hooks/codex-worktree.py, .ai/install.py payload/host_payload/merge_toml/MANAGED_HOOKS/HOST_HOOKS/managed_scripts/hook_settings, all three owned installer suites, research's saved schema/help/probe helper</read_first>
  <precondition>A is integrated and its direct-runtime GREEN is recorded, while the installed tracer remains explicitly pending B with no skip/xfail or weakened assertion. Existing native Codex and research's reproducible local-provider helper/help are available for actual smoke; absent capability is reported, never repaired with installation or external model access.</precondition>
  <behavior>Fresh, repeated and managed-update fixtures must ship one Codex-only launcher and one required synchronous registration per event without disturbing old managed/custom hooks. features.hooks=false, user ordinary config, native agent model/effort TOMLs and Claude payload remain preserved. Actual generated Windows/POSIX commands propagate denial. Generated-launcher regressions preserve sandbox/approval settings and refuse stricter, differing or ambiguous policies before model startup. Generated-guard fixtures also prove active runtime-owned worker source/shell allowance without a session record and adopted ordinary phase-session use at a non-generated path, and reject malformed, duplicate, foreign or non-active wave ownership and adopted wrong-unit/branch/path records. Real native shell and apply_patch calls reach the installed adapter and are denied with no primary mutation.</behavior>
  <action>Implement CW-03/04/05 using A's agreed APIs. Commit genuine test-only RED before installer changes: assert missing reachable generated launcher/required registration or an installed primary shell mutation actually proceeds, with existing installation/setup succeeding. Add the Codex-only thin asset as .codex/codex-worktree.py using the existing payload/manifest ownership and update mechanisms; source install-assets stay excluded from ordinary payload except this explicit asset mapping. The hook/module copy through existing .ai-to-host paths; do not ship a Codex launch feature into Claude or change any agent/model rendering. Register the new Codex Python guard for synchronous PreToolUse with broad supported-tool matching plus SessionStart and UserPromptSubmit. Use native hook event names in config and actual hooks/list eventName spelling when validating, without inventing an event. Include every new script in managed registration identity/conservation, updater and migration inventories. Keep the existing shared editing group advisory-first/source-second byte behavior, all destructive/planning/context controls, existing timeouts and custom-hook conservation; host-specific guard registrations must not broaden Claude's namespace contract. Use the existing Python/runpy platform launcher pattern and bounded synchronous timeout, preserving actual exit2 and Unicode paths; test missing Python/runtime/script and unexpected adapter errors. Preserve user/global hooks=false and all config unrelated to this feature; --no-hooks install remains unregistered and the launcher then refuses known unenforced setup. Native --enable hooks applies only to the selected invocation. Use the observed OS-selected hooks/list command identity, comparing commandWindows on Windows and command on POSIX; route any actual-platform mismatch to A's owner through the coordinator. Test fresh/reinstall/update/migration, aged managed groups, custom commands in managed groups, malformed config, duplicate registration, features=false, untrusted/modified/managed-disabled and launchability failures with sentinel byte preservation. Through the installed generated guard, create a real active plan worker via worktrees.create and prove structured source and shell calls are allowed with no ordinary session, while malformed/ambiguous/non-active/foreign wave ownership refuses; also prove a valid adopted named ordinary phase session at its recorded non-generated path remains usable and wrong phase/label, branch or path records refuse. Preserve root/branch/base and primary/index controls. Persist the bounded local mock Responses provider and native fixture in tests/test_install.py, adapting canned_guard_fixture.py from the capability directory above. Its new helper is AST/help-only evidence until these actual runs; the old inline probe alone established the successful wire protocol. The native test must never use account credentials or contact an external model: use a new OS-temp CODEX_HOME/Git fixture, explicit sanitized child environment with no inherited credential/provider variables, loopback-only canned provider, finite request count, process/network timeouts and captured sanitized request/response/hook logs. Disable plugins with the actually established --disable plugins feature control in the temporary native fixture; disabledPluginIds alone does not filter capabilities. Inspect the effective fixture and outgoing requests; if plugin suppression cannot be demonstrated, report the exact limitation and do not claim an entirely local clean smoke. Do not change the real Codex home or user hook trust. A vetted fixture-only trust bypass may be used to exercise known temporary hooks; label it and prove the production launcher has no bypass. Run two separately attributed actual-native checks: successful launcher destination/default-root evidence under valid reviewed trust, and PreToolUse refusal for shell plus patch against primary/invalid roots. If SessionStart prevents the latter model from issuing a tool, use a reviewed temporary fixture registration limited to the generated PreToolUse handler to exercise that handler independently; retain a separate full-registration startup-refusal case. Capture canonical native tool_name/tool_input/cwd, the generated handler's denial reason, returned tool denial and unchanged primary/index sentinels. A fixture-only capture shim may log the sanitized hook payload and forward identical stdin to the exact emitted generated command, preserving stdout/stderr/exit; label the shim and verify that the production handler, not the shim or machine policy, supplied denial. Do not add production transcript logging. Absence of a tool call, generic probe denial, simulated router, machine-policy block, missing config or setup error is not CW-05. Record the exact native executable/version, source/install revision, fixture trust exception, environment/provider constraints, per-case results and sanitized local evidence paths. Native-unavailable CI skips are explicit and cannot satisfy the required local CW-05 receipt. Commit owned installation changes and CODEX-INSTALL-SUMMARY.</action>
  <acceptance_criteria>The installed entry point reaches A's launcher and required guard registrations are enabled/trusted when native policy permits; all known unsafe setups, including read-only or ambiguous/differing effective policy, fail before a model run without sandbox/approval overrides. Existing user/managed hooks and unrelated model/config bytes survive all supported install paths. Installed active-worker source/shell allowance and invalid wave refusal are demonstrated separately from launcher phase/quick selection. Actual generated-adapter native Bash and apply_patch denials have distinct captured evidence; startup defaults/refusal and simulated cases are reported separately.</acceptance_criteria>
  <verify>
    <automated>python -m unittest discover -s tests -p test_codex_worktree.py -k installed_primary_shell_is_denied -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, skipped/xfail tracer, weakened assertion or primary mutation proceeding; the identical retained behavioral RED must now be GREEN.</fails_when>
    <automated>python -m unittest discover -s tests -p test_install.py -k codex_worktree_install -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, missing generated path/registration or native denial, corrupted custom/model/config bytes; a required actual-native case skipped or blocked only by startup/machine policy leaves CW-05 unverified.</fails_when>
    <automated>python -m unittest discover -s tests -p test_install.py -k codex_worktree_native_generated_guard -v</automated>
    <fails_when>Nonzero exit, zero cases, any skip, no actual generated-handler shell or patch denial, external-provider/credential use, missing captured native payload/reason, or changed primary/index sentinels.</fails_when>
    <automated>python -m unittest discover -s tests -p test_install.py -k selected_host_preserves_settings_instructions_and_worker_routes -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, lost custom hook, modified features.hooks=false/model values, damaged personal instructions or changed worker routes.</fails_when>
    <automated>python -m unittest discover -s tests -p test_install_update.py -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, lost/duplicated managed/custom hook, changed user features/model values or unreviewed ownership/config replacement.</fails_when>
    <automated>python -m unittest discover -s tests -p test_install_migration.py -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, changed migration preservation/backup behavior, missing relocated guard or changed Claude/model routing.</fails_when>
  </verify>
  <done>B's RED/GREEN and native receipts are committed with CODEX-INSTALL-SUMMARY; actual shell AND patch refusal are observed before CW-05 is claimed. Coordinator integrates B and reruns A's SAME retained installed tracer plus full test_codex_worktree suite to establish final installed GREEN, then supplies interfaces/results to C.</done>
</task>

<task type="auto">
  <name>Task 6C: Document reachable startup isolation and preserve the active-session truth</name>
  <files>.ai/references/same-agent-worktree.md, .ai/references/worktree-sessions.md, .ai/hooks/README.md, .ai/runtime/README.md, .ai/RULES.md, .ai/workflows/quick.md, .ai/workflows/discuss-phase.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md, tests/test_same_agent_worktree.py</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/doc-writer.md, .ai/runtime/TEMPLATE-CONTRACT.md, docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md, docs/maintenance/issue87-auto-worktree/CONTEXT.md, docs/maintenance/issue87-auto-worktree/CODEX-RESEARCH.md, docs/maintenance/issue87-auto-worktree/CODEX-RUNTIME-SUMMARY.md, docs/maintenance/issue87-auto-worktree/CODEX-INSTALL-SUMMARY.md, all eleven exact documentation paths in frontmatter, tests/test_same_agent_worktree.py existing six-consumer and workflow-order assertions, installed launcher CLI and hook behavior</read_first>
  <precondition>Integrated A+B interfaces and actual checks are available. Unsupported or skipped behavior remains explicitly unverified; documentation does not convert it to acceptance.</precondition>
  <action>Implement CW-06 and preserve CW-01..05 instructions with the full doc-writer method. Add one canonical Codex startup section to same-agent-worktree.md with executable installed launcher examples for explicit existing phase/quick labels, local base semantics, required installed destination files, native hook review/trust, workspace-write roots, preserved effective sandbox/approval restrictions with read-only/differing/ambiguous-policy refusal, invocation-only hook enabling and precise refusal/remediation paths. Explain the strict ordinary phase/quick launcher selection separately from hook validation of an existing active runtime-owned plan-worker wave entry; include exact active identity and rejection of merged/closed/stale or ambiguous metadata without any linked-branch shortcut. Preserve ordinary adopted phase-session receipt/Git validation at non-generated paths and distinguish it from excluded Claude-journal or detached adoption. Explain starting a new native run versus continuing an existing active conversation; the latter needs supported idle native entry or an authenticated controlling host not owned here. Retain the existing precise unsupported automatic in-flight boundary and Claude conditional native-entry sequence; do not replace truthful historical evidence with a universal success claim. Explain broad supported-tool hooks, startup/pre-prompt validation and known fail-open paths, missing/modified/untrusted hooks, unsupported tools, opaque shell/MCP writers, write_stdin sessions not re-hooked, specialized opt-outs and outer sandbox scope. Distinguish actual-native generated-adapter evidence from simulated contracts and the earlier generic probe, including fixture-only trust. State no complete security-boundary promise. Add short Codex-specific references to the canonical section in all six workflows; preserve Claude request/begin/confirm, locate/init ordering, native existing-path approvals and fresh reconstructed edit behavior. A shell cd or model-spawned child never becomes same-agent movement. Keep skills/commands as mirrors that point to workflows; do not duplicate whole workflow text there. Update worktree-sessions, hooks/runtime README and only the relevant Hooks and validation/worktree prose in RULES for reachable launch, install preservation and transport limits. Source-before-doc conflicts go to the source owner, not prose that excuses a defect. In tests/test_same_agent_worktree.py touch only documentation/export/reference assertions needed to verify six installed Codex references and preserved Claude order/permissions; retain the 13 existing native/Claude behaviors without weakening assertions. Use suitable scoped inspection for prose and existing behavioral checks for the changed consumer contract, not artificial word-count tests. Commit owned docs/assertions with CODEX-DOCUMENTATION-SUMMARY and a per-path claim/evidence handoff.</action>
  <acceptance_criteria>All eleven assigned documents match installed source and actual receipts. Six workflows reach one canonical Codex protocol; Claude behavior/order and precise active-session limitation remain. Examples use only the implemented CLI. Original AW pending/human_needed acceptance and open issue87 are preserved.</acceptance_criteria>
  <verify>
    <automated>python -m unittest discover -s tests -p test_same_agent_worktree.py -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, a lost native/Claude case, incorrect workflow initialization order, missing installed Codex canonical reference or simulation labeled actual host movement.</fails_when>
    <automated>python -m unittest discover -s tests -p test_workflow_links.py -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, unresolved source/installed workflow references or host namespace/link drift.</fails_when>
    <automated>git diff --check</automated>
    <fails_when>Nonzero exit or whitespace/conflict-marker diagnostics.</fails_when>
  </verify>
  <done>C is committed with its summary and per-document claim packet; coordinator obtains a fresh doc-verifier and code/integration review on the integrated revision. No claimed full acceptance follows merely from passing documentation checks.</done>
</task>
</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Caller launch options and selected Git unit -> native Codex cwd/workspace | Untrusted redirection, stale/tampered session records and detached/foreign checkouts must not establish isolation. |
| Installed hook configuration/native trust -> model/tool startup | Disabled, replaced, untrusted or unlaunchable handlers must not be advertised as enforcement; host fail-open behavior remains external. |
| Native supported tool payload -> source/note decision | Default root and structured targets are observable; arbitrary opaque writer semantics and unhooked transports are outside the bounded guard. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| [T-AW-01](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | Tampering / Elevation of Privilege | Codex root/structured-target guard and writable-root boundary | high | mitigate | A validates root/unit and structured mutations, preserves narrow notes and source/index sentinels; A test_codex_worktree/test_prewrite and B native shell/patch cases. C states opaque/unhooked host limits; outer workspace-write policy is required. |
| [T-AW-02](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | Spoofing / Tampering / Denial of Service | Session selection, captured base and conflicting launcher options | high | mitigate | A reuses existing session.open without sync for launch selection and separately validates active worker wave identity for hooks under PC-06-codex-worker-compatibility-01. Exact common root/registered path/branch/unit/base and active status are required for worker units; ordinary adopted phase sessions use authoritative receipt/Git/phase identity without generated-name inference; malformed/duplicate/foreign/closed ownership and detached/unsafe options refuse. A real-Git and B installed-worker cases preserve parallel worker behavior; this is the same unit-identity risk occurrence. |
| [T-AW-03](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | Spoofing / Tampering | Native hook capability/trust, generated registration and startup claims | high | mitigate | A's native hooks/list and config/read preservation-or-refusal preflight with bounded launchability checks; B install/update/migration conservation and actual generated-native denials; C separates startup, active-session, simulation and actual evidence. Native trust/fail-open and later host changes remain explicit external limits. |

Reuse issue98's canonical keys
`Tasaddar12/ai-engineering-template/source-prewrite/target-confinement`,
`.../unit-identity`, `.../host-transition-proof` and existing aliases. These
are planned mitigations, not resolution or closure evidence. Coordinator owns
serialized risk-issue reconciliation/readback under the canonical Git workflow.
No new risk issue, closing reference, approval prompt or provider worker write.
L2 review applies to these changed validation/isolation boundaries.
</threat_model>

<verification>
Preparation runs no tests or native probes and edits no source. Commands above
are grounded in existing unittest discovery patterns; A creates the new suite,
B creates the named native test before running it, and all other files already
exist. Each command has an explicit failing direction. Genuine behavioral RED
must precede production and have a committed test-only receipt; setup failures,
zero discovery and unexpected preexisting GREEN require correction before
implementation. Refactor only within owned changed code and rerun affected tests.

Coordinator checklist, on captured integrated revisions:

- Obtain independent phase-checker acceptance before source release; route
  concrete findings without another implementation-authorization question.
- Pin each worker root/branch/base; preserve unrelated index/working changes;
  commit with exact-path --only and each required summary. Integrate A, then B,
  then C; no worker push/merge/rebase/cleanup/provider edits.
- Retain actual A/B RED and corresponding named GREEN receipts. Run the
  frontmatter focused checks once on joined source/installed inputs; repeat only
  checks affected by corrections. Include existing installed planning-integrity
  and runtime-verb-contract tests if installer registration changes affect them.
- Require CW-05's actual generated-native shell AND patch denial with native
  payload/root/denial/no-change evidence, and separate native startup destination
  defaults/refusal. No generic capability probe or startup-only refusal substitutes.
- Require reproducible saved local-provider fixture, sanitized environment,
  controlled native trust exception and proven plugin suppression; if missing,
  retain the exact unverified claim rather than fabricate a receipt.
- Verify byte/content preservation for custom hooks, features.hooks=false,
  models/agent TOMLs, Claude registrations/behavior, GitHub/GitLab provider paths,
  planning skeleton and primary staged/unstaged/untracked/ignored data. Check
  source diff against the assigned revision; no PR99 routing hunk is absorbed.
- Obtain fresh independent code-reviewer, doc-verifier and integration-checker
  reports on one frozen integrated revision. Review the native trust/preflight
  and error paths, actual generated registration/launcher, workflow reachability,
  note controls and absence of any child/controller/movement overclaim. Wait for
  all results before accepting the batch or fixing sources.
- A fresh verifier reconciles CW-01..06 and original AW outcomes against exact
  source/receipt revisions; original live-native human_needed remains unless
  separately observed. Do not relabel historical original-six composition or
  generic Codex capability receipts as new execution.
- Coordinator publishes only to existing draft97 on93-on92, keeps frozen parent
  heads and original six untouched, preserves separate unmerged PR99, updates
  canonical issue98 tracking and issue87's open acceptance honestly. Observe
  current required CI on the actual published revision: both platforms, full
  configured Python/four Bash suites and aggregate validate. Prior CI is not
  the new run. No unchanged full original-six suites/benchmarks are required.
</verification>

## Four-source coverage audit

| Source | ID | Required outcome / disposition | Component | Status |
|---|---|---|---|---|
| GOAL | Task 6 | Supported forced Codex workflow in existing PR97; preserve original same-agent acceptance | A/B/C + coordinator final verification | Covered |
| REQ | ISSUE87 / CW-01 | Runtime-owned selection and native destination defaults, no primary-data change | A selection tests; B actual launch evidence | Covered |
| REQ | CW-02 | Supported synchronous denial and narrow note allowance | A guard/real-Git controls; B generated-native cases | Covered |
| REQ | CW-03 | Fresh/repeated/update installation and preservation | B installer/update/migration | Covered |
| REQ | CW-04 | Known setup/option failures and sandbox/approval preservation-or-refusal before model run | A policy/hook preflight; B installed trust/error controls | Covered |
| REQ | CW-05 | Actual installed Codex generated shell and patch denial | B reproducible native fixture; verifier reconciles | Covered, future execution required |
| REQ | CW-06 | Exact startup/active-session/trust/root/transport guarantees | C eleven documents/six consumers; coordinator PR | Covered |
| CONTEXT | Codex startup/no detached adoption | Existing runtime phase/quick route, no controller or child substitute | A/C | Covered |
| CONTEXT | Guard/note/advisory preservation | Structured-target classifier reused; advisory script unchanged | A/B/C | Covered |
| CONTEXT | Configuration/trust preservation | Invocation hook enabling; effective native trust/known disable refusal; no model edits | A/B | Covered |
| CONTEXT | Installed destination/no dirty copy | Missing committed runtime/config is a dependency, not sync/copy authority | A/B/C | Covered |
| CONTEXT | Disjoint isolated workers / existing stack | Exact A/B/C paths and genuine prerequisite order; coordinator publication only | Execution table/checklist | Covered |
| CONTEXT | Native local evidence and scope limits | Generated-adapter shell/patch proof; no external model/credentials/install/benchmark | B/checklist | Covered |
| RESEARCH | Actual native capability, schema and fail-open limits | Reuse evidence, validate effective handler representation, distinct new receipts | A/B/C | Covered |
| RESEARCH | Native --worktree detached / idle worktree / controller | Detached shortcut and active-turn controller excluded; accurate idle/active limitations | A rejects; C explains | Covered |
| EXCLUSION | Original six, 73/74, PR99 routing, Whiskance/game, infrastructure/cleanup | No edits, import, merge or revalidation project | All components | Preserved |

<success_criteria>
All six CW outcomes have implemented producer/consumer wiring and appropriate
behavioral evidence, with actual native cases distinguished from fixtures.
No unresolved required behavior is hidden by changed prose, skips or generic
capability success. Original AW acceptance remains independently reported;
issue87 stays open and all PRs remain unmerged. Missing credentials/capability,
trust or host transport coverage is an explicit dependent blocker, not an excuse
to broaden scope or silently start an unenforced model.
</success_criteria>

<output>
Each component returns its owned commits, exact test/install/native revisions,
RED/GREEN evidence, required summary, coverage and remaining limitations to the
coordinator. No adoption ROADMAP/STATE/PROJECT update is proposed. Coordinator
adds this checked companion as existing maintenance Task 6, reconciles shared
CONTEXT/MATRIX/VERIFICATION and draft97, and retains all historical evidence.
</output>
