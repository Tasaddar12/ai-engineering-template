<purpose>

Interactive command center for managing a milestone from a single terminal. Shows a dashboard of all phases with visual status, dispatches discuss inline and runs plan/execute inline (backgrounded when dispatch-should-flatten returns false), and loops back to the dashboard after each action. Enables parallel phase work from one terminal.

</purpose>

<required_reading>

Read all files referenced by the invoking prompt's execution_context before starting.

</required_reading>

<process>

<step name="initialize" priority="first">

## 1. Initialize

Bootstrap via manager init:

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
_ENGINEER_SHIM_NAME="engineer_run"; _ENGINEER_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; ENGINEER_TOOLS="${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}"; _engineer_at() { for _p; do if [ -f "$_p" ]; then ENGINEER_TOOLS="$_p"; return 0; fi; done; return 1; }; _engineer_id_ok() { case "$("$1" runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"engineer-runtime"'*'}') return 0;; *) return 1;; esac; }; _engineer_homes() { set -- "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; for _h; do _engineer_at "$_h/engineer/bin/${_ENGINEER_SHIM_NAME}" && return 0; done; return 1; }; if _engineer_at "${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.claude/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.codex/engineer/bin/${_ENGINEER_SHIM_NAME}"; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif _engineer_homes; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif unset -f engineer_run; _G="$(command -v engineer_run)"; [ -n "$_G" ] && _engineer_id_ok "$_G"; then ENGINEER_TOOLS="$_G"; engineer_run() { "$ENGINEER_TOOLS" "$@"; }; else echo "ERROR: engineer_run not found at $ENGINEER_TOOLS and no identity-proving engineer_run is on PATH. Run: python -I bin/install.py --source <local-source> --ref <pinned-ref> --target <project-root> --host claude --local" >&2; exit 1; fi; ENGINEER_IDENTITY_STATUS=unverified; _engineer_id_ok engineer_run && ENGINEER_IDENTITY_STATUS=ok; export ENGINEER_IDENTITY_STATUS; [ "$ENGINEER_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$ENGINEER_TOOLS\" did not prove it is engineer-runtime - it is either a different package or an engineer-runtime older than the runtime-identity verb." >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${ENGINEER_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${ENGINEER_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
INIT=$(engineer_run query init.manager )
```

Parse JSON for: `milestone_version`, `milestone_name`, `phase_count`, `completed_count`, `in_progress_count`, `phases`, `recommended_actions`, `all_complete`, `waiting_signal`, `manager_flags`, `response_language`, and the optional trio `queued_milestone_version`, `queued_milestone_name`, `queued_phases` (added in SDK fix `2495-2496-2497` — may be absent on older SDK versions, treat missing as empty).

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated. Subagent dispatches (discuss/plan/execute) stay in English at the prompt level; include `response_language` in their spawn args per the workflow being dispatched.

`manager_flags` contains per-step passthrough flags from config:
- `manager_flags.discuss` — appended to `/discuss-phase` args (e.g. `"--auto --analyze"`)
- `manager_flags.plan` — appended to plan agent init command
- `manager_flags.execute` — appended to execute agent init command

These are empty strings by default. Set via: `engineer_run query config-set manager.flags.discuss "--auto --analyze"`

**If error:** Display the error message and exit.

Resolve the dispatch capability **once per manager session**, after successful initialization and before displaying or dispatching any action:

```bash
if FLATTEN=$(engineer_run query dispatch-should-flatten --raw); then
  case "$FLATTEN" in
    true) PLAN_EXECUTE_MODE=inline ;;
    false) PLAN_EXECUTE_MODE=background ;;
    *) printf 'ERROR: invalid dispatch-should-flatten result: %s (expected true or false)\n' "$FLATTEN" >&2; exit 1 ;;
  esac
else
  echo "ERROR: dispatch-should-flatten capability query failed; manager stopped." >&2
  exit 1
