# Research a phase

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
