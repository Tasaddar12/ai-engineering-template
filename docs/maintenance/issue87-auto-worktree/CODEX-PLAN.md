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
resources: [issue87-codex-safe-export-fixtures]
checks:
  - [git, diff, --check]
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
      provides: Non-executing generated-file/configuration export assertions; native generated-adapter proof remains blocked and unverified.
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

## Binding safe-continuation amendment after platform flag

The latest human restrictions in CONTEXT's "Restricted safe continuation after
platform flag", recorded at 56a2773960d4474338f678c645ca8adfcc64db81, supersede
every earlier executable instruction/check in this plan and prior producer
summaries that would run generated commands, hooks, launchers, native Codex,
model servers, command-injection probes or suspected flagged operations. Do not
disable safeguards, retry a denial, or move a blocked action to another route.
Stop a newly denied action and report its exact target. The flag's original
invocation is unavailable; do not reconstruct or investigate it by execution.

Current source authorization is only saved-review CR-01 Windows literal-prompt
handling/direct native .exe prerequisite with .cmd/.bat refusal, and CR-02
ordinary primary-note preservation through UserPromptSubmit. Use static review
and safe in-process unit fixtures with stub process runners. No new effective
feature, RPC or policy behavior is authorized by this continuation; the earlier
feature question remains unverified. The active source fixer owns those repairs;
other workers do not inspect or edit its uncommitted files.

After those repairs and independent static review integrate, B may edit its
existing installer/configuration/assets and write non-executing export fixtures
selected by codex_worktree_export_safe in the three owned installer test files.
Their future permitted design is import/render/merge and temporary installed-file
export inspection; all Python execution is now paused as specified below.
No generated command, hook, launcher, native executable or server is executed.
Do not run full mixed runtime/installer suites, the retained installed tracer,
native fixtures, or alternative proof routes. Leave the retained tracer active
and unmodified, explicitly unrun/pending under this restriction; do not skip,
xfail, weaken or report it GREEN.

C updates the eleven assigned documents against committed generated source and
safe receipts, with static inspection only. Source/doc/integration specialists
review one frozen revision statically. Final verification remains human_needed
and incomplete: CW-05 actual shell AND patch proof is blocked/unverified, and
other runtime/live CW/AW claims need their original evidence. Safe unit/export
results do not satisfy native acceptance or ship readiness. No issue closes or
PR merges. Preserve historical receipts/capability observations as history, not
permission to repeat their operations.

Keep the existing CI workflow, actions, tests, protections and failure semantics;
no skip-ci directive, removed gate or manual probe run. An ordinary authorized
push may trigger configured CI; observe those results without manually invoking
probes or converting CI into a new native acceptance claim. PR97 stays an
explicitly incomplete draft on its existing stack, with the original six frozen
and PR99 routing separate.

All technical contracts below remain intended/source-review context unless
the current safe tasks explicitly authorize an edit. In particular, the earlier
native helper instructions, full-suite commands, actual-native evidence steps
and retained-tracer execution/GREEN directions are suspended, not waived. The
current task bodies/checks below define executable continuation scope.

### Subsequent execution block: all Python checks NOT_RUN

After the restriction above, a safe-unit selector was denied before Python
started at the exact target
`C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`
with ResourceUnavailable/file-access refusal, as reported by the coordinator.
All further Python execution on this host is now paused, including unit/export
tests, imports/render execution, runtime validators and static Python validators.
Do not retry the target, escalate, select another interpreter, use a manual
remote CI route, or build an alternative PowerShell test harness. Stop/report
the denied target; no new denial investigation or workaround is authorized.

