<!-- workflow
step: new-milestone
agent-roles: orchestrator, researcher
produces: ROADMAP.md milestone section and phases, REQUIREMENTS.md scope, STATE.md position
consumes: PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md
-->

<purpose>
Start a new milestone cycle on an existing project. Loads project context,
gathers the milestone goal, optionally runs research, defines scoped requirements
with REQ ids, breaks the milestone into phases, and commits the result.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- researcher — researches technical approaches and options
- codebase-mapper — maps existing code before scoping new work
</available_agent_types>

<model_selection>
Model and effort are injected inline at dispatch, never read from an agent's
frontmatter. Resolve both from the runtime and pass them on the `Agent(...)`
call:

```bash
phase_run query resolve-model <agent> --raw
phase_run query resolve-effort <agent> --raw
```

A result of `inherit` means the project set no override — **omit that argument
entirely** and let the host choose. Pass `model` only when resolution returned a
concrete model id, and `effort` only when it returned one of `low`, `medium`,
`high`, `xhigh` or `max`. The two resolve independently: a role can carry an
effort and no model, or the reverse. The `models` and `efforts` maps in each
init bundle carry the same resolved values for every agent that workflow
dispatches.
</model_selection>

<process>

<step name="load_context">
Parse `$ARGUMENTS`: the remaining text is the milestone name, e.g.
`/new-milestone "v1.1 Key hardening"`.

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.new-milestone)
```

Extract: `current_milestone`, `milestones`, `phase_count`, `open_phases`,
`next_phase_number`, `project_exists`, `roadmap_exists`, `models`, `efforts`,
`commit_docs`, `text_mode`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

**Text mode** (`text_mode` true, or `--text`): replace every AskUserQuestion with
a plain-text numbered list and ask the user to type a number.

If `project_exists` or `roadmap_exists` is false:

```
ERROR: No project found (.planning/PROJECT.md, .planning/ROADMAP.md).
Run onboarding first — a milestone groups phases of an existing project.
```

Exit.

Read PROJECT.md and REQUIREMENTS.md for the project's vision, constraints and
existing requirement ids.
</step>

<step name="check_open_work">
If `open_phases` is non-empty, the current milestone has unfinished phases:

```
The current milestone ({current_milestone}) still has open phases: {open_phases}

Starting a new milestone now leaves them open.
```

Use AskUserQuestion (header: "Open work"; options: "Close the current milestone
first" / "Start the new milestone anyway" / "Cancel"). On the first option,
stop and recommend `/complete-milestone`.
</step>

<step name="gather_goal">
Establish what this milestone delivers. Ask the user directly — this is vision,
not something to infer from the codebase:

- What does this milestone deliver that the last one did not?
- What is explicitly out of scope for it?
- What has to be true for it to ship?

Keep asking until the goal is concrete enough to break into phases. A milestone
goal that cannot be decomposed is not yet a goal.
</step>

<step name="research">
**Optional — only when the approach is genuinely unknown.** Skip when the work is
well understood; research here is for technical unknowns, not for reassurance.

```
Agent(
  prompt="
Research the technical approach for this milestone.

**Milestone:** ${MILESTONE_NAME}
**Goal:** ${MILESTONE_GOAL}
**Project:** read ${paths.project} and ${paths.requirements}

Investigate implementation approaches, library options and known pitfalls that
would change how this milestone is broken into phases. Report options with
trade-offs, not a single recommendation.

Return: ## RESEARCH COMPLETE with findings and their implications for scoping.
",
  subagent_type="researcher",
  ${models['researcher'] === 'inherit' ? '' : `model="${models['researcher']}",`}
  ${efforts['researcher'] === 'inherit' ? '' : `effort="${efforts['researcher']}",`}
  description="Research milestone ${MILESTONE_NAME}"
)
```

> **ORCHESTRATOR RULE**: after calling Agent(), stop working on this task until
> the subagent returns. Do not read more files or start scoping in parallel.
</step>

<step name="define_requirements">
Add requirements for this milestone to REQUIREMENTS.md, continuing the existing
REQ id sequence — never restarting it. Each requirement is an observable
capability, not a task.

Record explicitly what is out of scope for the milestone. The out-of-scope list
is what makes the scope guard enforceable later.
</step>

<step name="create_milestone">
**Delegate the milestone declaration to the runtime:**

```bash
RESULT=$(phase_run query milestone.create "${MILESTONE_NAME}" --goal "${MILESTONE_GOAL}")
```

The runtime adds the milestone to the roadmap's `## Milestones` list marked in
progress, demotes any previously in-progress milestone to planned, and opens the
milestone's section above `## Progress`.

Extract: `name`, `slug`, `goal`, `status`.
</step>

<step name="break_into_phases">
Break the milestone into phases with the user. Each phase delivers something
coherent and independently verifiable; 3–8 phases is the usual range.

For each phase, in order, add it through the runtime so numbering, directories,
the checklist and the Progress table all stay consistent:

```bash
phase_run query phase.add "${PHASE_TITLE}" --goal "${PHASE_GOAL}" --requirements "${REQ_IDS}"
```

Phase numbering continues from the previous milestone — it never restarts at 1.
The runtime derives the next number; do not pass one.

Do not create plans here. Planning is per phase, and happens in `/plan-phase`.
</step>

<step name="update_state">
Point STATE.md at the first phase of the new milestone and record the change:

```bash
phase_run query state.begin-phase "${FIRST_PHASE}" --status "Ready to plan"
phase_run query state.add-roadmap-evolution "Milestone ${MILESTONE_NAME} started: phases ${FIRST_PHASE}-${LAST_PHASE}"
```
</step>

<step name="git_commit">
```bash
phase_run query commit "docs(roadmap): start milestone ${MILESTONE_NAME}" \
  --files .planning/ROADMAP.md .planning/REQUIREMENTS.md .planning/PROJECT.md .planning/STATE.md
```
</step>

<step name="completion">
```
Milestone started: {name}

Goal: {goal}
Phases: {first}-{last} ({count} phases)
Requirements: {REQ ids added}

Roadmap updated: .planning/ROADMAP.md

---

## ▶ Next Up

**Phase {first}: {name}** — {goal}

`/clear` then:

`/discuss-phase {first}`

---
```
</step>

</process>

<anti_patterns>
- Don't restart phase numbering at 1 — numbering is continuous across milestones
- Don't create plans here; `/plan-phase` owns them
- Don't hand-edit ROADMAP.md — `milestone.create` and `phase.add` own its structure
- Don't research by default; research a genuine unknown or skip the step
- Don't start a milestone over open phases without the user saying so
</anti_patterns>

<success_criteria>
- [ ] Milestone goal established with the user, concrete enough to decompose
- [ ] Requirements added with continuing REQ ids and an explicit out-of-scope list
- [ ] Milestone declared through `milestone.create`
- [ ] Phases added through `phase.add`, numbering continuous
- [ ] STATE.md pointed at the first phase
- [ ] Everything committed
- [ ] User knows the next step
</success_criteria>
