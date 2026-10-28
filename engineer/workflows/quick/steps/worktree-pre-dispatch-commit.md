**Step 5.6: Pre-dispatch artifact commit (worktree mode only)**

When `USE_WORKTREES !== "false"`, commit PLAN.md — plus CONTEXT.md and/or RESEARCH.md
when the discussion/research phases produced them — to the current branch **before**
spawning the executor. This ensures the worktree inherits these artifacts at its branch
HEAD so the executor can read them via a worktree-rooted path — avoiding the main-repo
path priming that triggers CC path-resolution drift, and avoiding the locked
decisions (CONTEXT.md) and research findings (RESEARCH.md) being stranded outside the
worktree while only PLAN.md reaches it.

Skip this step entirely if `USE_WORKTREES === "false"` (non-worktree mode: these artifacts
are committed in Step 8 as usual).

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
QUICK_PLAN_PARENT=""
QUICK_PLAN_COMMIT=""
if [ "${USE_WORKTREES}" != "false" ]; then
  COMMIT_DOCS=$(engineer_run query config-get commit_docs --raw 2>/dev/null || echo "true")
  if [ "$COMMIT_DOCS" != "false" ]; then
    # pre-dispatch plan commit — PLAN.md is always in scope. CONTEXT.md/RESEARCH.md
    # join it only when their phase actually ran AND actually produced a file — a
    # mode flag alone is not proof the file exists. An array (not a
    # space-joined string) keeps each path a single git argument under `set -u`
    # word-splitting rules (ShellCheck SC2086).
    QUICK_PREDISPATCH_PATHS=("${QUICK_DIR}/${quick_id}-PLAN.md")
    if [ "${DISCUSS_MODE}" = "true" ] && [ -f "${QUICK_DIR}/${quick_id}-CONTEXT.md" ]; then
      QUICK_PREDISPATCH_PATHS+=("${QUICK_DIR}/${quick_id}-CONTEXT.md")
    fi
    if [ "${RESEARCH_MODE}" = "true" ] && [ -f "${QUICK_DIR}/${quick_id}-RESEARCH.md" ]; then
      QUICK_PREDISPATCH_PATHS+=("${QUICK_DIR}/${quick_id}-RESEARCH.md")
    fi
    git add "${QUICK_PREDISPATCH_PATHS[@]}"
    # No-op skip if nothing actually staged (idempotent re-runs).
    if git diff --cached --quiet -- "${QUICK_PREDISPATCH_PATHS[@]}"; then
      echo "ℹ Pre-dispatch artifact commit skipped (no staged changes)"
    else
      # Run hooks normally. If a project opts out via
      # workflow.worktree_skip_hooks=true, honor that opt-in only.
      SKIP_HOOKS=$(engineer_run query config-get workflow.worktree_skip_hooks --raw 2>/dev/null || echo "false")
      if [ "$SKIP_HOOKS" = "true" ]; then
        git commit --no-verify -m "docs(${quick_id}): pre-dispatch artifacts for ${DESCRIPTION}" -- "${QUICK_PREDISPATCH_PATHS[@]}" \
          || { echo "ERROR: pre-dispatch artifact commit failed (--no-verify path). Aborting before executor dispatch." >&2; exit 1; }
      else
        git commit -m "docs(${quick_id}): pre-dispatch artifacts for ${DESCRIPTION}" -- "${QUICK_PREDISPATCH_PATHS[@]}" \
          || { echo "ERROR: pre-dispatch artifact commit failed — likely a pre-commit hook failure. Fix the hook output above (or set workflow.worktree_skip_hooks=true to bypass) and re-run." >&2; exit 1; }
      fi
      QUICK_PLAN_COMMIT=$(git rev-parse HEAD)
    fi
  fi
  if [ -z "$QUICK_PLAN_COMMIT" ]; then
    QUICK_PLAN_COMMIT=$(git rev-parse HEAD)
  fi
  # The alternate base is the PLAN commit's immediate parent, read AFTER the
  # commit attempt so it holds whether the planner already committed the plan or this
  # step just did. Empty when docs commits are off and for a root commit.
  if [ "$COMMIT_DOCS" != "false" ]; then
    _ENGINEER_PLAN_AT=$(git log -1 --format=%H -- "${QUICK_DIR}/${quick_id}-PLAN.md" 2>/dev/null || true)
    [ -n "$_ENGINEER_PLAN_AT" ] || _ENGINEER_PLAN_AT="$QUICK_PLAN_COMMIT"
    QUICK_PLAN_PARENT=$(git rev-parse --verify --quiet "${_ENGINEER_PLAN_AT}^" 2>/dev/null || true)
  fi
fi
```
