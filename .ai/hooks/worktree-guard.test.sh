#!/usr/bin/env bash
# Behavioural suite for worktree-guard.sh. Builds a real repository with a real
# linked worktree, because what the hook decides is a git fact, not a string
# match.
set -eu
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hook="$script_dir/worktree-guard.sh"
passed=0
failed=0

check() { # check <description> <expected-exit> <expect-substring|-> <payload> [cwd]
  local description="$1" expect_exit="$2" expect_text="$3" payload="$4" cwd="${5:-$PWD}"
  local output status
  set +e
  output="$(cd "$cwd" && printf '%s' "$payload" | bash "$hook" 2>&1)"
  status=$?
  set -e
  if [[ "$status" != "$expect_exit" ]]; then
    printf 'FAIL  %s: exit %s, wanted %s\n' "$description" "$status" "$expect_exit" >&2
    failed=$((failed + 1)); return
  fi
  if [[ "$expect_text" == "-" ]]; then
    if [[ -n "$output" ]]; then
      printf 'FAIL  %s: wanted no output, got: %s\n' "$description" "$output" >&2
      failed=$((failed + 1)); return
    fi
  elif [[ "$output" != *"$expect_text"* ]]; then
    printf 'FAIL  %s: output lacked %s\n' "$description" "$expect_text" >&2
    failed=$((failed + 1)); return
  fi
  passed=$((passed + 1))
}

# --- dispatch enforcement (no repository needed) -----------------------------

for agent in coder doc-writer debugger; do
  check "unisolated $agent is blocked" 2 'BLOCKED' \
    "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$agent\"}}"
  check "isolated $agent is allowed" 0 '-' \
    "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$agent\",\"isolation\":\"worktree\"}}"
  check "$agent under the Task tool name is blocked too" 2 'BLOCKED' \
    "{\"tool_name\":\"Task\",\"tool_input\":{\"subagent_type\":\"$agent\"}}"
done

# A wrong isolation value is not a pass: only "worktree" isolates the checkout.
check 'isolation="remote" does not satisfy the requirement' 2 'BLOCKED' \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"coder","isolation":"remote"}}'
check 'the block names the value that was passed' 2 'isolation="remote"' \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"coder","isolation":"remote"}}'

for agent in researcher verifier code-reviewer doc-verifier codebase-mapper phase-checker; do
  check "read-only $agent needs no isolation" 0 '-' \
    "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$agent\"}}"
done

check 'an unrelated tool is ignored' 0 '-' '{"tool_name":"Read","tool_input":{"file_path":"x"}}'
check 'an empty payload is ignored' 0 '-' '{}'
check 'a malformed payload is ignored' 0 '-' 'not json at all'

# --- write warnings (real repository, real worktree) -------------------------

work="$(mktemp -d 2>/dev/null || mktemp -d -t wtguard)"
trap 'rm -rf "$work" 2>/dev/null || true' EXIT
cd "$work"
git init -q .
git config user.email guard@example.test
git config user.name 'Guard Test'
printf '.worktrees/\n' > .gitignore
mkdir src
printf 'hi\n' > src/a.txt
git add -A
git commit -qm baseline
git worktree add -q -b agent-probe .worktrees/probe HEAD

primary="$work"
worktree="$work/.worktrees/probe"

check 'a source edit in the primary checkout warns' 0 'editing outside a worktree' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$primary"
check 'an Edit in the primary checkout warns' 0 'editing outside a worktree' \
  '{"tool_name":"Edit","tool_input":{"file_path":"src/a.txt"}}' "$primary"
check 'the warning names the hard requirement' 0 'hard requirement' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$primary"

# Planning records belong to the orchestrator, which works in the primary
# checkout by design -- warning there would bury the signal.
check 'a planning record in the primary checkout is silent' 0 '-' \
  '{"tool_name":"Write","tool_input":{".planning/STATE.md":""},"tool_input":{"file_path":".planning/STATE.md"}}' "$primary"
check 'a nested planning record is silent' 0 '-' \
  '{"tool_name":"Write","tool_input":{"file_path":"repo/.planning/phases/01-x/01-CONTEXT.md"}}' "$primary"

check 'a relative edit inside the worktree is silent' 0 '-' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$worktree"
check 'an absolute path inside the worktree is silent' 0 '-' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$worktree/src/a.txt\"}}" "$worktree"
check 'an absolute path into the primary checkout warns' 0 'outside the active worktree' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$primary/src/a.txt\"}}" "$worktree"
check 'a Windows-escaped path into the primary checkout warns' 0 'outside the active worktree' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$(printf '%s' "$primary" | sed 's#/#\\\\#g')\\\\src\\\\a.txt\"}}" "$worktree"

check 'a notebook edit is covered' 0 'editing outside a worktree' \
  '{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"src/nb.ipynb"}}' "$primary"
check 'an apply_patch Add File is covered' 0 'editing outside a worktree' \
  '{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Add File: src/new.txt\n+x\n*** End Patch"}}' "$primary"

# A path with no file field has nothing to judge.
check 'a file tool with no path is ignored' 0 '-' \
  '{"tool_name":"Write","tool_input":{}}' "$primary"

cd "$script_dir"
printf '%s passed, %s failed\n' "$passed" "$failed"
[[ "$failed" -eq 0 ]]
