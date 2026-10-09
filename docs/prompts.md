# Workflow prompt cookbook

These prompts are source-checked against repository revision
`6e3280a06b680547972fe9def3240f872fb842dd`; they have not been runtime-tested.
Replace every `<placeholder>` with a real value. The prompts describe the
artifacts to request, not a guarantee that a workflow will pass its checks.

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
