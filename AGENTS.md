# Agent entry point

Before acting, read [.ai/RULES.md](.ai/RULES.md), then the owners listed in
[.ai/truth-map.md](.ai/truth-map.md), current [state](.ai/state/STATE.md), and your
role under [.ai/agents](.ai/agents). Follow the relevant [.ai/policies](.ai/policies/README.md)
and evaluate the [.ai/gates](.ai/gates/README.md) named by the selected workflow.

**Hard requirement:** follow the report, templated summary and user-decision gate in
RULES.md. A bug report or a request to fix something does not skip that gate.
Use [.ai/templates/decision-summary.md](.ai/templates/decision-summary.md) for the
user-facing output. Wait for yes, no, or requested changes before the stated action.

Operate only in the assigned worktree. Read the selected plan and relevant specs
before implementation. Rules, authority and fact ownership are defined in `.ai`;
this file is an entry point, not a second rulebook.
