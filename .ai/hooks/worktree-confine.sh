#!/usr/bin/env bash
# PreToolUse hook. WARNS about file writes that land outside the checkout this
# session is working in. Advisory only -- it blocks nothing.
#
# Advisory behavior follows enforcement: advisory in .ai/config.yaml.
#
# Why this exists: /orchestrate runs each track in its own git worktree, and a
# track writing into the main checkout or a sibling worktree corrupts work
# nobody is reviewing. This hook surfaces that mistake early.
#
# Host permissions and assigned-worktree instructions remain in effect.
# This hook is not a sandbox.
#
# The boundary is derived from git, NOT from $CLAUDE_PROJECT_DIR — the hooks
# documentation is explicit that in a worktree that variable stays at the
# project root, which is exactly the case this hook exists for.
#
# What is allowed depends on the tool, and the split is load-bearing — see
# `inside` and `inside_bash` below:
#
#   file tools   this checkout's toplevel, and the OS temp roots
#   Bash         the above, plus the shared git directory
#
# Enforcement is honest about its limits:
#   Write / Edit / NotebookEdit  warned, from a real file_path field
#   Bash                         narrow best-effort — an unambiguous redirect
#                                to somewhere outside. Shell cannot be parsed
#                                reliably, so this catches accidents, not a
#                                determined escape.
#
# Register explicitly with your host; no settings template is supplied.

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

# Escape caller-provided paths before inserting them into the JSON warning.
json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\t'/ }"
  s="${s//$'\r'/ }"
  s="${s//$'\n'/ }"
  printf '%s' "$s"
}

# A warning adds transcript context without overriding host permissions.
warn() {
  printf '{"systemMessage":"%s"}\n' "$(json_escape "$1")"
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
n_dotgit="$(norm "$root/.git")"   # the main checkout's, which lives inside root

# The session scratchpad is not in the payload. `scratchpad_dir` is not a field
# PreToolUse carries, so reading it always yielded the empty string and every
# write to the scratchpad the harness tells agents to use was denied. The temp
# roots come from the environment instead. They are allowed because none of them
# is another checkout of this repository, which is the only thing this hook
# exists to protect.
n_tmpdirs=()
for _t in "${CLAUDE_SCRATCHPAD_DIR:-}" "${TMPDIR:-}" "${TEMP:-}" "${TMP:-}" /tmp; do
  [[ -n "$_t" ]] || continue
  _n="$(norm "$_t")"
  [[ -n "$_n" ]] && n_tmpdirs+=("$_n")
done

# Two boundaries, not one, and the difference is the point.
#
# Git genuinely needs write access under --git-common-dir: a worktree's .git is
# a *file* pointing into the main repository's .git/worktrees/<name>, so deny it
# and git stops working. But git needs it through `git`, which is a Bash call.
# No Write or Edit ever legitimately targets that directory, and allowing them
# there hands over .git/hooks/pre-commit and .git/config — either one is
# arbitrary code execution in the main checkout and in every sibling worktree at
# the next git operation. That is a complete bypass of the confinement, through
# the very allowance meant to support it.
# The git-directory exclusion has to come FIRST, before the toplevel check.
# In a worktree the shared git dir is outside the checkout, so ordering did not
# matter; in the main checkout `.git` sits *inside* the toplevel, so a root-first
# test allows .git/hooks/pre-commit and the exclusion below never runs. That is
# the same code-execution path in the place it does the most damage.
in_gitdir() {
  local p; p="$(norm "$1")"
  [[ -n "$n_gitdir" && ( "$p" == "$n_gitdir" || "$p" == "$n_gitdir"/* ) ]] && return 0
  [[ -n "$n_dotgit" && ( "$p" == "$n_dotgit" || "$p" == "$n_dotgit"/* ) ]] && return 0
  return 1
}

inside() {
  in_gitdir "$1" && return 1
  local p; p="$(norm "$1")"
  [[ "$p" == "$n_root" || "$p" == "$n_root"/* ]] && return 0
  local d
  for d in ${n_tmpdirs[@]+"${n_tmpdirs[@]}"}; do
    [[ "$p" == "$d" || "$p" == "$d"/* ]] && return 0
  done
  return 1
}

inside_bash() {
  in_gitdir "$1" && return 0
  inside "$1"
}

case "$tool" in
  Write|Edit|MultiEdit|NotebookEdit)
    target="$(field file_path)"
    [[ -n "$target" ]] || target="$(field notebook_path)"
    [[ -n "$target" ]] || exit 0
    abs="$(resolve "$target")"
    if ! inside "$abs"; then
      warn "Heads up: $target is outside this checkout ($root). If this session is an /orchestrate track, the main checkout and sibling worktrees belong to other tracks and are being changed concurrently -- prefer 'git show <base>:<path>' over reaching across the filesystem. Writing outside is legitimate for things that belong to no track, such as the agent memory directory. Not blocked."
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

    # The bare-path scan runs over a copy with every quoted span blanked out.
    # Without that, an absolute path sitting inside a string literal reads as a
    # redirect target: `echo "see > /usr/local/bin" >> notes.md` was denied, and
    # that command writes nowhere near it. Quoted redirects are matched exactly
    # by the two scans below, so blanking them here loses nothing.
    cmd_bare="$(printf '%s' "$cmd" | sed -E 's/"[^"]*"/ /g' | sed -E "s/'[^']*'/ /g")"

    # Quoted targets first (these are exact), then bare ones.
    targets="$(printf '%s' "$cmd" | grep -oE '>>?[[:space:]]*"[^"]+"' | sed -E 's/^>>?[[:space:]]*"//; s/"$//')
$(printf '%s' "$cmd" | grep -oE ">>?[[:space:]]*'[^']+'" | sed -E "s/^>>?[[:space:]]*'//; s/'\$//")
$(printf '%s' "$cmd_bare" | grep -oE '>>?[[:space:]]*(/|[A-Za-z]:/)[^[:space:];|&)]*' | sed -E 's/^>>?[[:space:]]*//')"

    while read -r hit; do
      [[ -n "$hit" ]] || continue
      # The device files are not filesystem locations. They match the bare-path
      # pattern, they are never inside the checkout, and `2>/dev/null` is an
      # everyday idiom — denying it costs an agent turn and teaches nothing.
      case "$(norm "$hit")" in
        /dev/null|/dev/zero|/dev/tty|/dev/stdin|/dev/stdout|/dev/stderr|/dev/fd/*)
          continue ;;
      esac
      abs="$(resolve "$hit")"
      inside_bash "$abs" && continue
      # A bare path is cut at the first space, so a repo under e.g.
      # "C:/Users/me/Visual Studio Code/proj" yields the fragment
      # "C:/Users/me/Visual". Treat a fragment that the boundary starts with as
      # a truncated path into it, not an escape. Paths with spaces are normal on
      # Windows and blocking them would break far more than it caught.
      n_hit="$(norm "$abs")"
      [[ -n "$n_hit" && "$n_root" == "$n_hit"* ]] && continue
      warn "Heads up: this command appears to redirect into $hit, outside this checkout ($root). If that was not intended, write inside the worktree. Note this scan reads the whole command string, so it can misfire on a heredoc whose body merely mentions an outside path. Not blocked."
    done <<< "$targets"
    ;;
esac

exit 0
