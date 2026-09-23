#!/usr/bin/env bash
# Behavioural suite for context-handoff.sh. Builds a real repository with real
# transcripts and runs the hook as a host would: JSON on stdin, decisions read
# back off the filesystem and stdout.
set -eu

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hook="$script_dir/context-handoff.sh"
guard="$script_dir/worktree-guard.sh"
passed=0
failed=0

check() {
  if [[ "$2" == "$3" ]]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    printf 'FAIL  %s\n      expected: %s\n      actual:   %s\n' "$1" "$3" "$2" >&2
  fi
}

contains() {
  if [[ "$2" == *"$3"* ]]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    printf 'FAIL  %s\n      %q does not contain %q\n' "$1" "$2" "$3" >&2
  fi
}

lacks() {
  if [[ "$2" != *"$3"* ]]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    printf 'FAIL  %s\n      %q contains %q\n' "$1" "$2" "$3" >&2
  fi
}

workspace="$(mktemp -d)"
trap 'rm -rf "$workspace"' EXIT

repo="$workspace/repo"
mkdir -p "$repo/.planning"
git -C "$repo" init --quiet
git -C "$repo" config user.email test@example.com
git -C "$repo" config user.name Test
printf 'seed\n' > "$repo/seed.txt"
git -C "$repo" add seed.txt
git -C "$repo" commit --quiet -m seed

# 200000 * 60% = 120000, which is below the 250000 ceiling, so the percentage
# binds. Both keys are set explicitly so the suite tests the resolution rather
# than the defaults happening to agree with it.
cat > "$repo/.planning/config.yaml" <<'YAML'
context_window: 200000
handoff:
  context_percent: 60
  context_tokens: 250000
YAML

handoffs="$repo/.planning/handoffs"

# A Claude Code transcript: the LAST usage block is current occupancy, so an
# earlier larger reading must not win.
claude_transcript() {
  local path="$1" total="$2"
  {
    printf '{"type":"assistant","message":{"usage":{"input_tokens":999000,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0}}}\n'
    printf '{"type":"user","content":"no usage here"}\n'
    printf '{"type":"assistant","message":{"usage":{"input_tokens":%s,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0}}}\n' "$total"
  } > "$path"
}

# A Codex rollout: a TokenUsageRecord carrying thread_token_usage.total_tokens.
codex_transcript() {
  printf '{"type":"token_usage_record","payload":{"turn_token_usage":{"total_tokens":10},"thread_token_usage":{"total_tokens":%s}}}\n' "$2" > "$1"
}

# CLAUDE_PROJECT_DIR marks a Claude Code hook; it is cleared here so the suite
# tests the host-agnostic path unless a case sets it on purpose.
run_hook() {
  ( cd "$repo" && printf '%s' "$1" | env -u CLAUDE_PROJECT_DIR bash "$hook" 2>/dev/null )
}

payload_for() {
  printf '{"hook_event_name":"%s","session_id":"%s","cwd":"%s","transcript_path":"%s"}' \
    "$1" "$2" "$repo" "$3"
}

# --- preflight ---------------------------------------------------------------
#
# The hook is deliberately silent when it cannot measure occupancy, so an
# environment with no working interpreter turns every assertion below into a
# vacuous pass -- which is how a mute hook reached CI unnoticed. Establish that
# the measuring path works at all, and say which tier answered, before trusting
# a single silence in this file.

. "$script_dir/lib/handoff-io.sh"
printf 'interpreter: %s   jq: %s
'   "${HANDOFF_PY:-<none found>}" "$(command -v jq >/dev/null 2>&1 && echo yes || echo no)"
if [[ -z "$HANDOFF_PY" ]]; then
  echo "FAIL  no working python interpreter: the hook cannot measure occupancy," >&2
  echo "      so every silence this suite checks would be silence for the wrong reason." >&2
  exit 1
fi
# The extractor is checked before any behaviour that depends on it. jq on
# Windows emits CRLF, and `read` keeps the CR, so `event` bound with a trailing
# carriage return and matched no case arm -- the hook then exited silently on
# every tool call. Nothing about that was visible: the value echoed identically
# to the correct one, and a mute hook produces the silence most of the
# assertions below are checking for, so the suite failed five tests for a
# reason none of them named. %q prints the bytes, not the rendering.
(
  payload='{"hook_event_name":"PostToolUse","session_id":"probe-id","tool_input":{"file_path":"/x"}}'
  . "$script_dir/lib/json-field.sh"
  { read -r _event; read -r _session; read -r _path; read -r _absent; } \
    < <(many_fields hook_event_name session_id file_path agent_type)
  printf 'extractor: %s\n' "$_JSON"
  if [[ "$_event" != "PostToolUse" || "$_session" != "probe-id" \
        || "$_path" != "/x" || -n "$_absent" ]]; then
    printf 'FAIL  many_fields via the %s tier bound %q %q %q %q\n' \
      "$_JSON" "$_event" "$_session" "$_path" "$_absent" >&2
    exit 1
  fi
) || exit 1

