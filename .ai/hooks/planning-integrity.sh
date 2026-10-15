#!/usr/bin/env bash
# Native PreToolUse planning checker; preserve stdin and denial exit status.
set -u
hook_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || exit 2
for interpreter in python3 python; do
  if command -v "$interpreter" >/dev/null 2>&1; then
    exec "$interpreter" "$hook_dir/planning-integrity.py"
  fi
done
printf '%s\n' 'planning-integrity: Python 3.11+ and the installed runtime/PyYAML are required.' >&2
exit 2
