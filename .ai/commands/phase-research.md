# Research a phase

Research never starts implementation. A recommended approach or next action
cannot authorize phase execution; follow
[phase authority](../RULES.md#phase-authority).

Read [RULES](../RULES.md), CONTEXT and the actual relevant code. The coordinator
assigns bounded questions to the [researcher](../agents/researcher.md).

Find existing entry points, callers, interfaces, patterns and tests. Investigate
technical unknowns and external primary sources where needed. Consider what
must be validated and documented, not just what code to write.

Write RESEARCH only when it saves subsequent work. Include source revision,
findings, evidence, options, recommended boundaries, risks and unresolved choices.
Link relevant codebase maps; refresh stale areas rather than copying them.
Research informs decisions but cannot override CONTEXT.

The coordinator records any resolved choices in CONTEXT and routes remaining
questions. Commit authorized findings and continue to [prepare](phase-prepare.md).
A research-only phase can conclude with supported findings without claiming code
implementation, acceptance of unknown behavior or merged delivery.

## Full research method

Read [research](../templates/research.md) and the
[researcher](../agents/researcher.md). Preserve locked decisions,
primary sources, version/compatibility evidence, recommendations and uncertainty
in the actual result. Project-wide research can use the complete
[research-project templates](../templates/research-project/). Distinguish the
question being answered from background information; link the evidence the planner
will need instead of replacing it with a confidence claim. Follow the
[local adaptation](../references/agent-adaptation.md) for host-specific tools.
