#!/usr/bin/env bash
# Context-triggered and exit-triggered handoff hook.
#
# Three jobs, dispatched on hook_event_name:
#
#   1. PostToolUse  -- read the CALLING agent's transcript (a subagent's own,
#      never its parent's), compare occupancy against the configured limit
#      (60% of the context window or 250,000 tokens, whichever is lower), and
#      at or over it write a handoff record and inject an advisory. What the
#      advisory asks depends on the role: a plan executor hands the rest of
#      its plan on, an artifact role such as the researcher writes what it has
#      and returns it as partial. Advisory only: this hook NEVER blocks a tool
#      call. An agent that ignores the warning still has its handoff on disk.
#      The orchestrating session is never told to stop: on Claude it is not
#      measured at all, and elsewhere the advisory tells it to keep going.
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
# shellcheck source=lib/agent-roles.sh
. "$script_dir/lib/agent-roles.sh"

payload="$(cat 2>/dev/null || true)"

# One extraction for every field: this hook rides every tool use, so a process
# per field is the difference between an advisory and a tax.
#
# `agent_id` and `agent_type` say WHICH agent is calling. Claude Code sets both
# on any hook fired from inside a subagent -- tool use and SubagentStop alike --
# and leaves them empty for the root session. Codex sets them on SubagentStop,
# with `agent_transcript_path` beside them. Reading them here costs nothing,
# whereas a second extraction inside a branch costs another interpreter.
{
  read -r event
  read -r session
  read -r transcript
  read -r cwd
  read -r agent_type
  read -r agent_transcript
  read -r agent_id
} < <(many_fields hook_event_name session_id transcript_path cwd \
                  agent_type agent_transcript_path agent_id)
[[ -n "${cwd:-}" ]] || cwd="$PWD"

# The calling subagent's OWN transcript, or nothing.
#
# `transcript_path` on a subagent's hook is the PARENT session's transcript.
# Measuring it reads the orchestrator's occupancy and stops the subagent for
# it -- a researcher at 30k told to hand off because its orchestrator is at
# 130k. Codex names the subagent's transcript outright; Claude Code keeps it
# beside the parent's, at <parent without .jsonl>/subagents/agent-<id>.jsonl.
subagent_transcript() {
  if [[ -n "${agent_transcript:-}" ]]; then
    printf '%s' "$agent_transcript"
    return 0
  fi
  [[ -n "${agent_id:-}" && -n "${transcript:-}" ]] || return 0
  handoff_slug "$agent_id" >/dev/null || return 0
  printf '%s/subagents/agent-%s.jsonl' "${transcript%.jsonl}" "$agent_id"
}

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

# --- shared by both SubagentStop paths ----------------------------------------

# The SUMMARY a plan is expected to leave behind.
summary_for() {
  [[ -n "${1-}" ]] || return 0
  printf '%s' "${1%-PLAN.md}-SUMMARY.md"
}

# A SUMMARY whose frontmatter says `complete` is finished work: no handoff.
# Anything else -- missing, blocked, or a plan path that could not be recovered
# -- is treated as unfinished. Over-reporting costs the orchestrator one
# inspection; under-reporting silently drops the work.
plan_finished() {
  [[ -n "${1-}" && -f "$cwd/$1" ]] || return 1
  grep -qE '^status:[[:space:]]*complete[[:space:]]*$' "$cwd/$1" 2>/dev/null
}

