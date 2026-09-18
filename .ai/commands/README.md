# Command procedures

These Markdown files are the command surface. Each one mirrors the skill of the
same name under `.agents/skills/` — same contract, same routing — so a host that
registers slash commands and a host that discovers skills behave identically.

A command does not perform the work. It names the workflow under
[`../workflows/`](../workflows/) that holds the step-by-step procedure, and that
workflow performs every record mutation through the
[phase runtime](../runtime/README.md) rather than editing planning files by hand.

| Command | Purpose | Workflow |
|---|---|---|
| [install](install.md) | Install into a new or existing project and bootstrap Git | Standalone `.ai/install.py` |
| [onboard](onboard.md) | Initialize PROJECT.md, REQUIREMENTS.md and a phased ROADMAP.md | onboard |
| [phase](phase.md) | Add, insert, remove or edit phases in the roadmap | add-phase, insert-phase, remove-phase, edit-phase |
| [discuss-phase](discuss-phase.md) | Capture the decisions a phase needs before planning | discuss-phase |
| [plan-phase](plan-phase.md) | Turn decisions into executable plans, checked goal-backward | plan-phase |
| [execute-phase](execute-phase.md) | Run a phase's plans in dependency waves, then review the code | execute-phase |
| [verify-work](verify-work.md) | Verify the phase delivered its goal, close or record gaps | verify-work |
| [new-milestone](new-milestone.md) | Open a milestone and break it into phases | new-milestone |
| [complete-milestone](complete-milestone.md) | Close a milestone and record what shipped | complete-milestone |
| [milestone-summary](milestone-summary.md) | Explain a milestone to someone who was not there | milestone-summary |
| [capture](capture.md) | Capture a todo, or review pending todos with `--list` | add-todo, check-todos |
| [quick](quick.md) | Make one small change with a plan, commits and tracked state | quick |
| [progress](progress.md) | Report where the project stands and recommend the next step | progress |
| [next](next.md) | Detect state and advance to the next step | next |
| [ship](ship.md) | Publish verified phase work as a pull request | ship |

## The lifecycle

```
/onboard                   initialize the project          → PROJECT / REQUIREMENTS / ROADMAP
/phase "<description>"     add the phase to the roadmap
  → /discuss-phase {N}     capture decisions        → {NN}-CONTEXT.md
  → /plan-phase {N}        research and plan        → {NN}-{MM}-PLAN.md
  → /execute-phase {N}     implement                → {NN}-{MM}-SUMMARY.md
  → /verify-work {N}       confirm the goal is met  → {NN}-VERIFICATION.md
  → /ship {N}              publish the verified work       → pull request
  → /complete-milestone    when the milestone's phases are all done
```

`/progress` reports and recommends. `/next` decides and proceeds.
`/quick` sits outside this loop for changes too small to warrant a phase, and
`/capture` parks anything that surfaces without derailing the current work.

## Layering

All procedures follow [RULES](../RULES.md). The
[agent methods](../agents/README.md) define the roles a workflow dispatches and
what each returns. The [template catalog](../templates/README.md) holds the
artifact shapes those agents produce.

A command file naming a workflow is not proof the host registered a slash
command; a user can equally name the procedure in ordinary language.
