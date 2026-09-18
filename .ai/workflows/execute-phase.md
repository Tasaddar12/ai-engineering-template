<!-- workflow
step: execute
agent-roles: orchestrator, coder, code-reviewer
produces: {NN}-{MM}-SUMMARY.md, commits, roadmap plan ticks
consumes: {NN}-{MM}-PLAN.md, CONTEXT.md, STATE.md
-->

<purpose>
Execute a phase's plans. Group them into dependency waves, dispatch a coder per
plan, review the resulting code, confirm the phase goal was achieved, then tick
the roadmap.

The orchestrator routes and integrates. It does not write the implementation.
</purpose>

<required_reading>
@~/.ai/references/universal-anti-patterns.md
@~/.ai/references/methods/checkpoints.md
@~/.ai/references/methods/gates.md
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- coder — executes plan tasks, commits atomically, writes SUMMARY.md
- code-reviewer — reviews changed source for bugs and security issues
- doc-writer — writes documentation a plan declares
- verifier — verifies phase goal achievement
- debugger — investigates a failure the coder could not resolve
</available_agent_types>

<authority>
**Executing a phase changes the codebase.** Do not start execution unless the
user has explicitly asked for this phase to be implemented. Phase creation,
discussion, planning and readiness do not grant implementation permission.
</authority>

<process>

<step name="parse_args">
Recognised flags:
- `--plan {id}` — execute only this plan
- `--wave {n}` — execute only this wave
- `--sequential` — run one plan at a time even when a wave allows parallelism
- `--resume` — continue a phase whose execution stopped partway
- `--no-review` — skip the code review gate (requires the user to say so)
</step>

<step name="initialize">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.execute-phase "${PHASE}")
```

Parse: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `has_context`, `has_plans`, `plan_count`, `summary_count`, `plan_index`,
`verification`, `checks_configured`, `models`, `agents_installed`,
`missing_agents`, `context_window`, `commit_docs`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

If `phase_found` is false, or `has_plans` is false:

```
Phase {N} has no plans to execute.
Run `/plan-phase {N}` first.
```

Exit.

If `agents_installed` is false, report `missing_agents` and stop.

Display: `► EXECUTE PHASE {phase_number}: {phase_name}`
</step>

<step name="safe_resume_gate">
If `summary_count` is greater than 0 and `--resume` was not passed, execution
already ran at least partly:

```
Phase {N} has {summary_count} of {plan_count} plans already executed.

Re-running from the start would re-execute completed work.
```

Use AskUserQuestion (header: "Partial execution"; options: "Resume the remaining
plans" / "Re-run everything" / "Cancel"). Default to resuming.

On resume, the plans to run are those in `plan_index` whose `summary` is null.
</step>

<step name="check_blocking_antipatterns">
**MANDATORY.** Look for `.continue-here.md` in the phase directory:

```bash
ls ${phase_dir}/.continue-here.md 2>/dev/null || true
```

If it exists, parse its "Critical Anti-Patterns" table for `severity: blocking`
rows. For each, answer inline before continuing:

1. What is this anti-pattern?
2. How did it manifest?
3. What structural mechanism — not acknowledgment — prevents it recurring?

If a blocking row cannot be answered from the file, stop and ask the user.
</step>

<step name="preflight">
Confirm the working tree is in a fit state to execute:

```bash
git status --porcelain
git rev-parse --abbrev-ref HEAD
```

If the tree has uncommitted changes outside `.planning/`, report them and ask
whether to continue. Executing over dirty state makes the phase's commits
ambiguous.

If the current branch is the repository's default branch, say so and offer to
branch before executing:

```bash
phase_run query git.base-branch
```
</step>

<step name="discover_and_group_plans">
```bash
phase_run query phase-plan-index "${phase_number}"
```

For each plan, read its frontmatter `wave` and `depends_on`. Group into waves:

- Plans with no unmet dependencies form wave 1
- A plan enters a wave only once every id in its `depends_on` has a SUMMARY.md
- Plans that declare overlapping `files_modified` must NOT share a wave — put the
  later one in a following wave, whatever its declared wave says

Report the grouping before executing:

```
Execution plan for Phase {N}:
  Wave 1 (parallel): {01-01}, {01-02}
  Wave 2: {01-03} (depends on 01-01)
