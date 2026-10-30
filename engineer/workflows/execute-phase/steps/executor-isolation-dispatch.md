# Executor isolation dispatch

Read and follow this fragment from `execute-phase.md` step 3 when dispatching a wave.
It owns the per-host dispatch detail so the host workflow stays inside its
ADR-857 Phase 6 byte budget — the host step keeps only the `ISOLATION`
resolution and its fail-closed guard.

## Resolve ISOLATION

The resolution rule is shared with every other dispatch site — see
@~/.claude/engineer/references/dispatch-isolation-gate.md, the canonical statement of the
`ISOLATION`-not-`RUNTIME` contract. This fragment keeps the wave-specific

Run this in the config-gate step, before dispatch.

```bash
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
# Isolation is a NEGOTIATED CAPABILITY, not a runtime id. Fail-closed to none.
# CORE REDESIGN: `dispatch-isolation` PERSISTS this resolution to the
# run-scoped sentinel the isolation guard hooks read, as an unconditional
# side effect of resolving it — this call is the ONLY way the workflow learns
# ISOLATION at all, so the recording cannot be skipped the way a separate
# "and now also run this to record it" prose instruction could be. `--phase`
# threads the phase identifier into that same atomic write (mode + harnessFlag
# + phase together — see hooks/lib/isolation-sentinel.js for how the guards
# consume it).
# Keep the resolver's own failure DISTINGUISHABLE from a genuine `none`, exactly
# as references/dispatch-isolation-gate.md does — this site declares that gate
# canonical, so it must not carry the older collapsing shape. Both outcomes fail
# closed, which is right, but only one of them may claim the host declared no
# primitive ( review).
_ISOLATION_RAW=$(engineer_run query dispatch-isolation --raw --phase "${PHASE_NUMBER:-}" 2>/dev/null)
_ISOLATION_RC=$?
if [ $_ISOLATION_RC -ne 0 ] || [ -z "$_ISOLATION_RAW" ]; then
  ISOLATION=none
  ISOLATION_RESOLVED=false      # fail closed, but we did NOT learn a verdict
else
  ISOLATION="$_ISOLATION_RAW"
  ISOLATION_RESOLVED=true
fi
case "$ISOLATION" in
  harness-worktree|orchestrator-worktree|none) ;;
  *) ISOLATION=none; ISOLATION_RESOLVED=false ;;   # out of vocabulary is not a verdict either
esac

case "$ISOLATION" in
  harness-worktree|orchestrator-worktree) ;;
  *) echo "FATAL: mandatory executor isolation could not be established" >&2; exit 1 ;;
esac

# Sweep orphaned locked worktrees from prior crashed sessions.
[ "$ISOLATION" != "none" ] && engineer_run query worktree.reap-orphans 2>/dev/null || true
```

`ISOLATION` — not `RUNTIME` — selects how the wave fans out. These two values are the only
branch points; **never add a `RUNTIME = "codex"` test to the scheduler.** The per-host
invocation detail is descriptor data, surfaced by `dispatch-isolation --json` as
`harnessFlag` / `exec`.

| `ISOLATION` | Fan-out | What the scheduler does |
|---|---|---|
| `harness-worktree` | host-driven | Pass the host's own declared isolation flag (`harnessFlag`) on each executor dispatch and let the harness create + bind the worktree. Engineer runs no git. |
| `orchestrator-worktree` | Engineer-driven | Engineer creates the worktree (`worktree create`), then dispatches the native executor bound to it. Engineer performs all git operations. |

Unavailable or unresolvable isolation stops dispatch. Neither supported adapter permits primary-checkout execution.

## harness-worktree — pass the host flag

Read the flag once before dispatching; it is descriptor data, never hardcoded per runtime:

```bash
# CORE REDESIGN: `dispatch-isolation --json` already resolves and
# atomically records `harnessFlag` together with `isolation` and `phase` in
# ONE write, as a side effect of this same call (routeDispatchIsolation,
# engineer/bin/engineer.py) — there is no separate "now also record the
# flag" step, and therefore no flagless window between recording the mode and
# recording the flag.
HARNESS_FLAG=$(engineer_run query dispatch-isolation --json --phase "${PHASE_NUMBER:-}" 2>/dev/null \
  | engineer_run query json.get --field harnessFlag --default "" --raw)
[ -n "$HARNESS_FLAG" ] || { echo "FATAL: runtime declares dispatch.isolation=harness-worktree but no harnessIsolationFlag — refusing to dispatch executors that would believe they are isolated." >&2; exit 1; }
```

Substitute `$HARNESS_FLAG`'s value for the `{harnessFlag}` placeholder in the `Agent()` dispatch
in `execute-phase.md` step 3 (on Claude Code it is literally `isolation="worktree"`).

## orchestrator-worktree — runtime checkout, native agent

The selected `plan_json` is the exact current `phase-plan-index` entry. Its `id` is the full PLAN filename stem (for example `01-02`), not the bare frontmatter plan number; use that same identity for checkout ownership, committed SUMMARY and terminal receipt.

