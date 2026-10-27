#!/usr/bin/env bash
# Standard-library hooks: use a configured interpreter, then Python 3 probes.
set -u
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || exit 0
script=${1:-}
case "$script" in ''|*/*|*\\*|..*) exit 0 ;; esac
shift
for python in "${ENGINEER_PYTHON:-}" python3 python; do
  [ -n "$python" ] || continue
  command -v "$python" >/dev/null 2>&1 || continue
  "$python" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1 || continue
  exec "$python" "$here/$script" "$@"
done
if [ "$script" = planning-integrity.py ]; then
  echo "Planning integrity requires Python 3.11 or newer" >&2
  exit 2
fi
exit 0
