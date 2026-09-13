#!/usr/bin/env bash
set -eu
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
passed=0
for path in '.planning/phases/01-example/01-CONTEXT.md' '/repo/.planning/specs/SPEC-001-example.md' 'C:\\repo\\.planning\\decisions\\ADR-0001-example.md' '.planning/STATE.md' '.planning/PROJECT.md' '.planning/REQUIREMENTS.md' '.planning/ROADMAP.md'; do
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