Static defensive source, installer/configuration/document edits and writing
non-executing regression fixtures remain allowed, as does ordinary Git. The
active checks list therefore contains only git diff --check. Planned safe unit
and export selectors are future specifications below, all currently NOT_RUN;
they establish no RED/GREEN or component pass. Native CW-05 and other unproved
acceptance remain blocked without waiver. Normal authorized push/configured CI
observation stays unchanged; no manual workflow dispatch or test rerouting.

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
| A: committed runtime plus defensive follow-up | Existing launcher_main/hook_main; current edits only CR-01/CR-02 and written stub fixtures | .ai/runtime/lib/codex_worktree.py; .ai/hooks/codex-worktree.py; tests/test_codex_worktree.py; CODEX-RUNTIME-SUMMARY.md in this maintenance directory | First |
| B: static installation/export continuation | Committed repaired A API; edits generated launcher/registrations/config and writes non-executing export fixtures; execution NOT_RUN | .ai/install-assets/codex-worktree.py; .ai/install.py; tests/test_install.py; tests/test_install_update.py; tests/test_install_migration.py; CODEX-INSTALL-SUMMARY.md in this directory | Depends on integrated A |
| C: static documentation consumers | Integrated safe A+B and static receipts; writes eleven guides/six references with runtime/native gaps | All eleven documentation paths in frontmatter; tests/test_same_agent_worktree.py frozen; CODEX-DOCUMENTATION-SUMMARY.md in this directory | Depends on integrated A+B |

Disjoint paths alone do not establish independence. B's generated source and
written export expectations consume A, so A -> B -> C remains deliberate. Do not dispatch B against
unintegrated A and call broken fixtures RED or fabricate parallel GREEN. There
is no shared mutable native fixture across workers. Keep summaries distinct;
coordinator writes shared CONTEXT/MATRIX/VERIFICATION and the PR body. No worker
owns model tables, agent TOMLs, .planning/config.yaml, source-prewrite.sh,
worktree-guard.sh, .github, runtime lifecycle/cleanup or the six original drafts.

Historical TDD/registration frontier (execution suspended by the binding safe
amendment): A names direct-runtime cases with `runtime` in their unittest method names.
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
<task type="auto">
  <name>Task 6A continuation: CR-01 and CR-02 defensive repairs only</name>
  <files>.ai/runtime/lib/codex_worktree.py, tests/test_codex_worktree.py</files>
  <read_first>docs/maintenance/issue87-auto-worktree/CONTEXT.md restricted continuation, this binding safe amendment, saved source REVIEW-01 CR-01/CR-02, committed CODEX-RUNTIME-SUMMARY.md from a832c6c65cbda7195f7d25962d142b8382d74078, the fixer's own assigned module/tests</read_first>
  <precondition>The already assigned isolated source fixer alone owns the active repair files; other workers wait for its committed result and static review. All Python execution remains paused after the exact reported target refusal.</precondition>
  <behavior>Written safe unit fixtures specify literal Windows prompt argv and direct .exe prerequisites, refusal of .cmd/.bat before any runner, and ordinary primary note allowance through UserPromptSubmit while source attempts remain subject to PreToolUse. Every process/native/RPC boundary in those fixtures is a stub; the fixtures are NOT_RUN under the current block.</behavior>
  <action>Repair only saved-review CR-01 and CR-02. Preserve literal prompt data and native argument separation using the direct Windows executable prerequisite; refuse Windows batch shims visibly instead of invoking their shell parsing. Do not execute injection strings or a launcher/native probe to investigate quoting. Preserve primary note-only lifecycle use at UserPromptSubmit while retaining the existing supported-tool source decision boundary. Write bounded in-process unit fixtures with stub process runners and ordinary harmless input; do not execute them now. Do not introduce new feature/RPC/effective-policy behavior or rerun the historical feature question. Preserve the checked policy/worker/adopted-session contracts outside these two defects. Leave the retained installed tracer active and unchanged but do not run it, the mixed runtime suite, generated hooks or native tools. Commit the authorized defensive edits and repair summary with static findings and tests NOT_RUN; report blocked acceptance rather than component GREEN. If any action is denied, stop that action and report its exact target without retry, escalation or alternate execution route.</action>
  <acceptance_criteria>Static review traces both defensive repairs and their written stub fixtures; primary note lifecycle and source tool decisions remain distinct. No native/batch/generated-command execution or safeguard bypass occurs. Runtime/native acceptance and required test outcomes remain unverified, not completed by source inspection.</acceptance_criteria>
  <verify>
    <automated>git diff --check</automated>
    <fails_when>Nonzero exit or whitespace/conflict-marker diagnostics; exit0 proves only this static diff property.</fails_when>
    <inspection>Fresh independent static source review examines the committed CR-01/CR-02 diff and stub fixture design. Safe-unit execution is NOT_RUN because the Python target was denied; no replacement harness or component pass.</inspection>
  </verify>
  <done>Owned defensive repair and summary are committed, reviewed statically and integrated by the coordinator. A's safe repair boundary can be handed to B; Task6 remains incomplete and no new runtime or native GREEN is claimed.</done>
