# Schema catalog

Canonical files are `schemas/v1/*.schema.json`; JSON Schema Draft 2020-12, schema version `1.0`. Unknown keys are rejected. IDs and content hashes are portable; timestamps are UTC RFC 3339. Schema document IDs use an intentionally nonresolving domain; validation never retrieves them from the network.

| Schema | Purpose |
| --- | --- |
| [project-state](../../schemas/v1/project-state.schema.json) | Project state contract |
| [framework-installation](../../schemas/v1/framework-installation.schema.json) | Framework installation contract |
| [plan](../../schemas/v1/plan.schema.json) | Plan contract |
| [task](../../schemas/v1/task.schema.json) | Task contract |
| [task-graph](../../schemas/v1/task-graph.schema.json) | Task graph contract |
| [worktree](../../schemas/v1/worktree.schema.json) | Worktree contract |
| [workflow-run](../../schemas/v1/workflow-run.schema.json) | Workflow run contract |
| [agent-request](../../schemas/v1/agent-request.schema.json) | Agent request contract |
| [agent-run](../../schemas/v1/agent-run.schema.json) | Agent run contract |
| [agent-output](../../schemas/v1/agent-output.schema.json) | Agent output contract |
| [context-bundle](../../schemas/v1/context-bundle.schema.json) | Context bundle contract |
| [handoff](../../schemas/v1/handoff.schema.json) | Handoff contract |
| [candidate](../../schemas/v1/candidate.schema.json) | Candidate contract |
| [review-result](../../schemas/v1/review-result.schema.json) | Review result contract |
| [isolation-review](../../schemas/v1/isolation-review.schema.json) | Isolation review contract |
| [recovery](../../schemas/v1/recovery.schema.json) | Recovery contract |
| [research-item](../../schemas/v1/research-item.schema.json) | Research item contract |
| [adr-index](../../schemas/v1/adr-index.schema.json) | Adr index contract |
| [spec](../../schemas/v1/spec.schema.json) | Spec contract |
| [command-definition](../../schemas/v1/command-definition.schema.json) | Command definition contract |
| [command-evidence](../../schemas/v1/command-evidence.schema.json) | Command evidence contract |
| [policy](../../schemas/v1/policy.schema.json) | Policy contract |
| [pr-state](../../schemas/v1/pr-state.schema.json) | Pr state contract |
| [state-event](../../schemas/v1/state-event.schema.json) | State event contract |
| [archive-manifest](../../schemas/v1/archive-manifest.schema.json) | Archive manifest contract |
| [asset-manifest](../../schemas/v1/asset-manifest.schema.json) | Asset manifest contract |

Shape checks are necessary, not sufficient. See [semantic invariants](../state/semantic-invariants.md). Nullable fields explicitly represent unobserved facts. No nullable OID can satisfy a revision-bound gate. IDs, hashes and success flags in synthetic fixtures are not execution evidence.

The contract draft follows [JSON Schema 2020-12](https://json-schema.org/draft/2020-12), consulted 2026-09-05. The schema source is canonical; Python typed parsing must be tested for parity. Breaking changes require a schema version and migration; even additive fields need compatibility handling because unknown fields are rejected.
