# Command procedures

These Markdown files are instructions an assistant can follow. They do not
register slash commands or install a host dispatcher. A user can name a procedure
or ask for the same work in ordinary language. The Python CLI supplies the
executable steps; see [runtime](../runtime/README.md).

| Procedure | Purpose | CLI where applicable |
|---|---|---|
| [onboard](onboard.md) | Establish project context, intent and real checks | Inspection and authorized edits |
| [worktree](worktree.md) | Assign an isolated checkout | Git worktree operations |
| [phase-new](phase-new.md) | Receive a request into a stable phase | `new` |
| [phase-discuss](phase-discuss.md) | Resolve scope, decisions and acceptance | Coordinator edits |
| [phase-research](phase-research.md) | Investigate relevant questions | Research assignment |
| [phase-prepare](phase-prepare.md) | Define and check bounded components | `check` |
| [phase-start](phase-start.md) | Execute ready component assignments | `run` |
| [phase-verify](phase-verify.md) | Independently assess the integrated outcome | `verify` |
| [phase-uat](phase-uat.md) | Preserve human acceptance observations | `uat` |
| [phase-status](phase-status.md) | Report evidence and next action | `status` |
| [phase-resume](phase-resume.md) | Reconcile interrupted execution | `resume` |
| [phase-ship](phase-ship.md) | Publish a verified PR within authorization | `publish` |

All procedures follow [RULES](../RULES.md). Read-only operations need no new
worktree or commit. Tracked mutations use the assigned worktree. Related
preparation, implementation and documentation normally share one phase PR.