claude_transcript "$workspace/preflight.jsonl" 123456
preflight="$(handoff_used_tokens "$workspace/preflight.jsonl")"
if [[ "$preflight" != "123456" ]]; then
  echo "FAIL  the interpreter ran but could not read a transcript at this path shape" >&2
  echo "      (measured '$preflight', wanted 123456; transcript at $workspace/preflight.jsonl)" >&2
  exit 1
fi

# --- below the limit stays silent --------------------------------------------

claude_transcript "$workspace/low.jsonl" 100000
out="$(run_hook "$(payload_for PostToolUse sess-low "$workspace/low.jsonl")")"
check "below limit emits nothing" "$out" ""
check "below limit writes no handoff" "$(ls "$handoffs" 2>/dev/null | wc -l | tr -d ' ')" "0"

# --- at the limit warns and records ------------------------------------------

claude_transcript "$workspace/high.jsonl" 130000
out="$(run_hook "$(payload_for PostToolUse sess-high "$workspace/high.jsonl")")"
contains "over limit emits an advisory" "$out" "CONTEXT HANDOFF"
contains "advisory names the occupancy" "$out" "130000"
contains "advisory names the limit" "$out" "120000"
contains "advisory uses the injection envelope" "$out" "additionalContext"
check "over limit writes a handoff" "$([[ -f "$handoffs/sess-high.json" ]] && echo yes)" "yes"

record="$(cat "$handoffs/sess-high.json")"
contains "handoff records the reason" "$record" '"reason": "context-threshold"'
contains "handoff records occupancy" "$record" '"used_tokens": 130000'
contains "handoff records the threshold" "$record" '"threshold_tokens": 120000'
contains "handoff is pending" "$record" '"status": "pending"'
contains "handoff records the branch" "$record" '"branch": "'

# --- the exact boundary counts as over ---------------------------------------

claude_transcript "$workspace/exact.jsonl" 120000
out="$(run_hook "$(payload_for PostToolUse sess-exact "$workspace/exact.jsonl")")"
contains "the threshold itself fires" "$out" "CONTEXT HANDOFF"

# --- the ceiling binds when the percentage would not -------------------------

cat > "$repo/.planning/config.yaml" <<'YAML'
context_window: 1000000
handoff:
  context_percent: 60
  context_tokens: 250000
YAML
claude_transcript "$workspace/big.jsonl" 260000
out="$(run_hook "$(payload_for PostToolUse sess-big "$workspace/big.jsonl")")"
contains "the absolute ceiling binds on a large window" "$out" "at or over the 250000-token limit"
# 600000 would be 60% of this window; a reading under the ceiling must not fire.
claude_transcript "$workspace/mid.jsonl" 240000
out="$(run_hook "$(payload_for PostToolUse sess-mid "$workspace/mid.jsonl")")"
check "under the ceiling stays silent on a large window" "$out" ""
cat > "$repo/.planning/config.yaml" <<'YAML'
context_window: 200000
handoff:
  context_percent: 60
  context_tokens: 250000
YAML

# --- Codex rollout transcripts are understood --------------------------------

codex_transcript "$workspace/codex.jsonl" 150000
out="$(run_hook "$(payload_for PostToolUse sess-codex "$workspace/codex.jsonl")")"
contains "a Codex rollout is measured" "$out" "150000"
check "a Codex session gets a handoff" \
  "$([[ -f "$handoffs/sess-codex.json" ]] && echo yes)" "yes"

# --- repeats debounce but keep the record current ----------------------------

emitted=0
for _ in 1 2 3 4; do
  out="$(run_hook "$(payload_for PostToolUse sess-high "$workspace/high.jsonl")")"
  [[ -n "$out" ]] && emitted=$((emitted + 1))
done
check "four repeats inside the debounce window stay silent" "$emitted" "0"
out="$(run_hook "$(payload_for PostToolUse sess-high "$workspace/high.jsonl")")"
contains "the fifth repeat warns again" "$out" "CONTEXT HANDOFF"
check "repeats do not duplicate the handoff" \
  "$(ls "$handoffs"/sess-high*.json | wc -l | tr -d ' ')" "1"

# --- unusable input fails open -----------------------------------------------

check "a missing transcript is silent" \
  "$(run_hook "$(payload_for PostToolUse sess-none "$workspace/absent.jsonl")")" ""
