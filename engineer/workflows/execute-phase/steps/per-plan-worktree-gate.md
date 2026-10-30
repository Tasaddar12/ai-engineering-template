# Per-plan worktree isolation and dispatch record

## Part 1 — Preserve each plan's declared scope

Run for every plan in the wave before dispatch. Worktree isolation is mandatory for every executor; this gate does not disable or downgrade it. Submodules are unsupported by this workflow.

`PLAN_FILES` and `PLAN_DELETIONS` come from the plan's `phase-plan-index` JSON in `discover_and_group_plans`:

```bash
# plan_json is the JSON object for this plan from PLAN_INDEX.plans[]
# files_modified is an array of repo-relative paths or globs
PLAN_FILES=$(jq -r '.files_modified // [] | join(" ")' <<<"$plan_json")
# Keep deletion authorization separate from general modified-file scope.
PLAN_DELETIONS=$(jq -r '.files_deleted // [] | join(" ")' <<<"$plan_json")
plan_id=$(jq -r '.id' <<<"$plan_json")
```

Keep both lists with this plan. Re-extract them from its JSON immediately before dispatch; never infer a deletion authorization from `PLAN_FILES`.

## Part 2 — Record isolation for THIS plan

Run in `execute_waves` step 3 immediately before dispatching the plan. This records the mandatory worktree mode under the plan being dispatched:

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
engineer_run query dispatch-isolation --raw --phase "${PHASE_NUMBER:-}" --plan "$plan_id" || exit 1
```

Pass `PLAN_FILES` as `--files "$PLAN_FILES"` and `PLAN_DELETIONS` as `--deletions "$PLAN_DELETIONS"` to the step-3 `worktree.record-agent` / `worktree.create` calls. The first records declared modification scope for comparison with the branch diff; the second authorizes only the listed deletions. Neither list replaces the other.
