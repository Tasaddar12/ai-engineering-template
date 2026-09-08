# Architecture

## Product boundary

A reusable central Python package installs versioned framework assets into new or existing Git projects. Each project owns its requirements, decisions, history, commands, and autonomy policy. A local coordinator executes plans using interchangeable agent and hosting adapters. The first release does not require a database server, message broker, web UI, or distributed workers.

## Major abstractions

| Abstraction | Responsibility |
| --- | --- |
| Project / installation | Identity, compatibility, asset ownership, policy |
| Spec / ADR / research | Intended behavior, rationale, sourced evidence |
| Plan / task / graph revision | Acceptance, isolated scope, dependencies and supersession |
| Workflow run / attempt | Resumable execution, budgets, leases and side-effect intents |
| Worktree / Git snapshot | Observed workspace and immutable code revisions |
| Context bundle | Minimal, hashed inputs selected for a role |
| Agent adapter / agent run | Structured invocation, polling, cancellation and verified output |
| Command runner / evidence | Allowed processes and captured execution facts |
| Review / candidate | Checklist verdict bound to code and engineering context |
| Recovery proposal | Transactional graph rewrite with preserved lineage |
| Delivery / PR | Integration candidate, remote checks, approvals and observed merge |
| State store / reconciler | Serialized workflow intent and comparison against Git facts |

## Data and control

The coordinator owns a dedicated control worktree on `ai/state`. All canonical `.ai/` changes are checkpoint commits on that branch. Task worktrees branch from a plan integration commit and contain code changes only; their copied `.ai/` is a snapshot and never a live coordination store. Each agent receives an explicit control snapshot in its context bundle. Local outboxes and leases are under Git's common directory, outside tracked files.

A plan has a separate integration worktree/branch. The coordinator serially integrates accepted task commits there and records provenance. Dependencies start only after prerequisites are accepted and integrated into the task's base. Parallel unrelated tasks may start from the same earlier base. Every integration that changes the review base requires the affected task's two reviews and validation on a new candidate before acceptance; final plan review checks the full combined tree.

The state branch is retained and must be pushed when an authorized delivery publishes the plan. Delivery assembles a sanitized project-state snapshot into the plan PR. A fresh clone fetches the retained state branch to resume unmerged work. Offline/unpushed state is durable locally but unavailable to another machine; status must expose this limitation.

## Dependency direction

`cli -> workflows -> domain services -> ports`; adapters implement ports. Pure schema/domain/planning/review rules never call Git, providers, clocks, or the filesystem directly. `orchestration` schedules; `workflows` handles lifecycle steps. `git` reports facts; `worktrees` combines Git operations with ownership policy. `state` persists decisions; it never invents Git facts.

See [package boundaries](python.md), [persistence protocol](../state/persistence.md), [orchestration](../workflows/plan-implementation.md), and [ADRs](../../decisions/README.md).
