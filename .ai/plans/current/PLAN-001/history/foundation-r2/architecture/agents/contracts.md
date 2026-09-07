# Agent invocation and output contracts

Every request is a schema-valid immutable object containing workflow/run/task/plan identity, role, graph revision, base/current code OIDs, logical worktree ID, host-resolved worktree path (ephemeral only), allowed/prohibited scope, explicit context documents/digests, commands, acceptance, handoff refs, checklist, model profile and autonomy permissions. Portable requests reference the worktree ID; adapters enrich paths locally.

Context construction selects required spec sections, current plan goals relevant to the task, accepted ADRs, source files, contract definitions and completed dependency handoffs. R2 additionally sees relevant sibling handoffs, interfaces/schema, plan assumptions and R1 report. Review roles receive a broader but still explicit manifest. A token budget overflow is resolved by referenced summaries with source hashes or an explicit context request; never silently truncate a required acceptance criterion.

Request output is an envelope with request/attempt identity, status, actual model provenance, result artifact references, discoveries, scope-change requests, command evidence and failure category. Validate it against the role schema and actual Git/command observations. Prose alone cannot advance a gate.

Implementation handoffs contain exact branch/commit/base, changed paths, tests/commands and validation results, assumptions, risks, deviations, interfaces changed, dependency notes and reviewer notes. Verify the changed-file list from Git, including renames/deletions. Validation success needs trusted runner evidence, not the author's claim.

Agent adapters support start/poll/cancel and declare structured-output, sandbox, model identity, idempotency and resume capabilities. Fake deterministic adapter ships first for tests. No provider is selected in phase one; production use must configure and capability-check one.

Model routing uses project-configured profiles (`implementation`, `review_high`, `planning`, `recovery`) with explicit ranked capability and provenance. Enforce `review_high.rank > implementation.rank`; separate fresh R1/R2 sessions and no downgrade fallback. Rank is a project policy assertion, not an objective benchmark. A requested exact model is bound at configuration time and verified against provider responses; this foundation makes no claim of access to a particular commercial model.

Permission grants are references to immutable project policy and a run-scoped subset. Agents cannot edit them. A context request or structural discovery returns to the coordinator; it is not permission to read credentials or edit another task's files.