fi
```

The planned API contract is an explicit boolean: `true` selects complete plan/execute pipelines inline; `false` selects background orchestrators capable of nesting those pipelines' workers. Preserve the captured `FLATTEN` and `PLAN_EXECUTE_MODE` for all dashboard refreshes, compound actions and individual plan/execute handlers. Do not re-query or substitute a default after an error. Both routes retain the complete Skill pipelines, worker isolation and quality gates.

Display startup banner:

```
### Engineer ► MANAGER

 {milestone_version} — {milestone_name}
 {phase_count} phases · {completed_count} complete

 ✓ Discuss → inline    ◆ Plan/Execute → {PLAN_EXECUTE_MODE}
 Dashboard auto-refreshes when background work is active.

---
```

Proceed to dashboard step.

</step>

<step name="dashboard">

## 2. Dashboard (Refresh Point)

**Every time this step is reached**, re-read state from disk to pick up changes from background agents:

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
INIT=$(engineer_run query init.manager )
```

Parse the full JSON. Build the dashboard display. Show `◆ Plan/Execute → {PLAN_EXECUTE_MODE}` using the session's captured mode; state refresh does not resolve dispatch capability again.

Build dashboard from JSON. Symbols: `✓` done, `◆` active, `○` pending, `·` queued. Progress bar: 20-char `█░`.

**Status mapping** (disk_status → D P E Status):

- `complete` → `✓ ✓ ✓` `✓ Complete`
- `executed` → `✓ ✓ ◆` `◆ Verification required`
- `partial` → `✓ ✓ ◆` `◆ Executing...`
- `planned` → `✓ ✓ ○` `○ Ready to execute`
- `discussed` → `✓ ○ ·` `○ Ready to plan`
- `researched` → `◆ · ·` `○ Ready to plan`
- `empty`/`no_directory` + `is_next_to_discuss` → `○ · ·` `○ Ready to discuss`
- `empty`/`no_directory` otherwise → `· · ·` `· Up next`
- If `is_active`, replace status icon with `◆` and append `(active)`

If any `is_active` phases, show: `◆ Background: {action} Phase {N}, ...` above grid.

Use `display_name` (not `name`) for the Phase column — it's pre-truncated to 20 chars with `…` if clipped. Pad all phase names to the same width for alignment.

Use `deps_display` from init JSON for the Deps column — shows which phases this phase depends on (e.g. `1,3`) or `—` for none.

Example output:

```
### Engineer ► DASHBOARD
 ████████████░░░░░░░░ 60%  (3/5 phases)
 ◆ Background: Planning Phase 4
 | # | Phase                | Deps | D | P | E | Status              |
 |---|----------------------|------|---|---|---|---------------------|
 | 1 | Foundation           | —    | ✓ | ✓ | ✓ | ✓ Complete          |
 | 2 | API Layer            | 1    | ✓ | ✓ | ◆ | ◆ Executing (active)|
 | 3 | Auth System          | 1    | ✓ | ✓ | ○ | ○ Ready to execute  |
 | 4 | Dashboard UI & Set…  | 1,2  | ✓ | ◆ | · | ◆ Planning (active) |
 | 5 | Notifications        | —    | ○ | · | · | ○ Ready to discuss  |
 | 6 | Polish & Final Mail… | 1-5  | · | · | · | · Up next           |
```

**Queued section (next milestone preview):**

If `queued_phases` is present and non-empty, render a compact preview of the next milestone's phases directly below the main table. This surfaces upcoming work without cluttering the active-milestone grid. Skip this section entirely when `queued_phases` is empty or missing (e.g. the active milestone is the last one in the roadmap).

Use `queued_milestone_version` and `queued_milestone_name` for the header. Phases render without D/P/E columns since they aren't discussed yet — just number, name (pre-truncated `display_name`), dependencies (`deps_display`), and a fixed `· Queued` status. Phase-name padding should match the active-table column width for visual alignment.

Example:

```
### ◆ Queued — {queued_milestone_version} {queued_milestone_name}  ({queued_phases.length} phases)
 | # | Phase                | Deps | Status       |
 |---|----------------------|------|--------------|
 | 31| Email Logs           | —    | · Queued     |
 | 32| Today's Sheets       | 31   | · Queued     |
 | 33| Resend Backfill      | 31   | · Queued     |
 | 34| Business Day Audit   | 31   | · Queued     |
```

Queued phases are NOT eligible for the Continue action menu — they live in a future milestone and must wait for the current milestone to ship. The preview exists purely for situational awareness.

**Recommendations section:**

If `all_complete` is true:

