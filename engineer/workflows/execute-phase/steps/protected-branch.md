# Protected-branch warning for `branching_strategy: none`

Run this from the `handle_branching` step's `"none"` arm, after deciding to
continue on the current branch. It warns without refusing execution — the
`"none"` strategy still runs on whatever branch it started on.

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
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || true)
IS_PROTECTED=$(engineer_run query git.base-branch --is-protected "$CURRENT_BRANCH") || IS_PROTECTED=""
if [ "$IS_PROTECTED" = true ]; then
  echo "⚠ Current branch '$CURRENT_BRANCH' is a protected branch; branching_strategy=none will continue here." >&2
elif [ -z "$IS_PROTECTED" ]; then
  echo "⚠ Could not determine whether '$CURRENT_BRANCH' is protected — the query failed. Continuing." >&2
fi
```

The `IS_PROTECTED=""` fallback on the first line, and the second `elif`, exist
so a failed or missing `engineer_run` invocation degrades **visibly** (an explicit
"could not determine" warning) rather than silently reading as "not
protected" under `set -e` ( review, round 5).