check "an empty payload is silent" "$(run_hook '{}')" ""
check "malformed JSON is silent" "$(run_hook 'not json at all')" ""
out="$(run_hook '{"hook_event_name":"PostToolUse","session_id":"../escape","cwd":"'"$repo"'","transcript_path":"'"$workspace/high.jsonl"'"}')"
check "a traversing session id is refused" "$out" ""
check "a traversing session id writes nothing" \
  "$(ls "$handoffs"/*escape* 2>/dev/null | wc -l | tr -d ' ')" "0"

# --- Stop clears state without writing a handoff -----------------------------

before="$(ls "$handoffs"/*.json | wc -l | tr -d ' ')"
run_hook "$(payload_for Stop sess-high "$workspace/high.jsonl")" >/dev/null
check "Stop leaves the handoff count unchanged" \
  "$(ls "$handoffs"/*.json | wc -l | tr -d ' ')" "$before"
check "Stop clears the debounce sentinel" \
  "$([[ -f "$handoffs/.state-sess-high.json" ]] && echo present || echo gone)" "gone"

# --- an executor that stopped early gets a handoff ---------------------------

mkdir -p "$repo/.planning/phases/03-thing"
printf '{"agent": "coder", "plan": ".planning/phases/03-thing/03-01-PLAN.md", "at": "now"}\n' \
  > "$handoffs/.active-sess-exit.jsonl"
run_hook "$(payload_for SubagentStop sess-exit "$workspace/high.jsonl")" >/dev/null
check "an executor with no SUMMARY produces a handoff" \
  "$([[ -f "$handoffs/sess-exit--03-01.json" ]] && echo yes)" "yes"
record="$(cat "$handoffs/sess-exit--03-01.json")"
contains "the exit handoff names the reason" "$record" '"reason": "incomplete-exit"'
contains "the exit handoff names the plan" "$record" '03-01-PLAN.md'
contains "the exit handoff names the SUMMARY to read" "$record" '03-01-SUMMARY.md'
contains "the exit handoff names the agent" "$record" '"agent": "coder"'
check "a consumed dispatch leaves the active stack" \
  "$([[ -f "$handoffs/.active-sess-exit.jsonl" ]] && echo present || echo gone)" "gone"

# --- a completed executor produces nothing -----------------------------------

printf -- '---\nstatus: complete\n---\n' > "$repo/.planning/phases/03-thing/03-02-SUMMARY.md"
printf '{"agent": "coder", "plan": ".planning/phases/03-thing/03-02-PLAN.md", "at": "now"}\n' \
  > "$handoffs/.active-sess-done.jsonl"
run_hook "$(payload_for SubagentStop sess-done "$workspace/high.jsonl")" >/dev/null
check "a complete SUMMARY produces no handoff" \
  "$(ls "$handoffs"/sess-done*.json 2>/dev/null | wc -l | tr -d ' ')" "0"
check "a complete dispatch still leaves the stack" \
  "$([[ -f "$handoffs/.active-sess-done.jsonl" ]] && echo present || echo gone)" "gone"

# --- a blocked SUMMARY is still unfinished work ------------------------------

printf -- '---\nstatus: blocked\n---\n' > "$repo/.planning/phases/03-thing/03-03-SUMMARY.md"
printf '{"agent": "coder", "plan": ".planning/phases/03-thing/03-03-PLAN.md", "at": "now"}\n' \
  > "$handoffs/.active-sess-blocked.jsonl"
run_hook "$(payload_for SubagentStop sess-blocked "$workspace/high.jsonl")" >/dev/null
check "a blocked SUMMARY produces a handoff" \
  "$([[ -f "$handoffs/sess-blocked--03-03.json" ]] && echo yes)" "yes"

# --- SubagentStop never emits an envelope ------------------------------------

printf '{"agent": "coder", "plan": ".planning/phases/03-thing/03-04-PLAN.md", "at": "now"}\n' \
  > "$handoffs/.active-sess-quiet.jsonl"
check "SubagentStop emits nothing on stdout" \
  "$(run_hook "$(payload_for SubagentStop sess-quiet "$workspace/high.jsonl")")" ""

# --- only one dispatch closes per stop ---------------------------------------

{
  printf '{"agent": "coder", "plan": ".planning/phases/03-thing/03-05-PLAN.md", "at": "now"}\n'
  printf '{"agent": "debugger", "plan": ".planning/phases/03-thing/03-06-PLAN.md", "at": "now"}\n'
} > "$handoffs/.active-sess-two.jsonl"
run_hook "$(payload_for SubagentStop sess-two "$workspace/high.jsonl")" >/dev/null
check "the first dispatch is handed off" \
  "$([[ -f "$handoffs/sess-two--03-05.json" ]] && echo yes)" "yes"
check "the second dispatch is not yet handed off" \
  "$([[ -f "$handoffs/sess-two--03-06.json" ]] && echo yes || echo no)" "no"
check "the second dispatch stays on the stack" \
  "$(grep -c '03-06-PLAN' "$handoffs/.active-sess-two.jsonl" 2>/dev/null || echo 0)" "1"
