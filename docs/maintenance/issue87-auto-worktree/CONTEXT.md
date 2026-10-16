# Issue 87: automatic worktree handoff

## Authority and scope

The actual human request delivered through Jarvis was: “AI Workflows often ignore needing a worktree... different hook to force it to open a worktree when it tries to write or edit anything and its not currently in one... Look into it and get another PR if we dont have something open for it already.” The coordinator owns duplicate checking and publication. This maintenance record does not fill the adoption skeleton or establish an adopting project's phases.

## Decisions

- Investigate the current host hook contract and prepare a separate draft implementation for a matching gap; never merge.
- Preserve PR 86's preference for scratchpad warnings. Distinguish task notes from source edits; do not restore a repeated hard-halt retry loop.
- Preserve uncommitted changes and prevent writes to the old checkout from continuing after a claimed handoff.
- Keep the six existing drafts separate and frozen. Work 73/74, live infrastructure, tool installation and real cleanup are out of scope.

## Claude's Discretion

- Researcher may choose the bounded evidence and recommend an implementation and test boundary. Recommendations are technical findings, not additional human decisions.
- Researcher owns only this CONTEXT.md and RESEARCH.md. No production edits, test execution, provider writes, publication or merge.

## Deferred Ideas

- Work 73/74, unrelated drafts, live infrastructure, tool installs and real cleanup.

## Coordinator technical scope decisions

