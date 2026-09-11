#!/usr/bin/env bash
# Run: bash .ai/hooks/worktree-confine.test.sh
# Exercise advisory output through the real JSON/stdin hook interface.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hook="$here/worktree-confine.sh"
pass=0; fail=0

# Stable Windows boundaries on every host, independent of the CI temp folder.
git() {
  case "$*" in
    *--show-toplevel) printf 'C:/Repo/worktree' ;;
    *--git-common-dir) printf 'C:/Repo/.git' ;;
    *) return 1 ;;
  esac
}
export -f git
export TMPDIR='C:/TestScratch' TEMP='C:/TestScratch' TMP='C:/TestScratch'
export CLAUDE_SCRATCHPAD_DIR='C:/AgentScratch'

esc() {
  local s="${1//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  printf '%s' "$s"
}

check() { # expected label cwd tool field value
  local want="$1" label="$2" out status got
  out="$(printf '{"cwd":"%s","tool_name":"%s","tool_input":{"%s":"%s"}}' \
    "$(esc "$3")" "$4" "$5" "$(esc "$6")" | bash "$hook")"
  status=$?
  got=INVALID
  if [[ $status -eq 0 && "$out" != *permissionDecision* ]]; then
    if [[ -z "$out" ]]; then got=QUIET
    elif [[ "$out" == '{"systemMessage":"Heads up: '* && "$out" == *'Not blocked."}' ]]; then got=WARN
    fi
  fi
  if [[ "$got" == "$want" ]]; then pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf 'FAIL %s: expected %s, got %s (exit %s)\n%s\n' "$label" "$want" "$got" "$status" "$out"
  fi
}
w() { check "$1" "$2" "$3" Write file_path "$4"; }
b() { check "$1" "$2" 'C:/Repo/worktree' Bash command "$3"; }

for cwd in 'C:/Repo/worktree' 'C:\Repo\worktree'; do
  for target in 'C:/Repo/worktree/docs/x.md' 'C:\Repo\worktree\docs\x.md' 'docs/x.md' 'src\..\x.md'; do
    w QUIET "owned $cwd / $target" "$cwd" "$target"
  done
  for target in 'C:/Repo/sibling/x.md' 'C:\Repo\sibling\x.md' '../sibling/x.md' 'C:/Repo/worktree-other/x.md' 'C:\Repo\worktree\..\..\x.md'; do
    w WARN "outside $cwd / $target" "$cwd" "$target"
  done
done
w QUIET 'root itself' 'C:/Repo/worktree' 'C:/Repo/worktree'
w WARN 'shared Git metadata file edit' 'C:/Repo/worktree' 'C:/Repo/.git/config'
w WARN 'checkout .git file edit' 'C:/Repo/worktree' '.git'
w WARN 'quoted filename' 'C:/Repo/worktree' 'C:/Repo/a"quoted.txt'
w WARN 'newline filename' 'C:/Repo/worktree' $'C:/Repo/a\nfile.txt'
for target in 'C:/TestScratch/session.txt' 'C:/AgentScratch/session.txt' '/tmp/session.txt'; do
  w QUIET 'scratch directory' 'C:/Repo/worktree' "$target"
done
for tool in Edit MultiEdit NotebookEdit; do
  check WARN "$tool outside" 'C:/Repo/worktree' "$tool" notebook_path 'C:/Repo/outside.ipynb'
done
check QUIET 'missing cwd' '' Write file_path 'C:/Repo/outside.txt'
check QUIET 'read tools' 'C:/Repo/worktree' Read file_path 'C:/Repo/outside.txt'
b QUIET 'no redirect' 'git status --porcelain'
b QUIET 'redirect inside' 'echo hi > C:/Repo/worktree/out.txt'
b QUIET 'Git metadata shell access' 'echo hi > C:/Repo/.git/index.lock'
b QUIET 'quoted prose' 'echo "see > /usr/local/bin" >> notes.md'
b WARN 'outside redirect' 'echo hi > C:/Repo/out.txt'
b WARN 'outside append' 'echo hi >> C:/Repo/out.txt'
b WARN 'quoted outside redirect' 'echo hi > "C:/Repo/e f.txt"'
b WARN 'single quoted outside redirect' "echo hi > 'C:/Repo/e f.txt'"
for device in /dev/null /dev/zero /dev/tty /dev/stdin /dev/stdout /dev/stderr /dev/fd/2; do
  b QUIET "device $device" "echo hi > $device"
done
b QUIET 'stderr mid-pipeline' 'grep -q x file 2>/dev/null && echo y'
b WARN 'device prefix is a normal path' 'echo hi > /dev/null-output'

# A non-repository invocation must be a no-op even for an outside target.
git() { return 1; }; export -f git
w QUIET 'outside Git' 'C:/NoRepo' 'C:/Elsewhere/file.txt'
printf '%d passed, %d failed\n' "$pass" "$fail"
[[ $fail -eq 0 ]]