The coordinator creates each checkout before dispatch and parses the runtime's actual returned fields. Keep the plan's exact `PLAN_FILES`/`PLAN_DELETIONS` and committed `SUMMARY_PATH` in coordinator state; these same values must be used when recording the terminal receipt.

```bash
ORCH_ROOT=$(git rev-parse --show-toplevel) || exit $?
EXPECTED_BASE=$(git rev-parse HEAD) || exit $?
PHASE_DIR_REL=$(git -C "$phase_dir" rev-parse --show-prefix) || exit $?
PHASE_DIR_REL="${PHASE_DIR_REL%/}"
[ "$(git -C "$phase_dir" rev-parse --show-toplevel)" = "$ORCH_ROOT" ] || exit 42
plan_id=$(engineer_run query json.get --payload "$plan_json" --field id --raw) || exit $?
SUMMARY_PATH="${PHASE_DIR_REL%/}/${plan_id}-SUMMARY.md"
CREATED_WORKTREE=$(engineer_run query worktree.create "$plan_id" --phase "$PHASE_NUMBER" --manifest "$WAVE_WORKTREE_MANIFEST" --root "$ORCH_ROOT" --base "$EXPECTED_BASE" --files "$PLAN_FILES" --deletions "$PLAN_DELETIONS" --summary-path "$SUMMARY_PATH") || exit $?
WORKTREE_PATH=$(engineer_run query json.get --payload "$CREATED_WORKTREE" --field worktree_path --raw) || exit $?
WORKTREE_BRANCH=$(engineer_run query json.get --payload "$CREATED_WORKTREE" --field branch --raw) || exit $?
EXPECTED_BASE=$(engineer_run query json.get --payload "$CREATED_WORKTREE" --field expected_base --raw) || exit $?
ALLOWED_BASES_JSON=$(engineer_run query json.get --payload "$CREATED_WORKTREE" --field allowed_bases) || exit $?
PLAN_FILES_JSON=$(engineer_run query json.get --payload "$CREATED_WORKTREE" --field files) || exit $?
PLAN_DELETIONS_JSON=$(engineer_run query json.get --payload "$CREATED_WORKTREE" --field deletions) || exit $?
[ "$(git -C "$WORKTREE_PATH" rev-parse HEAD)" = "$EXPECTED_BASE" ] || exit 42
[ "$(git -C "$WORKTREE_PATH" branch --show-current)" = "$WORKTREE_BRANCH" ] || exit 42
```

Bind the native executor's working-directory/workspace input to this exact `WORKTREE_PATH`. Before composing the call, copy the complete runnable root guard from `sequential-root-pin.md` with this returned root embedded; no checkout creation or nested dispatch instruction may remain inside the executor prompt. Resolve model and effort inline. Pass the full assigned PLAN, required reading, constraints and committed SUMMARY requirement unchanged. If the host cannot bind an isolated native worker, stop before dispatch and preserve the created checkout.

Before dispatch, read each file below and inline its actual contents verbatim in the executor prompt's `<execution_context>`, in this order. Keep the provenance list with the prompt; if a required source is missing or truncated, stop before dispatch rather than asking the executor to reconstruct it:

- `agents/executor.md` (executor role definition, per-commit HEAD/cwd-drift/path-guard requirements, and final commit contract)
- `engineer/templates/summary.md`
- `engineer/references/checkpoints.md`
- `engineer/references/tdd.md` when this plan is TDD (`type: tdd`, `tdd: "true"`, or `workflow.tdd_mode`)
- `engineer/references/worktree-path-safety.md`
- `engineer/references/executor-examples.md` when `CONTEXT_WINDOW >= 200000`

The prompt's provenance list names the files embedded, and the text of every listed file is present in the prompt. Preserve the mandatory SUMMARY commit and gitignored-planning skip semantics from those embedded sources.

At execution start, the executor reads these project inputs, resolving each path from the worktree root:

- `{phase_dir}/{plan_file}`
- `.planning/PROJECT.md`
- `.planning/STATE.md`
- `.planning/config.json`, if present
- `{phase_dir}/*-CONTEXT.md`, if present
- `{phase_dir}/*-RESEARCH.md`, if present
- `{prior_wave_summaries}`, when this is not wave 1
- `CLAUDE.md`, if present
- `.claude/skills/` or `.agents/skills/`, if present; read each applicable `SKILL.md`

Capture the actual host agent id from the dispatch tool's result. Follow the native host's lifecycle, `completion-reconciliation.md` and the confirmed-stop rule: a timeout is not proof of exit. Wait for the terminal result and run the receipt procedure below before integrating. Preserve failed, dirty and unmerged checkouts.

## Native terminal receipt — both isolation modes

