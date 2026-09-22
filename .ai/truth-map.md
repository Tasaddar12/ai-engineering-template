# Fact ownership

| Fact | Owner | Other documents |
|---|---|---|
| Project purpose and boundaries | [PROJECT](../.planning/PROJECT.md) | Reference applicable constraints |
| Desired outcomes | [REQUIREMENTS](../.planning/REQUIREMENTS.md) | Map them to phases |
| Phase order and navigation | [ROADMAP](../.planning/ROADMAP.md) | Link to the phase |
| Exact scope, acceptance, decisions and authorization | `NN-CONTEXT.md` | Reference acceptance IDs and decisions |
| What was discussed | Required `NN-DISCUSSION-LOG.md` | Do not infer decisions from transcripts |
| Technical findings at a revision | Optional `NN-RESEARCH.md` and `.planning/codebase/` maps | Verify relevant findings before reuse |
| Plan actions, ownership, prerequisites and checks | `NN-MM-PLAN.md` | Dispatch the committed assignment |
| A plan's observed result | `NN-MM-SUMMARY.md` | Use commits and actual evidence |
| Checking strategy | `NN-VALIDATION.md` when needed | Executable commands live in config/instructions |
| Independent phase assessment | `NN-VERIFICATION.md` | Summaries do not replace verification |
| Captured ideas not yet scoped | `.planning/todos/pending/` | Fold them in through discussion, never silently |
| Small changes outside the roadmap | `.planning/quick/{id}/QUICK.md` | Quick tasks never enter ROADMAP.md |
| What a milestone shipped | `.planning/MILESTONES.md` | Written by `milestone.complete`, not by hand |
| Continuation guidance | Optional `.continue-here.md` | Reconcile with actual Git/process state |
| Compact current summary | [STATE](../.planning/STATE.md) | Derived; does not override evidence |
| Phase-level desired behavior | `NN-SPEC.md` using the complete `spec.md` template | Reference from CONTEXT canonical references |
| Current correct behavior | `.planning/specs/SPEC-*.md` | Reference contracts instead of copying them |
| Significant rationale | `.planning/decisions/ADR-*.md` | Accepted decisions govern; superseded ones are history |
| Whether a proposed technology works | The evidence recorded in the decision's rationale | A check that was run, not a claim that it would pass |
| Durable decision log | [PROJECT](../.planning/PROJECT.md) Key Decisions | STATE.md keeps only the 5 most recent |
| Whether a requirement is met | [REQUIREMENTS](../.planning/REQUIREMENTS.md) Traceability Status | Written by `requirements.*` on a passing verification |
| Whether a codebase map still holds | `codebase.status`, from the commit that last wrote it | A date says when someone looked, not whether the code moved |
| Ordinary change history | Git and phase artifacts | No duplicate journal required |
| Project usage/operations guidance | The project's established documentation paths | Link to the relevant guide |
| Shared rules | [RULES](RULES.md) | Link rather than restating |
| Whether a dispatch is isolated | `dispatch-isolation`, recorded by the runtime | Workflows branch on the result, never on the host name |
| What an isolated wave produced | The wave manifest and `worktree.merge-wave` | Summaries do not establish that a branch merged |
| Role scope, inputs and outputs | [agents](agents/README.md) | Assign a responsibility |
| Workflow entry points | [commands](commands/README.md) | Mirrored one-for-one by `.agents/skills/` |
| Workflow procedure | `workflows/*.md` | The command names it; the workflow owns it |
| Artifact and handoff contract details | `references/` | Load only when relevant |
| Skill discovery and installation | [install](commands/install.md) | Skills install at each host's discovery location |
| Commit behavior, model overrides and project checks | [config](../.planning/config.yaml) | Avoid duplicating defaults |
| Runtime verb interface | [runtime](runtime/README.md) | Use verified verb spellings |
| Phase numbering, roadmap structure, derived counters | The runtime | Never hand-edit what a verb owns |

The phase artifacts above live together under `.planning/phases/NN-slug/`.
Use [conflict rules](RULES.md#documents-and-conflicts) when sources disagree.
Code and observed checks establish implementation evidence; neither silently
redefines the desired outcome.