run_hook "$(payload_for SubagentStop sess-two "$workspace/high.jsonl")" >/dev/null
check "the second stop hands off the second dispatch" \
  "$([[ -f "$handoffs/sess-two--03-06.json" ]] && echo yes)" "yes"

# --- the dispatch guard records what it lets through -------------------------

dispatch='{"hook_event_name":"PreToolUse","session_id":"sess-guard","cwd":"'"$repo"'","tool_name":"Agent","tool_input":{"subagent_type":"coder","isolation":"worktree","prompt":"Execute .planning/phases/03-thing/03-09-PLAN.md now"}}'
set +e
( cd "$repo" && printf '%s' "$dispatch" | bash "$guard" >/dev/null 2>&1 )
status=$?
set -e
check "an isolated dispatch is still allowed" "$status" "0"
check "the guard records the dispatch" \
  "$([[ -f "$handoffs/.active-sess-guard.jsonl" ]] && echo yes)" "yes"
contains "the guard captured the plan path" \
  "$(cat "$handoffs/.active-sess-guard.jsonl" 2>/dev/null)" "03-09-PLAN.md"

# An unisolated dispatch is refused, and a refused dispatch never runs, so it
# must not leave an active entry behind for a stop that will never come.
blocked='{"hook_event_name":"PreToolUse","session_id":"sess-blockedguard","cwd":"'"$repo"'","tool_name":"Agent","tool_input":{"subagent_type":"coder","prompt":"Execute .planning/phases/03-thing/03-10-PLAN.md now"}}'
set +e
( cd "$repo" && printf '%s' "$blocked" | bash "$guard" >/dev/null 2>&1 )
status=$?
set -e
check "an unisolated dispatch is still blocked" "$status" "2"
check "a blocked dispatch records nothing" \
  "$([[ -f "$handoffs/.active-sess-blockedguard.jsonl" ]] && echo present || echo gone)" "gone"

# A read-only agent needs no worktree and no handoff.
readonly_dispatch='{"hook_event_name":"PreToolUse","session_id":"sess-ro","cwd":"'"$repo"'","tool_name":"Agent","tool_input":{"subagent_type":"researcher","prompt":"Research .planning/phases/03-thing/03-11-PLAN.md"}}'
set +e
( cd "$repo" && printf '%s' "$readonly_dispatch" | bash "$guard" >/dev/null 2>&1 )
status=$?
set -e
check "a read-only dispatch is allowed" "$status" "0"
check "a read-only dispatch records nothing" \
  "$([[ -f "$handoffs/.active-sess-ro.jsonl" ]] && echo present || echo gone)" "gone"


# --- Codex SubagentStop: identity comes from the payload ---------------------
#
# Codex never produces a PreToolUse dispatch, so the active stack is empty and
# every fact has to come from the stop payload plus the subagent's own
# transcript. These cases run with NO .active-* file on purpose.

codex_agent_transcript() { # <path> <plan-mention>
  printf '{"type":"message","role":"user","content":"Execute the plan at %s and report."}\n' "$2" > "$1"
}

codex_stop_payload() { # <session> <agent_type> <agent_transcript_path>
  printf '{"hook_event_name":"SubagentStop","session_id":"%s","cwd":"%s","transcript_path":"%s","turn_id":"t1","agent_id":"a1","agent_type":"%s","agent_transcript_path":"%s","stop_hook_active":false}' \
    "$1" "$repo" "$workspace/high.jsonl" "$2" "$3"
}

mkdir -p "$repo/.planning/phases/05-codex"

# An executor that stopped with no SUMMARY at all.
codex_agent_transcript "$workspace/cx-exit.jsonl" ".planning/phases/05-codex/05-01-PLAN.md"
run_hook "$(codex_stop_payload cx-exit coder "$workspace/cx-exit.jsonl")" >/dev/null
check "codex: an executor with no SUMMARY produces a handoff" \
  "$([[ -f "$handoffs/cx-exit--05-01.json" ]] && echo yes)" "yes"
record="$(cat "$handoffs/cx-exit--05-01.json" 2>/dev/null || true)"
contains "codex: the handoff names the reason" "$record" '"reason": "incomplete-exit"'
contains "codex: the handoff names the plan" "$record" '05-01-PLAN.md'
contains "codex: the handoff names the SUMMARY to read" "$record" '05-01-SUMMARY.md'
contains "codex: the handoff names the agent from agent_type" "$record" '"agent": "coder"'

