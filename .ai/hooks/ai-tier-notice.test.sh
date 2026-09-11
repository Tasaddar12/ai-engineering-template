#!/usr/bin/env bash
set -eu
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
passed=0
for path in '.ai/plans/backlog/PLAN-001-example.md' '/repo/.ai/specs/SPEC-001-example.md' 'C:\\repo\\.ai\\decisions\\ADR-0001-example.md' '.ai/fixes/open/FIX-001-example.md' '.ai/state/PROJECT.md'; do
  output="$(printf '{"file_path":"%s"}' "$path" | bash "$script_dir/ai-tier-notice.sh")"
  [[ "$output" == *'NOTICE '* && "$output" == *'.ai/RULES.md#'* && "$output" == *'assigned role'* ]]
  [[ "$output" != *'rewrite freely'* && "$output" != *'add its id'* && "$output" != *'commit both with the code change'* ]]
  passed=$((passed + 1))
done
for payload in '{}' '{"file_path":"src/example.py"}'; do
  [[ -z "$(printf '%s' "$payload" | bash "$script_dir/ai-tier-notice.sh")" ]]
  passed=$((passed + 1))
done
printf '%s passed, 0 failed\n' "$passed"
