# AI engineering orchestration template

This repository provides the Markdown instructions, records and optional hook
scripts used to plan, implement, verify and deliver approved engineering work.
Start with [AGENTS.md](AGENTS.md) and the [project description](.ai/state/PROJECT.md).

The [operating guide](.ai/README.md) explains the structure. Specs describe
current behavior, plans carry proposed changes, ADRs explain decisions, and
amendments and the journal retain history. [Truth map](.ai/truth-map.md) names
the owner of each fact; [config](.ai/config.yaml) defines paths and identifiers.

| Need | Entry point |
| --- | --- |
| Understand this checkout | [onboard](.ai/commands/onboard.md) |
| Report a finding for a decision | [report](.ai/commands/report.md) |
| See every plan and current blockers | [plan-status](.ai/commands/plan-status.md) |
| Plan a change or repair a defect | [plan-new](.ai/commands/plan-new.md), [fix](.ai/commands/fix.md) |
| Verify before delivery | [plan-verify](.ai/commands/plan-verify.md) |
| Coordinate several worktrees | [orchestration guide](docs/ORCHESTRATION.md) |
| Publish and clean up merged work | [deliver](.ai/commands/deliver.md) |

[Commands](.ai/commands/README.md) own the detailed procedures and show how to
combine them for common tasks; [agents](.ai/agents/README.md) define role scopes.
[Policies](.ai/policies/README.md) hold firm requirements and
[gates](.ai/gates/README.md) define pass/fail transitions. Copy a
[flat template](.ai/templates/README.md) when creating a record or report.

To use this in another project, follow [ADOPTING.md](docs/ADOPTING.md).
The slash-style names in these documents identify Markdown procedures;
copying this repository does not register commands, launch agents or install
hooks. Manual dispatch is configured. The optional
[hook scripts](.ai/hooks/README.md) need a compatible host and explicit setup.
There is no application package, dependency installer or CI pipeline here.
