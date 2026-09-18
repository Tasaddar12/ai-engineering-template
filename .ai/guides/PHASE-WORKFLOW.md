# Project and phase workflow

The workflow turns a project outcome into checked, documented implementation.
Project records live in `.planning/`; reusable instructions and tools live in
`.ai/`. An orchestrator carries the request through the user's authorized
boundary, spawning fresh agents for bounded assignments.

| Reference | Owns |
|---|---|
| [RULES](../RULES.md) | Authority, work boundaries and completion policy |
| [Truth map](../truth-map.md) | Each fact's authoritative record |
| [Runtime guide](../runtime/README.md) | The verb interface every workflow calls |
| [Template contract](../runtime/TEMPLATE-CONTRACT.md) | How the complete templates meet the runtime |
| [Template guide](ARTIFACT-GUIDE.md) | Artifact selection, producers, consumers, lifecycle |
| [Feature guide](WORKFLOW-FEATURES.md) | Capability inventory, safeguards and limits |

## How a command becomes work

```
command (commands/) ── the entry point; names a workflow, changes nothing
  └─ workflow (workflows/) ── the procedure: what to load, whom to spawn,
                               what to ask, which runtime verbs to call
       ├─ runtime (runtime/phase.py) ── every planning-record read and write
       └─ agent (agents/) ── a bounded role, spawned with its own context
```

The command file is a thin router: it declares the tools the work needs and names
its workflow. The workflow holds the steps. Anything that changes a planning
record — phase numbering, the roadmap checklist, the progress table, STATE.md's
derived counters, todos, quick tasks, milestones — goes through a runtime verb,
because the runtime owns the structure of those files.

Skills under `.agents/skills/` mirror the commands one-for-one, so a host that
discovers skills behaves the same as one that registers slash commands.

## 1. Onboard a new or existing project

`/onboard` is the only workflow that creates the records everything else reads.

| Step | New project | Existing project | Saved result |
|---|---|---|---|
| Inspect the baseline | Note the starter files and available checks | Spawn `codebase-mapper` to trace entry points, data flow, tests and conventions | `.planning/codebase/` maps |
| Establish intent | Question until the vision is concrete | Confirm purpose against the actual product | `.planning/PROJECT.md` |
| Identify outcomes | Record needed capabilities as REQ ids | Record desired changes and confirmed gaps | `.planning/REQUIREMENTS.md` |
| Order phases | Group outcomes into coherent deliverables | Respect existing interfaces and real dependencies | `.planning/ROADMAP.md` |
| Configure execution | Set the project's real checks | Run the real commands and record the baseline | `.planning/config.yaml` |

Questioning follows threads rather than walking a checklist; see
[questioning](../references/questioning.md). A record still containing `CHANGEME`
or bracketed placeholders was copied, not filled.

**Configure `verification.commands`.** Without the project's real checks, every
phase is verified by reading alone, and the verification report has to say so.

## 2. Shape the work

| Command | Effect |
|---|---|
| `/phase "<description>" --goal "<goal>"` | Append the next integer phase at the end of the milestone |
| `/phase --insert {N} "<description>"` | Insert urgent work as a decimal phase (2.1, 2.2) without renumbering |
| `/phase --remove {N}` | Remove a future, unstarted phase and renumber later ones |
| `/phase --edit {N}` | Change a phase's title, goal, dependencies or requirements in place |
| `/new-milestone "<name>"` | Open a milestone and break it into phases |

Phase numbering is continuous and never restarts across milestones. Integer
phases are planned work; decimal phases are urgent insertions, marked
`(INSERTED)`. The runtime allocates every number — do not choose one.

## 3. Take a phase through the loop

### Discuss — `/discuss-phase {N}`

Identifies the gray areas that would change the result, lets the user pick which
to discuss, and records the outcome in `NN-CONTEXT.md`. Decisions recorded here
are locked: research and planning act on them rather than re-opening them.

The phase boundary comes from ROADMAP.md and is fixed. Discussion clarifies *how*
to implement what is scoped, never *whether* to add capabilities — anything else
becomes a deferred idea or a todo.

Pending todos are cross-referenced here, so an idea captured weeks ago gets folded
into the phase it belongs to instead of being lost.

### Plan — `/plan-phase {N}`

Researches the approach where it is genuinely unknown, then spawns the
`phase-preparer` to write `NN-MM-PLAN.md` files: tasks with `read_first`,
`acceptance_criteria` and a `verify` command paired with the failure signal that
would reveal it doing nothing. The `phase-checker` then asks goal-backward whether
executing exactly those plans would deliver the phase.

Revisions are capped at three rounds; after that the outstanding findings go to
the user rather than being approved to end the loop.

### Execute — `/execute-phase {N}`

Groups plans into waves by dependency *and* by declared file overlap, then spawns a
`coder` per plan — concurrently within a wave. The orchestrator waits: reading
files or editing code while agents run conflicts with their edits.

Checkpoints go to the user. A plan whose agent returned "complete" with no
SUMMARY.md, or with no commits, did not complete. A `code-reviewer` reviews the
result before the phase can close, and critical findings block.

**Execution requires explicit authorization.** Creating, discussing and planning a
phase do not grant it.

### Verify — `/verify-work {N}`

Runs the configured checks as evidence, then spawns a fresh `verifier` to judge
the codebase goal-backward — the summaries are the claims under test, not the
evidence. A criterion that cannot be confirmed abstains rather than passing.

Gaps are either closed and re-verified, or recorded as todos with the user's
agreement. The roadmap is only ticked on a pass or an explicit acceptance.

### Ship — `/ship {N}`

Publishes verified work as a pull request. It is gated on `status: passed` for
the current revision, a clean tree, a non-protected branch and passing checks.
There is no bypass. Shipping publishes; it does not merge.

## 4. Close the milestone

`/complete-milestone` audits every phase for missing plans, summaries and
verification, refuses while any phase is open, then writes the MILESTONES.md entry
and marks the milestone shipped. `/milestone-summary` explains what shipped to
someone who was not there.

## Work that is not a phase

| Situation | Command |
|---|---|
| An idea surfaces mid-session | `/capture "<description>"` — parks it as a todo and returns you to the work |
| Reviewing what has piled up | `/capture --list [area]` — loads one todo and routes it |
| A change too small for a phase | `/quick "<description>"` — one plan, 1–3 tasks, atomic commits, tracked |

Quick tasks deliberately stay out of ROADMAP.md. If the work needs more than
three tasks or touches several subsystems, it is a phase.

## Knowing where you are

`/progress` derives progress from the roadmap, reports recent work, position,
decisions, blockers, pending todos and open quick tasks, then recommends one next
step. `/next` makes the same determination and proceeds.

Both check the same invariant first: the lowest-numbered phase whose plan files
outnumber its summary files has unfinished execution, and it is resumed ahead of
new work. An advanced STATE.md position is exactly when work gets silently
dropped.

## Artifacts a phase accumulates

```
.planning/phases/NN-slug/
  NN-CONTEXT.md          decisions, canonical refs, deferred ideas   (discuss)
  NN-DISCUSSION-LOG.md   what was asked and answered; audit only     (discuss)
  NN-RESEARCH.md         technical findings at a revision            (plan)
  NN-MM-PLAN.md          tasks, ownership, dependencies, must-haves  (plan)
  NN-MM-SUMMARY.md       what was built, with evidence               (execute)
  NN-VERIFICATION.md     what is actually true, with findings        (verify)
```

[Truth map](../truth-map.md) names the owner of each fact. When records disagree,
use [conflict rules](../RULES.md#documents-and-conflicts): establish which side is
wrong with evidence rather than reconciling silently.
