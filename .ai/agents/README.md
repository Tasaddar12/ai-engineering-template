# Agent responsibilities

Read [RULES](../RULES.md) first. An assignment narrows a role's write scope.
These files are instructions, not installed dispatchers or permission controls.

| Role | Input | Result |
|---|---|---|
| [Coordinator](coordinator.md) | Human request, phase records, runtime evidence | Assignments, integration, status and authorized publication |
| [Researcher](researcher.md) | Phase questions and relevant sources | Reusable findings with evidence |
| [Phase preparer](phase-preparer.md) | CONTEXT, relevant research and current code | Bounded IMPLEMENT instructions and validation approach |
| [Phase checker](phase-checker.md) | Prepared phase and actual repository | Readiness findings; no checkout edits |
| [Coder](coder.md) | One implementation assignment | Committed changes, tests and SUMMARY |
| [Documentor](documentor.md) | Documentation assignment and implementation evidence | Committed verified documentation and SUMMARY |
| [Verifier](verifier.md) | Integrated phase at an assigned revision | Independent external verification report; no checkout edits |

The coordinator chooses which responsibilities are needed. Small phases do not
require every role. Runtime dispatch covers coders, documentors and the verifier;
discussion, research and preparation are coordinator-led procedures.