The coordinator obtains stop evidence from the **native host wait/status tool result**, never from the executor's final prose or its `<worktree_metadata>` claim. Capture the original tool result unchanged as JSON in `HOST_TERMINAL_EVENT_PATH` outside the worker checkout. From that actual tool metadata bind `HOST_AGENT_ID`, `HOST_KIND` (`claude` or `codex`) and `HOST_TERMINAL_STATUS`. Accept complete/completed/stopped only when the host result explicitly establishes terminal state; an active, unknown, timed-out or missing result blocks recording and merge. Do not synthesize a terminal state because SUMMARY exists. Preserve the original event beside the projected receipt so the source of the stop assertion remains reviewable.

For a harness-created checkout, get its path from the host's own metadata and verify its branch with Git; use the base/allowed bases captured before dispatch. Bind `WORKTREE_PATH`, `WORKTREE_BRANCH`, `EXPECTED_BASE`, `ALLOWED_BASES_JSON`, `PLAN_FILES_JSON`, `PLAN_DELETIONS_JSON`, `SUMMARY_PATH`, `plan_id` and the same owned `WAVE_WORKTREE_MANIFEST` before running the commands below. For a runtime-created checkout these are the captured create result above; `record-agent` attaches the first validated receipt and actual host id to that existing ownership entry. Subsequent receipts/ids are immutable.

```bash
: "${HOST_TERMINAL_EVENT_PATH:?Capture the actual terminal host tool result first}"
: "${HOST_AGENT_ID:?Use the actual native host agent id}"
: "${HOST_KIND:?Use the observed native host kind}"
: "${HOST_TERMINAL_STATUS:?Use the terminal state observed by the host tool}"
case "$HOST_TERMINAL_STATUS" in complete|completed|stopped) ;; *) echo "BLOCKED: host worker is not confirmed stopped" >&2; exit 1 ;; esac
WORKER_BRANCH=$(git -C "$WORKTREE_PATH" branch --show-current) || exit $?
[ "$WORKER_BRANCH" = "$WORKTREE_BRANCH" ] || { echo "FATAL: worker branch drift" >&2; exit 42; }
WORKER_HEAD=$(git -C "$WORKTREE_PATH" rev-parse HEAD) || exit $?
NATIVE_TERMINAL_RECEIPT=$(mktemp "${TMPDIR:-/tmp}/engineer-native-terminal-XXXXXX") || exit $?
mv "$NATIVE_TERMINAL_RECEIPT" "${NATIVE_TERMINAL_RECEIPT}.json" && NATIVE_TERMINAL_RECEIPT="${NATIVE_TERMINAL_RECEIPT}.json" || exit 1
HOST_TERMINAL_EVENT_PATH="$HOST_TERMINAL_EVENT_PATH" HOST_AGENT_ID="$HOST_AGENT_ID" HOST_KIND="$HOST_KIND" HOST_TERMINAL_STATUS="$HOST_TERMINAL_STATUS" WORKTREE_PATH="$WORKTREE_PATH" WORKER_BRANCH="$WORKER_BRANCH" WORKER_HEAD="$WORKER_HEAD" SUMMARY_PATH="$SUMMARY_PATH" node <<'NODE' > "$NATIVE_TERMINAL_RECEIPT"
const fs = require('fs');
const e = process.env;
const hostEvent = JSON.parse(fs.readFileSync(e.HOST_TERMINAL_EVENT_PATH, 'utf8'));
if (!hostEvent || typeof hostEvent !== 'object' || !['claude','codex'].includes(e.HOST_KIND) || !['complete','completed','stopped'].includes(e.HOST_TERMINAL_STATUS)) process.exit(1);
process.stdout.write(JSON.stringify({host:e.HOST_KIND, source:'native-host', status:e.HOST_TERMINAL_STATUS, agent_id:e.HOST_AGENT_ID, branch:e.WORKER_BRANCH, head:e.WORKER_HEAD, worktree_path:e.WORKTREE_PATH, summary_path:e.SUMMARY_PATH, host_event:hostEvent})+'\n');
NODE
[ "$?" -eq 0 ] || exit 1
engineer_run query worktree.record-agent "$plan_id" --manifest "$WAVE_WORKTREE_MANIFEST" --agent-id "$HOST_AGENT_ID" --path "$WORKTREE_PATH" --branch "$WORKTREE_BRANCH" --base "$EXPECTED_BASE" --allowed-bases "$ALLOWED_BASES_JSON" --files-json "$PLAN_FILES_JSON" --deletions-json "$PLAN_DELETIONS_JSON" --summary-path "$SUMMARY_PATH" --terminal-receipt "$NATIVE_TERMINAL_RECEIPT" || exit $?
```

A host event that cannot be mapped from its actual documented metadata remains unknown; preserve it and the checkout rather than guess. After **every** wave worker has its receipt recorded and its committed output reconciled, integrate through `worktree.merge-wave --manifest "$WAVE_WORKTREE_MANIFEST"`, then `worktree.cleanup-wave` only with repository merge evidence. Never use retired worker-record/status/complete operations or `--completed` as stop proof.
