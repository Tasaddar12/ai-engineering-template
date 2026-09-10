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
  .ai/state/PROJECT.md|*/.ai/state/PROJECT.md|.ai/RULES.md|*/.ai/RULES.md|.ai/policies/approval.md|*/.ai/policies/approval.md)
    echo "NOTICE  intent tier — human authority. Edit only under explicit human instruction; otherwise propose and wait. Surface any unauthorized edit to the user. See .ai/RULES.md#mutability-tiers"
    ;;
  */.ai/specs/*)
    echo "NOTICE  contract tier — amendable, but the change needs a record. Write .ai/decisions/amendments/AMD-{nnn}-{slug}.md from the template, add its id to this document's links:, and commit both with the code change. See .ai/RULES.md#the-amendment-protocol"
    echo "NOTICE  a spec states what IS — present tense, no history, no intentions. Replace wording, never annotate it: no 'deprecated', 'removed in v2', 'was previously', 'not yet implemented', TODO or strikethrough. If a requirement is gone, delete it; the amendment record holds what it said. See .ai/RULES.md#what-each-document-is-for"
    ;;
  */.ai/decisions/ADR-*)
    echo "NOTICE  contract tier — amendable, but the change needs a record. Write .ai/decisions/amendments/AMD-{nnn}-{slug}.md from the template, add its id to this document's links:, and commit both with the code change. See .ai/RULES.md#the-amendment-protocol"
    echo "NOTICE  an ADR is a dated record and may describe the past. Changing the decision means a NEW ADR naming this one in supersedes:, plus status: superseded and superseded_by: here — never a rewrite of the Context, Decision or Alternatives. That status flip needs no amendment record."
    ;;
  */.ai/decisions/amendments/*|*/.ai/state/journal/*)
    echo "NOTICE  log tier — append only. Do not edit or delete earlier entries; supersede them with a new one."
    ;;
  */.ai/plans/*)
    echo "NOTICE  plan tier — rewrite freely. A plan's stage is its directory: move it with 'git mv', and never add a status: field."
    echo "NOTICE  a plan carries the contract change it will make, under Contract changes: specs to create, amend or retire with the wording drafted, plus any ADR it needs, cites or supersedes. Nothing there is written into .ai/specs/ until the code works."
    ;;
  */.ai/fixes/*)
    echo "NOTICE  plan tier — a fix restores conformance with the contract; anything that changes what conformance means is a plan. Its stage is its directory ('git mv' between open/ and done/<period>/), no status: field. A fix is not done without a check that fails before it and passes after. See .ai/RULES.md#bug-fixes"
    ;;
esac

exit 0