```
### MILESTONE COMPLETE

All {phase_count} phases verified complete. Ready for final steps:
  → /verify-work — run acceptance testing
  → /complete-milestone — archive and wrap up
```

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.
Ask user via AskUserQuestion:
- **question:** "All phases complete. What next?"
- **options:** "Verify work" / "Complete milestone" / "Exit manager"

Handle responses:
- "Verify work": `Skill(skill="verify-work")` then loop to dashboard.
- "Complete milestone": `Skill(skill="complete-milestone")` then exit.
- "Exit manager": Go to exit step.

**If NOT all_complete**, build compound options from `recommended_actions`:

**Compound option logic:** Group plan/execute actions together, then verification and the single discuss action when present. Label every plan/execute action with the captured `{PLAN_EXECUTE_MODE}`; verification and discuss always run inline. One option may dispatch multiple actions.

**Building options:**

1. Collect all plan/execute actions (execute and plan recommendations) — there can be multiple of each.
2. Collect verification actions (`verify`) for implementation-complete phases whose canonical verification has not passed.
3. Collect the inline action (discuss recommendation, if any — there will be at most one since discuss is sequential).
4. Build compound options:

   **If there are ANY recommended actions:**
   Create ONE primary "Continue" option that dispatches ALL of them together:
   - Label: `"Continue"` — always this exact word
   - Below the label, list every action that will happen. Enumerate ALL recommended actions — do not cap or truncate:
     ```
     Continue:
       → Execute Phase 32 ({PLAN_EXECUTE_MODE})
       → Plan Phase 34 ({PLAN_EXECUTE_MODE})
       → Verify Phase 33
       → Discuss Phase 35 (inline)
     ```
   - For `FLATTEN=false`, dispatch all plan/execute background orchestrators first, then run verification actions and discuss inline. For `FLATTEN=true`, complete plan/execute inline in listed order, then verification and discuss.
   - If there is no discuss, refresh the dashboard after these dispatches and inline actions.

   **Important:** The Continue option must include EVERY action from `recommended_actions` — not just 2. If there are 3 actions, list 3. If there are 5, list 5.

4. Always add:
   - `"Refresh dashboard"`
   - `"Exit manager"`

Display recommendations compactly:

```
### ▶ Next Steps

Continue:
  → Execute Phase 32 ({PLAN_EXECUTE_MODE})
  → Plan Phase 34 ({PLAN_EXECUTE_MODE})
  → Discuss Phase 35 (inline)
```

**Auto-refresh:** If background agents are running (`is_active` is true for any phase), set a 60-second auto-refresh cycle. After presenting the action menu, if no user input is received within 60 seconds, automatically refresh the dashboard. This interval is configurable via `manager_refresh_interval` in Engineer config (default: 60 seconds, set to 0 to disable).

Present via AskUserQuestion:
- **question:** "What would you like to do?"
- **options:** (compound options as built above + refresh + exit, AskUserQuestion auto-adds "Other")

**On "Other" (free text):** Parse intent — if it mentions a phase number and action, dispatch accordingly. If unclear, display available actions and loop to action_menu.

Proceed to handle_action step with the selected action.

</step>

<step name="handle_action">

## 4. Handle Action

### Refresh Dashboard

Loop back to dashboard step.

### Exit Manager

Go to exit step.

### Compound Action (resolved plan/execute mode + inline verification/discuss)

Use the session's captured `FLATTEN` and the Plan Phase N / Execute Phase N handlers below:

- **If `FLATTEN=false`:** Dispatch all selected plan/execute background orchestrators first, then run verification actions inline, then discuss inline. The background pipelines continue during verification/discussion. In a compound action, defer each handler's dashboard return until all selected actions have been dispatched; do not wait for background completion before dispatching the remaining actions.
- **If `FLATTEN=true`:** Complete the selected plan/execute pipelines inline in listed order, then verification actions, then discuss. Defer each handler's dashboard return until the compound action finishes. There is no overlap.

Inline verification:

For each verification recommendation, dispatch by the recommended action's `command`:
- If `command` contains `execute-phase`, run `Skill(skill="execute-phase", args="{PHASE_NUM} {manager_flags.execute}")`.
- If `command` contains `verify-work`, run `Skill(skill="verify-work", args="{PHASE_NUM}")`.
- If `command` is missing or unrecognized, stop and show the recommendation row instead of guessing.

