#!/usr/bin/env bash
# PreToolUse advisory hook. Workflows start source work in isolated worktrees.
#
# Two jobs, dispatched on tool_name:
#   1. Agent/Task dispatch of a write-capable subagent without
#      isolation="worktree" -> warn on stderr, continue and record its handoff.
#   2. Write/Edit/MultiEdit/NotebookEdit/apply_patch from the primary checkout
#      (including planning records and scratchpads), or targeting another
#      checkout -> warn on stderr and continue.
#
# Fails OPEN on anything it cannot determine -- no git, no JSON parser, an
# unparseable payload. Warnings require a recognized write-capable dispatch
# or a path git places outside the active linked worktree. Exit is always 0.

set -u

payload="$(cat 2>/dev/null || true)"

# Which roles write files comes from lib/agent-roles.sh, because
# context-handoff.sh needs the same answer at SubagentStop and a list kept in
# two places is a hole in whichever copy was missed. Sourced defensively: this
# hook fails open, so an unreadable lib must not abort the dispatch check.
_guard_lib="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/agent-roles.sh"
if [[ -f "$_guard_lib" ]]; then
  # shellcheck source=lib/agent-roles.sh
  . "$_guard_lib"
else
  WRITE_CAPABLE_AGENTS="coder doc-writer debugger targeted-fixer"
fi

# --- extract a top-level or tool_input string field ---------------------------
# Same tiering as ai-tier-notice.sh: jq, then Python, then a limited sed
# fallback that stops at the first quote. Paths and short identifiers survive
# the fallback; a Bash command line generally does not, which fails open.
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
    d = json.loads(sys.stdin.buffer.read().decode("utf-8"))
except Exception:
    sys.exit(0)
k = sys.argv[1]
v = d.get(k)
if not isinstance(v, str):
    v = (d.get("tool_input") or {}).get(k)
sys.stdout.buffer.write((v if isinstance(v, str) else "").encode("utf-8"))
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

# Append one allowed write-capable dispatch to the session's active-agent
# stack, which context-handoff.sh reads at SubagentStop. The plan path is the
# only field that matters downstream, and it is pulled out of the dispatch
# prompt by shape -- the orchestrator always names the plan it is assigning.
# When the prompt is unreadable (the sed tier of field() truncates prose), the
# entry is still recorded with an empty plan: an unattributed handoff the
# orchestrator must inspect beats no handoff at all.
record_dispatch() {
  local guard_dir slug dir prompt plan summary
  guard_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  [[ -f "$guard_dir/lib/handoff-io.sh" ]] || return 0
  # shellcheck source=lib/handoff-io.sh
  . "$guard_dir/lib/handoff-io.sh" || return 0
  slug="$(handoff_slug "$(field session_id)")" || return 0
  dir="$(handoff_dir)"
  prompt="$(field prompt)"
  [[ -n "$prompt" ]] || prompt="$(field description)"
  plan="$(printf '%s' "$prompt" \
    | grep -oE '[A-Za-z0-9_./-]*[0-9]{2}(\.[0-9]+)?-[0-9]{2}-PLAN\.md' \
    | head -n 1)"
  summary="$(printf '%s\n' "$prompt" \
    | sed -nE 's/^[[:space:]]*summary_path:[[:space:]]*(.*)$/\1/p' \
    | head -n 1)"
  plan="$(handoff_safe_repo_path "$plan" "$(handoff_root)")"
  summary="$(handoff_safe_repo_path "$summary" "$(handoff_root)")"
  handoff_append_active "$dir/.active-$slug.jsonl" "$1" "$plan" "$summary"
  return 0
}

tool="$(field tool_name)"

# --- job 1: warn about an unisolated executor dispatch -----------------------

if [[ "$tool" == "Agent" || "$tool" == "Task" ]]; then
  subagent="$(field subagent_type)"
  role="${subagent##*:}"
  isolation="$(field isolation)"
  # Built before the heredoc on purpose: ${var:+word} applies quote removal to
  # `word`, so an inline ${isolation:+isolation="$isolation"} would print
  # isolation=remote and hide the quoting the reader needs to see.
  if [[ -n "$isolation" ]]; then
    carried="isolation=\"$isolation\""
  else
    carried="no isolation argument"
  fi
  for candidate in $WRITE_CAPABLE_AGENTS; do
    [[ "$role" == "$candidate" ]] || continue
    if [[ "$isolation" != "worktree" ]]; then
      cat >&2 <<REASON
WARNING  dispatch without worktree isolation: subagent_type="$subagent".

This dispatch carries $carried, so the agent would
edit and commit in the primary checkout alongside every other agent in its
wave. Concurrent agents in one tree interleave their commits into one history,
which makes a plan impossible to attribute or revert.

Add isolation="worktree" to the Agent(...) or Task(...) call.

