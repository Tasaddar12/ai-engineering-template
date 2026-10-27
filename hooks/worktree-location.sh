#!/usr/bin/env bash
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || exit 0
exec bash "$here/python-hook.sh" worktree-location.py "$@"
