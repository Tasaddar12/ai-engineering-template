#!/usr/bin/env bash
# Where Claude Code puts the worktrees it creates. Registered for Claude only.
#
# Two jobs, dispatched on hook_event_name:
#
#   1. WorktreeCreate -- a subagent dispatched with isolation="worktree" (or a
#      --worktree / background session) needs a checkout. Claude Code's default
#      puts it under .claude/worktrees/ and branches it from the repository's
#      default branch. Both are wrong here: every worktree lives under the
#      project's worktree root (`worktree.root`, default .worktrees -- the same
#      root the runtime uses), and a coder must start from the phase it is
#      building, not from main. Without that, a wave-2 coder started without
#      wave 1's work and halted at its branch check.
#
#      So this creates the worktree itself, under <primary>/<root>/<name>, on
#      branch worktree-<name> (Claude's own naming, which the integration step
#      already merges by), from the HEAD of the checkout that dispatched it.
#      Claude Code reads the last line of stdout as the worktree path, so every
#      other line goes to stderr. Any failure exits non-zero, which makes Claude
#      refuse the dispatch rather than fall back to .claude/worktrees/.
#
#   2. WorktreeRemove -- the subagent finished. Remove its checkout only when
#      git agrees it is clean (no --force), and never its branch: the branch is
#      what the wave merges, and a dirty checkout is unfinished work to inspect.
#      Always exits 0; a checkout that could not be removed simply stays.

set -u

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/json-field.sh
. "$script_dir/lib/json-field.sh"

payload="$(cat 2>/dev/null || true)"
{
  read -r event
  read -r name
  read -r cwd
  read -r removing
} < <(many_fields hook_event_name name cwd worktree_path)
[[ -n "${cwd:-}" ]] || cwd="$PWD"

fail() {
  printf 'worktree-location: %s\n' "$1" >&2
  exit 1
}

# The primary checkout owns the worktree root, whichever worktree dispatched
# the agent: a coder dispatched from a phase-session worktree still belongs
# beside that session under the one root, never nested inside it.
common="$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
[[ -n "$common" && "${common##*/}" == .git ]] || {
  [[ "$event" == WorktreeRemove ]] && exit 0
  fail "not inside a git repository with a .git directory: $cwd"
}
primary="${common%/.git}"

# `worktree.root` from the project config, as the runtime reads it. Only a plain
# relative path is accepted; anything else falls back to .worktrees.
root="$(sed -n '/^worktree:[[:space:]]*$/,/^[^[:space:]#]/ s/^[[:space:]][[:space:]]*root:[[:space:]]*\([^[:space:]#]*\).*/\1/p' \
  "$primary/.planning/config.yaml" 2>/dev/null | head -n 1)"
root="${root%\"}"
root="${root#\"}"
root="${root%/}"
case "$root" in
  ""|/*|*..*|*\\*|[A-Za-z]:*) root=".worktrees" ;;
esac
base="$primary/$root"

# One spelling for a path, so a comparison is not defeated by how a host wrote
# it: forward slashes, and on Windows a lower-case drive letter. Git prints
# C:/..., while Claude Code can hand back c:\... for the same directory.
normal() { # <path>
  local path="${1//\\//}"
  if [[ "$path" =~ ^([A-Za-z]):(.*)$ ]]; then
    path="$(printf '%s' "${BASH_REMATCH[1]}" | tr 'A-Z' 'a-z'):${BASH_REMATCH[2]}"
  fi
  printf '%s' "${path%/}"
}

registered() { # <path>
  local want line
  want="$(normal "$1")"
  while IFS= read -r line; do
    line="${line%$'\r'}"
    [[ "$line" == "worktree "* ]] || continue
    [[ "$(normal "${line#worktree }")" == "$want" ]] && return 0
  done < <(git -C "$primary" worktree list --porcelain 2>/dev/null)
  return 1
}

case "$event" in
  WorktreeCreate)
    case "${name:-}" in
      ""|*[!A-Za-z0-9._-]*|.*|*..*) fail "unusable worktree name: ${name:-<empty>}" ;;
    esac
    destination="$base/$name"
    branch="worktree-$name"
    # A reopened name gets its existing checkout back rather than a failure.
    if registered "$destination"; then
      printf '%s\n' "$destination"
      exit 0
    fi
    [[ -e "$destination" ]] && fail "exists but is not a registered worktree: $destination"
    mkdir -p "$base" || fail "cannot create $base"
    if git -C "$primary" show-ref --verify --quiet "refs/heads/$branch"; then
      git -C "$cwd" worktree add "$destination" "$branch" >&2 \
        || fail "git worktree add failed for $destination"
    else
      git -C "$cwd" worktree add -b "$branch" "$destination" HEAD >&2 \
        || fail "git worktree add failed for $destination"
    fi
    printf '%s\n' "$destination"
    ;;

  WorktreeRemove)
    target="${removing:-}"
    # Only a checkout under the root, and only one git knows about.
    case "$(normal "$target")" in
      "$(normal "$base")"/*) ;;
      *) exit 0 ;;
    esac
    registered "$target" || exit 0
    git -C "$primary" worktree remove "$target" >&2 2>/dev/null || true
    exit 0
    ;;

  *) exit 0 ;;
esac