# A finished plan is not handed off.
printf -- '---\nstatus: complete\n---\n' > "$repo/.planning/phases/05-codex/05-02-SUMMARY.md"
codex_agent_transcript "$workspace/cx-done.jsonl" ".planning/phases/05-codex/05-02-PLAN.md"
run_hook "$(codex_stop_payload cx-done coder "$workspace/cx-done.jsonl")" >/dev/null
check "codex: a complete SUMMARY produces no handoff" \
  "$(ls "$handoffs"/cx-done*.json 2>/dev/null | wc -l | tr -d ' ')" "0"

# blocked is unfinished, exactly as on Claude.
printf -- '---\nstatus: blocked\n---\n' > "$repo/.planning/phases/05-codex/05-03-SUMMARY.md"
codex_agent_transcript "$workspace/cx-blocked.jsonl" ".planning/phases/05-codex/05-03-PLAN.md"
run_hook "$(codex_stop_payload cx-blocked coder "$workspace/cx-blocked.jsonl")" >/dev/null
check "codex: a blocked SUMMARY produces a handoff" \
  "$([[ -f "$handoffs/cx-blocked--05-03.json" ]] && echo yes)" "yes"

# Every write-capable role is covered, and read-only roles are not.
for role in coder doc-writer debugger; do
  codex_agent_transcript "$workspace/cx-$role.jsonl" ".planning/phases/05-codex/05-04-PLAN.md"
  rm -f "$handoffs"/cx-role-$role*.json
  run_hook "$(codex_stop_payload "cx-role-$role" "$role" "$workspace/cx-$role.jsonl")" >/dev/null
  check "codex: write-capable $role is handed off" \
    "$([[ -f "$handoffs/cx-role-$role--05-04.json" ]] && echo yes)" "yes"
done
for role in researcher verifier code-reviewer doc-verifier codebase-mapper phase-checker integration-checker; do
  codex_agent_transcript "$workspace/cx-$role.jsonl" ".planning/phases/05-codex/05-05-PLAN.md"
  run_hook "$(codex_stop_payload "cx-role-$role" "$role" "$workspace/cx-$role.jsonl")" >/dev/null
  check "codex: read-only $role produces no handoff" \
    "$(ls "$handoffs"/cx-role-$role*.json 2>/dev/null | wc -l | tr -d ' ')" "0"
done

# An unreadable or absent agent transcript still produces an attributable
# handoff -- an unattributed one the orchestrator must inspect beats none.
run_hook "$(codex_stop_payload cx-noplan coder "$workspace/does-not-exist.jsonl")" >/dev/null
check "codex: a missing agent transcript still produces a handoff" \
  "$(ls "$handoffs"/cx-noplan*.json 2>/dev/null | wc -l | tr -d ' ')" "1"
contains "codex: the unattributed handoff still names the agent" \
  "$(cat "$handoffs"/cx-noplan*.json)" '"agent": "coder"'

# A Windows checkout path in the transcript resolves to the repo-relative plan.
BS=$(awk 'BEGIN{printf "%c", 92}')
ESC="$BS$BS"
printf '{"content":"run C:%swork%srepo%s.planning%sphases%s05-codex%s05-07-PLAN.md"}\n' "$ESC" "$ESC" "$ESC" "$ESC" "$ESC" "$ESC" > "$workspace/cx-win.jsonl"
run_hook "$(codex_stop_payload cx-win coder "$workspace/cx-win.jsonl")" >/dev/null
contains "codex: a Windows transcript path resolves repo-relative" \
  "$(cat "$handoffs/cx-win--05-07.json" 2>/dev/null || true)" \
  '".planning/phases/05-codex/05-07-PLAN.md"'

# Codex SubagentStop is silent on stdout, exactly as Claude's is.
codex_agent_transcript "$workspace/cx-quiet.jsonl" ".planning/phases/05-codex/05-08-PLAN.md"
check "codex: SubagentStop emits nothing on stdout" \
  "$(run_hook "$(codex_stop_payload cx-quiet coder "$workspace/cx-quiet.jsonl")")" ""

# --- the advisory envelope is identical on both hosts ------------------------
#
# Codex's PostToolUse accepts hookSpecificOutput.additionalContext just as
# Claude's does, so one emitted shape has to satisfy both.

codex_transcript "$workspace/cx-ctx.jsonl" 150000
out="$(run_hook "$(payload_for PostToolUse cx-ctx "$workspace/cx-ctx.jsonl")")"
contains "codex: the advisory uses the shared envelope" "$out" '"hookEventName": "PostToolUse"'
contains "codex: the advisory carries additionalContext" "$out" '"additionalContext"'
contains "codex: the advisory names the handoff path" "$out" '.planning/handoffs/cx-ctx.json'

# --- the root session's advisory covers every reader -------------------------
#
# With no agent identity, and no way to tell which host installed it, the hook
# cannot tell an orchestrator from a host that does not name its subagents, so
# the advisory has to be right for both -- and it must never stop the
# orchestrator: that is what stranded /execute-phase at 250k of a 1M window.

