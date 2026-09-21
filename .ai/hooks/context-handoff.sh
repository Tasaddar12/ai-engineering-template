#!/usr/bin/env bash
# Context-triggered and exit-triggered handoff hook.
#
# Three jobs, dispatched on hook_event_name:
#
#   1. PostToolUse  -- read the session transcript, compare occupancy against
#      the configured limit (60% of the context window or 250,000 tokens,
#      whichever is lower), and at or over it write a handoff record and inject
#      an advisory telling the agent to stop taking new work. Advisory only:
#      this hook NEVER blocks a tool call. An agent that ignores the warning
#      still has its handoff on disk.
#
#   2. SubagentStop -- a write-capable subagent that was dispatched but left no
#      `complete` SUMMARY.md did not finish. Write a handoff so the orchestrator
#      can put a fresh subagent on the remainder instead of replaying the plan.
#      The dispatch side of this is worktree-guard.sh, which records each
#      write-capable dispatch to the active-agent stack this reads.
#
#   3. Stop -- the root session ended. Clear the per-session debounce state.
#      Handoffs are NOT written here: the root session is the orchestrator, and
#      an orchestrator context is not a plan another subagent picks up.
#
# The envelope matters. `hookSpecificOutput.additionalContext` is only a valid
# output shape on PostToolUse; Stop and SubagentStop reject it outright, so
# those paths write their records and exit silently.
#
# Fails OPEN on everything: no Python, no git, no transcript, an unparseable
# payload. Exit is always 0.

set -u

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/json-field.sh
. "$script_dir/lib/json-field.sh"
# shellcheck source=lib/handoff-io.sh
. "$script_dir/lib/handoff-io.sh"

payload="$(cat 2>/dev/null || true)"

# One extraction for all four: this hook rides every tool use, so a process per
# field is the difference between an advisory and a tax.
{
  read -r event
  read -r session
  read -r transcript
  read -r cwd
} < <(many_fields hook_event_name session_id transcript_path cwd)
[[ -n "${cwd:-}" ]] || cwd="$PWD"

slug="$(handoff_slug "$session")" || exit 0
dir="$(handoff_dir)"
state_file="$dir/.state-$slug.json"
active_file="$dir/.active-$slug.jsonl"

# Repeated advisories crowd out the work they are warning about. Five tool uses
# between them is enough to stay visible without becoming the transcript.
DEBOUNCE_CALLS=5

git_at() { git -C "$cwd" "$@" 2>/dev/null || true; }

# Write one handoff record. An existing record is refreshed, not duplicated: a
# session that crosses the limit once and then runs four more tools has one
# handoff, carrying current numbers and its original created_at.
write_handoff() {
  local file="$1" reason="$2" agent="$3" plan="$4" summary="$5" used="$6" limit="$7"
  local window="$8" percent="$9"
  handoff_record "$file" \
    reason "$reason" \
    session_id "$session" \
    agent "$agent" \
    plan "$plan" \
    summary "$summary" \
    cwd "$cwd" \
    branch "$(git_at branch --show-current)" \
    head "$(git_at rev-parse HEAD)" \
    dirty "$(git_at status --short)" \
    transcript_path "$transcript" \
    used_tokens "$used" \
    threshold_tokens "$limit" \
    context_window "$window" \
    context_percent "$percent"
}

case "$event" in
  Stop)
    rm -f "$state_file" 2>/dev/null
    exit 0
    ;;

  SubagentStop)
    # Each line is one dispatch worktree-guard.sh let through. A line whose
    # plan has no `complete` SUMMARY is work that stopped early.
    [[ -f "$active_file" ]] || exit 0
    remaining=""
    wrote=0
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      agent="$(printf '%s' "$line" | sed -n 's/.*"agent"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
      plan="$(printf '%s' "$line" | sed -n 's/.*"plan"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
      summary=""
      [[ -n "$plan" ]] && summary="${plan%-PLAN.md}-SUMMARY.md"
      # A SUMMARY whose frontmatter says `complete` is a finished plan: no
      # handoff, and the entry leaves the stack. Anything else -- missing,
      # blocked, or a plan path that could not be read out of the dispatch --
      # is treated as unfinished. Over-reporting costs the orchestrator one
      # inspection; under-reporting silently drops the work.
      if [[ -n "$summary" && -f "$cwd/$summary" ]] \
         && grep -qE '^status:[[:space:]]*complete[[:space:]]*$' "$cwd/$summary" 2>/dev/null; then
        continue
      fi
      # One SubagentStop closes one dispatch. Later entries stay on the stack
      # for their own stop events rather than all collapsing into this one.
      if [[ "$wrote" -eq 0 ]]; then
        identifier="$(printf '%s' "${plan##*/}" | sed -n 's/^\([0-9][0-9.]*-[0-9][0-9]*\)-PLAN\.md$/\1/p')"
        [[ -n "$identifier" ]] || identifier="$(date -u +%H%M%S 2>/dev/null || printf 'exit')"
        write_handoff "$dir/$slug--$identifier.json" "incomplete-exit" \
          "$agent" "$plan" "$summary" "" "" "" ""
        wrote=1
        continue
      fi
      remaining="$remaining$line
"
    done < "$active_file"
    if [[ -n "$remaining" ]]; then
      printf '%s' "$remaining" > "$active_file" 2>/dev/null
    else
      rm -f "$active_file" 2>/dev/null
    fi
    exit 0
    ;;

  PostToolUse|AfterTool|"") ;;
  *) exit 0 ;;
esac

# --- PostToolUse: measure and advise -----------------------------------------

used="$(handoff_used_tokens "$transcript")"
[[ -n "$used" ]] || exit 0

read -r limit window percent ceiling <<< "$(handoff_limits)"
[[ -n "${limit:-}" ]] || exit 0
[[ "$limit" -gt 0 ]] 2>/dev/null || exit 0
[[ "$used" -ge "$limit" ]] 2>/dev/null || exit 0

write_handoff "$dir/$slug.json" "context-threshold" "" "" "" \
  "$used" "$limit" "$window" "$percent"

calls=0
if [[ -f "$state_file" ]]; then
  calls="$(sed -n 's/.*"calls"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p' "$state_file" | head -n 1)"
  [[ -n "$calls" ]] || calls=0
  calls=$((calls + 1))
  if [[ "$calls" -lt "$DEBOUNCE_CALLS" ]]; then
    mkdir -p "$dir" 2>/dev/null && printf '{"calls": %s}\n' "$calls" > "$state_file" 2>/dev/null
    exit 0
  fi
fi
mkdir -p "$dir" 2>/dev/null && printf '{"calls": 0}\n' > "$state_file" 2>/dev/null

message="CONTEXT HANDOFF  $used tokens in use, at or over the $limit-token limit \
(${percent}% of a ${window}-token window, capped at ${ceiling}). A handoff record is on \
disk at .planning/handoffs/$slug.json. Do not begin another task or repair. Finish only \
the operation needed to preserve work, commit safe partial results, write your SUMMARY.md \
with status: blocked naming completed and remaining tasks, and report the handoff to the \
orchestrator. Do not set status: complete to avoid the handoff."

if [[ -n "$HANDOFF_PY" ]]; then
  "$HANDOFF_PY" -c '
import sys, json
sys.stdout.write(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": sys.argv[1],
    }
}))
' "$message" 2>/dev/null
fi

exit 0
