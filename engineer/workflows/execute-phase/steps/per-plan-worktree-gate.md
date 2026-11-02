# Per-plan worktree decision and per-dispatch isolation record
## Part 1 — Decide (run for each plan in the wave, up front, at `execute_waves` step 2.5)

Worktree isolation is mandatory for every executor. A plan touching a registered submodule is blocked before dispatch; this gate never downgrades a plan to sequential execution.

`SUBMODULE_PATHS` is computed once in the `initialize` step (parsed from `.gitmodules`).

`PLAN_FILES` is the whitespace-separated list of paths the plan declared it will touch, extracted from the `phase-plan-index` JSON loaded in `discover_and_group_plans`:

```bash
# plan_json is the JSON object for this plan from PLAN_INDEX.plans[]
# files_modified is an array of strings (repo-relative paths or globs)
PLAN_FILES=$(jq -r '.files_modified // [] | join(" ")' <<<"$plan_json")
# Files_deleted is the paths the plan declared it will REMOVE. Separate from
# files_modified on purpose — it authorizes the cleanup-wave deletions guard, and a
# deletion authorization must never be inferred from a general scope declaration.
PLAN_DELETIONS=$(jq -r '.files_deleted // [] | join(" ")' <<<"$plan_json")
plan_id=$(jq -r '.id' <<<"$plan_json")
```

Then run the per-plan gate:

```bash
SUBMODULE_PATHS=$(git config --file .gitmodules --get-regexp path 2>/dev/null | awk '{print $2}')

# This gate asks "does the plan touch a submodule at all", and REMOVING a file
# inside one is as much a touch as modifying it. Both declared channels feed the
# intersection: before files_deleted existed a deleted path had to appear in
# files_modified to be planned at all, so the gate saw it. Now that plan-md.md tells
# authors a deleted path needs no files_modified entry, reading files_modified alone
# would let a deletion-only submodule plan keep worktree isolation on.
# Note this is the OPPOSITE posture from the cleanup-wave
# deletions guard: there the two channels are kept apart because a deletion
# AUTHORIZATION must never be inferred; here they are merged so neither kind of
# declared path can hide a submodule touch.
PLAN_SCOPE_PATHS=$(printf '%s %s' "$PLAN_FILES" "$PLAN_DELETIONS" | tr -s ' ' | sed 's/^ //; s/ $//')

if [ -n "$SUBMODULE_PATHS" ]; then
  if [ -z "$PLAN_SCOPE_PATHS" ]; then
    # Scope is unknown, so the intersection cannot be ruled out safely.
    echo "[worktree] Plan ${plan_id}: files_modified and files_deleted are both missing/unparseable — blocking dispatch because submodule scope cannot be established"
    exit 1
  else
    # Compute intersection with glob-safe normalization. Both sides are
    # normalized (collapse repeated separators, remove leading and internal
    # "/./" segments, strip trailing "/") and matched
    # bidirectionally so a globby planned path like "vendor/**/*.c" still
    # matches submodule "vendor/foo", and "./vendor/foo/bar.c" matches
    # submodule "vendor/foo".
    INTERSECT=""
    set -f  # disable globbing while iterating literal patterns
    normalize_scope_path() {
      local path="$1" previous
      # Keep reducing until repeated separators and dot segments are gone.
      # This is lexical normalization only: do not resolve symlinks or expand
      # glob characters from a plan's literal scope patterns.
      while :; do
        previous="$path"
        path="${path//\/\//\/}"
        path="${path//\/\.\//\/}"
        [ "$path" = "$previous" ] && break
      done
      while [ "${path#./}" != "$path" ]; do path="${path#./}"; done
      path="${path%/}"
      printf '%s' "$path"
    }
    # Rewrapped through unquoted command substitution (): a bare
    # `$VAR` word-splits under bash but not zsh, collapsing every element onto
    # one iteration there.
    for sm_raw in $(printf '%s' "$SUBMODULE_PATHS"); do
      # Normalize the submodule path before comparing it with plan scope.
      sm=$(normalize_scope_path "$sm_raw")
      [ -z "$sm" ] && continue
      # Rewrapped through unquoted command substitution (): a bare
      # `$VAR` word-splits under bash but not zsh, collapsing every element onto
      # one iteration there.
      for pf_raw in $(printf '%s' "$PLAN_SCOPE_PATHS"); do
        # Normalize the planned path the same way; retain pf_raw for reporting.
        pf=$(normalize_scope_path "$pf_raw")
        [ -z "$pf" ] && continue
        matched=0
        # Direction 1: planned path is the submodule or lies inside it
        case "$pf" in
          "$sm"|"$sm"/*) matched=1 ;;
        esac
        # Direction 2: submodule lies inside the planned path (e.g. plan
        # declares "vendor" or a glob expanding to a directory containing
        # the submodule).
        if [ "$matched" -eq 0 ]; then
          case "$sm" in
            "$pf"|"$pf"/*) matched=1 ;;
          esac
        fi
        # Direction 3: planned path uses a glob — strip glob wildcards
        # and check whether the resulting prefix overlaps the submodule
        # path in either direction.
        if [ "$matched" -eq 0 ]; then
          case "$pf" in
            *'*'*|*'?'*|*'['*)
              # Take the literal prefix before the first glob metachar.
              prefix="${pf%%[*?[]*}"
              prefix="${prefix%/}"
              if [ -n "$prefix" ]; then
                case "$sm" in
                  "$prefix"|"$prefix"/*) matched=1 ;;
                esac
                if [ "$matched" -eq 0 ]; then
                  case "$prefix" in
                    "$sm"|"$sm"/*) matched=1 ;;
                  esac
                fi
              fi
              ;;
          esac
        fi
        if [ "$matched" -eq 1 ]; then
          INTERSECT="$INTERSECT $pf_raw"
        fi
      done
    done
    set +f
    if [ -n "$INTERSECT" ]; then
      echo "[worktree] Plan ${plan_id}: planned paths intersect submodule paths (${INTERSECT# }) — blocking dispatch; submodule paths are unsupported"
      exit 1
    fi
  fi
fi
```

Keep `PLAN_FILES` and `PLAN_DELETIONS` per plan and re-extract them immediately before dispatch. A submodule intersection blocks this plan; every other ready plan retains mandatory worktree isolation.

## Part 2 — Re-record the dispatch-isolation sentinel, scoped to THIS plan ( BLOCKER 1)


The phase-level sentinel (written by the "Resolve ISOLATION" step, before per-plan dispatch) covers the phase. Record the isolation mode again for this plan immediately before dispatch so the sentinel is fresh and identifies the plan being dispatched. Submodule intersections and unknown submodule scope have already blocked above; this record must preserve mandatory worktree isolation for every dispatched plan:

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

**`PLAN_FILES` is reused after dispatch:** pass it as `--files "$PLAN_FILES"` on the step-3 `worktree.record-agent` call (and on `worktree.create` in the orchestrator-worktree path) so the post-wave cleanup gauntlet can compare each plan branch's actual committed diff against the scope the plan declared, and report any path outside it. That check is advisory — it warns, it never blocks the merge — and omitting the flag simply skips it for that plan.

**`PLAN_DELETIONS` is reused the same way:** pass it as `--deletions "$PLAN_DELETIONS"` on the same `worktree.record-agent` / `worktree.create` calls. Unlike `--files`, this one is **not** advisory — it is what lets the post-wave deletions guard merge a branch whose plan declared a file removal. Matching is exact per path: a declared path merges, anything else still blocks that entry (and only that entry). Omitting the flag keeps the guard's original behavior of blocking on any deletion at all, so a plan that declares nothing loses nothing.
