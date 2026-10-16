#!/usr/bin/env bash
# Real source wrapper decisions/status; isolated disposable repository only.
set -eu
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
. "$script_dir/lib/json-field.sh"
[[ -n "$_HOOK_PY" ]] || { printf 'Python unavailable\n' >&2; exit 1; }
hook="$script_dir/source-prewrite.sh"
temp_root="$(cd -- "${TMPDIR:-/tmp}" && pwd -P)"
workspace="$(mktemp -d "$temp_root/prewrite-shell.XXXXXX")"
workspace="$(cd -- "$workspace" && pwd -P)"
[[ "$workspace" == "$temp_root"/* ]] || exit 1
trap '[[ "$workspace" == "$temp_root"/* ]] && rm -rf -- "$workspace"' EXIT
mkdir -p "$workspace/repo/.planning"
cd -- "$workspace/repo"
git init --quiet
git config user.name Fixture
git config user.email fixture@example.invalid
printf 'worktree:\n  root: .worktrees\n' > .planning/config.yaml
printf '.worktrees/\n' > .gitignore
printf 'source\n' > source.txt
git add .
git commit --quiet -m fixture
passed=0
check() {
  if [[ "$2" != "$3" ]]; then
    printf 'FAIL %s: got %q expected %q\n' "$1" "$2" "$3" >&2
    exit 1
  fi
  passed=$((passed + 1))
}
payload() {
  "$_HOOK_PY" -c 'import json,os,sys; print(json.dumps({"hook_event_name":"PreToolUse","cwd":os.getcwd(),"session_id":"shell-session","agent_id":"shell-actor","tool_use_id":"shell-call","tool_name":sys.argv[1],"tool_input":{"file_path":sys.argv[2],"content":"pending"}}))' "$1" "$2"
}
run() {
  set +e
  printf '%s' "$1" | bash "$hook" > "$workspace/out" 2> "$workspace/err"
  observed=$?
  set -e
}
run "$(payload Write source.txt)"
check 'source native decision succeeds' "$observed" 0
"$_HOOK_PY" -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); assert set(d)=={"hookSpecificOutput"}; h=d["hookSpecificOutput"]; assert h["hookEventName"]=="PreToolUse" and h["permissionDecision"]=="deny" and h["permissionDecisionReason"]' "$workspace/out"
check 'source bytes unchanged' "$(cat source.txt)" source
check 'denial does not precreate a checkout' "$(git worktree list --porcelain | sed -n '/^worktree /p' | wc -l | tr -d ' ')" 1
run "$(payload Write .planning/scratchpads/note.md)"
check 'note permits' "$observed" 0
check 'note has no denial JSON' "$(cat "$workspace/out")" ''
run "$(payload Read source.txt)"
check 'read permits' "$observed" 0
check 'read has no denial JSON' "$(cat "$workspace/out")" ''
run '{'
check 'malformed JSON blocks synchronously' "$observed" 2
check 'malformed JSON never emits generic runtime stdout' "$(cat "$workspace/out")" ''
check 'malformed JSON has a diagnostic' "$([[ -s "$workspace/err" ]] && echo yes || echo no)" yes
printf '#!/usr/bin/env bash\nexit 7\n' > "$workspace/failing-python"
chmod +x "$workspace/failing-python"
set +e
payload Write source.txt | _HOOK_PY="$workspace/failing-python" bash "$hook" > "$workspace/out" 2> "$workspace/err"
observed=$?
set -e
check 'adapter crash status is converted to blocking exit 2' "$observed" 2
check 'adapter crash has no misleading success JSON' "$(cat "$workspace/out")" ''
printf '%s passed, 0 failed\n' "$passed"
