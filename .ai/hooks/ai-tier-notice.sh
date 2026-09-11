#!/usr/bin/env bash
# Advisory PostToolUse hook. Prints a mutability-tier reminder after a write to
# a file under .ai/. It NEVER blocks — exit is always 0.
#
# Blocking is deliberately not done here. Walls around documentation are what
# teach an agent that editing a stale spec is forbidden, which leaves it only
# two moves: refuse, or contort the code until the stale spec is satisfied.
# The behavior in .ai/RULES.md is carried by the agent prompts; this hook only
# makes the tier visible in the transcript.
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
  .ai/state/PROJECT.md|*/.ai/state/PROJECT.md|.ai/RULES.md|*/.ai/RULES.md)
    echo "NOTICE  intent tier. Follow human authorization and .ai/RULES.md#intent-and-plan-approval within your assigned role."
    ;;
  .ai/specs/*|*/.ai/specs/*)
    echo "NOTICE  contract tier. Follow .ai/RULES.md#the-amendment-protocol and .ai/RULES.md#review-and-documentation within your assigned role."
    ;;
  .ai/decisions/ADR-*|*/.ai/decisions/ADR-*)
    echo "NOTICE  contract tier. Follow ADR ownership and supersession in .ai/RULES.md#what-each-document-is-for within your assigned role."
    ;;
  .ai/decisions/amendments/*|*/.ai/decisions/amendments/*|.ai/state/journal/*|*/.ai/state/journal/*)
    echo "NOTICE  log tier. Follow .ai/RULES.md#mutability-tiers within your assigned role."
    ;;
  .ai/plans/*|*/.ai/plans/*)
    echo "NOTICE  plan tier. Follow .ai/RULES.md#plan-records-and-commits and .ai/RULES.md#review-and-documentation within your assigned role."
    ;;
  .ai/fixes/*|*/.ai/fixes/*)
    echo "NOTICE  plan tier. Follow .ai/RULES.md#bug-fixes within your assigned role."
    ;;
esac

exit 0
