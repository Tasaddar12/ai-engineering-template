<!-- workflow
step: progress
agent-roles: orchestrator
produces: status report, routing recommendation
consumes: PROJECT.md, ROADMAP.md, STATE.md, todos, quick tasks
-->

<purpose>
Report where the project stands — recent work, current position, decisions,
blockers and what is ahead — then route to the next action. Situational awareness
before continuing work.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="init_context">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
PROGRESS=$(phase_run query init.progress)
```

Extract: `totals`, `bar`, `phases`, `next_phase`, `incomplete_phase`,
`milestones`, `state`, `pending_todos`, `open_quick`, `response_language`,
`roadmap_exists`, `project_exists`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code and file paths stay in English.

If `roadmap_exists` is false:

```
No roadmap yet (.planning/ROADMAP.md).

Run onboarding to set up PROJECT.md, REQUIREMENTS.md and ROADMAP.md, or add a
first phase with `/phase "<description>"`.
```

Exit.
</step>

<step name="load">
Read `.planning/PROJECT.md` for the project name and core value.

> ⚠ Context authority: PROJECT.md, STATE.md and ROADMAP.md are the authoritative
> sources for project name, milestone, current phase and routing. A CLAUDE.md or
> AGENTS.md project blurb is a secondary aid that may be stale — do NOT use it as
> the source for any field in this report.
</step>

<step name="recent">
Summarise recent work from the most recent phase SUMMARY.md files. Read at most
the three newest and take one line each — do not read every summary in the
project.

```bash
ls -t .planning/phases/*/*-SUMMARY.md 2>/dev/null | head -3
```
</step>

<step name="record_health">
```bash
phase_run query planning.validate
```

Include the Record Health section below only when `warning_count` is above zero.
Report the findings as they are; do not fix them here.
</step>

<step name="report">
Present the report:

````
# {Project Name}

**Progress:** {bar} {totals.percent}% ({totals.plans_complete}/{totals.plans} plans)
**Milestone:** {milestones.current or "none declared"}

## Recent Work
- [Phase X, Plan Y]: {one line from the summary}
- [Phase X, Plan Z]: {one line from the summary}

## Current Position
Phase {state.position.Phase}
Plan {state.position.Plan}
Status: {state.position.Status}
CONTEXT: {✓ when the current phase has_context, otherwise -}

## Key Decisions Made
- {each entry from state.decisions}

## Blockers/Concerns
- {each entry from state.blockers}

## Pending Todos
- {pending_todos} pending — `/capture --list` to review
(omit this section when the count is 0)

## Open Quick Tasks
- {open_quick} open — `/quick` to resume
(omit this section when the count is 0)

## Record Health
- {each warning as "{record}: {message}"}
(omit this section entirely when warning_count is 0)

## What's Next
{next_phase.number}: {next_phase.name} — {next_phase.goal}
````

Name the verb that resolves each warning when you present it.
</step>

<step name="route">
**Route 0 — resume an incomplete phase (invariant).**

Before any current-phase routing, check `incomplete_phase` from the init JSON.
The runtime sets it to the lowest-numbered phase whose plan files outnumber its
summary files. This catches the case where STATE.md's position advanced past a
phase that still has unfinished execution — common after a session died
mid-execution. Without this guard, routing would inspect the wrong phase and skip
the unfinished work.

Skip this check when `--no-resume` or `--force` is in `$ARGUMENTS`.

**If `incomplete_phase` is set:**

```
---

## ▶ Next Up — Resuming incomplete Phase {incomplete_phase}

`/clear` then:

`/execute-phase {incomplete_phase}`

(plans without summaries detected; `--no-resume` skips this check and routes by
current position instead)
```

Stop here.

**Route 1 — the current phase needs context.** `has_context` false →
`/discuss-phase {number}`.

**Route 2 — the current phase has context but no plans.** → `/plan-phase {number}`.

**Route 3 — plans exist and are unexecuted.** → `/execute-phase {number}`.

**Route 4 — all plans executed, no verification.** → `/verify-work {number}`.

**Route 5 — the phase is verified and complete.** → the next open phase, or
`/complete-milestone` when the milestone's phases are all complete.

Present the chosen route as:

```
---

## ▶ Next Up

**Phase {N}: {name}** — {goal}

`/clear` then:

`/{command} {N}`

---
```
</step>

<step name="edge_cases">
- **No phases in the roadmap:** recommend `/phase "<description>"`.
- **Every phase complete:** report the project as current and recommend
  `/complete-milestone` if a milestone is open, otherwise say there is no
  outstanding work.
- **STATE.md missing:** report progress from the roadmap alone and note that
  position tracking is unavailable until STATE.md exists.
- **Position disagrees with the roadmap:** trust the roadmap for plan counts and
  say so explicitly rather than silently reconciling.
</step>

</process>

<anti_patterns>
- Don't read every SUMMARY.md — three recent ones is the budget
- Don't recompute progress by hand; `init.progress` derives it from the roadmap
- Don't skip Route 0 — an advanced position is exactly when work gets lost
- Don't start the recommended work; this workflow reports and routes
</anti_patterns>

<success_criteria>
- [ ] Progress derived from the roadmap, not from prose claims
- [ ] Recent work, position, decisions and blockers reported
- [ ] Pending todos and open quick tasks surfaced when non-zero
- [ ] Incomplete-phase invariant checked before routing
- [ ] A single clear next action presented
</success_criteria>
