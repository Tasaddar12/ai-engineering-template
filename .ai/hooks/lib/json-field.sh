#!/usr/bin/env bash
# Shared hook-payload field extraction. Sourced, never executed.
#
# Callers set `payload` to the raw stdin JSON, then call `field <key>`. The key
# is looked up at the top level first, then inside `tool_input` -- the two
# places every host puts the values a hook cares about.
#
# Tiered on purpose, and the tiers are NOT equivalent. The sed fallback stops at
# the first quote, so it truncates any value containing an escaped quote --
# which is most Bash command lines and every agent prompt. That fails OPEN (an
# empty value, so the caller takes no action), which is the safe direction for
# an advisory hook but makes the fallback near-useless for prose fields. jq or
# Python restores it. Path and identifier fields survive every tier.
#
# Extracted from ai-tier-notice.sh and worktree-guard.sh, which each carried
# their own copy. New hooks source this rather than adding a fourth.

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

# many_fields <key> [<key> ...] -- one value per line, in argument order.
#
# `field` costs a process per key. This hook fires on every tool use and wants
# four of them, so the single-key helper turns a per-tool advisory into four
# interpreter launches -- on Windows, more wall clock than the work being
# advised about. Values are newline-stripped: every field this serves (event
# name, session id, path, cwd) is single-line by construction, and collapsing
# is what keeps the line-per-key contract readable by `read`.
many_fields() {
  case "$_JSON" in
    jq)
      printf '%s' "$payload" | jq -r --args '
        . as $d | $ARGS.positional[] | . as $k
        | (($d[$k]? // $d.tool_input[$k]? // "")
           | if type == "string" then gsub("\n"; " ") else "" end)' -- "$@" 2>/dev/null
      ;;
    python3|python)
      printf '%s' "$payload" | "$_JSON" -c '
import sys, json
try:
    d = json.loads(sys.stdin.buffer.read().decode("utf-8"))
except Exception:
    d = {}
if not isinstance(d, dict):
    d = {}
nested = d.get("tool_input")
nested = nested if isinstance(nested, dict) else {}
lines = []
for key in sys.argv[1:]:
    value = d.get(key)
    if not isinstance(value, str):
        value = nested.get(key)
    lines.append(value.replace("\n", " ") if isinstance(value, str) else "")
# buffer.write, not write: text-mode stdout translates newlines to CRLF on
# Windows, and the trailing CR rides into every value the caller reads --
# turning an event name into one that matches nothing and a session id into
# a filename that cannot be written.
sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))
' "$@" 2>/dev/null
      ;;
    *)
      # The sed tier prints nothing for an absent key, which would silently
      # shift every later value up a line. printf restores the one-line-per-key
      # contract the callers read against.
      local key
      for key in "$@"; do
        printf '%s
' "$(field "$key")"
      done
      ;;
  esac
}
