# Review guidance

Implementation review checks the task's acceptance criteria, behavior, error paths, focused tests, scope, security boundaries, and documentation. Consistency review independently checks the same candidate against the plan, specification, decisions, interfaces, sibling handoffs, and repository conventions.

Each review records its reviewer, exact candidate identity, evidence, findings, and verdict inside the selected plan. A changed graph, scope, dependency, interface, implementation, or relevant context invalidates earlier approval. Never rewrite an old failure into a pass.

Resolve the role using the [model selection guide](MODELS.md). Verify that the reviewer model's rank exceeds the model that actually implemented the candidate, including any development escalation. Use separate fresh invocations for the review stages and record actual model and effort; a default configuration is not invocation evidence.