</task>

<task type="auto">
  <name>Task 6B continuation: installer/configuration and non-executing export fixtures only</name>
  <files>.ai/install-assets/codex-worktree.py, .ai/install.py, tests/test_install.py, tests/test_install_update.py, tests/test_install_migration.py</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/coder.md, this safe amendment, committed CODEX-RUNTIME-SUMMARY.md from a832c6c65cbda7195f7d25962d142b8382d74078, committed CR-01/CR-02 repair summary/static review, .ai/install.py payload/host_payload/merge_toml/managed inventory/hook_settings, all five exact owned files or their creation contract</read_first>
  <precondition>Defensive A repairs and independent static source review are integrated. Read only committed producer code/summaries; do not inspect active fixer files. Python tests/imports/render execution remain blocked.</precondition>
  <behavior>Written codex_worktree_export_safe fixtures specify fresh/repeated/update/migration generated-file and TOML preservation without executing generated commands, hooks, launchers, native Codex or model servers. They assert the agreed producer API and OS-selected command definitions, synchronous matcher/event/timeout inventory and unchanged custom/model/config values. They are currently NOT_RUN.</behavior>
  <action>Edit only the existing installer/assets/configuration surface and its three owned test files. Generate the thin Codex-only .codex/codex-worktree.py asset using adjacent runtime lib.codex_worktree.launcher_main, with no arbitrary native passthrough. The committed A CLI is phase|quick LABEL with --base, --prompt and --exec; literal flag-looking prompts use --prompt=--literal-flag and native prompt separation. Preserve CR-01's direct Windows .exe prerequisite and batch refusal. Use the committed guard_commands() definitions as the authoritative exported strings; read them statically now rather than invoking Python. Register the Codex-only synchronous PreToolUse matcher *, SessionStart and UserPromptSubmit definitions with timeout30, retaining exact existing advisory-first/source-second editing group behavior, all old managed/custom hooks and the ordinary Claude payload. Extend managed inventory/update/migration handling without agent/model/routing or .planning/config.yaml edits. Preserve features.hooks=false and every unrelated user value; hooks enabling remains invocation-scoped in source and known unsafe setup still has no acceptance claim until observed. Write only non-executing export fixtures named with codex_worktree_export_safe in test_install.py, test_install_update.py and test_install_migration.py. Their future permitted design is import/render/merge and temporary installed-file export/content inspection, with runners that reject any generated-command/hook/launcher/native/server execution. Cover exact asset mapping/API text, TOML registration identity/events/matcher/synchronous timeout, custom-hook conservation, repeated-install idempotence, managed update/migration preservation and unchanged model/effort/config values. Current Python execution block means none of these tests, imports or render routines are run now. Do not implement or execute the earlier native canned-provider fixture; no model server, host probe, injection probe, generated-command launch, installed behavioral tracer or full mixed suite is authorized. Leave existing retained tests/assertions intact. Keep configured CI/actions/protections unchanged; no skip-ci, disabled gate, manual dispatch or test reroute. Record static inspection, written fixture coverage and all test/native outcomes NOT_RUN in CODEX-INSTALL-SUMMARY, with incomplete/blocked behavioral acceptance. Commit only owned files and that summary.</action>
  <acceptance_criteria>Static inspection confirms reachable generated file paths, producer API references and registration/config preservation design with no unrelated model/PR99/Claude change. Written export fixtures use the exact safe selector and cannot invoke generated commands or native/model processes. No export/runtime/native GREEN is claimed while execution is blocked; CW-03 runtime installation and CW-05 remain pending.</acceptance_criteria>
  <verify>
    <automated>git diff --check</automated>
    <fails_when>Nonzero exit or whitespace/conflict-marker diagnostics; exit0 is not export or native acceptance.</fails_when>
    <inspection>Inspect the full scoped installer/asset/test diff and compare generated-string expectations against committed A guard_commands/launcher_main source without importing or executing it. The three future export selectors below remain NOT_RUN. Independent static source/integration review checks producer-consumer wiring.</inspection>
  </verify>
  <done>B's authorized source/configuration and written non-executing export fixtures are committed with CODEX-INSTALL-SUMMARY. Coordinator integrates and assigns C using static evidence; B reports behavioral acceptance incomplete, never installed-tracer or native GREEN.</done>
