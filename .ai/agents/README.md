# Agent roles

These are Markdown role definitions, not a running multi-agent system. Every role
follows [approval](../policies/approval.md), the assigned scope and its workflow gates.

| Agent | Responsibility | Primary report |
| --- | --- | --- |
| [orchestrator](orchestrator.md) | User decisions, routing, assignments and shared state | Decision summary |
| [researcher](researcher.md) | Bounded evidence gathering | Research record |
| [planner](planner.md) | Scope, tasks, acceptance and dependencies | Plan |
| [implementor](implementor.md) | Approved changes and spec updates | Completion |
| [reviewer](reviewer.md) | Independent proposal/diff review | Review result |
| [tester](tester.md) | Agreed final checks and actual outcomes | Test result |
| [bug-reviewer](bug-reviewer.md) | Read-only triage and repair recommendation | Intake |
| [pr-agent](pr-agent.md) | PR preparation and authorized Git actions | PR summary |

The orchestrator owns live state and delivery coordination. Workers return evidence;
they do not grant themselves authority or accept their own work.
