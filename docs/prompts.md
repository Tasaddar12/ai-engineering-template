# Workflow prompt cookbook

Existing prompts are source-checked against repository revision
`6e3280a06b680547972fe9def3240f872fb842dd`; the milestone discussion recipe
below is source-checked against `4822dcfad8fa1fe80ec28e74bdb5cb6381b17561`.
None have been runtime-tested. Replace every `<placeholder>` with a real value.
The prompts describe the artifacts to request, not a guarantee that a workflow
will pass its checks.

## Plan several phases

**Purpose:** Coordinate planning across phases whose dependencies are known.

**Prerequisites:** Phase discussion is complete and locked decisions are in each
phase's `CONTEXT.md`; the project and repository are available. The host must
support isolated worktrees for parallel preparation.

**Prompt:**

```text
Plan phases <phase IDs> with one coordinator. Inspect dependencies and locked
CONTEXT decisions. Create or adopt each phase session one at a time. Parallelize
phase-specific research and preparation in separate worktrees. Give each
preparer exclusive ownership of its phase plans. Serialize commits and reconcile
ROADMAP/STATE through the coordinator. Independently check every phase and
recheck downstream assumptions against delivered prerequisites. Do not execute
or ship.
```

`/plan-phase` accepts one phase, so invoke it separately for each phase; this
prompt coordinates those invocations. Session setup is sequential because
`.git/ai-phase/sessions.json` uses an unlocked read-modify-write. Plan
downstream phases as provisional until their prerequisites are delivered and
their assumptions are checked again. Planning never authorizes execution.

**Expected result:** Phase-specific plan files, with dependencies and ownership
recorded for review; downstream assumptions may need revision after prerequisites
land.

**Sources:** [plan-phase command](../.ai/commands/plan-phase.md),
[planning workflow](../.ai/workflows/plan-phase.md),
[session registry](../.ai/runtime/lib/worktrees.py),
[execution gate](../.ai/RULES.md#phase-authority).

## Define a milestone objective

**Purpose:** Start a milestone on an adopted project with a concrete, bounded
outcome.

**Prerequisites:** The project is adopted and repository records are available;
current milestone and unfinished phase state are known.

**Prompt:**

```text
/new-milestone "<milestone name>"
Objective: <observable outcomes this milestone should deliver>.
Out of scope: <explicit exclusions>.
Shipping criteria: <measurable conditions that must be true to ship>.
Use these boundaries to establish requirements and a coherent phase outline.
Stop after milestone setup; do not start /plan-phase or /execute-phase.
```

The command takes a milestone name. Supply the objective and boundaries as
ordinary prompt prose; do not add `--goal` or `--auto` flags. The workflow
establishes requirements and phases, so this prompt stops before phase planning
or execution.

**Expected result:** A milestone outline and scoped requirements in the project
records, subject to the workflow's checks and user decisions.

**Sources:** [new-milestone command](../.ai/commands/new-milestone.md),
[milestone workflow](../.ai/workflows/new-milestone.md).

## Discuss a phase

**Purpose:** Resolve implementation decisions that researchers and planners need
before planning a phase.

**Prerequisites:** The phase exists; project, requirements, state, and relevant
prior context records are available.

**Prompt:**

```text
/discuss-phase <phase ID>
Use prior project and phase context, inspect the phase, and raise only unresolved
implementation decisions that affect its scope or acceptance. Explore my selected
questions until the decisions are clear. Record durable project decisions in
PROJECT.md and phase decisions in CONTEXT.md. Keep unresolved questions explicit;
do not plan or implement the phase.
```

**Expected result:** A phase `CONTEXT.md` with recorded decisions and open
questions; durable decisions may also update `PROJECT.md`.

**Sources:** [discuss-phase command](../.ai/commands/discuss-phase.md),
[discussion skill](../.agents/skills/discuss-phase/SKILL.md),
[phase discussion rules](../.ai/RULES.md#phase-authority).

## Discuss unfinished phases in a milestone

**Purpose:** Gather phase-specific discussion proposals concurrently, then
surface cross-phase conflicts and decisions together for human resolution.

**Prerequisites:** The milestone, its unfinished phases, project requirements,
locked decisions, and relevant phase contexts are available at one source
revision. The host can run concurrent phase-specific agents. If isolated phase
sessions are needed, create or adopt them sequentially before dispatch; the
shared session registry uses an unlocked read-modify-write.

**Prompt:**

```text
Use one coordinator to discuss every unfinished phase in milestone <milestone
ID or name>. First enumerate all unfinished phase IDs and inspect the approved
requirements, locked decisions, phase contexts, and dependencies at source
revision <revision>. For each phase, give one discussion agent a bounded,
phase-specific assignment with that revision and only its relevant requirements,
locked decisions, and dependency context. Run agents concurrently within the
available slots. Agents must return read-only proposals: likely decisions,
supporting sources, unresolved questions, and assumptions; they must not write
PROJECT, ROADMAP, STATE, requirements, or phase context records. Do not let
agents make concurrent changes to those shared records or settle conflicts.

Wait for every agent before reconciling. Check each proposal against governing
requirements and locked decisions. Keep downstream assumptions provisional
until prerequisites are confirmed. Auto-decide only when approved requirements,
locked decisions, templates, or established conventions determine a compatible
choice, or for a reversible local implementation detail that does not change
product behavior, public interfaces or data contracts, architecture boundaries,
security, privacy, access, persistent data, paid services, or scope. Never
overwrite a locked decision, manufacture approval, or auto-resolve a contradiction.
Consolidate unresolved or conflicting decisions and cross-phase contracts into
one deduplicated human question list; include affected phase IDs, concrete
options, a recommendation, and consequences. Group the questions instead of
interrupting one at a time. Return one report with (1) auto-decisions and their
phase IDs, rationale, and sources, (2) the deduplicated human decision list, and
(3) unresolved dependency assumptions and blocked scope. Discuss only; do not
plan or execute. Use the runtime for any later authorized record changes.
```

**Expected result:** One consolidated report of supported local decisions,
questions needing human resolution, and provisional dependencies. The report is
discussion output, not a planning or execution authorization.

**Sources:** [discuss-phase command](../.ai/commands/discuss-phase.md),
[discussion skill](../.agents/skills/discuss-phase/SKILL.md),
[discussion workflow](../.ai/workflows/discuss-phase.md),
[phase authority and decision rules](../.ai/RULES.md#phase-authority),
[worktree session guidance](../.ai/references/worktree-sessions.md),
[session registry implementation](../.ai/runtime/lib/worktrees.py).

## Read-only progress check

**Purpose:** Get the current project position and one recommended next command
without advancing the workflow.

**Prerequisites:** Project records, recent phase summaries, and any pending task
records are available to inspect.

**Prompt:**

```text
/progress
Report progress from the roadmap and recent summaries. Include current position,
decisions, blockers, pending todos and quick tasks, record health, and the
incomplete-phase check. Recommend one next command, but do not run it.
```

**Expected result:** A status report and one recommendation. `/progress` reports;
`/next` decides and proceeds.

**Sources:** [progress command](../.ai/commands/progress.md),
[command overview](../.ai/commands/README.md#the-lifecycle).

## Future prompt ideas

This section is a tracking template only. Entries are proposals, not supported
commands. Mark evidence as source-checked or runtime-tested only after doing that
check; do not infer runtime support from source alone.

```text
Idea / purpose:
Candidate prompt:
Prerequisites:
Expected result (intended artifacts):
Source / check evidence:
Status: proposed | source-checked | runtime-tested
```
