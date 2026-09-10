#!/usr/bin/env bash
# Optional JSON PreToolUse example. No host registration is supplied.
# Reads cwd/tool_name/tool_input and emits a deny response for some obvious
# writes outside git's checkout root, shared Git directory or scratchpad_dir.
# This is an accident guard, not a sandbox. It fails open on missing context;
# lexical path checks do not resolve symlinks/junctions and lowercase paths
# even on case-sensitive filesystems. Shell checks cover only some redirects.
# It cannot justify bypassing the host's permission controls. See README.md.

set -u

payload="$(cat 2>/dev/null || true)"

# --- extract a top-level or tool_input string field ---------------------------
# Tiered on purpose. The sed fallback stops at the first quote, so it truncates
# any value containing an escaped quote — which is most Bash commands. That
# fails OPEN (no block), the safe direction, but it makes the Bash check
# near-useless without a real parser. jq or python restores it. The file-tool
# checks are unaffected either way: a file_path is a path, not a sentence.
if command -v jq >/dev/null 2>&1; then
  _JSON=jq
elif command -v python3 >/dev/null 2>&1; then
  _JSON=python3
elif command -v python >/dev/null 2>&1; then
  _JSON=python
else
  _JSON=sed
fi

_PYEX='
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
k = sys.argv[1]
v = d.get(k)
if not isinstance(v, str):
    v = (d.get("tool_input") or {}).get(k)
sys.stdout.write(v if isinstance(v, str) else "")
'

field() {
  case "$_JSON" in
    jq)
      printf '%s' "$payload" | jq -r --arg k "$1" \
        '(.[$k]? // .tool_input[$k]? // "") | if type=="string" then . else "" end' 2>/dev/null
      ;;
    python3|python)
      printf '%s' "$payload" | "$_JSON" -c "$_PYEX" "$1" 2>/dev/null
      ;;
    *)
      printf '%s' "$payload" \
        | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" \
        | head -n 1
      ;;
  esac
}

# Normalize a Windows-or-POSIX path for comparison: backslashes to forward,
# collapse doubled slashes, strip a trailing slash, lowercase (Windows paths
# are case-insensitive and git and the tool layer disagree on drive-letter case).
norm() {
  local p="${1//\\//}"
  while [[ "$p" == *"//"* ]]; do p="${p//\/\//\/}"; done
  p="${p%/}"
  printf '%s' "$p" | tr '[:upper:]' '[:lower:]'
}

# Resolve a possibly-relative path against $cwd and flatten any ".." segments.
resolve() {
  local p="${1//\\//}"
  case "$p" in
    /*|?:/*) ;;                 # already absolute (POSIX or C:/...)
    *) p="$cwd/$p" ;;
  esac
  local out=() seg
  local IFS=/
  for seg in $p; do
    case "$seg" in
      ''|.) ;;
      ..) [[ ${#out[@]} -gt 0 ]] && unset 'out[${#out[@]}-1]' ;;
      *) out+=("$seg") ;;
    esac
  done
  local joined="${out[*]}"
  case "$p" in /*) printf '/%s' "$joined" ;; *) printf '%s' "$joined" ;; esac
}

deny() {
  # permissionDecisionReason is shown to the user and fed back to the agent, so
  # it says what to do instead rather than only that this was refused.
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

tool="$(field tool_name)"
cwd="$(field cwd)"
[[ -n "$cwd" ]] || exit 0            # nothing to anchor against; stay out of the way

# Boundary. If this is not a git repository, this hook has no opinion.
root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" || exit 0
[[ -n "$root" ]] || exit 0
gitdir="$(git -C "$cwd" rev-parse --git-common-dir 2>/dev/null || true)"
case "$gitdir" in
  '') gitdir="$root/.git" ;;
  /*|?:/*) ;;
  *) gitdir="$cwd/$gitdir" ;;
esac

n_root="$(norm "$root")"
n_gitdir="$(norm "$gitdir")"
n_scratch="$(norm "$(field scratchpad_dir)")"

inside() {
  local p; p="$(norm "$1")"
  [[ "$p" == "$n_root" || "$p" == "$n_root"/* ]] && return 0
  [[ -n "$n_gitdir" && ( "$p" == "$n_gitdir" || "$p" == "$n_gitdir"/* ) ]] && return 0
  [[ -n "$n_scratch" && ( "$p" == "$n_scratch" || "$p" == "$n_scratch"/* ) ]] && return 0
  return 1
}

case "$tool" in
  Write|Edit|MultiEdit|NotebookEdit)
    target="$(field file_path)"
    [[ -n "$target" ]] || target="$(field notebook_path)"
    [[ -n "$target" ]] || exit 0
    abs="$(resolve "$target")"
    if ! inside "$abs"; then
      deny "Blocked: $target is outside this checkout ($root). You are confined to this worktree; the main checkout and sibling worktrees belong to other tracks and are being changed concurrently. If you need something from the base branch, read it with 'git show <base>:<path>' instead of reaching across the filesystem."
    fi
    ;;

  Bash)
    # Narrow and deliberately incomplete: an unambiguous redirect to an absolute
    # path outside the boundary. Shell cannot be parsed reliably, so anything
    # cleverer here produces false positives that break legitimate git work —
    # and a false block is worse than a missed catch, because it stops a run
    # that was doing the right thing.
    cmd="$(field command)"
    [[ -n "$cmd" ]] || exit 0

    # Quoted targets first (these are exact), then bare ones.
    targets="$(printf '%s' "$cmd" | grep -oE '>>?[[:space:]]*"[^"]+"' | sed -E 's/^>>?[[:space:]]*"//; s/"$//')
$(printf '%s' "$cmd" | grep -oE ">>?[[:space:]]*'[^']+'" | sed -E "s/^>>?[[:space:]]*'//; s/'\$//")
$(printf '%s' "$cmd" | grep -oE '>>?[[:space:]]*(/|[A-Za-z]:/)[^[:space:];|&)]*' | sed -E 's/^>>?[[:space:]]*//')"

    while read -r hit; do
      [[ -n "$hit" ]] || continue
      abs="$(resolve "$hit")"
      inside "$abs" && continue
      # A bare path is cut at the first space, so a repo under e.g.
      # "C:/Users/me/Visual Studio Code/proj" yields the fragment
      # "C:/Users/me/Visual". Treat a fragment that the boundary starts with as
      # a truncated path into it, not an escape. Paths with spaces are normal on
      # Windows and blocking them would break far more than it caught.
      n_hit="$(norm "$abs")"
      [[ -n "$n_hit" && "$n_root" == "$n_hit"* ]] && continue
      deny "Blocked: this command redirects into $hit, outside this checkout ($root). Write inside the worktree instead."
    done <<< "$targets"
    ;;
esac

exit 0