The workflow uses isolated worktrees -- see
.ai/RULES.md#worktrees-integration-and-cleanup. This advisory hook allows the
dispatch to continue.
REASON
    fi
    # Every allowed write-capable dispatch, including one just warned about,
    # is recorded once for SubagentStop. Use the same normalized role as the
    # warning check so qualified agent names retain handoff tracking.
    record_dispatch "$role"
    break
  done
  exit 0
fi

# --- job 2: warn about an edit outside a worktree -----------------------------

case "$tool" in
  Write|Edit|MultiEdit|NotebookEdit|apply_patch) ;;
  *) exit 0 ;;
esac

command -v git >/dev/null 2>&1 || exit 0

toplevel="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$toplevel" ]] || exit 0         # not a git repository -- nothing to say
# Query both from the root: in a nested primary directory git can return an
# absolute git-dir but a relative common-dir for the same directory.
git_dir="$(git -C "$toplevel" rev-parse --git-dir 2>/dev/null || true)"
common_dir="$(git -C "$toplevel" rev-parse --git-common-dir 2>/dev/null || true)"
[[ -n "$git_dir" ]] || exit 0

# A linked worktree is the one case where these two differ: its own git dir sits
# under <common>/worktrees/<name>. Comparing git's answers from the same root
# avoids path-separator and short-name pitfalls of matching the string ourselves.
in_worktree=0
[[ -n "$common_dir" && "$git_dir" != "$common_dir" ]] && in_worktree=1

if [[ "$tool" == apply_patch ]]; then
  paths="$(field command | sed -nE 's/^\*\*\* (Add File|Update File|Delete File|Move to): (.*)\r?$/\2/p' | tr -d '\r')"
else
  paths="$(field file_path)"
  [[ -n "$paths" ]] || paths="$(field notebook_path)"
fi
[[ -n "$paths" ]] || exit 0

# Walk up to the nearest directory that exists: a Write creates a new file, so
# the target itself frequently does not exist yet, but an ancestor must.
nearest_existing_dir() {
  local candidate previous
  candidate="$(dirname -- "$1")"
  previous=""
  while [[ "$candidate" != "$previous" ]]; do
    if [[ -d "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
    previous="$candidate"
    candidate="$(dirname -- "$candidate")"
  done
  return 0
}

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  # Unescape the backslashes Windows paths arrive with, and normalize.
  path="${path//\\\\//}"
  path="${path//\\//}"

  if [[ "$in_worktree" -eq 0 ]]; then
    cat >&2 <<NOTICE
WARNING  editing outside a worktree: $path

This checkout is not a linked worktree, so this write would land in the primary
checkout, on a branch with no pull request behind it. Nothing in this project
reaches the base branch that way -- planning records included.

Open the session this work belongs to and write there instead:

  phase_run query session.open <phase|quick|milestone|onboard> <label>

It returns the worktree path; run the rest of the command from it. An existing
session for the same unit is reused, so a phase accumulates onto one branch and
into one pull request.

If you are an executor running a plan, you were meant to be dispatched with
isolation="worktree". Prefer the assigned worktree for plan writes
(.ai/RULES.md#worktrees-integration-and-cleanup).

This advisory hook allows the write to continue.
NOTICE
    continue
  fi

  # Inside a worktree, an absolute path built from the orchestrator's directory
  # resolves to the primary checkout: the write lands there, and the commit made
  # here then sees a clean tree, so the work is silently lost.
  #
  # The comparison is git-vs-git. A shell prefix test against --show-toplevel is
  # not portable: MSYS spells a temp directory /tmp/x while git spells the same
  # place C:/Users/.../Temp/x, and the two compare unequal. Asking git for the
  # target's own toplevel makes both sides its own emission, which settles
  # separators, drive letters and short names by construction.
  case "$path" in
    /*|[A-Za-z]:/*)
      target_dir="$(nearest_existing_dir "$path")"
      [[ -n "$target_dir" ]] || continue
      target_top="$(git -C "$target_dir" rev-parse --show-toplevel 2>/dev/null || true)"
      # Outside every repository (a scratch directory, a home-relative cache) is
      # not the primary-checkout vector this warns about.
      [[ -n "$target_top" ]] || continue
      if [[ -n "$toplevel" && "$target_top" != "$toplevel" ]]; then
        cat >&2 <<NOTICE
WARNING  absolute path outside the active worktree: $path

The active worktree is $toplevel. A path built from the orchestrator's directory
resolves to a different checkout, where the write would be invisible to this
worktree's commit -- the work would appear to succeed and then be lost.

Use a relative path, or rebuild the absolute path from
\`git rev-parse --show-toplevel\` run inside this worktree
(.ai/references/worktree-path-safety.md).

This advisory hook allows the write to continue.
NOTICE
      fi
      ;;
  esac
done <<< "$paths"

exit 0