# Handoff filename stem: the plan identifier when one is known, a timestamp
# otherwise, so two unattributed stops in one session do not collide.
handoff_identifier() {
  local identifier
  identifier="$(printf '%s' "${1##*/}" | sed -n 's/^\([0-9][0-9.]*-[0-9][0-9]*\)-PLAN\.md$/\1/p')"
  [[ -n "$identifier" ]] || identifier="$(date -u +%H%M%S 2>/dev/null || printf 'exit')"
  printf '%s' "$identifier"
}

# Remove the dispatch this stop closes from the active stack: the first entry
# for agent $1 on plan $2 (on any plan when $2 is empty). A stop attributed
# from the payload never reaches the stack walk below, and an entry left
# behind would be handed off by some later, unrelated stop.
drop_active() {
  [[ -f "$active_file" ]] || return 0
  local want_agent="$1" want_plan="$2" kept="" dropped=0 line entry_agent entry_plan
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    if [[ "$dropped" -eq 0 ]]; then
      entry_agent="$(printf '%s' "$line" | sed -n 's/.*"agent"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
      entry_plan="$(printf '%s' "$line" | sed -n 's/.*"plan"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
      if [[ "$entry_agent" == "$want_agent" && ( -z "$want_plan" || "$entry_plan" == "$want_plan" ) ]]; then
        dropped=1
        continue
      fi
    fi
    kept="$kept$line
"
  done < "$active_file"
  if [[ -n "$kept" ]]; then
    printf '%s' "$kept" > "$active_file" 2>/dev/null
  else
    rm -f "$active_file" 2>/dev/null
  fi
}

case "$event" in
  Stop)
    # The root's sentinel and every subagent's, which are keyed per agent.
    rm -f "$state_file" "$dir/.state-$slug--"*.json 2>/dev/null
    exit 0
    ;;

  SubagentStop)
    # Two hosts reach this event from opposite directions, so identity is
    # resolved from whichever side actually carries it.
    #
    # Codex dispatches a subagent through SubagentStart/SubagentStop rather
    # than through a tool call, so worktree-guard.sh never sees a PreToolUse
    # dispatch and the active stack is empty -- this branch used to exit here,
    # and Codex got no exit handoff at all. Its stop payload names the role in
    # `agent_type` and the subagent's own transcript in `agent_transcript_path`,
    # where the assigned plan is named.
    #
    # Claude Code now sends `agent_type` and `agent_id` here too, so it takes
    # this branch as well. Its transcript is found from `agent_id`; without
    # that, the plan was never recovered and every coder stop -- finished or
    # not -- left an unattributed handoff behind.
    if [[ -n "${agent_type:-}" ]]; then
      # A read-only role leaves no half-written plan behind.
      agent_writes_files "$agent_type" || exit 0
      plan="$(handoff_plan_in_transcript "$(subagent_transcript)")"
      # A plan that could not be recovered, on a host that also recorded the
      # dispatch, is attributed from the stack below instead.
      if [[ -n "$plan" || ! -f "$active_file" ]]; then
        drop_active "$agent_type" "$plan"
        summary="$(summary_for "$plan")"
        plan_finished "$summary" && exit 0
        # An agent that crossed the limit already has a record, carrying the
        # digest it wrote. Its exit is folded into that record rather than a
        # second one, so the orchestrator reads one handoff per stopped agent
        # and the continuation it dispatches is handed the digest.
        target="$dir/$slug--$(handoff_identifier "$plan").json"
        if [[ -n "${agent_id:-}" ]] && handoff_slug "$agent_id" >/dev/null \
           && [[ -f "$dir/$slug--agent-$agent_id.json" ]]; then
          target="$dir/$slug--agent-$agent_id.json"
        fi
        write_handoff "$target" "incomplete-exit" "$agent_type" "$plan" "$summary" "" "" "" ""
        exit 0
      fi
    fi

    # Claude: identity comes from the stack worktree-guard.sh recorded at
    # dispatch. Each line is one dispatch it let through, and a line whose plan
    # has no `complete` SUMMARY is work that stopped early.
    [[ -f "$active_file" ]] || exit 0
    remaining=""
    wrote=0
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      agent="$(printf '%s' "$line" | sed -n 's/.*"agent"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
      plan="$(printf '%s' "$line" | sed -n 's/.*"plan"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
      summary="$(summary_for "$plan")"
      # A finished plan leaves the stack without a handoff.
      if plan_finished "$summary"; then
        continue
      fi
      # One SubagentStop closes one dispatch. Later entries stay on the stack
      # for their own stop events rather than all collapsing into this one.
      if [[ "$wrote" -eq 0 ]]; then
        write_handoff "$dir/$slug--$(handoff_identifier "$plan").json" "incomplete-exit" \
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

# The limit is for subagents, never for the orchestrating session. A subagent
# handing off costs one fresh subagent; an orchestrator that stops strands the
# whole phase and leaves the user to resume it -- which is what the old advisory
# did, telling the root session to "dispatch nothing new" at 250k of a 1M window.
#
# Claude Code names the calling agent (`agent_id`) on every hook fired inside a
# subagent, so on Claude a tool use with no agent identity IS the orchestrator:
# measure nothing, write nothing, say nothing. The host is read from where this
# copy was installed, because CLAUDECODE leaks into every shell Claude starts
# and would misfire for a Codex session launched from one.
host_is_claude() {
  [[ "$script_dir" == */.claude/hooks || -n "${CLAUDE_PROJECT_DIR:-}" ]]
}
if [[ -z "${agent_id:-}${agent_transcript:-}" ]] && host_is_claude; then
  exit 0
