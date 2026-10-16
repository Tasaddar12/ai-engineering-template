#!/usr/bin/env bash
# Synchronous native source decision. Never runs a host transition or edit.
set -u
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
. "$script_dir/lib/json-field.sh"
if [[ -z "$_HOOK_PY" ]]; then
  printf 'source-prewrite: a working Python interpreter is required\n' >&2
  exit 2
fi
namespace="$(basename "$(dirname "$script_dir")")"
case "$namespace" in
  .claude) host=claude ;;
  .codex|.ai) host=codex ;;
  *) printf 'source-prewrite: unknown installed namespace\n' >&2; exit 2 ;;
esac
"$_HOOK_PY" "$script_dir/../runtime/lib/prewrite.py" hook --host "$host"
status=$?
[[ "$status" == 0 || "$status" == 2 ]] && exit "$status"
printf 'source-prewrite: adapter failed (status %s); edit blocked\n' "$status" >&2
exit 2
