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
  local output status stdout stderr_file
  stderr_file="$(mktemp)"
  set +e
  stdout="$(cd "$cwd" && printf '%s' "$payload" | bash "$hook" 2>"$stderr_file")"
  status=$?
  set -e
  output="$(cat "$stderr_file")"
  rm -f "$stderr_file"
  if [[ -n "$stdout" ]]; then
    printf 'FAIL  %s: wanted no stdout, got: %s\n' "$description" "$stdout" >&2
    failed=$((failed + 1)); return
  fi
  if [[ "$expect_text" != "-" && "$output" != *WARNING* ]]; then
    printf 'FAIL  %s: stderr lacked WARNING\n' "$description" >&2
    failed=$((failed + 1)); return
  fi
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

# --- dispatch warnings (no repository needed) -----------------------------

for agent in coder doc-writer debugger targeted-fixer plugin:workflow:targeted-fixer; do
  check "unisolated $agent warns and continues" 0 'WARNING' \
    "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$agent\"}}"
  check "isolated $agent is allowed" 0 '-' \
    "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$agent\",\"isolation\":\"worktree\"}}"
  check "$agent under the Task tool name warns and continues too" 0 'WARNING' \
    "{\"tool_name\":\"Task\",\"tool_input\":{\"subagent_type\":\"$agent\"}}"
done

# A wrong isolation value is not a pass: only "worktree" isolates the checkout.
check 'isolation="remote" warns and continues' 0 'WARNING' \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"coder","isolation":"remote"}}'
check 'the warning names the value that was passed' 0 'isolation="remote"' \
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

# A relocated hook without its library retains fixed-role guidance.
cp "$hook" "$work/fallback.sh"
saved_hook="$hook"
hook="$work/fallback.sh"
for tool in Agent Task; do
  for agent in targeted-fixer plugin:workflow:targeted-fixer; do
    check "fallback warns for $tool $agent" 0 'WARNING' \
      "{\"tool_name\":\"$tool\",\"tool_input\":{\"subagent_type\":\"$agent\"}}"
    check "fallback permits isolated $tool $agent" 0 '-' \
      "{\"tool_name\":\"$tool\",\"tool_input\":{\"subagent_type\":\"$agent\",\"isolation\":\"worktree\"}}"
  done
done
hook="$saved_hook"
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

check 'a source edit in the primary checkout warns and continues' 0 'editing outside a worktree' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$primary"
check 'an Edit in the primary checkout warns and continues' 0 'editing outside a worktree' \
  '{"tool_name":"Edit","tool_input":{"file_path":"src/a.txt"}}' "$primary"
check 'the warning recommends worktrees' 0 'worktree' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$primary"
check 'the warning names the session verb' 0 'session.open' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$primary"

# Planning records are no longer exempt. The orchestrator opens a session
# worktree before it writes, so a planning write landing in the primary
# checkout means that never happened.
check 'a planning record in the primary checkout warns and continues' 0 'editing outside a worktree' \
  '{"tool_name":"Write","tool_input":{"file_path":".planning/STATE.md"}}' "$primary"
check 'a nested planning record warns and continues' 0 'editing outside a worktree' \
  '{"tool_name":"Write","tool_input":{"file_path":"repo/.planning/phases/01-x/01-CONTEXT.md"}}' "$primary"

check 'a scratchpad in the primary checkout warns and continues' 0 'session.open' \
  '{"tool_name":"Write","tool_input":{"file_path":".planning/scratchpads/notes.md"}}' "$primary"
check 'a MultiEdit in the primary checkout warns and continues' 0 'editing outside a worktree' \
  '{"tool_name":"MultiEdit","tool_input":{"file_path":"src/a.txt","edits":[]}}' "$primary"
check 'dispatch guidance names isolation' 0 'isolation="worktree"' \
  '{"tool_name":"Task","tool_input":{"subagent_type":"plugin:workflow:coder"}}'

check 'a relative edit inside the worktree is silent' 0 '-' \
  '{"tool_name":"Write","tool_input":{"file_path":"src/a.txt"}}' "$worktree"
check 'a planning record inside the worktree is silent' 0 '-' \
  '{"tool_name":"Write","tool_input":{"file_path":".planning/STATE.md"}}' "$worktree"
check 'an absolute path inside the worktree is silent' 0 '-' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$worktree/src/a.txt\"}}" "$worktree"
check 'an absolute path into the primary checkout warns and continues' 0 'outside the active worktree' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$primary/src/a.txt\"}}" "$worktree"
check 'a Windows-escaped path into the primary checkout warns and continues' 0 'outside the active worktree' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$(printf '%s' "$primary" | sed 's#/#\\\\#g')\\\\src\\\\a.txt\"}}" "$worktree"

check 'a notebook edit is covered' 0 'editing outside a worktree' \
  '{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"src/nb.ipynb"}}' "$primary"
check 'an apply_patch Add File is covered' 0 'editing outside a worktree' \
  '{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Add File: src/new.txt\n+x\n*** End Patch"}}' "$primary"

check 'a MultiEdit inside the worktree is silent' 0 '-' \
  '{"tool_name":"MultiEdit","tool_input":{"file_path":"src/a.txt","edits":[]}}' "$worktree"
check 'a scratchpad absolute path warns with rebuilding guidance' 0 'Use a relative path' \
  "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$primary/.planning/scratchpads/notes.md\"}}" "$worktree"
check 'apply_patch scans a scratchpad after a safe worktree target' 0 "$primary/.planning/scratchpads/notes.md" \
  "{\"tool_name\":\"apply_patch\",\"tool_input\":{\"command\":\"*** Begin Patch\n*** Update File: src/a.txt\n@@\n-hi\n+hello\n*** Add File: $primary/.planning/scratchpads/notes.md\n+x\n*** End Patch\"}}" "$worktree"
for header in 'Update File' 'Delete File' 'Move to'; do
  check "apply_patch $header outside the worktree warns" 0 'outside the active worktree' \
    "{\"tool_name\":\"apply_patch\",\"tool_input\":{\"command\":\"*** Begin Patch\n*** $header: $primary/src/a.txt\n*** End Patch\"}}" "$worktree"
done
scratch="$(mktemp -d)"
check 'a scratch path outside repositories stays silent' 0 '-' \
  "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$scratch/notes.md\"}}" "$worktree"
rmdir "$scratch"

# A path with no file field has nothing to judge.
check 'a file tool with no path is ignored' 0 '-' \
  '{"tool_name":"Write","tool_input":{}}' "$primary"

cd "$script_dir"
printf '%s passed, %s failed\n' "$passed" "$failed"
[[ "$failed" -eq 0 ]]
