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
| [e2e](e2e.md) | Agreed user journeys across system boundaries | Test result |
| [decoupler](decoupler.md) | Bounded tasks, interfaces and dependency order | Proposed assignments |
| [bug-reviewer](bug-reviewer.md) | Evidence triage and repair recommendation | Intake or confirmed FIX |
| [pr-agent](pr-agent.md) | PR preparation and authorized Git actions | PR summary |

The orchestrator owns live state and delivery coordination. Workers return evidence;
they do not grant themselves authority or accept their own work.