```

A dependency cycle is a planning defect: report it and stop rather than picking
an order.
</step>

<step name="execute_waves">
Execute waves in order. Within a wave, dispatch every plan **in a single message
with multiple Agent calls** so they run concurrently, unless `--sequential` was
passed or the wave has one plan.

For each plan:

```
Agent(
  prompt="
<execution_context>
**Phase:** {phase_number} — {phase_name}
**Plan:** {phase_dir}/{plan_file}

<required_reading>
- {phase_dir}/{plan_file} (your plan — the authority on what to change)
- {phase_dir}/{padded_phase}-CONTEXT.md (locked decisions)
- every file named in your plan's `read_first` fields
</required_reading>
${context_window >= 500000 ? `
**Prior wave summaries:** {paths of SUMMARY.md files from earlier waves in this phase}
` : ''}

**Project instructions:** read ./CLAUDE.md or ./AGENTS.md if either exists.
**Project skills:** check `.agents/skills/` or `.claude/skills/` — read the SKILL.md
files and follow their rules.
</execution_context>

<constraints>
- Execute ONLY the tasks in your plan. New capability is out of scope: record it
  in your summary as a deferred item rather than building it
- Read every `read_first` file before editing; do not act on assumptions about
  current state
- Touch only the paths your plan declares in `files_modified`
- Commit each completed task atomically with a descriptive message
- Run each task's `<verify>` command and record its actual output. A task whose
  verify command was not run is not complete
- If the plan is wrong, stop and report it. Do not improvise a different change
</constraints>

<output>
Write: {phase_dir}/{plan_id}-SUMMARY.md with:
- frontmatter: status (complete|blocked), commits, files changed, requirements covered
- what was built, and the evidence each acceptance criterion was met
- anything deferred, and why
Return: ## EXECUTION COMPLETE with status and the summary path
</output>
",
  subagent_type="coder",
  model="{models['coder']}",
  description="Execute {plan_id}"
)
```

> **ORCHESTRATOR RULE**: after dispatching a wave, stop working on this task. Do
> not read files, edit code or run tests while coders are active — you would
> conflict with their edits. Wait for every agent in the wave to return before
> starting the next one.

After each wave, verify on disk rather than trusting the returns:

```bash
phase_run query phase-plan-index "${phase_number}"
git log --oneline -n 20
```

A plan whose agent reported "complete" with no SUMMARY.md, or with no commits, did
not complete. Treat it as blocked and say so.
</step>

<step name="checkpoint_handling">
A plan may return `blocked` with a checkpoint — a decision it cannot make alone.

For each checkpoint:
1. Present what the coder found and the options it identified
2. Ask the user to decide (AskUserQuestion, or plain text in text mode)
3. Record the decision: `phase_run query state.add-decision "{decision}"`
4. Re-dispatch that plan with the decision added to its execution context

A checkpoint is not a failure. Do not resolve one by guessing so the wave can
finish.
</step>

<step name="run_checks">
If `checks_configured` is true, run the project's configured checks once per
wave, after the wave's agents have all returned:

```bash
phase_run query verification.run-checks
```

Report any failing check with its command and output tail. A failing check blocks
the next wave: hand it to the responsible coder, or to the debugger when the
cause is unclear.
</step>

<step name="aggregate_results">
Read each SUMMARY.md and build the phase picture:

- Which plans completed, which are blocked
- Which requirement ids are covered across all summaries
- What was deferred
- Which files changed overall

Report any phase requirement id that no summary claims. That is a gap, whether or
not every plan reported complete.
</step>

<step name="code_review_gate">
**Skip only when `--no-review` was passed and the user asked for it.**

```
Agent(
  prompt="
Review the source changes made by Phase {phase_number}.

**Changed files:** {aggregate files_modified across summaries}
**Plans:** {plan paths}
**Diff base:** {commit before the first wave}

Review the changed source for correctness bugs, security issues and code quality
problems. Judge the code as it now stands, not the summaries' claims about it.

Return:
## CODE REVIEW
Findings: <numbered, each with file:line, severity (critical|warning), and why it is wrong>
",
  subagent_type="code-reviewer",
  model="{models['code-reviewer']}",
  description="Review phase {phase_number} changes"
)
```

**Critical findings block completion.** Dispatch a coder to fix them, then
re-review. Warnings are recorded in the phase summary for the verifier to weigh;
they do not block.
</step>

<step name="verify_phase_goal">
Execution completing is not the same as the phase delivering its goal. Hand
verification to `/verify-work`:

```
Phase {N} executed: {completed}/{plan_count} plans.

