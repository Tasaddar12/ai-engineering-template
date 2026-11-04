#!/bin/sh
# Select the hook beside this helper and the Python available on this machine.
set -eu
hook_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
hook_entry=$hook_dir/worktree-path-guard.py
if command -v cygpath >/dev/null 2>&1; then
    hook_entry=$(cygpath -m -- "$hook_entry")
fi
for interpreter in python3 python; do
    if command -v "$interpreter" >/dev/null 2>&1; then
        exec "$interpreter" -I "$hook_entry" "$@"
    fi
done
printf '%s\n' 'Engineer hooks require Python 3.11 or newer' >&2
exit 127
