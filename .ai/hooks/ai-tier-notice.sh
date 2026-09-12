#!/usr/bin/env bash
# Advisory PostToolUse hook. Prints a document-ownership reminder after a write to
# a file under .ai/. It NEVER blocks — exit is always 0.
#
# Rules and assigned roles govern changes; this optional hook only displays them.
#
# Optional JSON hook example; registration is not supplied. See README.md.

set -u

payload="$(cat 2>/dev/null || true)"

# Pull "file_path":"..." out of the hook payload without requiring jq.
path="$(printf '%s' "$payload" \
  | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
  | head -n 1)"

# Unescape the backslashes Windows paths arrive with, and normalize.
path="${path//\\\\//}"
path="${path//\\//}"

case "$path" in
  .ai/PROJECT.md|*/.ai/PROJECT.md|.ai/REQUIREMENTS.md|*/.ai/REQUIREMENTS.md|.ai/RULES.md|*/.ai/RULES.md)
    echo "NOTICE  intent ownership. Follow human authorization and .ai/RULES.md#phase-authority within your assigned role."
    ;;
  .ai/specs/*|*/.ai/specs/*)
    echo "NOTICE  current behavior. Resolve evidence and documentation through .ai/RULES.md#documents-and-conflicts within your assigned role."
    ;;
  .ai/decisions/ADR-*|*/.ai/decisions/ADR-*)
    echo "NOTICE  decision history. Follow ADR ownership and supersession in .ai/RULES.md#documents-and-conflicts within your assigned role."
    ;;
  .ai/phases/*|*/.ai/phases/*)
    echo "NOTICE  phase evidence. Follow .ai/RULES.md#phase-authority and .ai/RULES.md#components-and-handoffs within your assigned role."
    ;;
  .ai/STATE.md|*/.ai/STATE.md|.ai/ROADMAP.md|*/.ai/ROADMAP.md)
    echo "NOTICE  derived status and navigation. Follow .ai/RULES.md#phase-authority within your assigned role."
    ;;
esac

exit 0