`/verify-work {N}`
```

When the user asked for the phase to be carried through, read `workflows/verify-work.md`
and execute it now rather than only printing the command.
</step>

<step name="update_roadmap">
Tick each completed plan through the runtime so the roadmap, the progress table
and STATE.md counters all move together:

```bash
phase_run query roadmap.update-plan-progress "${plan_id}"
```

Only tick a plan that has a SUMMARY.md with `status: complete`. When every plan
in the phase is ticked, the runtime marks the phase complete in the overview
checklist automatically.
</step>

<step name="close_phase_todos">
Any todo folded into this phase during discussion is now resolved. Move each one
and refresh the state section:

```bash
phase_run query todo.complete "${todo_file}"
phase_run query state.sync-todos
```

Leave todos that were reviewed but not folded in exactly where they are.
</step>

<step name="update_state">
```bash
phase_run query state.update-progress
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} executed (${completed}/${plan_count} plans)" \
  --resume-file "${phase_dir}/${padded_phase}-VERIFICATION.md"
phase_run query commit "chore(${padded_phase}): record phase execution" \
  --files .planning/ROADMAP.md .planning/STATE.md .planning/todos
```
</step>

<step name="completion">
```
Phase {phase_number} executed.

Plans: {completed}/{plan_count} complete{blocked ? ", {blocked} blocked" : ""}
Requirements covered: {ids}
Checks: {passed | failed with detail | not configured}
Code review: {clean | N warnings recorded | N critical fixed}
{deferred ? "Deferred: {items}" : ""}

---

## ▶ Next Up

`/clear` then:

`/verify-work {phase_number}`

---
```
</step>

</process>

<anti_patterns>
- Don't implement anything yourself — dispatch coders and integrate their work
- Don't work while a wave is running; you will conflict with the agents' edits
- Don't accept "complete" without a SUMMARY.md and real commits
- Don't resolve a checkpoint by guessing so the wave can finish
- Don't put plans with overlapping `files_modified` in the same wave
- Don't tick a roadmap plan that has no complete summary
- Don't skip the code review gate on your own initiative
- Don't treat execution completing as the phase being verified
</anti_patterns>

<success_criteria>
- [ ] Implementation authority confirmed before execution started
- [ ] Blocking anti-patterns answered before any work
- [ ] Plans grouped into waves respecting dependencies and file overlap
- [ ] Each plan executed by a coder subagent, verified on disk
- [ ] Checkpoints escalated to the user, not guessed
- [ ] Configured checks run per wave and passing
- [ ] Requirement coverage aggregated, with gaps reported
- [ ] Code review run; critical findings fixed and re-reviewed
- [ ] Roadmap plans ticked only for complete summaries
- [ ] Folded todos closed, STATE.md updated, work committed
</success_criteria>
