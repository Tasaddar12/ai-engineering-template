# Fact ownership

| Fact | Owner | Other documents |
|---|---|---|
| Project purpose and boundaries | [PROJECT](PROJECT.md) | Reference applicable constraints |
| Desired outcomes | [REQUIREMENTS](REQUIREMENTS.md) | Map them to phases |
| Phase order and navigation | [ROADMAP](ROADMAP.md) | Link to the phase |
| Exact scope, acceptance, decisions and authorization | `NN-CONTEXT.md` | Reference acceptance IDs and decisions |
| What was discussed | Optional `NN-DISCUSSION-LOG.md` | Do not infer decisions from transcripts |
| Technical findings at a revision | Optional `NN-RESEARCH.md` and `codebase/` maps | Verify relevant findings before reuse |
| Component actions, ownership, prerequisites and checks | `NN-CC-IMPLEMENT.md` | Dispatch the committed assignment |
| Component's observed result | `NN-CC-SUMMARY.md` | Use commits and actual evidence |
| Checking strategy | `NN-VALIDATION.md` when needed | Executable commands live in config/instructions |
| Independent phase assessment | `NN-VERIFICATION.md` | Summaries do not replace verification |
| User acceptance observations | `NN-UAT.md` when applicable | Preserve pending, failed and blocked cases |
| Processes, integration and checkpoints | Operational state in Git common directory | Inspect through runtime status |
| Continuation guidance | Optional `.continue-here.md` | Reconcile with actual Git/process state |
| Compact current summary | [STATE](STATE.md) | Derived; does not override evidence |
| Current correct behavior | `specs/SPEC-*.md` | Reference contracts instead of copying them |
| Significant rationale | `decisions/ADR-*.md` | Accepted decisions govern; superseded ones are history |
| Ordinary change history | Git and phase artifacts | No duplicate journal required |
| Human usage/operations guidance | `docs/` | Link to the relevant guide |
| Shared rules | [RULES](RULES.md) | Link rather than restating |
| Role scope, inputs and outputs | [agents](agents/README.md) | Assign a responsibility |
| Workflow procedure | [commands](commands/README.md) | Entry points load the procedure |
| Reusable detailed method | `references/` | Load only when relevant |
| Commands, capacity and worker routes | [config](config.yaml) | Avoid duplicating defaults |
| CLI interface | [runtime](runtime/README.md) | Use verified syntax |

The phase artifacts above live together under `phases/NN-slug/`.
Use [conflict rules](RULES.md#documents-and-conflicts) when sources disagree.
Code and observed checks establish implementation evidence; neither silently
redefines the desired outcome.