out="$(run_hook "$(payload_for PostToolUse sess-rootmsg "$workspace/high.jsonl")")"
contains "root: the advisory still tells a plan executor to block" "$out" "status: blocked"
contains "root: the advisory tells an orchestrator the limit is not its own" "$out" "does not apply to you"
contains "root: the advisory tells an orchestrator to keep going" "$out" "keep running the workflow"
lacks "root: the advisory never tells an orchestrator to stop dispatching" "$out" "dispatch nothing new"
lacks "root: the advisory never recommends continuing elsewhere" "$out" "recommend continuing"
contains "root: the advisory tells an artifact writer it is not blocked" "$out" "not a blocker"

# --- a Claude subagent is measured on its own transcript ---------------------
#
# Claude Code hands a subagent's hook the PARENT's transcript_path, plus
# agent_id and agent_type. The subagent's own transcript sits beside the
# parent's, at <parent without .jsonl>/subagents/agent-<id>.jsonl.

claude_transcript "$workspace/parent.jsonl" 130000
mkdir -p "$workspace/parent/subagents"

subagent_payload() { # <event> <session> <agent_id> <agent_type>
  printf '{"hook_event_name":"%s","session_id":"%s","cwd":"%s","transcript_path":"%s","agent_id":"%s","agent_type":"%s"}' \
    "$1" "$2" "$repo" "$workspace/parent.jsonl" "$3" "$4"
}

claude_transcript "$workspace/parent/subagents/agent-r1.jsonl" 30000
out="$(run_hook "$(subagent_payload PostToolUse sess-sub r1 researcher)")"
check "subagent: an over-limit parent does not stop a subagent under it" "$out" ""
check "subagent: the parent's occupancy writes no record for the subagent" \
  "$(ls "$handoffs"/sess-sub*.json 2>/dev/null | wc -l | tr -d ' ')" "0"

out="$(run_hook "$(subagent_payload PostToolUse sess-sub r-missing researcher)")"
check "subagent: a missing own transcript is silent, not the parent's reading" "$out" ""

claude_transcript "$workspace/parent/subagents/agent-r2.jsonl" 130000
out="$(run_hook "$(subagent_payload PostToolUse sess-sub r2 researcher)")"
contains "researcher: an over-limit subagent is advised" "$out" "CONTEXT HANDOFF"
contains "researcher: the advisory measures its own transcript" "$out" "130000 tokens"
contains "researcher: the advisory says the limit is not a blocker" "$out" "not a blocker"
contains "researcher: the advisory asks for a partial return" "$out" "RESEARCH PARTIAL"
contains "researcher: the advisory names where open questions go" "$out" "Not Yet Researched"
lacks "researcher: the advisory never asks for a SUMMARY" "$out" "SUMMARY.md"
contains "researcher: the advisory names the per-agent record" "$out" ".planning/handoffs/sess-sub--agent-r2.json"
record="$(cat "$handoffs/sess-sub--agent-r2.json" 2>/dev/null || true)"
contains "researcher: the record is keyed to the agent and names its role" "$record" '"agent": "researcher"'
check "researcher: the parent's record is not written by the subagent" \
  "$([[ -f "$handoffs/sess-sub.json" ]] && echo present || echo absent)" "absent"

# The root session's debounce does not swallow a subagent's first warning.
run_hook "$(payload_for PostToolUse sess-deb "$workspace/parent.jsonl")" >/dev/null
claude_transcript "$workspace/parent/subagents/agent-d1.jsonl" 130000
out="$(run_hook "$(subagent_payload PostToolUse sess-deb d1 researcher)")"
contains "subagent: the root's debounce does not silence a subagent" "$out" "CONTEXT HANDOFF"

for pair in coder:"status: blocked" codebase-mapper:"marked partial" \
            phase-preparer:"marked partial" verifier:"name the scope you did not reach" \
            plugin:x:researcher:"RESEARCH PARTIAL"; do
  role="${pair%:*}"
  want="${pair##*:}"
  id="role-${role//:/-}"
  claude_transcript "$workspace/parent/subagents/agent-$id.jsonl" 130000
  out="$(run_hook "$(subagent_payload PostToolUse sess-roles "$id" "$role")")"
  contains "role: $role is advised for what it produces" "$out" "$want"
done

# Stop clears the per-agent sentinels as well as the root's.
run_hook "$(payload_for Stop sess-roles "$workspace/parent.jsonl")" >/dev/null
check "Stop clears per-agent debounce sentinels" \
  "$(ls "$handoffs"/.state-sess-roles* 2>/dev/null | wc -l | tr -d ' ')" "0"

# --- a Claude SubagentStop is attributed from the subagent's transcript ------

