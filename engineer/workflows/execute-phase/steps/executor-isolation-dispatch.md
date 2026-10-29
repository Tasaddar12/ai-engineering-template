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

Create each isolated checkout with `engineer_run query worktree.create` using the captured base, plan id, declared files and deletions. Dispatch the same native `executor` agent into the returned checkout with an embedded `<project_root_pin>` guard from `sequential-root-pin.md`. Resolve model and effort inline. Pass the assigned PLAN, required reading, constraints and SUMMARY path unchanged.

Record the host agent identifier and checkout metadata before waiting. Follow the native host's worker lifecycle, `completion-reconciliation.md` and the confirmed-stop rule: a timeout is not proof of exit. Wait for all wave workers and reconcile artifacts and commits before accepting completion; never reassign paths while a worker remains active or unknown. Preserve failed, dirty and unmerged checkouts. Integrate through `worktree.merge-wave`, then `worktree.cleanup-wave` only with repository merge evidence.