</task>

<task type="auto">
  <name>Task 6C continuation: document committed source and blocked acceptance</name>
  <files>.ai/references/same-agent-worktree.md, .ai/references/worktree-sessions.md, .ai/hooks/README.md, .ai/runtime/README.md, .ai/RULES.md, .ai/workflows/quick.md, .ai/workflows/discuss-phase.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/doc-writer.md, this safe amendment, committed A/B source and summaries/static reviews, all eleven assigned documentation paths, original CW/AW acceptance and historical CODEX-RESEARCH.md</read_first>
  <precondition>A then B committed safe changes and static evidence are integrated. No active fixer source is read. Current execution limits remain in force; tests/test_same_agent_worktree.py is frozen in this continuation.</precondition>
  <action>Update only the eleven assigned documents against actual committed generated source. Keep one canonical Codex startup section and short references in all six workflows. Describe phase/quick startup versus an existing active agent precisely; no active-agent movement claim. Explain the exact Windows direct native .exe prerequisite, literal prompt handling and refusal of .cmd/.bat shims. Explain ordinary primary-note lifecycle allowance at UserPromptSubmit separately from source enforcement at supported PreToolUse; preserve Claude native-entry/fresh-read ordering, narrow notes, ordinary adopted-phase and active-worker identities, and the existing sandbox/approval preservation-or-refusal source contract. State what source inspection supports and which behavior remains unverified, including the prior effective-feature question, real generated-adapter shell/patch evidence, transport/opaque-writer limits and the Python execution block. Do not make historical probes current or present static/export fixtures as actual native success. Preserve native trust prerequisites; no bypass/retry/alternative route. Examples describe source API use but are not executed in this work. Keep the original AW human_needed outcomes, CW-05 blocked/unverified and PR97 incomplete, with issue87 open. Do not edit or run tests/test_same_agent_worktree.py or any mixed workflow test suite. Commit docs with CODEX-DOCUMENTATION-SUMMARY and a per-path static claim/evidence packet.</action>
  <acceptance_criteria>All eleven documents match committed generated source, label unverified runtime/native claims and state current execution restrictions. Six consumers point to one protocol, Claude behavior is preserved, and no startup/source-code claim substitutes for active-session movement or CW-05 acceptance.</acceptance_criteria>
  <verify>
    <automated>git diff --check</automated>
    <fails_when>Nonzero exit or whitespace/conflict-marker diagnostics.</fails_when>
    <inspection>Independent doc-verifier statically traces per-path claims to committed source and actual historical/safe receipts. Required unobserved runtime/native claims remain unverifiable. No Python, generated example, native host or replacement test harness is executed.</inspection>
  </verify>
  <done>Eleven docs and summary are committed and statically reviewed on the joined revision. Final verifier reports human_needed/incomplete with explicit NOT_RUN checks and blocked native acceptance; no ship-ready, issue-closing or merge claim.</done>
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
| [T-AW-01](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | Tampering / Elevation of Privilege | Codex root/structured-target guard and writable-root boundary | high | mitigate | A validates root/unit and structured mutations, preserves narrow notes and source/index sentinels; historical A unit evidence and written B export expectations. Native shell/patch proof remains blocked/unverified. C states opaque/unhooked host limits; outer workspace-write policy is required. |
| [T-AW-02](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | Spoofing / Tampering / Denial of Service | Session selection, captured base and conflicting launcher options | high | mitigate | A reuses existing session.open without sync for launch selection and separately validates active worker wave identity for hooks under PC-06-codex-worker-compatibility-01. Exact common root/registered path/branch/unit/base and active status are required for worker units; ordinary adopted phase sessions use authoritative receipt/Git/phase identity without generated-name inference; malformed/duplicate/foreign/closed ownership and detached/unsafe options refuse. Historical A real-Git evidence and written B worker/export expectations preserve the compatibility contract without current execution; this is the same unit-identity risk occurrence. |
| [T-AW-03](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | Spoofing / Tampering | Native hook capability/trust, generated registration and startup claims | high | mitigate | A's native hooks/list and config/read preservation-or-refusal preflight with bounded launchability checks; B static install/update/migration conservation design, with actual generated-native denials still blocked/unverified; C separates startup, active-session, simulation and actual evidence. Native trust/fail-open and later host changes remain explicit external limits. |

Reuse issue98's canonical keys
`Tasaddar12/ai-engineering-template/source-prewrite/target-confinement`,
`.../unit-identity`, `.../host-transition-proof` and existing aliases. These
are planned mitigations, not resolution or closure evidence. Coordinator owns
serialized risk-issue reconciliation/readback under the canonical Git workflow.
No new risk issue, closing reference, approval prompt or provider worker write.
L2 review applies to these changed validation/isolation boundaries.
</threat_model>

<verification>
Current executable verification is static inspection and ordinary Git only.
All Python unit/export/runtime/static-validator execution is NOT_RUN after the
reported file-access denial; no interpreter retry, escalation, alternative
harness, manual remote CI or native probe route is authorized.

The following safe export selectors are retained as written future check
specifications, not commands to execute during this continuation. B creates the
named fixtures before any future separately authorized execution. They inspect
exports/configuration without running generated commands, hooks or launchers.

| Future check specification | Expected result / failing direction | Current result |
|---|---|---|
| python -m unittest discover -s tests -p test_install.py -k codex_worktree_export_safe -v | Nonempty safe export cases pass; nonzero exit, zero cases, unexpected generated/native/server execution or changed custom/model/config expectation would fail | NOT_RUN: Python target blocked |
| python -m unittest discover -s tests -p test_install_update.py -k codex_worktree_export_safe -v | Managed/update content conservation passes; nonzero exit, zero cases, lost/duplicated hook or changed unrelated settings would fail | NOT_RUN: Python target blocked |
| python -m unittest discover -s tests -p test_install_migration.py -k codex_worktree_export_safe -v | Migration/export content and user values survive; nonzero exit, zero cases, namespace/ownership/config damage would fail | NOT_RUN: Python target blocked |

A's two defensive stub-unit fixtures are likewise written but NOT_RUN. Its
historical direct-runtime receipts and retained installed RED remain evidence
at their recorded revisions only. Do not run the retained tracer, full mixed
suite or suspected flagged operation; keep the tracer active/unmodified with
pending acceptance, never skip/xfail or claim it GREEN.

Coordinator checklist for this bounded continuation:

- Obtain independent static check of this amendment before B source release.
  The earlier plan approvals do not waive the latest user restrictions.
- Wait for the active CR-01/CR-02 fixer, integrate its committed defensive diff
  and summary, and obtain fresh static source review. Do not add unrelated
  effective-feature, RPC or policy changes or inspect active uncommitted files.
- Dispatch B after integrated A and its static review, then C after integrated B.
  Keep exact isolated worker ownership and required summaries. B writes export
  fixtures but does not execute Python/import/render routines under the block.
- Preserve custom hooks/config, user features.hooks=false, model/agent TOMLs,
  separate PR99 routing, ordinary Claude behavior, primary/index data, adopted
  sessions and active-worker source contracts through scoped static review.
- Join independent static source, doc and integration reviews at one frozen
  revision before repairs or accepting evidence. Record source/API wiring,
  per-document unverifiable claims and written fixture design honestly.
- Final verifier records human_needed/incomplete, tests NOT_RUN and CW-05
  generated-native shell AND patch proof blocked/unverified. Other original CW
  and AW live/runtime requirements retain their evidence obligations. Static
  wiring, historical probes and written safe fixtures cannot pass them.
- Stop/report a newly denied action with its exact target. No safeguard disable,
  retry, interpreter substitution, new harness or alternate native route.
- Coordinator may publish reviewed safe commits through the ordinary existing
  draft97 stack. Keep current configured CI/actions/tests/protections unchanged;
  no skip-ci, gate bypass, manual workflow dispatch or test reroute. Observe any
  automatically triggered CI as that run's evidence only, without new native
  acceptance claims or ship readiness. All PRs remain unmerged; issue87 stays
  open, original six frozen, PR99 separate, adoption skeleton unchanged.
</verification>

## Four-source coverage audit

| Source | ID | Required outcome / disposition | Component | Status |
|---|---|---|---|---|
| GOAL | Task 6 | Supported forced Codex workflow in existing PR97; preserve original same-agent acceptance | Restricted A/B/C source/docs and coordinator incomplete report | Full goal incomplete; safe scope planned |
| REQ | ISSUE87 / CW-01 | Runtime-owned selection and native destination defaults, no primary-data change | Historical A fixtures/source; current static generated-source review | Native/default-root acceptance unverified |
| REQ | CW-02 | Supported synchronous denial and narrow note allowance | CR-02 defensive source/static review; existing historical controls | Current generated behavior unverified |
| REQ | CW-03 | Fresh/repeated/update installation and preservation | B static installer/config edits and written export fixtures | Export checks NOT_RUN |
| REQ | CW-04 | Known setup/option failures and sandbox/approval preservation-or-refusal before model run | Existing source contract preserved; CR-01 defensive repair/static review | Native/effective-feature behavior unverified |
| REQ | CW-05 | Actual installed Codex generated shell and patch denial | No current native fixture implementation/execution; verifier retains obligation | BLOCKED / UNVERIFIED under latest user restriction |
| REQ | CW-06 | Exact startup/active-session/trust/root/transport guarantees | C eleven documents/six consumers; coordinator incomplete PR | Static claims planned; runtime claims labeled unverified |
| CONTEXT | Codex startup/no detached adoption | Existing runtime phase/quick route, no controller or child substitute | A/C | Covered |
| CONTEXT | Guard/note/advisory preservation | Structured-target classifier reused; advisory script unchanged | A/B/C | Covered |
| CONTEXT | Configuration/trust preservation | Invocation hook enabling; effective native trust/known disable refusal; no model edits | A/B | Covered |
| CONTEXT | Installed destination/no dirty copy | Missing committed runtime/config is a dependency, not sync/copy authority | A/B/C | Covered |
| CONTEXT | Disjoint isolated workers / existing stack | Exact A/B/C paths and genuine prerequisite order; coordinator publication only | Execution table/checklist | Covered |
| CONTEXT | Restricted safe continuation and subsequent Python denial | Only two defensive repairs, static installer/docs and written safe export fixtures; no execution retry/reroute | Current A/B/C/checklist | Covered as bounded work; runtime/native acceptance incomplete |
| RESEARCH | Actual native capability, schema and fail-open limits | Reuse evidence, validate effective handler representation, distinct new receipts | A/B/C | Covered |
| RESEARCH | Native --worktree detached / idle worktree / controller | Detached shortcut and active-turn controller excluded; accurate idle/active limitations | A rejects; C explains | Covered |
| EXCLUSION | Original six, 73/74, PR99 routing, Whiskance/game, infrastructure/cleanup | No edits, import, merge or revalidation project | All components | Preserved |

<success_criteria>
The original full-goal success condition still requires all six CW outcomes
and appropriate behavioral/native evidence; it is not met or waived by this
safe continuation. Current deliverables are committed defensive repairs,
installer/configuration source, written non-executing export fixtures and eleven
accurate docs with static review. Python checks are NOT_RUN; CW-05 and other
unproved runtime/live outcomes remain blocked/unverified. Final status is
human_needed/incomplete, not ship-ready. Preserve original AW acceptance,
issue87 open, all PRs unmerged and every latest user execution restriction.
</success_criteria>

<output>
Each current worker returns its owned safe commits, static review evidence,
written fixture coverage, exact NOT_RUN checks, blocked acceptance and required
summary to the coordinator. Historical RED/GREEN retains its original revision;
no new runtime/native or component-pass claim follows from this continuation.
No adoption ROADMAP/STATE/PROJECT update is proposed. Coordinator reconciles
shared CONTEXT/MATRIX/VERIFICATION and incomplete draft97, retains historical
evidence and obtains independent static check before B. Final verification is
human_needed/incomplete; no issue close, ship readiness or merge.
</output>