fi

# A subagent is measured on its own transcript and keyed by its own id, so its
# record, its debounce and its advisory are never the orchestrator's. When its
# transcript cannot be found the hook stays silent rather than falling back to
# the parent's: measuring the wrong agent is exactly what stopped a researcher
# at a fraction of its window.
role="${agent_type:-}"
key="$slug"
measured="$transcript"
if [[ -n "${agent_id:-}${agent_transcript:-}" ]]; then
  measured="$(subagent_transcript)"
  [[ -n "$measured" ]] || exit 0
  ident="${agent_id:-${agent_type:-subagent}}"
  handoff_slug "$ident" >/dev/null || exit 0
  key="$slug--agent-$ident"
  state_file="$dir/.state-$key.json"
fi

used="$(handoff_used_tokens "$measured")"
[[ -n "$used" ]] || exit 0

read -r limit window percent ceiling <<< "$(handoff_limits)"
[[ -n "${limit:-}" ]] || exit 0
[[ "$limit" -gt 0 ]] 2>/dev/null || exit 0
[[ "$used" -ge "$limit" ]] 2>/dev/null || exit 0

write_handoff "$dir/$key.json" "context-threshold" "$role" "" "" \
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

# What the limit asks for depends on what the agent produces. A coder hands the
# rest of its plan on. A researcher that did the same would leave nothing --
# told to "write your SUMMARY.md with status: blocked", it wrote its research
# up as a handoff note and exited waiting for a human. An artifact role
# converges instead: it writes what it has and returns it as partial.
plan_stop="Do not begin another task or repair. Finish only the operation needed to \
preserve work, commit safe partial results, write your SUMMARY.md with status: blocked \
naming completed and remaining tasks, and report the handoff to the orchestrator. Do not \
set status: complete to avoid the handoff."
artifact_stop="This limit is not a blocker and needs no human: converge rather than stop. \
Start no new search, fetch or exploration. Write your assigned output now from what you \
already have, name what it does not yet cover, commit it if your assignment allows, and \
return it marked partial. The orchestrator continues the uncovered part in a fresh agent."
research_stop="This limit is not a blocker and needs no human: converge rather than stop. \
Start no new search, fetch or read. Write your assigned RESEARCH.md now from the findings \
you already have, with honest confidence levels, and list every question you did not reach \
under '## Not Yet Researched'. Commit it if your assignment allows, then return \
'## RESEARCH PARTIAL'. Do not return RESEARCH BLOCKED for this limit: the orchestrator \
continues the open questions in a fresh researcher."
review_stop="Examine nothing new. Write your report now on what you have already examined, \
name the scope you did not reach, and return it. The orchestrator dispatches a fresh \
reviewer for the remainder."
unknown_stop="If you are executing a plan: $plan_stop If you are writing an assigned \
artifact such as RESEARCH.md: write it now from what you have, list what it does not \
cover, and return it as partial -- this limit is not a blocker. If you are the \
orchestrating session, this limit does not apply to you: keep running the workflow to \
its end -- dispatch the next wave, verify and ship as it says -- and never stop, hand \
off, or tell the user to resume or start a fresh session because of it."

case "$(agent_stop_kind "$role")" in
  plan) instruction="$plan_stop" ;;
  artifact)
    if [[ "${role##*:}" == researcher ]]; then
      instruction="$research_stop"
    else
      instruction="$artifact_stop"
    fi
    ;;
  review) instruction="$review_stop" ;;
  *) instruction="$unknown_stop" ;;
esac

# The hook records where the attempt stopped; only the agent knows what it
# learned. Without that digest the continuation re-reads the whole assignment,
# so the advisory asks for it by the exact id of the record already on disk.
digest="Before you return, add what you learned to that record so the next agent \
ingests it instead of re-reading your assignment: phase_run query handoff.write $key \
--artifact <the file you are writing> --completed <item>... --findings <fact, with its \
path:line>... --files-read <path>... --remaining <item>... --next-action \"<the first \
thing to do next>\". A finding is anything the next agent would otherwise open a file to \
learn. Record it with what is already in your context: do not read anything to write it."

message="CONTEXT HANDOFF  $used tokens in use, at or over the $limit-token limit \
(${percent}% of a ${window}-token window, capped at ${ceiling}). A handoff record is on \
disk at .planning/handoffs/$key.json. $instruction $digest"

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