- The human clarified: "Well yeah we changed this earlier but that was for different reasons. This time we actually move the agent itself". Acceptance requires movement of the same existing agent/session, subsequent tools using the destination by default, and cancellation followed by fresh reconstruction of the pending edit. Checkout preparation, shell `cd`, path rewriting, cancellation alone and replacement children do not satisfy this outcome.
- Subsequent parent steering explicitly authorizes implementing a supported target-host route with capability gating. Current executor limitations must be distinguished from reusable-template host support. Official Claude documentation supports instruction-driven native `EnterWorktree` creation after synchronous cancellation. Replan for that conditional Claude route; do not release the earlier preparation-only plan.
- Gate Claude routing on actual native tool/schema availability, eligible role and policy, and the trusted creation hook. Preserve native approval requirements for existing outside paths; never disguise reuse as new creation to avoid approval. Verify native context binding before fresh destination reads and a rebuilt mutation. Preserve or fully account for staged, unstaged, untracked and ignored data.
- Codex currently lacks an authenticated same-thread host controller in this template. State that precise unsupported integration boundary; cancellation or a prepared checkout does not implement automatic movement. No universal enforcement or live-host success claim may be inferred from a simulated contract test. Live native smoke remains a distinct evidence requirement.
- These are bounded implementation choices under the user's existing authorization. The six original draft heads remain frozen, all PRs remain unmerged, and issue 87 stays open.
- Official pre-edit linkage evidence: `CLAUDE_CODE_SESSION_ID` is documented in Bash/PowerShell tool and hook subprocesses; `${CLAUDE_SESSION_ID}` is skill-content substitution, not a shell variable. No agent-ID environment variable was established. A known-unit workflow request can be provisional with repository, nonce and available session correlation; actual native hook identity must be compared and conflicts refused. CLI identity arguments are correlation claims, not authentication. Do not invent a main-agent ID or use request/journal success as movement proof. See [environment variables](https://code.claude.com/docs/en/env-vars), [skill substitutions](https://code.claude.com/docs/en/skills#available-string-substitutions) and [WorktreeCreate fields](https://code.claude.com/docs/en/hooks#worktreecreate-input). This is a bounded implementation clarification of the approved request/bootstrap contract.

- To implement the user's source-versus-task-note distinction without guessing from file extensions, ordinary external temporary artifacts are limited to plain unlinked create/update paths under the resolved OS temporary directory and outside every Git repository. No identity or preparation is needed there. This is a bounded technical choice under delegated implementation discretion, not an additional human approval.
- Mixed, rename/delete, linked/reparse/hardlinked, cross-repository and ambiguous paths receive source/unsupported handling. Non-temp external locations are not a note exemption.
- Independent RED review required the corresponding both-host control before production; corrected test-only38b7b1c retains genuine source refusal failures and passing ordinary-note controls. PLAN/MATRIX alignment and independent bounded recheck precede source release.

## Coordinator dependency reconciliation for Task 4

The user authorized preserving existing prior work through distinct adjustments
and stacked drafts. Coordinator therefore selects frozen PR93 (47593a3d3f71739bd146a6c2c3590798d7c73c2e),
already on frozen PR92 (d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6), as PR97's
dependency. After current code-05 review corrections integrate and this plan is
independently checked, use a local non-rewriting merge into97 and the bounded
native/planning runtime/installer union in STACK-PLAN. This is routine dependency
reconciliation within existing delegated authority, not a new human approval.
Preserve both frozen parent heads and PR89/91/94/88; no PR is merged. Change the
actual PR97 base only after checked integration; never import the original-six
umbrella/prototype into97 or copy independent PR91/94 policy into its own diff.
After final97, test/review a separate disposable local original-six composition
without publishing it. Existing maintenance acceptance and live-native uncertainty
remain; a real planning-preservation integration failure must be repaired, not
deferred. Native exit stays essential preservation, with no second cleanup project.

## Coordinator CI-budget reconciliation for Task 5

The user's existing issue87 implementation, publication, required-CI and
recoverable-diagnosis authorization covers a bounded response to the actual
run38832833234 failure at production21488caa19e3b76b11d84165bf4c69fb58f3ac96.
Coordinator captured the GitHub annotation that the job exceeded its maximum
execution time of30m0s. Windows job116755220118 ran01:01:36..01:31:48 (30m12s):
Python746 passed in1674.794s, skipped2; tier10 and advisory60 passed; context
handoff began01:30:26 and was canceled01:31:45; worktree-location was skipped.
Ubuntu job116755220585 succeeded with Python746/332.623s, skipped15, and all
four Bash suites (357 assertions). Aggregate validate failed. The whole run and
Windows Bash coverage are not GREEN.

Prior successful run38822540901 Windows job116722266702 took27m44s; its context
step took158s and location12s. The current context step's79s before cancellation
is shorter than that prior normal context duration, so the quiet interval does
not demonstrate a stall. Independent CR-CI-01 confirms budget exhaustion in
CI-DIAGNOSIS.md at fad210d9811b44daf7335601d0ea67d06da6abd7, read from Git
without changing this preparer's assigned input. CI-PLAN.md records evidence
provenance and exact verification; independent plan checking remains required.

Within delegated discretion, Task 5 permits only
`.github/workflows/validate.yml` platform-job timeout/comment: Windows45 minutes,
Ubuntu30, using existing matrix.os. All jobs, commands, four Bash suites, Python
and action versions, per-test bounds, triggers, permissions, aggregate failure
semantics and protections remain unchanged. No test removal, sharding, benchmark,
cache, infrastructure, installation or action upgrade is authorized. This is the
sole exception to earlier provider-workflow exclusions; it does not alter provider
behavior or grant worker publication. A fresh isolated worker owns that file and
CI-SUMMARY.md only after checked planning/diagnosis; coordinator owns integration,
publication, new CI observation, fresh bounded independent review and final
verifier reconciliation at the actual new revision.

Prior `.github` preservation statements are historical at their recorded source
or verification revision. The new exception changes only this job budget/comment;
canonical planning, advisory hook, attributes and provider behavior retain their
byte-preservation boundaries. Original-six and finalC composition evidence is
retained only for unchanged source inputs, never relabeled a new CI execution.
No original-six/finalC import into97, frozen-head change or PR merge is allowed.
PR97 retains actual base93 and draft state;73/74, Whiskance/game, infrastructure
and cleanup stay excluded. Actual native host movement/defaults/lifecycle remain
unverified/human_needed with no acceptance waiver; issue87 remains open.

## Authorized Codex enforcement addition (2026-10-16)

The user explicitly requested: "AI Workflows PR 97 should have a same forced workflow for Codex." Jarvis directed implementation of the supported equivalent, including generated/installable configuration, focused regression coverage, actual Codex support verification and publication to this existing draft. If mechanisms differ, report precise guarantees. This authorization supersedes the earlier b3cefa0 freeze only for this addition. PR99 has a separate active model-routing owner; do not edit that worktree or its model/agent routing scope.

Coordinator decisions within that delegated implementation discretion:

- Add a Codex startup route which creates or reuses the exact runtime-owned phase/quick worktree, validates its Git registration/common repository, branch, unit and captured base, and starts a new native Codex run at that destination. This is startup isolation, not relocation of an existing agent. Preserve the original AW acceptance and its live evidence requirements.
- Use the supported native `--cd` and invocation-scoped hook feature controls, backed by the installed runtime capability evidence in CODEX-RESEARCH.md. Do not introduce a new app-server orchestration product or a detached-worktree adoption contract. Codex's observed native `--worktree` output is detached and must not be admitted merely because it is linked.
- Add generated synchronous Codex tool guards and startup/pre-prompt root checks. Primary or invalid source execution must refuse before a supported tool acts. Preserve ordinary narrowly classified task notes and the PR86 advisory script. Explicitly state the transport, opaque-writer, trust and host fail-open limits; do not advertise a complete security boundary.
- Preserve user/global configuration and all agent/model settings. The explicitly selected workflow invocation enables the needed hooks without rewriting a user's `features.hooks=false`. Known managed disable, unresolved trust, missing configuration or unavailable guard/runtime must refuse rather than claim enforcement. Production must not silently bypass native hook trust or weaken sandbox/approval policy.
- Validate the destination's installed runtime/configuration. Missing or uncommitted installed files are a dependency, not permission to copy dirty primary state. No implicit sync/fetch, branch replacement, unrequested phase creation, cleanup or data migration.
- Reject conflicting launch arguments that redirect cwd, disable/bypass hooks, ignore project configuration or weaken the selected sandbox. Do not launch a replacement child from an active agent and call it same-agent movement. Existing active conversations require supported idle native worktree entry or an authenticated controlling host; this template does not own that controller.
- Source, installer and documentation workers must have disjoint ownership and isolated worktrees. A checked plan precedes implementation. Preserve Claude native behavior, GitHub/GitLab paths, PR93/PR92 ancestry, all six frozen drafts and the unfilled adoption skeleton.
- Actual post-implementation evidence must exercise the generated installed guard through native Codex for shell and patch attempts, using a bounded local canned-response fixture with no external model or credentials. Retain the earlier failed/confounded probes honestly. No benchmarks, installs, infrastructure changes, PR merge or work73/74 are authorized; Whiskance and game checkouts remain excluded.

Additional acceptance for the supported Codex equivalent:

- CW-01: The launcher selects one validated registered phase/quick worktree before native Codex startup; new-run defaults name that destination and primary data remain unchanged.
- CW-02: Generated synchronous supported-tool interception refuses primary/invalid source execution and retains narrow note allowances; no path/input rewrite is called movement.
- CW-03: Fresh install, repeated install and managed update produce the launcher/guards while preserving custom hooks, ordinary configuration, Claude behavior and model routing.
- CW-04: Missing/disabled/untrusted/invalid setup and conflicting startup options fail visibly without starting an unenforced model run or destroying state.
- CW-05: Real installed Codex executes the generated adapter and demonstrates a refused shell and patch attempt; simulated fixtures and actual host evidence are identified separately.
- CW-06: Documentation and the PR state exact startup versus active-session guarantees, writable-root/trust prerequisites and remaining live/transport limits. Original AW outcomes are not waived.

## Restricted safe continuation after platform flag

The user's subsequent instruction permits only ordinary defensive repairs for saved review CR-01 (literal Windows launcher arguments) and CR-02 (primary note operations through UserPromptSubmit), using static inspection and safe unit fixtures with stub process runners. Then continue installer/configuration edits and non-executing export tests, preserving separate PR99 routing. Publish reviewed safe changes through the existing PR97 stack; never merge.

Do not execute command-injection probes, native host probes or any suspected flagged operation; do not disable safeguards, retry a denial or move a blocked action to another route. Stop a newly denied action and report its exact target. The flag's exact original invocation is unavailable in the saved record. Native generated-adapter acceptance remains unverified and the draft remains explicitly incomplete; historical capability observations are not permission for further probes.

The safe `safe_literal_launcher` unittest selector was subsequently denied before process startup at `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe` (ResourceUnavailable/file access). No retry, alternate interpreter or relocated test is authorized. Further Python checks and runtime invocations remain paused. Continue static changes/review and ordinary Git operations only; coordinator-created Git worktrees retain exact root/base pins and owned paths without hand-editing runtime manifests. Report written tests as not_run, never RED/GREEN. Preserve existing CI configuration; do not manually dispatch a remote run as an alternative to the denied command.

## Bounded installer export-inventory clarification

The static B worker identified the committed `tests/test_install.py` assertion
that Codex has exactly one `SessionStart` group. The authorized new independent
Codex guard requires exactly two. Within existing installer/export-test scope,
update that count and assert both exact identities while preserving the old
context-handoff assertion, rerun-idempotence assertions and all behavioral tests.
Do not weaken to an open-ended count. The retained installed behavioral tracer
remains entirely unchanged. This corrects a directly stale export inventory;
it grants no Python/native execution, new behavior, acceptance or policy change.
All such fixtures and the edited existing case remain NOT_RUN in this work.
