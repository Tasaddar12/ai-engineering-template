#!/usr/bin/env bash
set -eu
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 "$here/hook_contracts.py"
