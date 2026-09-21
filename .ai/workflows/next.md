<!-- workflow
step: next
agent-roles: orchestrator
produces: routing decision
consumes: ROADMAP.md, STATE.md, phase artifacts
-->

<purpose>
Detect the project's current state and advance to the next logical step. Reads
the roadmap and phase artifacts to determine the discuss → plan → execute →
verify → complete progression, then runs the step it selected.

`/progress` reports and recommends. `/next` decides and proceeds.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="detect_state">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
PROGRESS=$(phase_run query init.progress)
```

Extract: `phases`, `next_phase`, `incomplete_phase`, `totals`, `state`,
`milestones`, `roadmap_exists`, `response_language`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`.

If `roadmap_exists` is false, stop and recommend onboarding or `/phase`.
</step>

<step name="safety_gates">
These gates stop automatic advancement. Each can be overridden with `--force`,
and the override must be the user's explicit instruction, not an inference.

1. **Uncommitted changes in planning records.** `git status --porcelain .planning`
   non-empty → report the dirty paths and stop. Advancing over uncommitted
   planning state loses decisions.
2. **A blocker recorded in STATE.md.** `state.blockers` non-empty → show them and
   ask whether they are resolved before advancing.
3. **Implementation authority.** `/next` may advance through discussion,
   planning and verification on its own. It must NOT start executing a phase
   unless the user has explicitly asked for that phase to be implemented.
   Reaching the execute step means presenting the command, not running it.
</step>

<step name="resume_incomplete_phase">
If `incomplete_phase` is set, that phase has plan files without matching
summaries — execution stopped partway. Route there before anything else:

```
Phase {incomplete_phase} has unfinished execution (plans without summaries).

`/execute-phase {incomplete_phase}`
```

Skip this check only with `--no-resume` or `--force`.
</step>

<step name="prior_phase_completeness">
Before advancing into a new phase, confirm the previous phase actually finished:
its plans all have summaries, and it has a verification report if the project
verifies phases. An unverified predecessor is a finding, not a formality — say so
and let the user decide whether to proceed.
</step>

<step name="determine_next_action">
Take the lowest-numbered phase that is not complete (`next_phase`), load its
artifact state and select:

| Phase state | Next action |
|-------------|-------------|
| No CONTEXT.md | `/discuss-phase {N}` |
| CONTEXT.md, no PLAN files | `/plan-phase {N}` |
| PLAN files, missing summaries | `/execute-phase {N}` |
| All plans summarised, no VERIFICATION.md | `/verify-work {N}` |
| Verified, plans unticked in the roadmap | `phase.complete {N}`, then re-run |
| Phase complete, later phases open | advance to the next open phase |
| Every phase in the milestone complete | `/complete-milestone` |
| Every phase complete, no milestone open | report the project as current |

```bash
phase_run query init.phase-op "${next_phase}"
```

Use `has_context`, `has_plans`, `plan_count`, `summary_count` and
`has_verification` from that bundle rather than inspecting the directory by hand.
</step>

<step name="show_and_execute">
Announce the decision, then act on it:

```
## ▶ Next: {action}

**Phase {N}: {name}** — {goal}
Reason: {which artifact state selected this}
```

- For discuss, plan, verify and milestone steps: read the corresponding workflow
  and execute it end to end.
- For the execute step: present the command and stop, unless the user has
  explicitly authorised implementing this phase in this session.

If a `--dry-run` flag is present, report the decision and stop without executing.
</step>

</process>

<anti_patterns>
- Don't advance past uncommitted planning changes
- Don't start implementation on your own initiative; authorisation is explicit
- Don't skip the incomplete-phase check — that is where work gets silently dropped
- Don't decide from STATE.md's position alone; phase artifacts on disk are the evidence
</anti_patterns>

<success_criteria>
- [ ] Project state detected from roadmap and phase artifacts
- [ ] Safety gates evaluated before advancing
- [ ] Incomplete execution resumed ahead of new work
- [ ] The selected action, and the evidence for it, stated plainly
- [ ] The step executed, or presented when it needs authorisation
</success_criteria>