mkdir -p "$repo/.planning/phases/06-claude"
printf '{"type":"user","message":{"role":"user","content":"Execute .planning/phases/06-claude/06-01-PLAN.md"}}\n' \
  > "$workspace/parent/subagents/agent-c1.jsonl"
printf '{"agent": "coder", "plan": ".planning/phases/06-claude/06-01-PLAN.md", "at": "now"}\n' \
  > "$handoffs/.active-sess-cstop.jsonl"
run_hook "$(subagent_payload SubagentStop sess-cstop c1 coder)" >/dev/null
check "claude stop: an unfinished coder is attributed to its plan" \
  "$([[ -f "$handoffs/sess-cstop--06-01.json" ]] && echo yes)" "yes"
check "claude stop: the closed dispatch leaves the active stack" \
  "$([[ -f "$handoffs/.active-sess-cstop.jsonl" ]] && echo present || echo gone)" "gone"

printf -- '---\nstatus: complete\n---\n' > "$repo/.planning/phases/06-claude/06-02-SUMMARY.md"
printf '{"type":"user","message":{"role":"user","content":"Execute .planning/phases/06-claude/06-02-PLAN.md"}}\n' \
  > "$workspace/parent/subagents/agent-c2.jsonl"
run_hook "$(subagent_payload SubagentStop sess-cdone c2 coder)" >/dev/null
check "claude stop: a finished coder leaves no handoff" \
  "$(ls "$handoffs"/sess-cdone*.json 2>/dev/null | wc -l | tr -d ' ')" "0"

# No readable subagent transcript, but the dispatch was recorded: the stack
# still attributes the stop rather than leaving it anonymous.
printf '{"agent": "coder", "plan": ".planning/phases/06-claude/06-03-PLAN.md", "at": "now"}\n' \
  > "$handoffs/.active-sess-cfall.jsonl"
run_hook "$(subagent_payload SubagentStop sess-cfall c-missing coder)" >/dev/null
check "claude stop: an unreadable transcript falls back to the stack" \
  "$([[ -f "$handoffs/sess-cfall--06-03.json" ]] && echo yes)" "yes"

run_hook "$(subagent_payload SubagentStop sess-cres r2 researcher)" >/dev/null
check "claude stop: a researcher stop writes no exit record" \
  "$(ls "$handoffs"/sess-cres*.json 2>/dev/null | wc -l | tr -d ' ')" "0"

# --- the agent's digest ------------------------------------------------------
#
# The hook records where an attempt stopped; the agent adds what it learned
# with `handoff.write` into the same record. Without that digest the
# continuation re-reads the whole assignment.

claude_transcript "$workspace/parent/subagents/agent-g1.jsonl" 130000
out="$(run_hook "$(subagent_payload PostToolUse sess-dig g1 researcher)")"
contains "digest: the advisory asks for the digest by the record's own id" \
  "$out" "handoff.write sess-dig--agent-g1"
contains "digest: the advisory names the files already read" "$out" "--files-read"
contains "digest: the advisory names the findings" "$out" "--findings"
contains "digest: the advisory forbids reading to write it" "$out" "do not read anything to write it"

# Stand in for `handoff.write`: add digest fields to the hook's record, then let
# the hook refresh it on a later tool use. The digest must survive the refresh.
add_digest() { # <record>
  "$HANDOFF_PY" -c '
import json, sys
path = sys.argv[1]
record = json.load(open(path, encoding="utf-8"))
record.update({"findings": ["auth lives in api/auth.py:12"], "files_read": ["api/auth.py"],
               "remaining": ["SAML"]})
open(path, "w", encoding="utf-8").write(json.dumps(record))
' "$(handoff_native_path "$1")"
}
add_digest "$handoffs/sess-dig--agent-g1.json"
claude_transcript "$workspace/parent/subagents/agent-g1.jsonl" 140000
run_hook "$(subagent_payload PostToolUse sess-dig g1 researcher)" >/dev/null
record="$(cat "$handoffs/sess-dig--agent-g1.json" 2>/dev/null || true)"
contains "digest: a later refresh keeps the agent's findings" "$record" "api/auth.py:12"
contains "digest: a later refresh keeps the files already read" "$record" '"files_read"'
contains "digest: a later refresh still updates occupancy" "$record" '"used_tokens": 140000'

# A coder that crossed the limit and then stopped unfinished has one record,
# not two: its exit folds into the threshold record that carries its digest.
claude_transcript "$workspace/parent/subagents/agent-k1.jsonl" 130000
run_hook "$(subagent_payload PostToolUse sess-fold k1 coder)" >/dev/null
add_digest "$handoffs/sess-fold--agent-k1.json"
printf '{"type":"user","message":{"role":"user","content":"Execute .planning/phases/06-claude/06-04-PLAN.md"}}\n' \
  > "$workspace/parent/subagents/agent-k1.jsonl"
