# Completion reconciliation (split A of )

Read and follow this fragment from `execute-phase.md` step 4 whenever an executor's
completion is in question. It owns the whole reconciliation policy — both arms — so the
host wait step stays inside the ADR-857 Phase 6 byte ceiling.

**Reconcile FIRST, classify SECOND.** How the child's session ended is bookkeeping
about the transport; what it wrote to disk and to git is the evidence about the work.

## When this runs

1. **No terminal response** — a spawned agent does not return a normal terminal
   completion signal but appears to have finished its work (or may still be running).
2. **Abnormal end** — the child's session ended without a normal terminal completion
   response: interrupted, aborted, closed, killed, timed out, or ended `turn_aborted` —
   INCLUDING ends the orchestrator itself initiated. **An abnormally-ended child is
   not evidence of failure:** the orchestrator's own interrupt/close says
   nothing about whether the work completed; only the artifacts do.

This policy applies to EVERY runtime and every isolation path — harness `Agent()`
dispatches, orchestrator-worktree process spawns, and sequential dispatch alike. Never
block indefinitely waiting for a signal; verify via filesystem and git state.

## Probes (per plan in the wave)

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
# For each plan in this wave, check if the executor finished:
SUMMARY_EXISTS=$(test -f "{phase_dir}/{plan_number}-{plan_padded}-SUMMARY.md" && echo "true" || echo "false")
# The plan's commits come from the evaluation-scope resolver — anchored on the SUBJECT,
# zero-pad tolerant, reachable from THIS branch only (the former
# any-branch lookup let a commit on another branch satisfy the probe); the 1-hour window stays.
# Exit 69 (UNAVAILABLE) is the resolver saying "could not look": an empty COMMITS_FOUND is then NOT "no commits".
COMMITS_SCOPE=$(engineer_run check evaluation-scope --plan "{phase_number}-{plan_padded}" --ref "${EXPECTED_BRANCH}" --commits-only --committed-since "1 hour ago" --raw 2>/dev/null) && COMMITS_SCOPE_RC=0 || COMMITS_SCOPE_RC=$?
COMMITS_FOUND=""
if [ "$COMMITS_SCOPE_RC" -eq 0 ]; then COMMITS_FOUND=$(printf '%s' "$COMMITS_SCOPE" | engineer_run query json.get --field commits.0.sha --default "" --raw); fi
COMMITS_SINCE_DISPATCH=$(git log "${EXPECTED_BRANCH}" --since="${DISPATCH_TS}" --oneline | head -1)
```

## Verdicts

**If `COMMITS_SCOPE_RC` is non-zero** (`69` `UNAVAILABLE`: the commit scope could not be resolved): the commit probe has no answer. Do not read the empty `COMMITS_FOUND` as "no matching commits", do not route to the failure handler on it, and do not re-dispatch an executor: surface `⚠ Commit probe unavailable for {Plan ID} (evaluation-scope exit {COMMITS_SCOPE_RC})` and stop for the user.

**If SUMMARY.md exists AND matching commits are found:** the agent completed
successfully — treat the plan as complete WITHOUT requiring another terminal child
response, proceed to step 5, and do NOT re-dispatch a fresh executor for this plan:
the work is already committed, and a second executor would redo it on top of itself.
Log: `"✓ {Plan ID} completed (verified via spot-check — completion signal not received)"`.

**If SUMMARY.md does NOT exist after a reasonable wait:** the agent may still be
running or may have failed silently. Check `git log --oneline -5` for recent
activity. If commits are still appearing, wait longer. If no activity, report the
plan as failed and route to the failure handler in step 6.

Evidence is BOTH probes or neither: a SUMMARY without matching commits, and matching
commits without a SUMMARY, are each incomplete evidence — never auto-complete on one
of them. When an abnormal end reconciles to no completion evidence, it stays failed:
route to the failure handler exactly as a normal failure would, and let the
safe-resume gate handle any un-summarized commits on the next run.
