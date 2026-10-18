# Same-existing-agent native worktree entry

This document covers two distinct host paths. Claude may conditionally move the
same existing caller through its native `EnterWorktree` route below. Codex uses a
bounded startup launcher for a **new** run, documented in [Codex startup](#codex-startup).
That launcher does not move an existing conversation or active agent.

## Codex startup

The installer exports a thin `.codex/codex-worktree.py` entry point. It accepts
`phase|quick LABEL [--base COMMIT] [--prompt TEXT] [--exec]` and calls the
adjacent installed `runtime/lib/codex_worktree.py` `launcher_main`; it does not
forward arbitrary native arguments. After installing and reviewing the Codex
project hooks, run:

```text
python .codex/codex-worktree.py phase 12 --prompt "Review the phase context"
python .codex/codex-worktree.py quick 261016-001-example --exec --prompt "Implement the approved change"
```

The launcher selects and validates one runtime-owned phase or quick session,
then starts the native `codex` executable with `--cd <destination> --enable
hooks`. `--exec` adds the native `exec` subcommand. A prompt is passed as one
argument after native `--`; a prompt that begins with a flag must use the
launcher form `--prompt=--literal-flag` so the launcher's option parser treats
it as prompt data. The launcher requires a directly resolvable native
executable. On Windows, `.bat` and `.cmd` shims are refused because their shell
parsing would alter argument boundaries.

Startup reuses the existing session-selection/runtime ownership checks and
never syncs or copies dirty data. Hook decisions also allow exactly the
validated ordinary phase/quick receipt or active orchestrator-worktree worker
receipt covered by the source contract; ordinary adopted phase sessions retain
their established identity and accumulated commits. The primary checkout's
ordinary note lifecycle may pass at `UserPromptSubmit`, while supported source
mutations are still classified and require an eligible isolated root at
`PreToolUse`. This distinction does not make `UserPromptSubmit` a source-write
guard.

The launcher verifies registered installation inputs, native hook definitions
and trust/managed status, then compares effective sandbox and approval policy.
It preserves those settings and refuses missing, changed, stricter, or ambiguous
policy rather than replacing it. Native trust and host policy remain required;
installation alone does not prove a live host will run the hooks. The generated
guard checks structured targets and supported tools. Opaque shell/MCP writers,
unhooked transports, host fail-open behavior and later configuration changes
remain outside its proof. The actual generated-adapter shell and patch denial,
effective-feature behavior and live host transition remain unverified here;
Python execution was blocked, so no current runtime or native success is claimed.

The launcher enables hooks for its native invocation with `--enable hooks`.
Whether that invocation setting interacts safely with every effective feature
or managed-policy configuration remains an open question; do not infer an
answer from source or export inspection.

This integration has no authenticated same-thread controller; active Codex
conversation or agent movement is unsupported. Start a new run with the phase or
quick command above. Do not invoke the launcher to simulate movement, replay a
cancelled edit, or substitute a child/fork or per-call directory override. Do
not infer a product-wide Codex limitation from this integration constraint.

## Claude native entry

The protocol below is Claude-specific. A hook cancels a source edit and provides
a request; it cannot move its caller. Only the same existing agent's actual
native `EnterWorktree` operation can perform entry. Hook output, a prepared
directory, a ticket, shell `cd`, per-call cwd/path overrides and a replacement
child/fork are never movement proof.

## Gate before native action

Inspect the tools and schema actually advertised to this caller. Require
`EnterWorktree` with the applicable creation/name or existing/path field. Use
the advertised field, never a guessed argument, minimum release or unnamed
creation. Missing/incompatible schema/tool is unsupported. Check actual role
permission (installed Claude coordinator/coder exports permit it), eligibility,
policy and hook trust/registration. A tool grant in a role or skill does not
manufacture tool availability. A pinned or already-isolated caller cannot use
new creation; honor the native path form's restrictions, including any limitation
to the session repository's `.claude/worktrees/`. Honor required approval for an
existing outside path. Never reuse a creation name to bypass that approval.

If a gate fails, report the exact unsupported route with the edit unapplied.
Do not repeatedly retry the edit, guess identity, dispatch a child or fall back
to shell movement. An already correctly isolated caller needs no native move;
validate its registered root/branch/unit and keep tools there by default.

## Obtain and bind one request

After intercepted source denial, use the exact `prewrite.begin <request>` ID in
its reason. The original call is cancelled, including all its targets. Do not
resubmit it or rewrite its arguments. Use the explicit known phase/quick unit;
for an ad-hoc edit use the ticket-local quick label in the denial. No newest
session, branch or transcript inference is allowed.

Workflow entry before any edit instead bootstraps its known unit from the
primary checkout, without inventing a pending edit:

```bash
phase_run query prewrite.request <phase|quick> <label> --mode <new|existing>
phase_run query prewrite.begin <request_id> <phase|quick> <label> --mode <new|existing>
```

Choose the mode explicitly from the exact unit/session facts: `new` requires no
open session; `existing` requires exactly one validated open session. These are
placeholders, not literal shell syntax. The real command uses the known unit
and returned request ID. Wrong/ambiguous ownership or mode refuses; never switch
modes to evade failure. The runtime uses documented `CLAUDE_CODE_SESSION_ID`
correlation from tool subprocesses. If it is unavailable, report unsupported
workflow correlation. `${CLAUDE_SESSION_ID}` is skill-content substitution,
not a shell environment variable. No agent-ID environment variable is assumed.
Optional CLI session/agent arguments are correlation claims, not authentication.
Workflow requests are provisional repo/nonce/unit/session bindings; actual native
hook session and optional agent identity are compared and conflicts refused.
Omitted agent identity alone does not establish main-agent eligibility.

`begin` reserves a fresh `wf-entry-<token>` name and `worktree-wf_<token>` branch
for new mode at the captured local committed base under the configured ignored
root. It creates no checkout and does not sync/fetch/copy dirty data. Existing
mode returns the exact ordinary session's root/branch/historical base with no
creation name or fabricated native journal. Preserve its accumulated commits.

## Invoke native entry as this same caller

For new mode, call the actual advertised `EnterWorktree` creation form with the
reserved identity using its advertised name field. The trusted registered
WorktreeCreate provider creates exactly that fresh checkout from the pinned
local commit. Its callback runs before native entry completes: returning a path
is creation evidence only. Existing destinations, branches, reused names and
uncertain earlier creation are refused, never returned as new creation.

For existing mode, use the actual advertised native existing-path form for the
returned root. Honor eligibility, policy and required approval. Do not invoke
creation/WorktreeCreate, adopt it again or rewrite its ownership/base. An
ordinary phase/quick session needs no native-creation journal.

If native entry is denied, times out or returns no result, inspect the same
session's native state, request journal and actual Git registration. Do not infer
completion or failure from the missing result. If evidence proves entry completed,
verify destination defaults before continuing; otherwise preserve the request as
pending and report it unverified. Do not create another tree, repeat native
entry, replay an edit or use a creation ticket to retry a native existing name.

A repeated source attempt from the same observed caller with a new tool-use ID
reuses its pending request only for the unchanged intent/root/branch/base. A
changed intent while entry is pending refuses; use an explicit known workflow
unit rather than silently reserving another ad-hoc tree. Creation tickets expire;
a Git-confirmed native unit retains its durable source-actor and Git checks for
continued edits without a new move. Incomplete records remain refused/preserved.

## Prove defaults, confirm Git, then reconstruct

Observe native completion for the same existing session/actor. Run subsequent
tools without cwd overrides, old absolute target arguments or prefixed `cd`.
Their actual default cwd and Git root/branch must be the destination; check its
registration and pinned base (existing sessions may have later commits). Confirm
destination write permission and reload destination CLAUDE/AGENTS, project
configuration and relevant instructions. Resolve the runtime again there and
rerun this workflow's locate/init inputs from those defaults. Replace old paths,
models, settings and context; do not use an old terminal's cwd as proof.
`CLAUDE_PROJECT_DIR` stays anchored to the original project; it is not the
post-entry working directory.

Then, from those actual default destination tools, run:

```bash
phase_run query prewrite.confirm <request_id>
```

It checks request/Git facts only and explicitly returns
`host_binding_verified: false`. New creation is adopted as one phase/quick unit
without another tree or primary sync. Existing confirmation returns `reused:
true`, preserving historical base, accumulated HEAD and exact session ownership.
Runtime success cannot certify host identity, permissions or context binding.

Freshly read every destination file, including rename/delete sources. Rebuild
the intended edit against those reads and apply once, using destination-relative
paths. Never reuse cancelled offsets/absolute paths/input. If intent depends on
dirty primary content absent in the fresh checkout, report that dependency and
preserve it; do not silently copy, stash, reset or replay it. Later tools and a
later turn must continue to use destination defaults. Preserve all staged,
unstaged, untracked and ignored data and account for any actual host relocation.

The registered native WorktreeRemove path preserves native-entry checkouts,
branches and journals even if clean, dirty, ignored-only or uncertain. Missing
or corrupt native identity is never permission to delete. Ordinary dispatch
removal retains its separate behavior. If the host ignores the trusted custom
provider, report lifecycle support unverified rather than promising preservation.

Deterministic fixtures use a **SIMULATED** host adapter and real installed hooks
and Git. They do not demonstrate that a live model calls native entry or that a
host rebinds its defaults. Live native smoke is unavailable in the selected
executor and remains required for conclusive same-agent movement acceptance.
