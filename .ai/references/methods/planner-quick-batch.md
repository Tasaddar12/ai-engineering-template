# Bounded Batch Planning — Planner Reference

Use when a coordinator supplies a catalog of small, related phase components.
Each worker prepares one bounded plan with 1-3 tasks. There is no separate quick
runtime or batch registry: every executable plan follows the complete
[runtime contract](../../runtime/TEMPLATE-CONTRACT.md).

## Dependencies — reference assigned sibling plan IDs

The catalog names relevant components and their objectives. If a component
consumes another component's output, use that exact sibling ID in `depends_on`.
Never invent IDs, refer to another phase's component as a local dependency, or
include the current component itself. Independent plans use `depends_on: []`.
Cross-phase prerequisites belong in phase CONTEXT through the coordinator.

```yaml
depends_on: ["03-01"]
files_modified: ["src/foo.ts", "tests/foo.test.ts"]
```

## Ownership — declare every path the component touches

`files_modified` lists exact files or directory prefixes ending in `/`.
`files_deleted` names exact deleted files separately; no implicit deletion grant.
Shared paths and exclusive resources serialize in the local runner even if two
plans share a displayed wave. Keep declarations accurate after revisions.

```yaml
files_deleted: ["legacy/old-module.ts"]
resources: ["integration-test-database"]
```

## Complete contract

Small scope does not waive nonempty requirements, acceptance, documentation,
meaningful argv checks, autonomous metadata or complete task/verification/output
sections. `must_haves` expresses observable outcomes and important wiring;
`user_setup` lists actual unresolved external prerequisites. Do not manufacture
requirements for standalone maintenance that has no phase; return the bounded
assignment to its coordinator instead of creating project identity records.