Inline discuss:

```
Skill(skill="discuss-phase", args="{PHASE_NUM} {manager_flags.discuss}")
```

After discuss completes, loop back to dashboard step.

### Discuss Phase N

Discussion is interactive — needs user input. Run inline with any configured flags:

```
Skill(skill="discuss-phase", args="{PHASE_NUM} {manager_flags.discuss}")
```

After discuss completes, loop back to dashboard step.

### Plan Phase N

Planning uses the session's captured `FLATTEN`; do not query again. Both routes invoke the complete Skill pipeline, including its worker isolation and quality gates.

**If `FLATTEN` is `false`:** Spawn a background agent that delegates to the Skill pipeline with any configured flags:

```
Agent(
  description="Plan phase {N}: {phase_name}",
  run_in_background=true,
  prompt="You are running the Engineer plan-phase workflow for phase {N} of the project.

Working directory: {cwd}
Phase: {N} — {phase_name}
Goal: {goal}
Manager flags: {manager_flags.plan}

Run the plan-phase Skill with any configured manager flags:
Skill(skill=\"plan-phase\", args=\"{N} --auto {manager_flags.plan}\")

This delegates to the full plan-phase pipeline including local patches, research, plan-checker, and all quality gates.

Important: You are running in the background. Do NOT use AskUserQuestion — make autonomous decisions based on project context. If you hit a blocker, write it to STATE.md as a blocker and stop. Do NOT silently work around permission or file access errors — let them fail so the manager can surface them with resolution hints. Do NOT use --no-verify on git commits."
)
```

> **ORCHESTRATOR RULE — BACKGROUND DISPATCH**: After calling Agent() above with `run_in_background=true`, do NOT do any planning work for this phase independently. Return to the dashboard immediately and wait for the background agent to report back. Only resume planning-related work when the subagent result is available. Use the dashboard loop while waiting; do not duplicate the background pipeline. For a compound action, dispatch the remaining selected actions before returning to the dashboard.

Display:

```
◆ Spawning planner for Phase {N}: {phase_name}... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Loop back to dashboard step.

**Otherwise (`FLATTEN` is `true` — run inline):** Run plan inline so the plan-checker and quality gates actually run — do NOT wrap it in `Agent(run_in_background=true, …)`:

```
Skill(skill="plan-phase", args="{N} --auto {manager_flags.plan}")
```

Display while it runs:

```
◆ Planning Phase {N}: {phase_name}... (runs inline so the plan-checker runs — the dashboard resumes when it returns, ~1–5 min; expected, not a freeze)
```

Then loop back to dashboard step.

### Execute Phase N

Execution uses the session's captured `FLATTEN`; do not query again. Both routes invoke the complete Skill pipeline, including its worker isolation and quality gates.

**If `FLATTEN` is `false`:** Spawn a background agent that delegates to the Skill pipeline with any configured flags:

```
Agent(
  description="Execute phase {N}: {phase_name}",
  run_in_background=true,
  prompt="You are running the Engineer execute-phase workflow for phase {N} of the project.

Working directory: {cwd}
Phase: {N} — {phase_name}
Goal: {goal}
Manager flags: {manager_flags.execute}

Run the execute-phase Skill with any configured manager flags:
Skill(skill=\"execute-phase\", args=\"{N} {manager_flags.execute}\")

This delegates to the full execute-phase pipeline including local patches, branching, worker worktree isolation, wave-based execution, verification, and all quality gates.

Important: You are running in the background. Do NOT use AskUserQuestion — make autonomous decisions. Do NOT use --no-verify on git commits — let pre-commit hooks run normally. If you hit a permission error, file lock, or any access issue, do NOT work around it — let it fail and write the error to STATE.md as a blocker so the manager can surface it with resolution guidance."
)
```

> **ORCHESTRATOR RULE — BACKGROUND DISPATCH**: After calling Agent() above with `run_in_background=true`, do NOT do any execution work for this phase independently. Return to the dashboard immediately and wait for the background agent to report back. Only resume execution-related work when the subagent result is available. Use the dashboard loop while waiting; do not duplicate the background pipeline. For a compound action, dispatch the remaining selected actions before returning to the dashboard.

Display:

```
◆ Spawning executor for Phase {N}: {phase_name}... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Loop back to dashboard step.

**Otherwise (`FLATTEN` is `true` — run inline):** Run execute inline so worktree isolation and the verifier actually run — do NOT wrap it in `Agent(run_in_background=true, …)`:

```
Skill(skill="execute-phase", args="{N} {manager_flags.execute}")
```

Display while it runs:

```
◆ Executing Phase {N}: {phase_name}... (runs inline so worktree isolation and verification run — the dashboard resumes when it returns; expected, not a freeze)
```

Then loop back to dashboard step.

</step>

<step name="background_completion">

## 5. Background Agent Completion

When notified that a background agent completed:

1. Read the result message from the agent.
2. Display a brief notification:

```
✓ {description}
  {brief summary from agent result}
```

3. Loop back to dashboard step.

**If the agent reported an error or blocker:**

Classify the error:

**Permission / tool access error** (e.g. tool not allowed, permission denied, sandbox restriction):
- Parse the error to identify which tool or command was blocked.
- Display the error clearly, then offer to fix it:
  - **question:** "Phase {N} failed — permission denied for `{tool_or_command}`. Want me to add it to settings.local.json so it's allowed?"
  - **options:** "Add permission and retry" / "Run this phase inline instead" / "Skip and continue"
  - "Add permission and retry": Use `Skill(skill="update-config")` to add the permission to `settings.local.json`, then re-spawn the background agent. Loop to dashboard.
  - "Run this phase inline instead": Dispatch the same action inline via the appropriate Skill — use `Skill(skill="plan-phase", args="{N} --auto {manager_flags.plan}")` if the failed action was planning, or `Skill(skill="execute-phase", args="{N} {manager_flags.execute}")` if the failed action was execution. Loop to dashboard after.
  - "Skip and continue": Loop to dashboard (phase stays in current state).

**Other errors** (git lock, file conflict, logic error, etc.):
- Display the error, then offer options via AskUserQuestion:
  - **question:** "Background agent for Phase {N} encountered an issue: {error}. What next?"
  - **options:** "Retry" / "Run inline instead" / "Skip and continue" / "View details"
  - "Retry": Re-spawn the same background agent. Loop to dashboard.
  - "Run inline instead": Dispatch the action inline via the appropriate Skill — use `Skill(skill="plan-phase", args="{N} --auto {manager_flags.plan}")` if the failed action was planning, or `Skill(skill="execute-phase", args="{N} {manager_flags.execute}")` if the failed action was execution. Loop to dashboard after.
  - "Skip and continue": Loop to dashboard (phase stays in current state).
  - "View details": Read STATE.md blockers section, display, then re-present options.

</step>

<step name="exit">

## 6. Exit

Display final status with progress bar:

```
### Engineer ► SESSION END

 {milestone_version} — {milestone_name}
 {PROGRESS_BAR} {progress_pct}%  ({completed_count}/{phase_count} phases)

 Resume anytime: /manager

---
```

**Note:** Any background agents still running will continue to completion. Their results will be visible on next `/manager` or `/progress` invocation.

</step>

</process>

<success_criteria>
- [ ] Dashboard displays all phases with correct status indicators (D/P/E/V columns)
- [ ] Progress bar shows accurate completion percentage
- [ ] Dependency resolution: blocked phases show which deps are missing
- [ ] Recommendations prioritize: execute > plan > discuss
- [ ] Discuss phases run inline via Skill() — interactive questions work
- [ ] Plan phases follow the captured capability: complete pipeline inline if true, background orchestrator if false — dashboard resumes when complete
- [ ] Execute phases follow the captured capability: complete pipeline inline if true, background orchestrator if false — dashboard resumes when complete
- [ ] Dashboard refreshes pick up changes from background agents via disk state
- [ ] Background agent completion triggers notification and dashboard refresh
- [ ] Background agent errors present retry/skip options
- [ ] All-complete state offers verify-work and complete-milestone
- [ ] Exit shows final status with resume instructions
- [ ] "Other" free-text input parsed for phase number and action
- [ ] Manager loop continues until user exits or milestone completes
- [ ] Queued section renders when `queued_phases` is non-empty; skipped when absent or empty
</success_criteria>
