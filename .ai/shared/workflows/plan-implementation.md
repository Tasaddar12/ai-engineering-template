# Plan implementation orchestrator

1. Resolve project, control branch, plan and run identity. Reconcile Git and any interrupted effects. Enforce version compatibility, policy, budgets, model profiles and adapter capabilities before dispatch.
2. Load current project summary and plan references. Context builder resolves explicit spec, ADR, research and contract references; missing required context blocks readiness rather than expanding to the entire history.
3. Validate task records, acceptance mappings, ownership and dependency edges. Invoke Task Isolation Reviewer. Apply approved rewrites transactionally, preserving prior graph and supersession.
4. Freeze an approved graph revision and digest. Topologically validate; detect cycles, unknown/self/cross-plan edges (cross-plan edges are deferred in v1), excluded superseded nodes and uncovered acceptance criteria.
5. Create plan integration branch/worktree from observed target revision. For each dependency-ready task, acquire scope/resource leases, record worktree/agent intents, create dedicated task branch/worktree, construct a hashed context bundle and dispatch an implementation invocation.
6. Schedule up to `max_parallel` workers with disjoint write scopes and semantic resource claims. Scope claims include contracts, database schemas, generated files and common registries. Dependencies wait until their prerequisite commits have been integrated and accepted.
7. Import implementation output; verify actual diff against allowed/prohibited scope and handoff, inspect clean committed head and run command-ID validation suites. The coordinator independently records execution outcomes.
8. Run fresh higher-capability R1; if passed, fresh independent R2. Retry defects within budgets. Structural triggers invoke recovery. Accepted results are bound to exact candidate and context.
9. Integrate one task at a time. If integration changes its base or content, form a new candidate and run targeted validation plus both task reviews again before updating accepted state. Integration conflicts go to recovery; do not let an integrator silently edit two task scopes. Hold dependents until acceptance is valid on the integrated base.
10. Once all live graph tasks are accepted, run full plan validation/E2E and independent higher-capability plan integration review on the combined revision. Missing work creates new tasks via recovery, never an untracked patch.
11. Prepare PR content and sanitized state snapshot. Continue publish/CI/repair only within configured authorization. Any CI repair is an isolated new/follow-up task with both reviews and refreshed integration gate. CI must refer to the current remote head.
12. Observe permitted merge, mark tasks/plan completed, retain checkpoints and archive manifests, clean only eligible worktrees, then reconcile current project state.

## Scheduling details

A bounded thread/async executor drives separate adapter invocations; this is concurrency, not a distributed service. Deterministic tie-break is task ID after dependency ordering. Ready tasks can proceed while a different branch is in repair. Graph mutation pauses and fences affected nodes and descendants; unaffected nodes may continue against unchanged graph inputs, but their results are revalidated against the new graph before import.

No exactly-once claim: dispatch is intent/reconcile/idempotency based. A provider without queryable idempotency must expose ambiguous outcome and pause that dispatch rather than duplicate it. Run-wide limits count attempts across replacement tasks to prevent replanning from resetting the budget.

## Example

A contract prerequisite T1 is integrated first. T2 (API adapter) and T3 (documentation parser) start on that accepted base with separate file/resource scopes. T2 integrates; T3 then rebases or merges onto the new integration head, obtains fresh candidate-bound reviews, and integrates. T4 consuming both starts only afterward. A newly discovered shared schema change becomes a prerequisite task and triggers graph re-review.
