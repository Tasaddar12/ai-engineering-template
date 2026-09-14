#!/usr/bin/env bash
# Advisory PostToolUse hook. Prints a document-ownership reminder after a write to
# a file under .planning/ or the shared .ai/RULES.md. It NEVER blocks -- exit is always 0.
#
# Rules and assigned roles govern changes; this optional hook only displays them.
#
# The installer registers this script directly for PostToolUse.

set -u

payload="$(cat 2>/dev/null || true)"

# --- extract a top-level or tool_input string field ---------------------------
# Tiered on purpose. The sed fallback stops at the first quote, so it truncates
# any value containing an escaped quote -- which is most Bash commands. That
# fails OPEN (no block), the safe direction, but it makes the Bash check
# near-useless without a real parser. jq or python restores it. The file-tool
# checks are unaffected either way: a file_path is a path, not a sentence.
if command -v jq >/dev/null 2>&1; then
  _JSON=jq
elif command -v python3 >/dev/null 2>&1; then
  _JSON=python3
elif command -v python >/dev/null 2>&1; then
  _JSON=python
else
  _JSON=sed
fi

_PYEX='
import sys, json
try:
    d = json.loads(sys.stdin.buffer.read().decode("utf-8"))
except Exception:
    sys.exit(0)
k = sys.argv[1]
v = d.get(k)
if not isinstance(v, str):
    v = (d.get("tool_input") or {}).get(k)
sys.stdout.buffer.write((v if isinstance(v, str) else "").encode("utf-8"))
'

field() {
  case "$_JSON" in
    jq)
      printf '%s' "$payload" | jq -r --arg k "$1" \
        '(.[$k]? // .tool_input[$k]? // "") | if type=="string" then . else "" end' 2>/dev/null
      ;;
    python3|python)
      printf '%s' "$payload" | "$_JSON" -c "$_PYEX" "$1" 2>/dev/null
      ;;
    *)
      printf '%s' "$payload" \
        | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" \
        | head -n 1
      ;;
  esac
}

if [[ "$(field tool_name)" == apply_patch ]]; then
  paths="$(field command | sed -nE 's/^\*\*\* (Add File|Update File|Delete File|Move to): (.*)\r?$/\2/p' | tr -d '\r')"
else
  paths="$(field file_path)"
  [[ -n "$paths" ]] || paths="$(field notebook_path)"
fi

while IFS= read -r path; do
# Unescape the backslashes Windows paths arrive with, and normalize.
path="${path//\\\\//}"
path="${path//\\//}"

case "$path" in
  .planning/PROJECT.md|*/.planning/PROJECT.md|.planning/REQUIREMENTS.md|*/.planning/REQUIREMENTS.md|.ai/RULES.md|*/.ai/RULES.md)
    echo "NOTICE  intent ownership. Follow human authorization and .ai/RULES.md#phase-authority within your assigned role."
    ;;
  .planning/specs/*|*/.planning/specs/*)
    echo "NOTICE  current behavior. Resolve evidence and documentation through .ai/RULES.md#documents-and-conflicts within your assigned role."
    ;;
  .planning/decisions/ADR-*|*/.planning/decisions/ADR-*)
    echo "NOTICE  decision history. Follow ADR ownership and supersession in .ai/RULES.md#documents-and-conflicts within your assigned role."
    ;;
  .planning/phases/*|*/.planning/phases/*)
    echo "NOTICE  phase evidence. Follow .ai/RULES.md#phase-authority and .ai/RULES.md#components-and-handoffs within your assigned role."
    ;;
  .planning/STATE.md|*/.planning/STATE.md|.planning/ROADMAP.md|*/.planning/ROADMAP.md)
    echo "NOTICE  derived status and navigation. Follow .ai/RULES.md#phase-authority within your assigned role."
    ;;
esac

done <<< "$paths"

exit 0