run_hook "$(subagent_payload SubagentStop sess-fold k1 coder)" >/dev/null
record="$(cat "$handoffs/sess-fold--agent-k1.json" 2>/dev/null || true)"
check "fold: an exit after the limit writes no second record" \
  "$(ls "$handoffs"/sess-fold*.json 2>/dev/null | wc -l | tr -d ' ')" "1"
contains "fold: the record now says the agent exited unfinished" "$record" '"reason": "incomplete-exit"'
contains "fold: the record gains the plan from the exit" "$record" "06-04-PLAN.md"
contains "fold: the digest survives the exit" "$record" "api/auth.py:12"
contains "fold: the occupancy survives the exit" "$record" '"used_tokens": 130000'

# --- on Codex the orchestrator is recognised by its transcript ---------------
#
# Codex gives a tool-use hook no agent identity: a subagent's call carries the
# parent's session id and nothing naming the agent. SessionStart records the
# orchestrator's own transcript, and a tool use reporting that transcript is
# the orchestrator -- silent. Any other transcript is a subagent's own.

codex_transcript "$workspace/cx-root.jsonl" 150000
out="$(run_hook "$(payload_for SessionStart cx-orch "$workspace/cx-root.jsonl")")"
check "codex: SessionStart prints nothing into the model's context" "$out" ""
check "codex: SessionStart records the orchestrator's transcript" \
  "$(cat "$handoffs/.root-cx-orch.json" 2>/dev/null | tr -d '\r')" "$workspace/cx-root.jsonl"

out="$(run_hook "$(payload_for PostToolUse cx-orch "$workspace/cx-root.jsonl")")"
check "codex: the orchestrator over the limit gets no advisory" "$out" ""
check "codex: the orchestrator over the limit gets no record" \
  "$([[ -f "$handoffs/cx-orch.json" ]] && echo present || echo absent)" "absent"

codex_transcript "$workspace/rollout-sub-1.jsonl" 150000
out="$(run_hook "$(payload_for PostToolUse cx-orch "$workspace/rollout-sub-1.jsonl")")"
contains "codex: a subagent over the limit is still advised" "$out" "CONTEXT HANDOFF"
contains "codex: a subagent's record is keyed to its own transcript" \
  "$out" ".planning/handoffs/cx-orch--agent-rollout-sub-1.json"
check "codex: the subagent's record exists under its own key" \
  "$([[ -f "$handoffs/cx-orch--agent-rollout-sub-1.json" ]] && echo yes || echo no)" "yes"

codex_transcript "$workspace/rollout-sub-2.jsonl" 30000
out="$(run_hook "$(payload_for PostToolUse cx-orch "$workspace/rollout-sub-2.jsonl")")"
check "codex: a subagent under the limit is measured on its own transcript" "$out" ""

run_hook "$(payload_for Stop cx-orch "$workspace/cx-root.jsonl")" >/dev/null
check "codex: Stop ends a turn and keeps the orchestrator's record" \
  "$([[ -f "$handoffs/.root-cx-orch.json" ]] && echo kept || echo gone)" "kept"

# --- on Claude the orchestrator is never measured ----------------------------
#
# Claude Code names the calling agent on every hook fired inside a subagent, so
# a tool use with no agent identity is the orchestrating session. It gets no
# advisory and no record: the limit is for subagents.

claude_hooks="$workspace/claude-install/.claude/hooks"
mkdir -p "$claude_hooks"
cp -R "$script_dir/." "$claude_hooks/"
run_claude_hook() {
  ( cd "$repo" && printf '%s' "$1" | env -u CLAUDE_PROJECT_DIR bash "$claude_hooks/context-handoff.sh" 2>/dev/null )
}

out="$(run_claude_hook "$(payload_for PostToolUse sess-corch "$workspace/high.jsonl")")"
check "claude: the orchestrator over the limit gets no advisory" "$out" ""
check "claude: the orchestrator over the limit gets no record" \
  "$([[ -f "$handoffs/sess-corch.json" ]] && echo present || echo absent)" "absent"

out="$( cd "$repo" && printf '%s' "$(payload_for PostToolUse sess-cenv "$workspace/high.jsonl")" \
  | CLAUDE_PROJECT_DIR="$repo" bash "$hook" 2>/dev/null )"
check "claude: CLAUDE_PROJECT_DIR alone marks the host" "$out" ""

claude_transcript "$workspace/parent/subagents/agent-cs1.jsonl" 130000
out="$(run_claude_hook "$(subagent_payload PostToolUse sess-csub cs1 coder)")"
contains "claude: a subagent over the limit is still advised" "$out" "CONTEXT HANDOFF"
contains "claude: a subagent still gets its role's instruction" "$out" "status: blocked"

printf '%s passed, %s failed\n' "$passed" "$failed"
[[ "$failed" -eq 0 ]]
