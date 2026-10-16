#!/usr/bin/env bash
# Behavioural suite for worktree-location.sh. Builds a real repository with a
# phase-session worktree and runs the hook the way Claude Code does: JSON on
# stdin, the worktree path read back from the last line of stdout.
set -eu

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hook="$script_dir/worktree-location.sh"
passed=0
failed=0

check() {
  if [[ "$2" == "$3" ]]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    printf 'FAIL  %s\n      got      %q\n      expected %q\n' "$1" "$2" "$3" >&2
  fi
}

workspace="$(mktemp -d)"
trap 'rm -rf "$workspace"' EXIT

repo="$workspace/repo"
mkdir -p "$repo/.planning"
git -C "$repo" init --quiet -b main
git -C "$repo" config user.email test@example.com
git -C "$repo" config user.name Test
printf 'worktree:\n  root: .worktrees\n' > "$repo/.planning/config.yaml"
printf '.worktrees/\n' > "$repo/.gitignore"
printf 'seed\n' > "$repo/seed.txt"
git -C "$repo" add -A
git -C "$repo" commit --quiet -m seed
primary="$(git -C "$repo" rev-parse --path-format=absolute --show-toplevel)"

# The phase session the orchestrator works in: a worktree under the root, on a
# branch that is ahead of main.
session="$repo/.worktrees/phase-01"
git -C "$repo" worktree add --quiet -b phase-01 "$session"
printf 'wave one\n' > "$session/wave1.txt"
git -C "$session" add wave1.txt
git -C "$session" commit --quiet -m "wave one"
session_head="$(git -C "$session" rev-parse HEAD)"

run_hook() { # <event> <cwd> <field> <value>
  (cd -- "$2" &&
    printf '{"hook_event_name":"%s","session_id":"s1","cwd":"%s","%s":"%s"}' "$1" "$2" "$3" "$4" \
      | bash "$hook" 2>/dev/null)
}

# --- creation ------------------------------------------------------------------

out="$(run_hook WorktreeCreate "$session" name agent-a1)"
status=$?
check "create: succeeds" "$status" "0"
check "create: prints exactly one line, the path" "$(printf '%s\n' "$out" | wc -l | tr -d ' ')" "1"
check "create: the worktree is under the project's .worktrees/" "$out" "$primary/.worktrees/agent-a1"
check "create: the directory exists" "$([[ -d "$out" ]] && echo yes || echo no)" "yes"
check "create: nothing is created under .claude/" \
  "$([[ -e "$repo/.claude" || -e "$session/.claude" ]] && echo present || echo absent)" "absent"
check "create: never nested inside the dispatching session worktree" \
  "$([[ -e "$session/.worktrees" ]] && echo nested || echo flat)" "flat"
check "create: on Claude's own branch name" \
  "$(git -C "$out" branch --show-current)" "worktree-agent-a1"
check "create: starts from the dispatching session's HEAD, not main" \
  "$(git -C "$out" rev-parse HEAD)" "$session_head"
check "create: carries the earlier wave's work" \
  "$([[ -f "$out/wave1.txt" ]] && echo yes || echo no)" "yes"

again="$(run_hook WorktreeCreate "$session" name agent-a1)"
check "create: a reopened name gets its existing checkout back" "$again" "$out"

set +e
bad="$(run_hook WorktreeCreate "$session" name ../escape)"
bad_status=$?
set -e
check "create: a traversing name is refused" "$([[ $bad_status -ne 0 ]] && echo refused || echo accepted)" "refused"
check "create: a refused name prints no path" "$bad" ""
check "create: a refused name creates nothing" \
  "$([[ -e "$repo/escape" || -e "$repo/.worktrees/../escape" ]] && echo created || echo none)" "none"

# A custom root in config is honoured, as the runtime honours it.
printf 'worktree:\n  root: trees\n' > "$repo/.planning/config.yaml"
custom="$(run_hook WorktreeCreate "$session" name agent-c1)"
check "create: worktree.root from config is honoured" "$custom" "$primary/trees/agent-c1"
printf 'worktree:\n  root: .worktrees\n' > "$repo/.planning/config.yaml"

# --- removal -------------------------------------------------------------------

clean="$(run_hook WorktreeCreate "$session" name agent-r1)"
printf 'done\n' > "$clean/done.txt"
git -C "$clean" add done.txt
git -C "$clean" commit --quiet -m "coder work"
run_hook WorktreeRemove "$session" worktree_path "$clean" >/dev/null
check "remove: a clean finished checkout is removed" \
  "$([[ -e "$clean" ]] && echo present || echo gone)" "gone"
check "remove: its branch stays, for the wave to merge" \
  "$(git -C "$repo" show-ref --verify --quiet refs/heads/worktree-agent-r1 && echo kept || echo deleted)" "kept"

dirty="$(run_hook WorktreeCreate "$session" name agent-r2)"
printf 'unfinished\n' > "$dirty/wip.txt"
set +e
run_hook WorktreeRemove "$session" worktree_path "$dirty" >/dev/null
remove_status=$?
set -e
check "remove: never fails the host" "$remove_status" "0"
check "remove: a dirty checkout is kept for inspection" \
  "$([[ -f "$dirty/wip.txt" ]] && echo kept || echo lost)" "kept"

outside="$workspace/elsewhere"
mkdir -p "$outside"
run_hook WorktreeRemove "$session" worktree_path "$outside" >/dev/null
check "remove: a path outside the root is never touched" \
  "$([[ -d "$outside" ]] && echo kept || echo removed)" "kept"

# Reserved native identities never use ordinary dispatch's name-reuse branch.
native_name=wf-entry-0123456789abcdef0123456789abcdef
set +e
unknown="$(run_hook WorktreeCreate "$session" name "$native_name")"
unknown_status=$?
set -e
check "native: missing ticket is refused" "$([[ $unknown_status -ne 0 ]] && echo yes || echo no)" yes
check "native: missing ticket returns no successful path" "$unknown" ""
native="$repo/.worktrees/$native_name"
git -C "$repo" worktree add --quiet -b worktree-wf_0123456789abcdef0123456789abcdef "$native"
printf 'native-private.bin\n' >> "$repo/.git/info/exclude"
printf 'ignored native data\n' > "$native/native-private.bin"
set +e
reused="$(run_hook WorktreeCreate "$session" name "$native_name")"
reused_status=$?
set -e
check "native: registered name cannot bypass real path approval" "$([[ $reused_status -ne 0 ]] && echo yes || echo no)" yes
check "native: rejected reuse returns no path" "$reused" ""
run_hook WorktreeRemove "$session" worktree_path "$native" >/dev/null
check "native: uncertain ignored-only checkout is preserved" "$(cat "$native/native-private.bin")" "ignored native data"
check "native: preserved checkout stays registered" \
  "$(git -C "$native" rev-parse --is-inside-work-tree)" true

printf '%s passed, %s failed\n' "$passed" "$failed"
[[ "$failed" -eq 0 ]]
